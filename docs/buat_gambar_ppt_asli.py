"""Buat gambar bukti ASLI utk PPT (bukan simulasi) -> output/ppt_asli/
1. frame asli IMG_5159 (HP) vs frame beranotasi pipeline (MP4 output)
2. bed_04_ready.jpg (foto asli) vs bed_04_ready_segmentasi.png (output batch)
3. grafik timeseries coverage asli dari CSV IMG_5159 (763 frame)
4. grafik tren coverage 7 foto batch asli (seedling->ready) dari JSON laporan
5. tabel PSI asli dari 7 laporan batch (cek_psi --laporan)
Jalankan: python docs/buat_gambar_ppt_asli.py
"""
import csv, json, cv2, numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "ppt_asli"
OUT.mkdir(parents=True, exist_ok=True)

# 1) ASLI vs ANOTASI (frame mentah HP vs output pipeline)
cap_raw = cv2.VideoCapture(str(ROOT / "data" / "videos" / "IMG_5159.MOV"))
cap_raw.set(cv2.CAP_PROP_POS_FRAMES, 100)
ok1, fr_raw = cap_raw.read(); cap_raw.release()
cap_an = cv2.VideoCapture(str(ROOT / "output" / "demo" / "IMG_5159_beranotasi.mp4"))
cap_an.set(cv2.CAP_PROP_POS_FRAMES, 100)
ok2, fr_an = cap_an.read(); cap_an.release()
assert ok1 and ok2, "gagal baca video"
fr_raw = cv2.resize(fr_raw, (960, 540))
fr_an = cv2.resize(fr_an, (960, 540))
gab = np.hstack([fr_raw, fr_an])
cv2.putText(gab, "ASLI (HP IMG_5159, frame 100)", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
cv2.putText(gab, "OUTPUT PIPELINE (grid+HUD)", (980, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
cv2.imwrite(str(OUT / "01_asli_vs_anotasi.jpg"), gab)
print("OK 01", gab.shape)

# 2) FOTO ASLI vs SEGMENTASI (bed_04_ready)
foto = cv2.imread(str(ROOT / "dataset1" / "bed_04_ready.jpg"))
seg = cv2.imread(str(ROOT / "output" / "segmentasi_batch" / "bed_04_ready_segmentasi.png"))
h, w = seg.shape[:2]
seg_crop = seg[int(h * 0.28):int(h * 0.78), int(w * 0.10):int(w * 0.90)]
foto_r = cv2.resize(foto, (seg_crop.shape[1], seg_crop.shape[0]))
gab2 = np.vstack([foto_r, seg_crop])
cv2.putText(gab2, "FOTO ASLI bed_04_ready.jpg (lapangan)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
cv2.putText(gab2, "OUTPUT batch_segmentasi.py (cov 22,56%)", (20, seg_crop.shape[0] + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
cv2.imwrite(str(OUT / "02_foto_vs_segmentasi.jpg"), gab2)
print("OK 02", gab2.shape)

# 3) TIMESERIES ASLI IMG_5159 (763 frame dari CSV pipeline)
with open(ROOT / "output" / "demo" / "IMG_5159_timeseries.csv", encoding="utf-8") as f:
    rd = csv.DictReader(f)
    cov = [float(r["coverage_global"]) for r in rd]
fig, ax = plt.subplots(figsize=(12, 4.5))
ax.plot(cov, linewidth=0.8)
ax.set_title("Timeseries ASLI coverage global — IMG_5159.MOV (763 frame, mode ADAPTIVE)")
ax.set_xlabel("frame"); ax.set_ylabel("coverage global (%)")
ax.grid(True, alpha=0.3)
ax.text(0.99, 0.95, f"n=763, mean={np.mean(cov):.1f}%, std={np.std(cov):.1f}%",
        transform=ax.transAxes, ha="right", fontsize=11,
        bbox=dict(facecolor="white", alpha=0.8))
fig.tight_layout(); fig.savefig(str(OUT / "03_timeseries_IMG5159.png"), dpi=130); plt.close(fig)
print(f"OK 03 n={len(cov)} mean={np.mean(cov):.1f}")

# 4) TREN 7 FOTO ASLI (seedling->ready) dari JSON laporan batch
urutan = ["bed_01_seedling", "bed_02_young", "bed_03_growing", "bed_04_ready",
          "bed_05_mixed", "Image_28lf7x28lf7x28lf", "Image_6islrm6islrm6isl"]
labels, covs, siap = [], [], []
for stem in urutan:
    d = json.load(open(ROOT / "output" / "segmentasi_batch" / f"{stem}_laporan.json", encoding="utf-8"))
    g = d["global"]
    labels.append(stem.replace("bed_", "").replace("_", " "))
    covs.append(g["coverage_rata"])
    siap.append(g["persen_siap"])
fig, ax1 = plt.subplots(figsize=(12, 4.5))
x = np.arange(len(labels))
b1 = ax1.bar(x - 0.2, covs, 0.4, label="coverage rata (%)")
ax1.set_xticks(x); ax1.set_xticklabels(labels, rotation=15, ha="right")
ax1.set_ylabel("coverage rata (%)"); ax1.set_title("Hasil ASLI batch 7 foto lapangan (batch_segmentasi.py)")
ax2 = ax1.twinx()
b2 = ax2.bar(x + 0.2, siap, 0.4, color="orange", label="% zona siap")
ax2.set_ylabel("% zona siap panen")
for i, (c, s) in enumerate(zip(covs, siap)):
    ax1.text(i - 0.2, c + 0.7, f"{c:.1f}", ha="center", fontsize=9)
    ax2.text(i + 0.2, s + 0.7, f"{s:.1f}", ha="center", fontsize=9)
fig.tight_layout(); fig.savefig(str(OUT / "04_tren_7foto.png"), dpi=130); plt.close(fig)
print("OK 04", list(zip(labels, covs)))

# 5) TABEL PSI ASLI (7 laporan batch -> PSI via hitung_psi, TANPA dummy)
import sys
sys.path.insert(0, str(ROOT / "files"))
from kangkung_cv import hitung_psi
rows = []
for stem in urutan:
    d = json.load(open(ROOT / "output" / "segmentasi_batch" / f"{stem}_laporan.json", encoding="utf-8"))
    g = d["global"]
    psi = hitung_psi(g["kuning_rata"], g["coklat_rata"])
    rows.append((stem, g["kuning_rata"], g["coklat_rata"], g["zona_sakit"], psi))
fig, ax = plt.subplots(figsize=(12, 3.6))
ax.axis("off")
ax.set_title("PSI ASLI dari 7 foto lapangan (hitung_psi: kuning/25 + coklat/8) — bed sehat = PSI ~0", fontsize=12, pad=15)
tab = [["foto", "kuning%", "coklat%", "zona sakit", "PSI"]] + \
      [[r[0][:22], f"{r[1]:.2f}", f"{r[2]:.2f}", str(r[3]), f"{r[4]:.1f}"] for r in rows]
t = ax.table(cellText=tab, loc="center", colWidths=[0.4, 0.15, 0.15, 0.15, 0.15])
t.auto_set_font_size(False); t.set_fontsize(10); t.scale(1, 1.5)
fig.tight_layout(); fig.savefig(str(OUT / "05_tabel_PSI_asli.png"), dpi=130); plt.close(fig)
print("OK 05")
for r in rows:
    print(f"  {r[0]:28s} K={r[1]:.2f} C={r[2]:.2f} sakit={r[3]} PSI={r[4]:.1f}")
print("SELESAI ->", OUT)
