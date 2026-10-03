# -*- coding: utf-8 -*-
"""Generator berkas ilustrasi bimbingan ke-3: Flowchart Prinsip Kerja Sistem.

Alur sesuai kode terverifikasi: raspi/kangkung_pi.py::siklus()
 (thermal guard -> ambil_frame -> analisis -> payload -> outbox -> sync)
 + kontrak aman skema v1.1 (stale/null/ACC/anti-spam, tanpa aktuasi otomatis).

Jalankan: python docs/buat_flowchart_bimbingan3.py
Output  : docs/BIMBINGAN3_FLOWCHART_SISTEM.png  (300 dpi, putih, simbol baku)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon, Ellipse

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "BIMBINGAN3_FLOWCHART_SISTEM.png"

BG = "white"
INK = "#1a1a1a"
MUT = "#555555"
HIJAU = "#1b5e20"
HIJAU_BG = "#e8f5e9"
BIRU = "#0d47a1"
BIRU_BG = "#e3f2fd"
KUNING_BG = "#fff8e1"
KUNING_LINE = "#f9a825"
MERAH = "#b71c1c"
MERAH_BG = "#ffebee"

fig, ax = plt.subplots(figsize=(12, 15.5))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 12)
ax.set_ylim(-0.4, 16.6)
ax.axis("off")

ax.text(6, 16.1, "BIMBINGAN KE-3  \u2014  FLOWCHART PRINSIP KERJA SISTEM",
        ha="center", va="center", fontsize=15, fontweight="bold", color=INK)
ax.text(6, 15.68, "Siklus 10 menit: thermal guard \u2192 capture \u2192 CV \u2192 PSI \u2192 Firebase \u2192 dashboard + fuzzy "
        "(siklus() di raspi/kangkung_pi.py)",
        ha="center", va="center", fontsize=9.5, color=MUT)

CX = 6.0


def teks(x, y, s, size=9.2, bold=False, color=INK, ha="center"):
    ax.text(x, y, s, ha=ha, va="center", fontsize=size,
            fontweight="bold" if bold else "normal", color=color,
            linespacing=1.4)


def oval(cx, y, w, h, s, bg=HIJAU_BG, line=HIJAU):
    ax.add_patch(Ellipse((cx, y), w, h, facecolor=bg, edgecolor=line, linewidth=1.8))
    teks(cx, y, s, bold=True)


def proses(cx, y, w, h, judul, sub="", bg="white", line=INK):
    ax.add_patch(FancyBboxPatch((cx - w / 2, y - h / 2), w, h,
                 boxstyle="round,pad=0.06", facecolor=bg,
                 edgecolor=line, linewidth=1.7))
    teks(cx, y + (0.18 if sub else 0), judul, bold=True)
    if sub:
        teks(cx, y - 0.30, sub, size=8.2, color=MUT)


def belah(cx, y, w, h, judul, sub="", bg=KUNING_BG, line=KUNING_LINE):
    ax.add_patch(Polygon([[cx - w / 2, y], [cx, y + h / 2],
                          [cx + w / 2, y], [cx, y - h / 2]],
                         closed=True, facecolor=bg, edgecolor=line, linewidth=1.7))
    teks(cx, y + 0.30, judul, bold=True, size=9.6)
    if sub:
        teks(cx, y - 0.32, sub, size=8.2, color=MUT)


def panah(y1, y2, x=CX, label="", side=0.0, col=INK, ls="-"):
    a = FancyArrowPatch((x, y1), (x, y2), arrowstyle="-|>", linestyle=ls,
                        linewidth=1.7, color=col, mutation_scale=13,
                        shrinkA=1, shrinkB=3)
    ax.add_patch(a)
    if label:
        ax.text(x + 0.25 + side, (y1 + y2) / 2, label, ha="left", va="center",
                fontsize=8.4, color=col,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.2))


def panah_ke(x1, y1, x2, y2, label="", col=INK, rad=0.0, ha="left"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", linewidth=1.5,
                        color=col, mutation_scale=12,
                        connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=3)
    ax.add_patch(a)
    if label:
        ax.text(x2 + 0.3, (y1 + y2) / 2, label, ha=ha, va="center",
                fontsize=8.2, color=col,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.2))


Y = 14.6
oval(CX, Y, 4.6, 0.85, "START (tiap 10 mnt)")
panah(Y - 0.43, 13.75)
belah(CX, 13.25, 5.2, 1.0, "Suhu SoC > 75 \u00b0C?", "thermal_guard.py", bg=MERAH_BG, line=MERAH)
# loop "ya" kanan: keluar sisi kanan belah ketupat, naik, masuk sisi kanan START
LX = CX + 4.6
a = FancyArrowPatch((CX + 2.6, 13.25), (LX, 13.25), arrowstyle="-",
                    linewidth=1.5, color=MERAH, mutation_scale=12, shrinkA=0, shrinkB=0)
ax.add_patch(a)
b = FancyArrowPatch((LX, 13.25), (LX, 14.6), arrowstyle="-",
                    linewidth=1.5, color=MERAH, mutation_scale=12, shrinkA=0, shrinkB=0)
ax.add_patch(b)
c = FancyArrowPatch((LX, 14.6), (CX + 2.3, 14.6), arrowstyle="-|>",
                    linewidth=1.5, color=MERAH, mutation_scale=12, shrinkA=0, shrinkB=2)
ax.add_patch(c)
teks(LX, 13.95, "ya:\ntunda", size=8.0, color=MERAH)
panah(12.75, 11.95, label="tidak")
proses(CX, 11.35, 7.6, 1.2, "Capture 1 frame + warmup AE/AWB 2 dtk",
       "camera_pi.py: Picamera2 \u2192 rpicam-jpeg  |  1296\u00d7972 \u2192 960px", bg=BIRU_BG, line=BIRU)
panah(10.75, 10.05)
belah(CX, 9.5, 5.2, 1.1, "Frame terbaca?", "kamera gagal \u2192 WARN")
# loop "tidak" kiri: keluar sisi kiri, turun, masuk sisi kiri END (coba siklus berikut)
LX2 = CX - 4.6
a = FancyArrowPatch((CX - 2.6, 9.5), (LX2, 9.5), arrowstyle="-",
                    linewidth=1.5, color=MERAH, mutation_scale=12, shrinkA=0, shrinkB=0)
ax.add_patch(a)
b = FancyArrowPatch((LX2, 9.5), (LX2, 0.45), arrowstyle="-",
                    linewidth=1.5, color=MERAH, mutation_scale=12, shrinkA=0, shrinkB=0)
ax.add_patch(b)
c = FancyArrowPatch((LX2, 0.45), (CX - 2.2, 0.45), arrowstyle="-|>",
                    linewidth=1.5, color=MERAH, mutation_scale=12, shrinkA=0, shrinkB=2)
ax.add_patch(c)
teks(LX2, 5.0, "tidak:\nsiklus berikut", size=8.0, color=MERAH)
panah(8.95, 8.15, label="ya")
proses(CX, 7.5, 7.6, 1.3, "CV: bed \u2192 warp \u2192 grid 4\u00d76 \u2192 coverage + kuning/coklat",
       "adaptive_bed.py + kangkung_cv.py  |  EMA \u03b1=0,2", bg=HIJAU_BG, line=HIJAU)
panah(6.85, 6.2)
belah(CX, 5.5, 5.2, 1.1, "Bed terdeteksi?", "pts None \u2192 WARN")
# loop "tidak" kanan: keluar sisi kanan, turun, masuk sisi kanan END
LX3 = CX + 4.6
a = FancyArrowPatch((CX + 2.6, 5.5), (LX3, 5.5), arrowstyle="-",
                    linewidth=1.5, color=MERAH, mutation_scale=12, shrinkA=0, shrinkB=0)
ax.add_patch(a)
b = FancyArrowPatch((LX3, 5.5), (LX3, 0.45), arrowstyle="-",
                    linewidth=1.5, color=MERAH, mutation_scale=12, shrinkA=0, shrinkB=0)
ax.add_patch(b)
c = FancyArrowPatch((LX3, 0.45), (CX + 2.2, 0.45), arrowstyle="-|>",
                    linewidth=1.5, color=MERAH, mutation_scale=12, shrinkA=0, shrinkB=2)
ax.add_patch(c)
teks(LX3, 3.0, "tidak", size=8.0, color=MERAH)
panah(4.95, 4.15, label="ya")
proses(CX, 3.5, 7.6, 1.3, "Hitung PSI + payload \u2192 outbox/*.json + *.jpg",
       "PSI=100\u00b7min(1, 0,4\u00b7kuning/25 + 0,6\u00b7coklat/8)  |  fuzzy_export.py", bg=BIRU_BG, line=BIRU)
panah(2.85, 2.3)
proses(CX, 1.65, 7.6, 1.3, "Sync Firebase \u2192 dashboard + tim fuzzy",
       "outbox \u2192 Storage + bed_readings \u2192 sent/  |  stale/null/ACC/anti-spam", bg=KUNING_BG, line=KUNING_LINE)
panah(1.0, 0.85)
oval(CX, 0.45, 4.4, 0.8, "END (sleep 10 mnt)")

ax.text(0.3, -0.25, "Simbol baku: elips = START/END \u2022 belah ketupat = keputusan \u2022 "
        "kotak = proses \u2022 panah = aliran. "
        "Tanpa aktuasi otomatis: keputusan_fuzzy selalu menunggu_acc.",
        ha="left", va="center", fontsize=7.8, color=MUT)

fig.tight_layout()
fig.savefig(str(OUT), dpi=300, facecolor=BG)
print("OK ->", OUT)
