"""
=============================================================================
  ADAPTIVE BED DETECTOR — Grid menyesuaikan tepi plant bed secara otomatis
  Standalone: uji dengan video HP top-down / webcam, tanpa ubah script lain.
=============================================================================
  CARA PAKAI:
    python adaptive_bed.py video_hp.mp4            # mode adaptive (default)
    python adaptive_bed.py video_hp.mp4 --manual   # klik 4 sudut manual
    python adaptive_bed.py video_hp.mp4 --step 3   # proses tiap frame ke-3
    python adaptive_bed.py video_hp.mp4 --save     # simpan video beranotasi
    python adaptive_bed.py video_hp.mp4 --no-gui   # headless (server/RPi)
    python adaptive_bed.py 0                       # dari webcam/kamera

  KONTROL (mode GUI):
    Q = keluar   S = snapshot PNG

  ALUR:
    1. Frame pertama → deteksi otomatis 4 sudut bed (Canny Edge → approx quad;
       jalur cadangan maska HSV bila Canny gagal)
    2. Gagal? → fallback klik manual 4 sudut
    3. Setiap frame: warp perspektif ke kanvas 1200x660 (2m x 1.1m)
       → grid 4x6 → segmentasi tanaman → coverage & status per zona
    4. Sudut dihaluskan EMA (anti-gemetar) + re-deteksi tiap --detect-every

  Basis metode: deteksi tepi Canny (Canny 1986) + aproksimasi quad +
  segmentasi warna HSV (Searson 2017; Yang 2015) + homografi 4-titik.
=============================================================================
"""

import cv2
import numpy as np
import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kangkung_cv import (BED_CONFIG, HSV_KANGKUNG, get_status,
                         get_kesehatan, parameter_adaptif,
                         segmentasi_hijau_adaptif)

# ─── Konfigurasi ─────────────────────────────────────────────────────────────
KANVAS_W, KANVAS_H = 1200, 660          # kanvas warp tetap (2m x 1.1m)
DST_QUAD = np.float32([[0, 0], [KANVAS_W - 1, 0],
                       [KANVAS_W - 1, KANVAS_H - 1], [0, KANVAS_H - 1]])
MAX_LEBAR = 1280                        # batas lebar frame input (hemat CPU)
SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "output" / "video"


# ─── UTILITAS GEOMETRI ───────────────────────────────────────────────────────

def urutkan_sudut(pts):
    """Urutkan 4 titik → [TL, TR, BR, BL]."""
    pts = np.asarray(pts, dtype=np.float32)
    s = pts.sum(axis=1)                      # x+y : min=TL, max=BR
    d = np.diff(pts, axis=1).ravel()         # y-x : min=TR, max=BL
    return np.float32([pts[np.argmin(s)], pts[np.argmin(d)],
                       pts[np.argmax(s)], pts[np.argmax(d)]])


class CornerSmoother:
    """Stabilisasi sudut antar-frame via Exponential Moving Average."""

    def __init__(self, alpha=0.2):
        self.alpha = alpha
        self.pts = None

    def update(self, pts):
        pts = np.asarray(pts, dtype=np.float32)
        if self.pts is None:
            self.pts = pts.copy()
        else:
            self.pts = self.alpha * pts + (1 - self.alpha) * self.pts
        return self.pts.copy()


# ─── DETEKSI OTOMATIS (OPSI A: CANNY EDGE + FALLBACK HSV) ────────────────────

def _intersect_lines(l1, l2):
    """Titik potong dua garis (vx, vy, x0, y0) atau None jika sejajar."""
    vx1, vy1, x1, y1 = l1
    vx2, vy2, x2, y2 = l2
    det = vx1 * (-vy2) - vy1 * (-vx2)
    if abs(det) < 1e-6:
        return None
    t = ((x2 - x1) * (-vy2) - (y2 - y1) * (-vx2)) / det
    return (float(x1 + t * vx1), float(y1 + t * vy1))


def validasi_quad(pts, w, h, min_area_ratio=0.12, max_area_ratio=0.94):
    """Validasi geometri quad: konveks, dalam batas frame, sudut & rasio bed."""
    if pts is None or len(pts) != 4:
        return False
    pts = urutkan_sudut(pts)
    if not cv2.isContourConvex(pts.astype(np.float32)):
        return False
    xs, ys = pts[:, 0], pts[:, 1]
    if (xs.min() < -w * 0.10 or ys.min() < -h * 0.08 or
            xs.max() > w * 1.12 or ys.max() > h * 1.12):
        return False
    frac = cv2.contourArea(pts.astype(np.float32)) / float(max(1, w * h))
    if frac < min_area_ratio or frac > max_area_ratio:
        return False

    for i in range(4):
        p0 = pts[i]
        v1, v2 = pts[(i - 1) % 4] - p0, pts[(i + 1) % 4] - p0
        n1, n2 = float(np.linalg.norm(v1)), float(np.linalg.norm(v2))
        if n1 < 25.0 or n2 < 25.0:
            return False
        ang = float(np.degrees(np.arccos(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))))
        if ang < 50.0 or ang > 130.0:
            return False

    w_top = float(np.linalg.norm(pts[1] - pts[0]))
    w_bot = float(np.linalg.norm(pts[2] - pts[3]))
    h_lt = float(np.linalg.norm(pts[3] - pts[0]))
    h_rt = float(np.linalg.norm(pts[2] - pts[1]))
    w_avg, h_avg = 0.5 * (w_top + w_bot), 0.5 * (h_lt + h_rt)
    if h_avg < 30.0 or w_avg < 40.0 or not (1.10 <= (w_avg / h_avg) <= 3.20):
        return False
    if max(w_top, w_bot) / max(1.0, min(w_top, w_bot)) > 2.1:
        return False
    if max(h_lt, h_rt) / max(1.0, min(h_lt, h_rt)) > 2.1:
        return False
    return True


def _deteksi_canny_contour_quad(frame, canny_lo=None, canny_hi=None,
                                min_area_ratio=0.12):
    """Canny Edge -> kontur tertutup -> approxPolyDP 4 titik tervalidasi."""
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    if canny_lo is not None and canny_hi is not None:
        thresholds = [(int(canny_lo), int(canny_hi))]
    else:
        med = float(np.median(blur))
        thresholds = [
            (max(15, int(0.40 * med)), min(190, int(1.25 * med))),
            (20, 60),
            (40, 120),
        ]

    best, best_area = None, 0.0
    k3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    for lo, hi in thresholds:
        edges = cv2.morphologyEx(cv2.Canny(blur, lo, hi), cv2.MORPH_CLOSE, k3)
        cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            area = cv2.contourArea(c)
            if area < min_area_ratio * w * h or area > 0.90 * w * h:
                continue
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) != 4:
                continue
            pts = urutkan_sudut(approx.reshape(-1, 2).astype(np.float32))
            if not validasi_quad(pts, w, h, min_area_ratio=min_area_ratio,
                                 max_area_ratio=0.90):
                continue
            xs, ys = pts[:, 0], pts[:, 1]
            touches = (int(xs.min() <= 4) + int(ys.min() <= 4) +
                       int(xs.max() >= w - 5) + int(ys.max() >= h - 5))
            if touches >= 3:
                continue
            if area > best_area:
                best_area, best = area, pts
    return best


def _extract_side_lines(edge_mask, orient, ws, hs, scale, side_name, limit=5):
    """Fit top-K garis lurus teratas pada masker tepi Canny terarah via Hough+Huber."""
    py, px = np.where(edge_mask > 0)
    if len(px) < 8:
        return []
    pts_eval = np.column_stack([px, py]).astype(np.float32)

    em = cv2.dilate(edge_mask, np.ones((3, 3), np.uint8))
    min_len = max(10, int((ws * 0.05) if orient == "H" else (hs * 0.045)))
    lines = cv2.HoughLinesP(em, 1, np.pi / 180, threshold=10,
                            minLineLength=min_len,
                            maxLineGap=max(10, int(35 * scale)))
    if lines is None:
        return []

    segs = lines[:, 0].astype(np.float32)
    dx, dy = segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1]
    L = np.hypot(dx, dy)
    ang = np.degrees(np.arctan2(np.abs(dy), np.abs(dx)))
    ok = (L >= 5.0) & ((ang <= 24.0) if orient == "H" else (ang >= 44.0))
    segs, dx, dy, L = segs[ok], dx[ok], dy[ok], L[ok]
    if len(segs) == 0:
        return []
    if len(segs) > 36:
        order = np.argsort(L)[::-1][:36]
        segs, dx, dy, L = segs[order], dx[order], dy[order], L[order]

    vx, vy = dx / L, dy / L
    tol = max(2.5, 4.5 * scale)
    dist = np.abs(vx[:, None] * (py[None, :] - segs[:, 1:2]) -
                  vy[:, None] * (px[None, :] - segs[:, 0:1]))
    inl_mat = dist <= tol

    cands = []
    for i in range(len(segs)):
        inl = inl_mat[i]
        cnt = int(inl.sum())
        if cnt < 8:
            continue
        in_pts = pts_eval[inl]
        proj = ((in_pts[:, 0] - segs[i, 0]) * vx[i] +
                (in_pts[:, 1] - segs[i, 1]) * vy[i])
        span = float(proj.max() - proj.min())
        if span < 18.0:
            continue
        n_bins = max(5, int(span / max(5.0, 10.0 * scale)))
        hist, _ = np.histogram(proj, bins=n_bins,
                               range=(float(proj.min()), float(proj.max())))
        cont = float((hist > 0).mean())
        if side_name == "left":
            outer_b = 1.0 + 0.35 * max(0.0, 1.0 - in_pts[:, 0].mean() / (ws * 0.42))
        elif side_name == "right":
            outer_b = 1.0 + 0.35 * max(0.0, (in_pts[:, 0].mean() - ws * 0.58) / (ws * 0.42))
        elif side_name == "top":
            outer_b = 1.0 + 0.25 * max(0.0, 1.0 - in_pts[:, 1].mean() / (hs * 0.50))
        else:
            outer_b = 1.0 + 0.25 * max(0.0, (in_pts[:, 1].mean() - hs * 0.50) / (hs * 0.50))
        norm_len = ws * 0.65 if orient == "H" else hs * 0.55
        sc = cnt * (0.3 + 0.7 * cont) * min(1.0, span / norm_len) * outer_b
        cands.append((sc, span, in_pts))

    cands.sort(key=lambda x: x[0], reverse=True)
    out = []
    for sc, span, in_pts in cands:
        fx, fy, x0, y0 = cv2.fitLine(in_pts, cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
        fx, fy, x0, y0 = float(fx), float(fy), float(x0), float(y0)
        if orient == "H":
            t_m = (ws * 0.5 - x0) / fx if abs(fx) > 1e-4 else 0.0
            pos, slope = y0 + t_m * fy, (fy / fx if abs(fx) > 1e-4 else 0.0)
        else:
            t_m = (hs * 0.5 - y0) / fy if abs(fy) > 1e-4 else 0.0
            pos, slope = x0 + t_m * fx, (fx / fy if abs(fy) > 1e-4 else 0.0)
        if any(abs(pos - up) < max(5.0, 12.0 * scale) and abs(slope - us) < 0.06
               for _, _, _, up, us in out):
            continue
        out.append((sc, span, (fx, fy, x0, y0), pos, slope))
        if len(out) >= limit:
            break
    return out


def _deteksi_canny_rim_quad(frame, canny_lo=None, canny_hi=None,
                            min_area_ratio=0.12):
    """
    Deteksi 4 sisi tepi bed dari Canny Edge pada bingkai berlawanan dengan
    interior bed, tangguh terhadap pantulan langit & oklusi daun sebagian.
    """
    h, w = frame.shape[:2]
    scale = min(1.0, 512.0 / w)
    fr = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1.0 else frame
    hs, ws = fr.shape[:2]

    gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    hsv = cv2.cvtColor(cv2.GaussianBlur(fr, (5, 5), 0), cv2.COLOR_BGR2HSV)
    H_ch, S_ch, V_ch = cv2.split(hsv)
    V_i16 = V_ch.astype(np.int16)

    rim_raw = (((S_ch <= 75) & (V_ch >= 126)) |
               ((S_ch <= 45) & (V_ch >= 112))).astype(np.uint8) * 255
    rim_solid = cv2.morphologyEx(
        rim_raw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
    rim_solid = cv2.morphologyEx(
        rim_solid, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    is_rim = rim_solid > 0

    is_green = (H_ch >= 25) & (H_ch <= 92) & (S_ch >= 42) & (V_ch >= 35)
    is_water = (V_ch <= 145) & (S_ch <= 60) & (~is_rim)
    is_bed_in = is_green | is_water | ((V_ch <= 120) & (~is_rim))
    is_red_soil = ((H_ch <= 18) | (H_ch >= 165)) & (S_ch >= 75) & (V_ch >= 50)
    is_pond_tarp = (H_ch >= 78) & (H_ch <= 105) & (S_ch >= 85) & (V_ch <= 155)

    if canny_lo is None or canny_hi is None:
        med = float(np.median(blur))
        canny_lo = int(max(18, 0.40 * med))
        canny_hi = int(min(190, 1.25 * med))

    edges = cv2.Canny(blur, canny_lo, canny_hi)
    n_lbl, lbl, stats, _ = cv2.connectedComponentsWithStats(edges, connectivity=8)
    valid_cc = np.zeros(n_lbl, dtype=np.uint8)
    if n_lbl > 1:
        keep_cc = (
            (np.maximum(stats[1:, cv2.CC_STAT_WIDTH], stats[1:, cv2.CC_STAT_HEIGHT])
             >= max(8, int(18 * scale))) |
            (stats[1:, cv2.CC_STAT_AREA] >= max(10, int(20 * scale)))
        )
        valid_cc[1:] = keep_cc.astype(np.uint8) * 255
    ed = valid_cc[lbl]

    ys_e, xs_e = np.where(ed > 0)
    keep = (xs_e > 2) & (xs_e < ws - 3) & (ys_e > 2) & (ys_e < hs - 3)
    xs_e, ys_e = xs_e[keep], ys_e[keep]
    if len(xs_e) < 30:
        return None

    o1, o2 = max(3, int(9 * scale)), max(6, int(17 * scale))
    yu1, yu2 = np.clip(ys_e - o1, 0, hs - 1), np.clip(ys_e - o2, 0, hs - 1)
    yd1, yd2 = np.clip(ys_e + o1, 0, hs - 1), np.clip(ys_e + o2, 0, hs - 1)
    xl1, xl2 = np.clip(xs_e - o1, 0, ws - 1), np.clip(xs_e - o2, 0, ws - 1)
    xr1, xr2 = np.clip(xs_e + o1, 0, ws - 1), np.clip(xs_e + o2, 0, ws - 1)

    step_t = (np.maximum(V_i16[yu1, xs_e], V_i16[yu2, xs_e]) - V_i16[yd1, xs_e]) >= 12
    step_b = (np.maximum(V_i16[yd1, xs_e], V_i16[yd2, xs_e]) - V_i16[yu1, xs_e]) >= 12
    step_l = (np.maximum(V_i16[ys_e, xl1], V_i16[ys_e, xl2]) - V_i16[ys_e, xr1]) >= 12
    step_r = (np.maximum(V_i16[ys_e, xr1], V_i16[ys_e, xr2]) - V_i16[ys_e, xl1]) >= 12

    side_idx = {
        "top": (is_rim[yu1, xs_e] | is_rim[yu2, xs_e]) & step_t & (is_bed_in[yd1, xs_e] & ~is_rim[yd1, xs_e]) & (~is_green[yu1, xs_e]) & (ys_e < hs * 0.55),
        "bot": (is_rim[yd1, xs_e] | is_rim[yd2, xs_e]) & step_b & (is_bed_in[yu1, xs_e] & ~is_rim[yu1, xs_e]) & (~is_green[yd1, xs_e]) & (ys_e > hs * 0.45),
        "left": (is_rim[ys_e, xl1] | is_rim[ys_e, xl2]) & step_l & (is_bed_in[ys_e, xr1] & ~is_rim[ys_e, xr1]) & (~is_green[ys_e, xl1]) & (xs_e < ws * 0.42),
        "right": (is_rim[ys_e, xr1] | is_rim[ys_e, xr2]) & step_r & (is_bed_in[ys_e, xl1] & ~is_rim[ys_e, xl1]) & (~is_green[ys_e, xr1]) & (xs_e > ws * 0.58),
    }

    masks = {}
    for k, idx in side_idx.items():
        m = np.zeros((hs, ws), dtype=np.uint8)
        m[ys_e[idx], xs_e[idx]] = 255
        masks[k] = m

    c_top = _extract_side_lines(masks["top"], "H", ws, hs, scale, "top", limit=5)
    c_bot = _extract_side_lines(masks["bot"], "H", ws, hs, scale, "bot", limit=5)
    c_lt = _extract_side_lines(masks["left"], "V", ws, hs, scale, "left", limit=5)
    c_rt = _extract_side_lines(masks["right"], "V", ws, hs, scale, "right", limit=5)

    # Jika tepi kanan tertutupi tajuk daun, tambahkan kandidat garis tepi struktural luar
    rt_used_struct = False
    if max((sp for _, sp, _, _, _ in c_rt), default=0.0) < hs * 0.60:
        not_canopy = (~(is_green[ys_e, xl1] & is_green[ys_e, xr1]) &
                      ~is_red_soil[ys_e, xl1] & ~is_red_soil[ys_e, xr1])
        rt_struct = np.zeros((hs, ws), dtype=np.uint8)
        x_lo = int(ws * 0.78)
        sel = not_canopy & (xs_e >= x_lo) & (xs_e < int(ws * 0.96))
        rt_struct[ys_e[sel], xs_e[sel]] = 255
        for item in _extract_side_lines(rt_struct, "V", ws, hs, scale, "right", limit=2):
            if not any(abs(item[3] - up) < max(5.0, 12.0 * scale) and
                       abs(item[4] - us) < 0.06 for _, _, _, up, us in c_rt):
                c_rt.append(item)
                rt_used_struct = True

    if not (c_top and c_bot and c_lt and c_rt):
        return None

    sw, sh = 120, 68
    sx, sy = sw / ws, sh / hs
    green_s = cv2.resize(is_green.astype(np.uint8), (sw, sh), interpolation=cv2.INTER_NEAREST) > 0
    bed_s = cv2.resize(is_bed_in.astype(np.uint8), (sw, sh), interpolation=cv2.INTER_NEAREST) > 0
    rim_s = cv2.resize(is_rim.astype(np.uint8), (sw, sh), interpolation=cv2.INTER_NEAREST) > 0
    soil_s = cv2.resize(is_red_soil.astype(np.uint8), (sw, sh), interpolation=cv2.INTER_NEAREST) > 0
    pond_s = cv2.resize(is_pond_tarp.astype(np.uint8), (sw, sh), interpolation=cv2.INTER_NEAREST) > 0
    tot_green = max(1, int(green_s.sum()))

    k_hit = np.ones((5, 5), np.uint8)
    edge_hits = {k: cv2.dilate(masks[k], k_hit) > 0 for k in masks}
    if rt_used_struct:
        edge_hits["right"] = edge_hits["right"] | (cv2.dilate(rt_struct, k_hit) > 0)

    def _edge_support(pa, pb, hit_map):
        ts = np.linspace(0.05, 0.95, 17)
        xs = np.round(pa[0] + ts * (pb[0] - pa[0])).astype(int)
        ys = np.round(pa[1] + ts * (pb[1] - pa[1])).astype(int)
        v = (xs >= 0) & (xs < ws) & (ys >= 0) & (ys < hs)
        return float(hit_map[ys[v], xs[v]].mean()) if v.sum() >= 4 else 0.0

    qmask = np.zeros((sh, sw), dtype=np.uint8)
    best_pts, best_score = None, -1e9
    lt_lines = [it[2] for it in c_lt]
    rt_lines = [it[2] for it in c_rt]
    for _, _, lt, _, _ in c_top:
        for _, _, lb, _, _ in c_bot:
            for ll in lt_lines:
                tl = _intersect_lines(lt, ll)
                bl = _intersect_lines(lb, ll)
                if tl is None or bl is None or bl[1] - tl[1] < hs * 0.20:
                    continue
                for lr in rt_lines:
                    tr = _intersect_lines(lt, lr)
                    br = _intersect_lines(lb, lr)
                    if tr is None or br is None:
                        continue
                    pts = urutkan_sudut(np.float32([tl, tr, br, bl]))
                    if not validasi_quad(pts, ws, hs, min_area_ratio=min_area_ratio,
                                         max_area_ratio=0.94):
                        continue

                    poly_s = np.round(pts * np.float32([sx, sy])).astype(np.int32).reshape(-1, 1, 2)
                    qmask.fill(0)
                    cv2.fillPoly(qmask, [poly_s], 1)
                    qm = qmask > 0
                    qa = max(1, int(qm.sum()))

                    in_gr = float((green_s & qm).sum()) / tot_green
                    in_pur = float((bed_s & qm).sum()) / qa
                    in_soil = float((soil_s & qm).sum()) / qa
                    in_pond = float((pond_s & qm).sum()) / qa
                    in_rim = float((rim_s & qm).sum()) / qa

                    e_t = _edge_support(pts[0], pts[1], edge_hits["top"])
                    e_r = _edge_support(pts[1], pts[2], edge_hits["right"])
                    e_b = _edge_support(pts[3], pts[2], edge_hits["bot"])
                    e_l = _edge_support(pts[0], pts[3], edge_hits["left"])
                    e_mean = 0.25 * (e_t + e_r + e_b + e_l)
                    e_min = min(e_t, e_r, e_b, e_l)

                    dx_l = pts[3][0] - pts[0][0]
                    dx_r = pts[2][0] - pts[1][0]
                    sym_pen = 0.25 if ((dx_l > 35 * scale and dx_r > 35 * scale) or
                                       (dx_l < -35 * scale and dx_r < -35 * scale)) else 0.0

                    qsc = (2.1 * in_gr + 1.6 * in_pur + 1.6 * e_mean + 0.9 * e_min
                           - 2.6 * in_soil - 2.6 * in_pond - 1.6 * in_rim - sym_pen)
                    if qsc > best_score:
                        best_score = qsc
                        best_pts = pts / scale
    return best_pts


def deteksi_sudut_canny(frame, canny_lo=None, canny_hi=None, min_area_ratio=0.12):
    """
    Method 1 (Utama): Deteksi tepi Canny → aproksimasi quad 4 sudut tervalidasi.
    Mendukung garis tepi bingkai lapangan (CannyRim) maupun kontur tertutup
    bersih (CannyPoly). Return 4 titik (TL,TR,BR,BL) atau None.
    """
    pts = _deteksi_canny_rim_quad(frame, canny_lo=canny_lo, canny_hi=canny_hi,
                                  min_area_ratio=min_area_ratio)
    if pts is not None:
        return pts
    return _deteksi_canny_contour_quad(frame, canny_lo=canny_lo, canny_hi=canny_hi,
                                       min_area_ratio=min_area_ratio)


def deteksi_sudut_hsv(frame, h_lo=0, h_hi=179, s_lo=0, s_hi=255,
                      v_lo=0, v_hi=110, min_area_ratio=0.10):
    """
    Jalur cadangan (fallback): mask HSV area gelap + morfologi + kontur terbesar
    → approxPolyDP / minAreaRect.
    """
    img = cv2.GaussianBlur(frame, (5, 5), 0)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (h_lo, s_lo, v_lo), (h_hi, s_hi, v_hi))

    k = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    if cv2.contourArea(c) < min_area_ratio * frame.shape[0] * frame.shape[1]:
        return None

    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.02 * peri, True)
    if len(approx) == 4:
        pts = approx.reshape(-1, 2).astype(np.float32)
    else:
        rect = cv2.minAreaRect(c)
        pts = cv2.boxPoints(rect).astype(np.float32)
    return urutkan_sudut(pts)


def _deteksi_sudut_kanopi_bed(frame, min_area_ratio=0.08):
    """
    Fallback adaptif berbasis sebaran kanopi tanaman kangkung:
    Bila tepi pipa/rim bed terhalang oklusi daun lebat atau pantulan intensif,
    temukan selubung konveks/minAreaRect dari piksel daun hijau terdeteksi,
    lalu lakukan ekspansi margin proporsional (8-12%) untuk mengestimasi tepi bed.
    """
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask_green = cv2.inRange(hsv, (24, 28, 25), (96, 255, 255))
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_CLOSE, k)

    cnts, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None

    pts_all = []
    tot_area = 0.0
    for c in cnts:
        a = cv2.contourArea(c)
        if a > 0.005 * w * h:
            tot_area += a
            pts_all.append(c)

    if tot_area < min_area_ratio * w * h or not pts_all:
        return None

    merged = np.vstack(pts_all)
    rect = cv2.minAreaRect(merged)
    (cx, cy), (rw, rh), angle = rect
    if rw < 30 or rh < 30:
        return None

    scale_margin = 1.08
    exp_rect = ((cx, cy), (rw * scale_margin, rh * scale_margin), angle)
    pts = cv2.boxPoints(exp_rect).astype(np.float32)
    pts = urutkan_sudut(pts)

    if validasi_quad(pts, w, h, min_area_ratio=min_area_ratio, max_area_ratio=0.95):
        return pts
    return None


def deteksi_sudut_bed(frame, h_lo=0, h_hi=179, s_lo=0, s_hi=255,
                      v_lo=0, v_hi=110, min_area_ratio=0.10,
                      canny_lo=None, canny_hi=None, metode="canny"):
    """
    Deteksi 4 sudut bed otomatis kontinu (antarmuka terpadu):
    1. Canny Rim + Poly quad (metode utama berakurasi tinggi)
    2. Fallback HSV bed gelap / talang
    3. Fallback cluster kanopi hijau kangkung (bila rim terhalang daun lebat)
    Return 4 titik (TL,TR,BR,BL) atau None.
    """
    if metode != "hsv":
        pts = deteksi_sudut_canny(frame, canny_lo=canny_lo, canny_hi=canny_hi,
                                  min_area_ratio=max(min_area_ratio, 0.12))
        if pts is not None:
            return pts
        if metode == "canny_only":
            return None

    pts_hsv = deteksi_sudut_hsv(frame, h_lo=h_lo, h_hi=h_hi, s_lo=s_lo, s_hi=s_hi,
                                v_lo=v_lo, v_hi=v_hi, min_area_ratio=min_area_ratio)
    if pts_hsv is not None:
        return pts_hsv

    return _deteksi_sudut_kanopi_bed(frame, min_area_ratio=min_area_ratio * 0.8)


# ─── WARP PERSPEKTIF ─────────────────────────────────────────────────────────

def matriks_warp(pts):
    """Homografi 4-titik: quad bed → kanvas tetap KANVAS_W x KANVAS_H."""
    return cv2.getPerspectiveTransform(urutkan_sudut(pts), DST_QUAD)


def warp_bed(frame, M):
    return cv2.warpPerspective(frame, M, (KANVAS_W, KANVAS_H))


# ─── SEGMENTASI TANAMAN + GRID (pipeline kangkung_cv) ────────────────────────

def mask_tanaman(bgr, adaptif=True):
    """Mask tanaman (muda+mature) dengan optimasi CLAHE V & glare S adaptif."""
    seg = segmentasi_hijau_adaptif(bgr, adaptif=adaptif)
    m = cv2.morphologyEx(seg["mask_hijau"], cv2.MORPH_OPEN,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    return m


def mask_tanaman_warna(bgr, adaptif=True):
    """
    Mask lengkap 4 kelas warna untuk analisis kesehatan daun:
      hijau (muda+mature adaptif CLAHE+glare), kuning (klorosis), coklat (nekrosis).
    Kuning/coklat mempertahankan seed statis pada HSV asli untuk konsistensi PSI.
    Return dict {"hijau", "kuning", "coklat", "tanaman", "info_adaptif"}.
    """
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k7 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    seg = segmentasi_hijau_adaptif(bgr, adaptif=adaptif)
    hsv = seg["hsv_raw"]
    rng = seg["rng"]
    info = seg["info"]

    hijau = cv2.morphologyEx(seg["mask_hijau"], cv2.MORPH_OPEN, k3)
    hijau = cv2.morphologyEx(hijau, cv2.MORPH_CLOSE, k7)

    kuning = cv2.morphologyEx(
        cv2.inRange(hsv, rng["kuning"]["lower"],
                         rng["kuning"]["upper"]),
        cv2.MORPH_OPEN, k3)
    kuning = cv2.bitwise_and(kuning, cv2.bitwise_not(hijau))

    # Coklat hanya valid bila berdekatan dengan kanopi hijau (media tanam
    # juga coklat — lihat catatan di kangkung_cv.segment())
    coklat_raw = cv2.inRange(hsv, rng["coklat"]["lower"],
                                  rng["coklat"]["upper"])
    adj = cv2.dilate(hijau,
                     cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)))
    coklat = cv2.morphologyEx(cv2.bitwise_and(coklat_raw, adj),
                              cv2.MORPH_OPEN, k3)

    tanaman = cv2.bitwise_or(cv2.bitwise_or(hijau, kuning), coklat)
    return {"hijau": hijau, "kuning": kuning,
            "coklat": coklat, "tanaman": tanaman, "info_adaptif": info}


WARNA_BGR = {
    "belum_siap":  (255, 152, 51),   # oranye-redish (belum siap)
    "hampir_siap": (243, 156, 18),   # oranye
    "siap_panen":  (46, 204, 113),   # hijau
    "harus_panen": (231, 76, 60),    # merah
    "warna_quad":  (0, 255, 0),      # hijau untuk tepi quad bed
}


def analisis_grid(warped):
    """
    Grid 4x6 pada kanvas warp → coverage & status per zona.
    Returns: (canvas_bergeri, cov_rata, zona_siap, total_zona, zona_list)
    zona_list: list of dict {"zona", "coverage", "status"} urut R1C1..R4C6
    """
    mask = mask_tanaman(warped)
    masks_warna = mask_tanaman_warna(warped)
    rows, cols = BED_CONFIG["grid_rows"], BED_CONFIG["grid_cols"]
    ch, cw = KANVAS_H // rows, KANVAS_W // cols

    overlay = warped.copy()
    total_cov = []
    zona_list = []
    siap = 0

    for r in range(rows):
        for c in range(cols):
            y1, y2 = r * ch, (r + 1) * ch if r < rows - 1 else KANVAS_H
            x1, x2 = c * cw, (c + 1) * cw if c < cols - 1 else KANVAS_W
            zona  = mask[y1:y2, x1:x2]
            zona_k = masks_warna["kuning"][y1:y2, x1:x2]
            zona_c = masks_warna["coklat"][y1:y2, x1:x2]
            zona_t = masks_warna["tanaman"][y1:y2, x1:x2]
            cov = zona.sum() / 255 / zona.size * 100
            total_cov.append(cov)
            status = get_status(cov)
            if status in ("siap_panen", "harus_panen"):
                siap += 1

            # Kesehatan daun: % kuning/coklat terhadap piksel TANAMAN
            tan_px = int(zona_t.sum()) // 255
            if tan_px > 0:
                pct_kuning = float(zona_k.sum()) / 255 / tan_px * 100
                pct_coklat = float(zona_c.sum()) / 255 / tan_px * 100
            else:
                pct_kuning = pct_coklat = 0.0

            zona_list.append({"zona": f"R{r+1}C{c+1}",
                              "coverage": round(float(cov), 2),
                              "pct_kuning": round(pct_kuning, 2),
                              "pct_coklat": round(pct_coklat, 2),
                              "kesehatan": get_kesehatan(pct_kuning, pct_coklat),
                              "status": status})
            bgr = WARNA_BGR[status]
            cv2.rectangle(overlay, (x1, y1), (x2, y2), bgr, -1)
            cv2.rectangle(warped, (x1, y1), (x2, y2), bgr, 2)
            cv2.putText(warped, f"{cov:.0f}%", (x1 + 6, y1 + 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    hasil = cv2.addWeighted(warped, 0.7, overlay, 0.3, 0)
    rata = float(np.mean(total_cov)) if total_cov else 0.0
    return hasil, rata, siap, rows * cols, zona_list


def analisis_bed_lengkap(warped, adaptif=True):
    """Analisis grid 4x6 lengkap untuk pipeline Raspberry Pi (kangkung_pi & camera_live).

    Mengembalikan dict berisi zona, piksel_zona (G/Y/B disjoint untuk PSI v2.0),
    coverage_rata, kuning_rata, coklat_rata, status_distribusi, kesehatan_distribusi,
    dan metadata info_adaptif S/V/CLAHE.
    """
    masks = mask_tanaman_warna(warped, adaptif=adaptif)
    rows, cols = BED_CONFIG["grid_rows"], BED_CONFIG["grid_cols"]
    H, W = warped.shape[:2]
    ch, cw = H // rows, W // cols

    zona, covs, kuns, coks, st_kes, piksel = {}, [], [], [], [], []
    dist = {"belum_siap": 0, "hampir_siap": 0, "siap_panen": 0, "harus_panen": 0}

    for r in range(rows):
        for c in range(cols):
            y1, y2 = r * ch, (r + 1) * ch if r < rows - 1 else H
            x1, x2 = c * cw, (c + 1) * cw if c < cols - 1 else W
            luas = max(1, (y2 - y1) * (x2 - x1))

            h_zona = masks["hijau"][y1:y2, x1:x2]
            k_zona = masks["kuning"][y1:y2, x1:x2]
            b_zona = masks["coklat"][y1:y2, x1:x2]
            t_zona = masks["tanaman"][y1:y2, x1:x2]

            h_px = int(h_zona.sum()) // 255
            t_px = int(t_zona.sum()) // 255
            k_px = int(k_zona.sum()) // 255
            b_px = int(b_zona.sum()) // 255

            cov = h_px / luas * 100.0
            pk = k_px / t_px * 100.0 if t_px else 0.0
            pc = b_px / t_px * 100.0 if t_px else 0.0
            status = get_status(cov)
            kes = get_kesehatan(pk, pc)
            dist[status] += 1

            zona[f"R{r+1}C{c+1}"] = {
                "coverage": round(cov, 2),
                "status": status,
                "pct_kuning": round(pk, 2),
                "pct_coklat": round(pc, 2),
                "kesehatan": kes,
            }
            covs.append(cov)
            kuns.append(pk)
            coks.append(pc)
            st_kes.append(kes)

            # Konstruksi piksel disjoint untuk kontrak PSI v2.0 (G+Y+B == |tanaman|)
            k_bukan_b = int(cv2.bitwise_and(k_zona, cv2.bitwise_not(b_zona)).sum()) // 255
            h_bukan_kb = int(cv2.bitwise_and(
                h_zona, cv2.bitwise_not(cv2.bitwise_or(k_zona, b_zona))).sum()) // 255
            piksel.append({
                "green": h_bukan_kb,
                "yellow": k_bukan_b,
                "brown": b_px,
                "plant_mask": t_px,
                "unclassified": max(0, t_px - (h_bukan_kb + k_bukan_b + b_px)),
            })

    siap = dist["siap_panen"] + dist["harus_panen"]
    return {
        "zona": zona,
        "canvas": warped.copy(),
        "coverage_rata": round(float(np.mean(covs)), 2),
        "coverage_std": round(float(np.std(covs)), 2),
        "status_distribusi": dist,
        "zona_siap_panen": siap,
        "persen_siap": round(siap / max(1, len(zona)) * 100, 1),
        "kuning_rata": round(float(np.mean(kuns)), 2),
        "coklat_rata": round(float(np.mean(coks)), 2),
        "kesehatan_distribusi": {s: st_kes.count(s)
                                 for s in ("sehat", "waspada", "sakit")},
        "piksel_zona": piksel,
        "info_adaptif": masks.get("info_adaptif", {}),
    }


def gambar_quad(frame, pts, warna=(0, 255, 0), tebal=2):
    """Gambar poligon 4 sudut terdeteksi di frame asli."""
    p = pts.astype(np.int32).reshape(-1, 1, 2)
    cv2.polylines(frame, [p], True, warna, tebal)
    for i, pt in enumerate(pts.astype(int)):
        cv2.circle(frame, tuple(pt), 6, (0, 0, 255), -1)
        cv2.putText(frame, f"P{i+1}", (pt[0] + 8, pt[1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    return frame


# ─── PROYEKSI GRID KE FRAME ASLI ─────────────────────────────────────────────

def proyeksi_grid_ke_frame(pts_src, rows=None, cols=None):
    """
    Hitung koordinat 24 sel grid (4x6) di frame asli, via invers homografi.

    Args:
        pts_src: 4 titik sudut bed di frame asli (TL, TR, BR, BL)
        rows, cols: dimensi grid (default dari BED_CONFIG)

    Returns:
        list of quad_array -- 24 sel dalam koordinat frame asli
    """
    if rows is None:
        rows = BED_CONFIG["grid_rows"]
    if cols is None:
        cols = BED_CONFIG["grid_cols"]

    # Titik grid di kanvas warp (1200x660)
    grid_pts = []
    for r in range(rows + 1):
        for c in range(cols + 1):
            x = c * KANVAS_W / cols
            y = r * KANVAS_H / rows
            grid_pts.append([x, y])
    grid_pts = np.float32(grid_pts).reshape(-1, 1, 2)

    # Invers homografi: kanvas -> frame asli
    M_inv = cv2.getPerspectiveTransform(DST_QUAD, pts_src.astype(np.float32))
    grid_asli = cv2.perspectiveTransform(grid_pts, M_inv)

    # Susun 24 sel
    sel_list = []
    for r in range(rows):
        for c in range(cols):
            p1 = grid_asli[r * (cols + 1) + c][0]
            p2 = grid_asli[r * (cols + 1) + c + 1][0]
            p3 = grid_asli[(r + 1) * (cols + 1) + c + 1][0]
            p4 = grid_asli[(r + 1) * (cols + 1) + c][0]
            sel_list.append(np.array([p1, p2, p3, p4], dtype=np.float32).reshape(-1, 1, 2))

    return sel_list


def gambar_grid_dalam_box(frame, pts, zona_list, alpha_fill=0.25, alpha_dark=0.4):
    """
    Gambar grid status 4x6 DI DALAM polygon bed di frame asli.

    Args:
        frame: frame asli (BGR)
        pts: 4 titik sudut bed (TL, TR, BR, BL)
        zona_list: list of dict {"zona", "coverage", "status"} dari analisis_grid()
        alpha_fill: opacity fill warna per zona
        alpha_dark: opacity dark overlay di luar bed

    Returns:
        frame dengan grid + overlay
    """
    overlay = frame.copy()
    zona_quads = proyeksi_grid_ke_frame(pts)

    # Gelapkan area di luar bed
    p = pts.astype(np.int32).reshape(-1, 1, 2)
    mask_bed = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask_bed, [p], 255)
    mask_out = cv2.bitwise_not(mask_bed)
    dark = frame.copy()
    dark[mask_out > 0] = (dark[mask_out > 0] * 0.6).astype(np.uint8)
    frame = cv2.addWeighted(frame, 1 - alpha_dark, dark, alpha_dark, 0)

    # Isi warna per zona
    for i, quad in enumerate(zona_quads):
        if i < len(zona_list):
            status = zona_list[i]["status"]
            bgr = WARNA_BGR.get(status, (128, 128, 128))
            cv2.fillPoly(overlay, [quad.astype(np.int32)], bgr)

    frame = cv2.addWeighted(frame, 1 - alpha_fill, overlay, alpha_fill, 0)

    # Border grid + label
    for i, quad in enumerate(zona_quads):
        cv2.polylines(frame, [quad.astype(np.int32)], True, (255, 255, 255), 1)
        if i < len(zona_list):
            cx = int(quad[0][0][0] + (quad[2][0][0] - quad[0][0][0]) * 0.5)
            cy = int(quad[0][0][1] + (quad[2][0][1] - quad[0][0][1]) * 0.5)
            cv2.putText(frame, zona_list[i]["zona"], (cx - 25, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    return frame



# ─── DETEKSI MANUAL (OPSI B) ─────────────────────────────────────────────

def pilih_sudut_manual(frame):
    """
    GUI klik 4 sudut bed: TL → TR → BR → BL (urutkan otomatis).
    Z = undo, Q/ESC = batal. Return 4 titik terurut atau None.
    """
    pts = []
    win = "Klik 4 sudut bed: TL->TR->BR->BL | Z=undo | Q=batal"
    disp0 = frame.copy()

    def cb(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(pts) < 4:
            pts.append([x, y])

    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(win, cb)

    while True:
        disp = disp0.copy()
        cv2.putText(disp, f"Klik sudut ke-{len(pts)+1}/4  (Z=undo, Q=batal)",
                    (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        for i, p in enumerate(pts):
            cv2.circle(disp, tuple(p), 7, (0, 0, 255), -1)
            cv2.putText(disp, f"P{i+1}", (p[0] + 10, p[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        if len(pts) >= 2:
            cv2.polylines(disp, [np.int32(pts).reshape(-1, 1, 2)],
                          len(pts) == 4, (0, 255, 0), 2)
        cv2.imshow(win, disp)
        k = cv2.waitKey(20) & 0xFF
        if k in (ord("q"), 27):
            cv2.destroyWindow(win)
            return None
        if k == ord("z") and pts:
            pts.pop()
        if len(pts) == 4:
            cv2.waitKey(300)
            cv2.destroyWindow(win)
            return urutkan_sudut(np.float32(pts))



# ─── MAIN ───────────────────────────────────────────────────────────────────

def resize_frame(frame):
    """Kecilkan frame jika lebih lebar dari MAX_LEBAR (hemat CPU)."""
    h, w = frame.shape[:2]
    if w > MAX_LEBAR:
        s = MAX_LEBAR / w
        frame = cv2.resize(frame, (MAX_LEBAR, int(h * s)))
    return frame


def main():
    ap = argparse.ArgumentParser(
        description="Adaptive bed detector - grid menyesuaikan tepi plant bed")
    ap.add_argument("source", help="Path video / index kamera (angka)")
    ap.add_argument("--manual", action="store_true")
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--detect-every", type=int, default=10)
    ap.add_argument("--save", nargs="?", const="auto", default=None)
    ap.add_argument("--no-gui", action="store_true")
    ap.add_argument("--max-frames", type=int, default=None)
    ap.add_argument("--v-hi", type=int, default=110)
    ap.add_argument("--min-area", type=float, default=0.10)
    args = ap.parse_args()

    try:
        src = int(args.source)
    except ValueError:
        src = args.source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"[ERROR] Tidak bisa membuka sumber: {src}")
        sys.exit(1)

    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Tidak ada frame yang bisa dibaca.")
        sys.exit(1)
    frame = resize_frame(frame)
    h, w = frame.shape[:2]

    smoother = CornerSmoother(alpha=0.2)
    if args.manual:
        pts = pilih_sudut_manual(frame)
        mode = "MANUAL"
    else:
        pts = deteksi_sudut_bed(frame, v_hi=args.v_hi,
                                min_area_ratio=args.min_area)
        mode = "AUTO"
        if pts is None:
            print("[WARN] Deteksi otomatis gagal.")
            pts = pilih_sudut_manual(frame)
            mode = "MANUAL"
    if pts is None:
        print("[ERROR] Sudut bed tidak didapat. Keluar.")
        sys.exit(1)
    if mode == "AUTO":
        smoother.update(pts)
    print(f"[MODE] {mode} | sudut awal:")
    print(np.round(pts, 1))

    writer, out_path = None, None
    if args.save:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        stem = Path(src).stem if isinstance(src, str) else f"kamera{src}"
        out_path = (SNAPSHOT_DIR / f"adaptive_{stem}.mp4" if args.save == "auto"
                    else Path(args.save))
        writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"),
                                 20.0, (w, h))
        if not writer.isOpened():
            out_path = out_path.with_suffix(".avi")
            writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"XVID"),
                                     20.0, (w, h))
        print(f"[INFO] Rekam: {out_path}")

    processed, frame_idx, bed_lost = 0, 0, 0
    t_proc = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[INFO] Video selesai.")
            break
        frame_idx += 1
        if args.step > 1 and (frame_idx - 1) % args.step:
            continue
        frame = resize_frame(frame)
        processed += 1
        t1 = time.perf_counter()

        if mode == "AUTO" and processed % args.detect_every == 0:
            baru = deteksi_sudut_bed(frame, v_hi=args.v_hi,
                                     min_area_ratio=args.min_area)
            if baru is not None:
                pts = smoother.update(baru)
                bed_lost = 0
            else:
                bed_lost += 1

        warped = warp_bed(frame, matriks_warp(pts))
        annot, cov_rata, siap, n_zona, zona_list = analisis_grid(warped)
        t_proc += time.perf_counter() - t1

        disp = gambar_grid_dalam_box(frame.copy(), pts, zona_list)
        if bed_lost:
            cv2.putText(disp, "BED LOST!", (12, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(disp, f"Cov: {cov_rata:.1f}%  Siap: {siap}/{n_zona}",
                    (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 150), 2)

        if writer is not None:
            writer.write(disp)

        if not args.no_gui:
            cv2.imshow("Adaptive Bed Detector - KANGKUNG AQUAPONIK",
                       cv2.resize(disp, (800, int(800 * h / w))))
            k = cv2.waitKey(1) & 0xFF
            if k == ord("q"):
                print("[INFO] Dihentikan user.")
                break
            if k == ord("s"):
                SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
                snap = SNAPSHOT_DIR / f"adaptive_snapshot_{int(time.time())}.png"
                cv2.imwrite(str(snap), disp)
                print(f"[INFO] Snapshot: {snap}")

        if args.max_frames and processed >= args.max_frames:
            print(f"[INFO] Batas {args.max_frames} frame tercapai.")
            break

    cap.release()
    if writer:
        writer.release()
        print(f"[INFO] Video tersimpan: {out_path}")
    if not args.no_gui:
        cv2.destroyAllWindows()

    ms = (t_proc / processed * 1000) if processed else 0
    print(f"\n[RINGKASAN] frame_terproses={processed} mode={mode} "
          f"waktu_per_frame={ms:.1f} ms")
    print(f"[RINGKASAN] sudut_akhir:")
    print(np.round(pts, 1))


if __name__ == "__main__":
    main()
