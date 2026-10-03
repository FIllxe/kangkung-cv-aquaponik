# -*- coding: utf-8 -*-
"""Generator PDF ilustrasi bimbingan ke-3 (2 halaman A4 landscape).

Halaman 1: Desain Wiring/Circuit (Pi + Kamera standalone).
Halaman 2: Flowchart Prinsip Kerja Sistem (siklus kangkung_pi.py).

Jalankan: python docs/buat_pdf_bimbingan3.py
Output  : docs/BIMBINGAN3_WIRING_DAN_FLOWCHART.pdf
Butuh   : docs/BIMBINGAN3_WIRING_PI_KAMERA.png + docs/BIMBINGAN3_FLOWCHART_SISTEM.png
          (dibuat oleh buat_wiring_bimbingan3.py + buat_flowchart_bimbingan3.py)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WIRING = ROOT / "docs" / "BIMBINGAN3_WIRING_PI_KAMERA.png"
FLOW = ROOT / "docs" / "BIMBINGAN3_FLOWCHART_SISTEM.png"
OUT = ROOT / "docs" / "BIMBINGAN3_WIRING_DAN_FLOWCHART.pdf"

JUDUL = ("Bimbingan ke-3 \u2014 Sistem Computer Vision Kangkung Aquaponik "
         "(Felix Enrique, bagian CV)")
KAKI = ("Sumber terverifikasi: raspi/config.json, camera_pi.py, kangkung_pi.py, "
        "fuzzy_export.py, thermal_guard.py, firebase_uplink.py, "
        "docs/SKEMA_FIREBASE_BED_READINGS.md  |  Sisi ESP32/pompa = bagian teman")


def halaman(img_path, judul_hal):
    img = Image.open(img_path).convert("RGB")
    fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape (inci)
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.03, 0.10, 0.94, 0.78])
    ax.imshow(img)
    ax.axis("off")
    fig.text(0.5, 0.95, JUDUL, ha="center", va="center", fontsize=11, fontweight="bold")
    fig.text(0.5, 0.92, judul_hal, ha="center", va="center", fontsize=10, color="#333333")
    fig.text(0.5, 0.035, KAKI, ha="center", va="center", fontsize=6.5, color="#555555")
    return fig


for p in (WIRING, FLOW):
    assert p.exists(), f"belum ada: {p} \u2014 jalankan generator PNG-nya dulu"

with PdfPages(str(OUT)) as pdf:
    pdf.savefig(halaman(WIRING, "Hal. 1/2 \u2014 Desain Wiring / Circuit (Pi + Kamera, standalone)"))
    plt.close("all")
    pdf.savefig(halaman(FLOW, "Hal. 2/2 \u2014 Flowchart Prinsip Kerja Sistem (siklus 10 menit)"))
    plt.close("all")

print("OK ->", OUT)
