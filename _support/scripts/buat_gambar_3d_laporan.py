# -*- coding: utf-8 -*-
"""Halaman gambar 3D siap tempel untuk laporan (dari hardware/renders/HD_*.png).

Empat halaman PNG (300 dpi, latar putih, konsisten dengan BIMBINGAN3_*):
  1. GAMBAR3D_1_RAKITAN.png   - rakitan penuh: isometrik + miring + samping
  2. GAMBAR3D_2_LEDAKAN.png   - exploded view + callout bernomor + legenda
  3. GAMBAR3D_3_XRAY.png      - dinding transparan + angka clearance terverifikasi
  4. GAMBAR3D_4_PART.png      - grid tiap part cetak terpisah

Prasyarat: jalankan `python hardware/buat_gambar_laporan.py` dulu supaya
hardware/renders/HD_*.png ada (latar sudah di-key putih, bebas teal/emas).

Jalankan: python docs/buat_gambar_3d_laporan.py
Catatan : nomor "Gambar 4.x" pada caption adalah default bab hasil -
          sesuaikan di skrip bila bab laporan Anda berbeda.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans"],
    "text.antialiased": True,
})

ROOT = Path(__file__).resolve().parent.parent
HD = ROOT / "hardware" / "renders"
DOCS = ROOT / "docs"

INK = "#1a1a1a"
MUT = "#555555"
CHIP = ["#b71c1c", "#0d47a1", "#1b5e20", "#e65100", "#4a148c", "#006064"]


def halaman(judul: str, sub: str):
    fig = plt.figure(figsize=(16, 9.2))
    fig.patch.set_facecolor("white")
    # Axes mengisi SELURUH figur supaya data-coord (0..16, 0..9.6) memetakan
    # persis ke fraksi figur -> sama dengan add_axes([x/16, y/9.6, ...]) pada
    # pasang(). Ini menjaga label teks dan gambar tetap sejajar.
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9.6)
    ax.axis("off")
    ax.text(8, 9.25, judul, ha="center", va="center",
            fontsize=16, fontweight="bold", color=INK)
    ax.text(8, 8.85, sub, ha="center", va="center",
            fontsize=10, color=MUT)
    return fig, ax


def pasang(fig, rect, path: Path):
    """Letakkan PNG persis di kotak [x,y,w,h] tanpa melar (aspect dipaksa
    pas dengan kotak), koordinat data = piksel gambar (y=0 di bawah)."""
    img = plt.imread(path)
    ih, iw = img.shape[:2]
    x, y, w, h = rect
    rasio = iw / ih
    if w / h > rasio:            # kotak terlalu lebar -> rapatkan lebar
        w2 = h * rasio
        x, w = x + (w - w2) / 2, w2
    else:                         # kotak terlalu tinggi -> rapatkan tinggi
        h2 = w / rasio
        y, h = y + (h - h2) / 2, h2
    ax = fig.add_axes([x / 16, y / 9.6, w / 16, h / 9.6])
    ax.imshow(img, extent=(0, iw, 0, ih), aspect="equal")
    ax.set_xlim(0, iw)
    ax.set_ylim(0, ih)
    ax.axis("off")
    return ax, iw, ih


def kaki(fig, caption: str, sumber: str):
    ax = fig.axes[0]
    ax.text(0.35, 0.42, caption, ha="left", va="center",
            fontsize=11.5, fontweight="bold", color=INK)
    ax.text(0.35, 0.10, sumber, ha="left", va="center",
            fontsize=8.6, color=MUT)
    ax.text(15.65, 0.10, "Model 3D OpenSCAD", ha="right", va="center",
            fontsize=8.6, color=MUT)


# ===========================================================================
# HALAMAN 1 - RAKITAN
# ===========================================================================
def hal_rakit():
    fig, ax = halaman(
        "MODEL 3D \u2014 RAKITAN KAMERA AQUAPONIK",
        "Panjang lengan 150 mm \u2022 sudut kemiringan 0\u00b0 (kamera top-down) \u2022 "
        "klem hollow 40 \u00d7 40 mm \u2022 box enclosure 143,8 \u00d7 90,8 \u00d7 56,8 mm")
    pasang(fig, (0.35, 1.05, 8.9, 7.4), HD / "HD_rakit_iso.png")
    pasang(fig, (9.55, 4.75, 6.1, 3.7), HD / "HD_rakit_miring.png")
    pasang(fig, (9.55, 1.05, 6.1, 3.3), HD / "HD_rakit_samping.png")
    ax.text(4.8, 1.25, "(a) Isometrik", ha="center", fontsize=10.5, color=MUT)
    ax.text(12.6, 4.95, "(b) Miring \u221230\u00b0 \u2013 optik tetap ke bawah",
            ha="center", fontsize=10.5, color=MUT)
    ax.text(12.6, 1.25, "(c) Samping \u2013 bidang mating lengan\u2013box sejajar",
            ha="center", fontsize=10.5, color=MUT)
    kaki(fig,
         "Gambar 4.1 \u2014 Rakitan penuh: klem hollow \u2192 lengan \u2192 pelat ujung "
         "(\u00d72 M4) \u2192 box enclosure (Pi 4B + kamera) + tutup, semuanya rapat pada satu bidang.",
         "Sumber: hardware/preview.scad (mode=rakit) \u2022 OpenSCAD 2021.01 --preview, supersample 2\u00d7, "
         "latar chroma-key putih \u2022 skrip: hardware/buat_gambar_laporan.py + docs/buat_gambar_3d_laporan.py")
    fig.savefig(str(DOCS / "GAMBAR3D_1_RAKITAN.png"), dpi=300, facecolor="white")
    plt.close(fig)


# ===========================================================================
# HALAMAN 2 - LEDAKAN (CALLOUT + LEGENDA)
# ===========================================================================
# Posisi callout = pecahan lebar/tinggi HD_ledakan_iso.png (fy diukur dari atas)
CALLOUT = [
    (1, 0.355, 0.660),   # klem hollow
    (2, 0.400, 0.545),   # lengan/flange
    (3, 0.487, 0.592),   # pelat ujung
    (4, 0.678, 0.575),   # box enclosure
    (5, 0.610, 0.508),   # jepit kamera
    (6, 0.600, 0.283),   # tutup
]

LEGENDA = [
    "Klem hollow 40 \u00d7 40 mm (mount_base) \u2014 cetak PETG",
    "Lengan + flange antarmuka (arm) \u2014 panjang 150 mm",
    "Pelat ujung, \u00d72 baut M4 \u00d7 25 ke paddle enclosure",
    "Box enclosure: Pi 4B + kamera CSI IR + ribbon",
    "Jepit kamera (camera_holder) \u2014 \u00d74 baut M2",
    "Tutup enclosure (enclosure_tutup) \u2014 jalur exhaust",
]


def hal_ledakan():
    fig, ax = halaman(
        "MODEL 3D \u2014 EXPLODED VIEW (RAKITAN TERURAI)",
        "Jarak exploded proporsional per lapis; phantom Pi/kamera dimatikan "
        "supaya hanya part cetak yang tampil")
    axim, iw, ih = pasang(fig, (0.35, 1.05, 10.4, 7.4), HD / "HD_ledakan_iso.png")

    # callout bernomor di atas gambar
    for no, fx, fy in CALLOUT:
        r = iw * 0.016
        cx, cy = fx * iw, (1 - fy) * ih
        axim.add_patch(Circle((cx, cy), r, facecolor=CHIP[no - 1],
                              edgecolor="white", linewidth=2.2, zorder=5))
        axim.text(cx, cy, str(no), ha="center", va="center",
                  fontsize=11.5, fontweight="bold", color="white", zorder=6)

    # legenda kanan
    ax.text(11.15, 8.15, "URUTAN PERAKITAN", fontsize=12,
            fontweight="bold", color=INK)
    for i, teks in enumerate(LEGENDA, start=1):
        y = 7.55 - (i - 1) * 0.97
        ax.add_patch(Circle((11.35, y), 0.17, facecolor=CHIP[i - 1],
                            edgecolor="white", linewidth=1.6))
        ax.text(11.35, y, str(i), ha="center", va="center",
                fontsize=10, fontweight="bold", color="white")
        ax.text(11.75, y, teks, ha="left", va="center",
                fontsize=9.8, color=INK)
    box = FancyBboxPatch((11.0, 0.95), 4.7, 1.35,
                         boxstyle="round,pad=0.10", facecolor="#f5f5f5",
                         edgecolor=MUT, linewidth=1.2)
    ax.add_patch(box)
    ax.text(13.35, 1.85, "Catatan:", ha="center", fontsize=9.6,
            fontweight="bold", color=INK)
    ax.text(13.35, 1.35, "mode ledakan mematikan phantom \u2014 gambar ini\n"
                         "hanya memuat part yang benar-benar dicetak.",
            ha="center", va="center", fontsize=9.2, color=INK)
    kaki(fig,
         "Gambar 4.2 \u2014 Exploded view: klem turun, lengan naik, box menjauh ke arah sumbu "
         "lengan \u00d7 atas; jepit kamera dan tutup naik berlapis.",
         "Sumber: hardware/preview.scad (mode=ledakan, explode=55 mm) \u2022 callout & legenda: "
         "docs/buat_gambar_3d_laporan.py")
    fig.savefig(str(DOCS / "GAMBAR3D_2_LEDAKAN.png"), dpi=300, facecolor="white")
    plt.close(fig)

# ===========================================================================
# HALAMAN 3 - XRAY (CLEARANCE INTERNAL)
# ===========================================================================
def hal_xray():
    fig, ax = halaman(
        "MODEL 3D \u2014 XRAY: CEK RUANG INTERNAL",
        "Dinding enclosure semi transparan (alpha 22%) \u2014 phantom PCB/port "
        "berukuran nyata untuk validasi clearance")
    pasang(fig, (0.35, 1.05, 9.6, 7.4), HD / "HD_xray_iso.png")

    ax.text(10.5, 8.15, "CLEARANCE TERVERIFIKASI", fontsize=12,
            fontweight="bold", color=INK)
    facts = [
        ("Sisi port (sumbu Y)", "clearance 15,0 mm \u2265 RJ45 13,5 mm"),
        ("Sisi tanpa port (X)", "clearance 3,5 mm (toleransi cetak)"),
        ("Ribbon CSI", "jalur kamera \u2192 konektor Pi, tidak terjepit dinding"),
        ("Bukaan", "kamera \u00d830 \u2022 IR \u00d840 \u00d72 \u2022 LDR \u00d810 mm"),
        ("Phantom hollow", "besi 40 \u00d7 40 mm dijepit klem (bukan part cetak)"),
    ]
    for i, (k, v) in enumerate(facts):
        y = 7.42 - i * 0.92
        ax.add_patch(FancyBboxPatch((10.35, y - 0.34), 5.35, 0.74,
                                    boxstyle="round,pad=0.06",
                                    facecolor="#f5f5f5" if i % 2 == 0 else "white",
                                    edgecolor="#cccccc", linewidth=1.0))
        ax.text(10.55, y, k, ha="left", va="center", fontsize=9.6,
                fontweight="bold", color=INK)
        ax.text(10.55, y - 0.30, v, ha="left", va="center", fontsize=9.2,
                color=INK)
    ax.text(13.0, 1.65, "Phantom = skala nyata, hanya untuk review \u2014\n"
                        "tidak dicetak dan tidak ikut di exploded view.",
            ha="center", va="center", fontsize=9.4, color=MUT)
    kaki(fig,
         "Gambar 4.3 \u2014 Xray rakitan: Pi 4B (PCB hijau) dan ribbon terlihat menembus "
         "dinding; posisi port dicek terhadap bukaan dinding sebelum cetak.",
         "Sumber: hardware/preview.scad (mode=xray) \u2022 angka clearance dari hardware/params.scad + "
         "echo preview saat render")
    fig.savefig(str(DOCS / "GAMBAR3D_3_XRAY.png"), dpi=300, facecolor="white")
    plt.close(fig)


# ===========================================================================
# HALAMAN 4 - GRID PART CETAK
# ===========================================================================
PART = [
    ("HD_part_klem.png",   "1. Klem hollow",      "mount_base.scad \u2014 44 cm3"),
    ("HD_part_lengan.png", "2. Lengan + pelat",   "arm.scad \u2014 28 cm3"),
    ("HD_part_box.png",    "3. Box enclosure",    "enclosure.scad \u2014 56 cm3"),
    ("HD_part_tutup.png",  "4. Tutup enclosure",  "enclosure_tutup.scad \u2014 17 cm3"),
    ("HD_part_jepit.png",  "5. Jepit kamera",     "camera_holder.scad \u2014 3 cm3"),
]


def hal_part():
    fig, ax = halaman(
        "MODEL 3D \u2014 TIAP PART CETAK TERPISAH",
        "Orientasi tampil = orientasi cetak (support tidak perlu) \u2022 "
        "volume dari build.ps1 \u2022 semuanya PETG 0,2 mm")
    # baris 1: tiga part, baris 2: dua part (diratakan tengah)
    kotak = [
        (0.55, 4.15, 4.7, 3.9), (5.75, 4.15, 4.7, 3.9), (10.95, 4.15, 4.7, 3.9),
        (3.15, 1.35, 4.7, 2.4), (8.35, 1.35, 4.7, 2.4),
    ]
    for (nama, judul, sub), (x, y, w, h) in zip(PART, kotak):
        _, iw, ih = pasang(fig, (x, y + 0.55, w, h - 0.55), HD / nama)
        cx = x + w / 2
        ax.text(cx, y + 0.30, judul, ha="center", fontsize=11,
                fontweight="bold", color=INK)
        ax.text(cx, y + 0.02, sub, ha="center", fontsize=9.2, color=MUT)
    kaki(fig,
         "Gambar 4.4 \u2014 Lima part cetak: klem, lengan (termasuk pelat ujung), box enclosure, "
         "tutup, dan jepit kamera; semuanya menyatu dengan rakitan pada Gambar 4.1\u20134.2.",
         "Sumber: hardware/*.scad render mandiri \u2022 volume: hardware/build.ps1 \u2022 "
         "orientasi cetak: hardware/README.md")
    fig.savefig(str(DOCS / "GAMBAR3D_4_PART.png"), dpi=300, facecolor="white")
    plt.close(fig)


def main():
    for f, fn in [("rakit", hal_rakit), ("ledakan", hal_ledakan),
                  ("xray", hal_xray), ("part", hal_part)]:
        fn()
        print(f"OK GAMBAR3D_{f}")
    print("Selesai ->", DOCS)


if __name__ == "__main__":
    main()

