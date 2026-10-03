# -*- coding: utf-8 -*-
"""Generator berkas ilustrasi bimbingan ke-3: Desain Wiring/Circuit.

Cakupan JUJUR (hanya yang terverifikasi di repo):
  - Pi 4B + adaptor 5V/3A USB-C + kamera CSI IR 5MP ov5647 (ribbon CSI) + box
  - microSD, WiFi/Tailscale, Firebase (cloud), dashboard web, tim fuzzy/ESP32
  - TIDAK menggambar detail ESP32/relay/pompa (bagian teman, belum ada di repo)

Jalankan: python docs/buat_wiring_bimbingan3.py
Output  : docs/BIMBINGAN3_WIRING_PI_KAMERA.png  (300 dpi, putih, siap cetak/PDF)
          dipakai juga oleh PDF ilustrasi + PPT putih.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "BIMBINGAN3_WIRING_PI_KAMERA.png"

# --- palet putih / print-friendly ---
BG = "white"
INK = "#1a1a1a"
MUT = "#555555"
HIJAU = "#1b5e20"
HIJAU_BG = "#e8f5e9"
BIRU = "#0d47a1"
BIRU_BG = "#e3f2fd"
KUNING_BG = "#fff8e1"
KUNING_LINE = "#f9a825"
ABU_BG = "#f5f5f5"
MERAH = "#b71c1c"

fig, ax = plt.subplots(figsize=(16, 9.2))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 16)
ax.set_ylim(0, 9.6)
ax.axis("off")

ax.text(8, 9.15, "BIMBINGAN KE-3  \u2014  DESAIN WIRING / CIRCUIT  (Pi + Kamera, standalone)",
        ha="center", va="center", fontsize=15, fontweight="bold", color=INK)
ax.text(8, 8.78, "Sistem Computer Vision Kangkung Aquaponik  \u2014  Felix Enrique (bagian CV)  |  "
        "Raspberry Pi 4B + Kamera CSI IR 5MP ov5647  |  Sisi ESP32/pompa = bagian teman (interface saja)",
        ha="center", va="center", fontsize=9.5, color=MUT)


def box(x, y, w, h, judul, isi, bg, line, tsize=11):
    b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                       facecolor=bg, edgecolor=line, linewidth=1.8)
    ax.add_patch(b)
    baris = isi.split("\n")
    # judul di atas, isi di tengah sisa ruang (dinamis ikut jumlah baris)
    y_judul = y + h - 0.35
    y_isi_top = y + h - 0.95
    y_isi_bottom = y + 0.30
    langkah = (y_isi_top - y_isi_bottom) / max(len(baris) - 1, 1) if len(baris) > 1 else 0
    langkah = min(langkah, 0.42)
    y_mulai = (y_isi_top + y_isi_bottom + langkah * (len(baris) - 1)) / 2
    ax.text(x + w / 2, y_judul, judul, ha="center", va="center",
            fontsize=tsize, fontweight="bold", color=INK)
    for i, br in enumerate(baris):
        ax.text(x + w / 2, y_mulai - i * langkah, br, ha="center",
                va="center", fontsize=8.6, color=INK)
    return b


def panah(x1, y1, x2, y2, label="", ls="-", lw=1.8, col=INK, rad=0.12):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                        linestyle=ls, linewidth=lw, color=col,
                        connectionstyle=f"arc3,rad={rad}",
                        mutation_scale=14, shrinkA=2, shrinkB=4)
    ax.add_patch(a)
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.18, label, ha="center",
                va="center", fontsize=8.4, color=col,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5))


# --- blok kiri: daya ---
box(0.4, 4.6, 2.9, 3.3, "DAYA",
    "Adaptor 5 V / 3 A\nUSB-C resmi\n(bukan charger PD pintar)\n\nmicroSD \u226516 GB\nhigh-endurance",
    ABU_BG, INK)
# --- blok tengah: Pi ---
box(4.1, 3.9, 4.2, 4.0, "RASPBERRY Pi 4B (2 GB)",
    "Debian 13 trixie aarch64\nPython 3.13, venv --system-site-packages\nopencv 4.10 + numpy 1.26.4\n+ firebase-admin 6.5.0\n\nsystemd user: kangkung.service\n(Conflicts: kangkung-camera)",
    HIJAU_BG, HIJAU)
# --- blok kamera ---
box(9.1, 4.6, 3.1, 3.3, "KAMERA CSI IR 5MP",
    "Modul ov5647 night-vision\n+ 2x IR LED 850 nm\nRibbon CSI \u2192 port CSI Pi\n1296\u00d7972, warmup AE/AWB 2 dtk\n\nBox PETG + mount (hardware/)",
    BIRU_BG, BIRU)
# --- blok cloud ---
box(12.9, 4.6, 2.7, 3.3, "CLOUD + USER",
    "Firestore: bed_readings\nStorage: snapshots/*.jpg\nDashboard web (read-only)\nRemote: SSH via Tailscale",
    KUNING_BG, KUNING_LINE)
# --- blok bawah: interface teman ---
box(3.3, 0.9, 9.4, 2.4, "INTERFACE KE TIM FUZZY / ESP32 (bagian teman \u2014 bukan wiring saya)",
    "Pi HANYA menulis fuzzy_input ke bed_readings:\n"
    "{ psi, psi_maks, zona_sakit, psi_versi }\n"
    "ESP32/teman membaca \u2192 keputusan_fuzzy (menunggu_acc)\n"
    "\u2192 ACC manusia \u2192 pompa\n"
    "Aman: stale >30 mnt ditolak \u2022 null = tahan \u2022 tanpa aktuasi otomatis \u2022 anti-spam 60 mnt",
    "white", MERAH, tsize=10.5)

# --- koneksi fisik ---
panah(3.3, 6.45, 4.1, 6.45, "USB-C 5V/3A")
panah(8.3, 6.45, 9.1, 6.45, "Ribbon CSI")
panah(12.2, 6.3, 12.9, 6.3, "WiFi", lw=1.8, col=BIRU)
panah(6.2, 4.0, 6.2, 3.3, "menulis fuzzy_input", lw=1.4, col=MERAH, rad=-0.15)
panah(9.9, 4.6, 9.9, 3.3, "dibaca tim fuzzy", lw=1.4, col=MERAH, rad=0.15)

# --- catatan kaki ---
ax.text(0.4, 0.55, "Catatan: Pi push-only (tidak melayani koneksi masuk). Kamera CSI eksklusif: monitor periodik \u22bb preview live "
        "(Conflicts di systemd). Thermal guard menunda capture bila SoC > 75 \u00b0C.",
        ha="left", va="center", fontsize=8.4, color=MUT)
ax.text(0.4, 0.18, "Sumber terverifikasi: raspi/config.json \u2022 raspi/camera_pi.py \u2022 raspi/kangkung_pi.py \u2022 "
        "raspi/service/*.service \u2022 hardware/params.scad \u2022 docs/SKEMA_FIREBASE_BED_READINGS.md",
        ha="left", va="center", fontsize=8.0, color=MUT)
ax.text(15.6, 0.18, "Bimbingan ke-3", ha="right", va="center", fontsize=8.0, color=MUT)

fig.tight_layout()
fig.savefig(str(OUT), dpi=300, facecolor=BG)
print("OK ->", OUT)
