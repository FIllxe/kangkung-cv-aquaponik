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
    1. Frame pertama → deteksi otomatis 4 sudut bed (mask HSV + kontur)
    2. Gagal? → fallback klik manual 4 sudut
    3. Setiap frame: warp perspektif ke kanvas 1200x660 (2m x 1.1m)
       → grid 4x6 → segmentasi tanaman → coverage & status per zona
    4. Sudut dihaluskan EMA (anti-gemetar) + re-deteksi tiap --detect-every

  Basis metode: segmentasi warna HSV + analisis kontur (Searson 2017;
  Yang 2015) + homografi 4-titik (projective transform).
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
                         get_kesehatan, parameter_adaptif)

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


# ─── DETEKSI OTOMATIS (OPSI A) ───────────────────────────────────────────────

def deteksi_sudut_bed(frame, h_lo=0, h_hi=179, s_lo=0, s_hi=255,
                      v_lo=0, v_hi=110, min_area_ratio=0.10):
    """
    Deteksi 4 sudut bed otomatis:
    mask HSV (default: area gelap = media tanam) → MORPH_CLOSE besar →
    kontur terbesar → approxPolyDP quad → fallback minAreaRect.
    Return 4 titik terurut (TL,TR,BR,BL) atau None jika gagal.
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


# ─── WARP PERSPEKTIF ─────────────────────────────────────────────────────────

def matriks_warp(pts):
    """Homografi 4-titik: quad bed → kanvas tetap KANVAS_W x KANVAS_H."""
    return cv2.getPerspectiveTransform(urutkan_sudut(pts), DST_QUAD)


def warp_bed(frame, M):
    return cv2.warpPerspective(frame, M, (KANVAS_W, KANVAS_H))


# ─── SEGMENTASI TANAMAN + GRID (pipeline kangkung_cv) ────────────────────────

def mask_tanaman(bgr, adaptif=True):
    """Mask tanaman (muda+mature) — range ADAPTIF (f = mean(V)/128) default."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    if adaptif:
        rng = parameter_adaptif(hsv)
    else:
        rng = {k: {"lower": HSV_KANGKUNG[k]["lower"],
                   "upper": HSV_KANGKUNG[k]["upper"]}
               for k in ("muda", "mature")}
    m = cv2.bitwise_or(
        cv2.inRange(hsv, rng["muda"]["lower"],   rng["muda"]["upper"]),
        cv2.inRange(hsv, rng["mature"]["lower"], rng["mature"]["upper"]))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    return m


def mask_tanaman_warna(bgr, adaptif=True):
    """
    Mask lengkap 4 kelas warna untuk analisis kesehatan daun:
      hijau (muda+mature), kuning (klorosis), coklat (nekrosis).
    Range HSV ADAPTIF (f = mean(V)/128); Hue tidak digeser.
    Kuning/coklat di-open saja agar bercak kecil tetap terdeteksi.
    Return dict {"hijau", "kuning", "coklat", "tanaman", "info_adaptif"}.
    """
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    if adaptif:
        rng = parameter_adaptif(hsv)
        info = rng["info"]
    else:
        rng = {k: {"lower": HSV_KANGKUNG[k]["lower"],
                   "upper": HSV_KANGKUNG[k]["upper"]}
               for k in HSV_KANGKUNG}
        info = {"f": 1.0, "s_lo": 40, "v_lo": 40, "v_hi": 255}

    hijau = mask_tanaman(bgr, adaptif=adaptif)
    kuning = cv2.morphologyEx(
        cv2.inRange(hsv, rng["kuning"]["lower"],
                         rng["kuning"]["upper"]),
        cv2.MORPH_OPEN, k3)

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
