"""Panel demo kesehatan daun: sebelum/sesudah blob sakit + heatmap kesehatan 24 zona.

Output: output/evaluasi/panel_kesehatan_daun.png
- Frame video dipilih otomatis: yang paling sedikit zona false-flag alami.
- Blob kuning/coklat disuntik di 2 zona dengan kanopi terpadat (tanaman px terbanyak),
  lalu status kesehatan dihitung murni oleh algoritma HSV (tanpa pemaksaan label).
"""
import os
import sys
import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proses_video import detek_sudut_robust
from adaptive_bed import (matriks_warp, warp_bed, resize_frame,
                          mask_tanaman_warna)
from kangkung_cv import get_kesehatan, BED_CONFIG

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO = os.path.join(ROOT, "data", "videos", "IMG_5159.MOV")

cap = cv2.VideoCapture(VIDEO)
ok, first = cap.read()
assert ok, f"video tidak bisa dibuka: {VIDEO}"
first = resize_frame(first)
pts, _ = detek_sudut_robust(first)
M = matriks_warp(pts)

rows, cols = BED_CONFIG["grid_rows"], BED_CONFIG["grid_cols"]
MIN_CANOPI_PCT = 30.0   # zona dengan kanopi < 30% area zona -> 'n/a' (tidak dievaluasi)


def zona_slice(r, c, H, W):
    ch, cw = H // rows, W // cols
    return (slice(r * ch, (r + 1) * ch if r < rows - 1 else H),
            slice(c * cw, (c + 1) * cw if c < cols - 1 else W))

def hitung(m, H, W):
    """Kesehatan per zona + validitas kanopi.

    Zona dengan kanopi < MIN_CANOPI_PCT dari area zona dianggap tidak layak
    evaluasi (artefak tepi warp / area luar bed) -> status 'n/a'.
    """
    res = {}
    for r in range(rows):
        for c in range(cols):
            sl = zona_slice(r, c, H, W)
            zarea = (sl[0].stop - sl[0].start) * (sl[1].stop - sl[1].start)
            t = int(m["tanaman"][sl].sum()) // 255
            pct_area = t / zarea * 100
            if pct_area < MIN_CANOPI_PCT:
                res[f"R{r+1}C{c+1}"] = (0.0, 0.0, "n/a", pct_area)
                continue
            pk = int(m["kuning"][sl].sum()) // 255 / t * 100 if t else 0.0
            pc = int(m["coklat"][sl].sum()) // 255 / t * 100 if t else 0.0
            res[f"R{r+1}C{c+1}"] = (pk, pc, get_kesehatan(pk, pc), pct_area)
    return res


def pilih_frame(cap):
    """Sampling frame: pilih yang paling sedikit zona 'sakit' alami (false flag)."""
    kandidat = []
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, n // 60)
    idx = 0
    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = cap.read()
        if not ok:
            break
        fr = resize_frame(fr)
        warped = warp_bed(fr, M)
        m = mask_tanaman_warna(warped)
        res = hitung(m, warped.shape[0], warped.shape[1])
        n_sakit = sum(1 for v in res.values() if v[2] == "sakit")
        cover = int(m["tanaman"].sum()) // 255
        kandidat.append((n_sakit, abs(cover - 200000), warped))
        idx += step
        if len(kandidat) >= 60:
            break
    kandidat.sort(key=lambda x: (x[0], x[1]))
    best = kandidat[0]
    print(f"frame terpilih: {best[0]} zona sakit alami "
          f"(dari {len(kandidat)} kandidat)")
    return best[2]


warped = pilih_frame(cap)
cap.release()
H, W = warped.shape[:2]

# ── pilih 2 zona dengan kanopi terpadat untuk injeksi blob ──
m_asli = mask_tanaman_warna(warped)
res_asli = hitung(m_asli, H, W)
cover_zona = {}
for z in res_asli:
    r, c = int(z[1]) - 1, int(z[3]) - 1
    sl_y, sl_x = zona_slice(r, c, H, W)
    cover_zona[z] = int(m_asli["tanaman"][sl_y, sl_x].sum()) // 255
urut = sorted(cover_zona, key=cover_zona.get, reverse=True)
ZK, ZC = urut[0], urut[1]          # zona untuk blob kuning & coklat
print(f"zona injeksi: kuning={ZK} ({cover_zona[ZK]} px), "
      f"coklat={ZC} ({cover_zona[ZC]} px)")

# ── suntik blob sakit ──
uji = warped.copy()
for zid, warna, faktor in ((ZK, (40, 210, 230), 0.42),   # kuning terang (BGR)
                           (ZC, (60, 90, 130), 0.38)):   # coklat nekrosis (BGR)
    r, c = int(zid[1]) - 1, int(zid[3]) - 1
    sl_y, sl_x = zona_slice(r, c, H, W)
    cy = (sl_y.start + sl_y.stop) // 2
    cx = (sl_x.start + sl_x.stop) // 2
    cv2.ellipse(uji, (cx, cy), (int(W / cols * faktor), int(H / rows * faktor)),
                0, 0, 360, warna, -1)

m_uji = mask_tanaman_warna(uji)
res_uji = hitung(m_uji, H, W)

KES_RGB = {"sehat": (46, 204, 113), "waspada": (243, 156, 18),
           "sakit": (231, 76, 60), "n/a": (140, 140, 140)}
BLOB_SAKIT = {ZK, ZC}

def overlay_kes(img_bgr, res):
    out = img_bgr.copy()
    ov = out.copy()
    for zid, v in res.items():
        kes = v[2]
        r, c = int(zid[1]) - 1, int(zid[3]) - 1
        x1, y1 = c * (W // cols), r * (H // rows)
        x2 = (c + 1) * (W // cols) if c < cols - 1 else W
        y2 = (r + 1) * (H // rows) if r < rows - 1 else H
        rr, g, b = KES_RGB[kes]          # KES_RGB disimpan sebagai RGB -> balik utk BGR
        cv2.rectangle(ov, (x1, y1), (x2, y2), (b, g, rr), -1)
    blended = cv2.addWeighted(out, 0.65, ov, 0.35, 0)
    # garis tepi zona agar batas grid terbaca jelas di slide
    for zid, v in res.items():
        kes = v[2]
        r, c = int(zid[1]) - 1, int(zid[3]) - 1
        x1, y1 = c * (W // cols), r * (H // rows)
        x2 = (c + 1) * (W // cols) if c < cols - 1 else W
        y2 = (r + 1) * (H // rows) if r < rows - 1 else H
        rr, g, b = KES_RGB[kes]
        cv2.rectangle(blended, (x1, y1), (x2 - 1, y2 - 1), (b, g, rr), 3)
    return blended


def rgb(img_bgr):
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


fig = plt.figure(figsize=(17, 7.5), facecolor="#f7f7f2")
fig.suptitle("Demo Kesehatan Daun per Zona - Kuning (Klorosis) & Coklat (Nekrosis)",
             fontsize=15, fontweight="bold", y=0.97)

ax1 = fig.add_axes([0.03, 0.52, 0.30, 0.38]); ax1.imshow(rgb(warped))
ax1.set_title("1) Bed asli (warp top-down)", fontsize=11); ax1.axis("off")
ax2 = fig.add_axes([0.35, 0.52, 0.30, 0.38]); ax2.imshow(rgb(uji))
ax2.set_title(f"2) + Blob kuning ({ZK}) & coklat ({ZC})", fontsize=11); ax2.axis("off")
ax3 = fig.add_axes([0.67, 0.52, 0.30, 0.38]); ax3.imshow(rgb(overlay_kes(uji, res_uji)))
ax3.set_title("3) Deteksi sistem - zona sakit otomatis", fontsize=11); ax3.axis("off")

# heatmap kesehatan 4x6 (hasil deteksi vs target injeksi)
ax4 = fig.add_axes([0.08, 0.08, 0.36, 0.30])
ax5 = fig.add_axes([0.56, 0.08, 0.36, 0.30])
gt = {z: (v[0], v[1], "sakit" if z in BLOB_SAKIT else v[2], v[3])
      for z, v in res_uji.items()}
for ax, res, judul in ((ax4, res_uji, "Deteksi HSV (kuning %K, coklat %C per zona)"),
                       (ax5, gt, "Target injeksi (zona blob = sakit)")):
    for zid, v in res.items():
        kes = v[2]
        r, c = int(zid[1]) - 1, int(zid[3]) - 1
        ax.add_patch(plt.Rectangle((c, r), 1, 1, color=np.array(KES_RGB[kes])/255))
        if kes == "n/a":
            label = f"{zid}\nn/a\n({v[3]:.0f}% kanopi)"
        else:
            label = f"{zid}\n{v[0]:.0f}%K\n{v[1]:.1f}%C"
        ax.text(c + 0.5, r + 0.5, label,
                ha="center", va="center", fontsize=6, color="white", fontweight="bold")
    ax.set_xlim(0, cols); ax.set_ylim(rows, 0)
    ax.set_xticks(range(cols)); ax.set_yticks(range(rows))
    ax.set_xticklabels([f"C{i+1}" for i in range(cols)], fontsize=7)
    ax.set_yticklabels([f"B{i+1}" for i in range(rows)], fontsize=7)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(judul, fontsize=10)

legend = [mpatches.Patch(color=np.array(v)/255, label=k)
          for k, v in KES_RGB.items()]
fig.legend(handles=legend, loc="lower center", ncol=4, fontsize=10,
           frameon=False, bbox_to_anchor=(0.5, 0.005))

out = os.path.join(ROOT, "output", "evaluasi", "panel_kesehatan_daun.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
fig.savefig(out, dpi=140, facecolor=fig.get_facecolor(), bbox_inches="tight")
print("saved:", out)
sakit = [z for z, v in res_uji.items() if v[2] == "sakit"]
print("zona sakit (deteksi HSV):", sakit)
print("zona blob suntik        :", sorted(BLOB_SAKIT))
print("blob terdeteksi sakit   :", all(z in sakit for z in BLOB_SAKIT))
