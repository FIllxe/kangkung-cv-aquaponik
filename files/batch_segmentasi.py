"""
=============================================================================
  BATCH SEGMENTASI — Bed Kangkung Aquaponik
  Auto-discovers semua gambar di folder images/ termasuk foto tambahan.

  CARA PAKAI:
    python3 batch_segmentasi.py                  # proses semua gambar
    python3 batch_segmentasi.py --new-only       # hanya gambar belum diproses
    python3 batch_segmentasi.py --file foto.jpg  # satu gambar spesifik
    python3 batch_segmentasi.py --watch          # mode monitor (auto-detect file baru)
=============================================================================
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import json, os, sys, glob, time, argparse, csv
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kangkung_cv import KangkungAnalyzer, BED_CONFIG, HSV_KANGKUNG

# ─── HSV override untuk gambar sintetis ──────────────────────────────────────
# HANYA aktifkan untuk gambar sintetis/hasil AI. Untuk foto nyata dari
# lapangan, biarkan False (pakai threshold default kangkung_cv.py atau hasil
# kalibrasi_hsv.py). Bisa juga diaktifkan via CLI: python batch_segmentasi.py --synthetic
SYNTHETIC_MODE = False


def apply_synthetic_hsv():
    """Override threshold HSV untuk citra sintetis (panggilan dari CLI --synthetic)."""
    global SYNTHETIC_MODE
    SYNTHETIC_MODE = True
    HSV_KANGKUNG["muda"]["lower"]   = np.array([28,  95, 60])
    HSV_KANGKUNG["muda"]["upper"]   = np.array([90, 255, 255])
    HSV_KANGKUNG["mature"]["lower"] = np.array([32, 100, 45])
    HSV_KANGKUNG["mature"]["upper"] = np.array([90, 255, 245])
    HSV_KANGKUNG["kuning"]["lower"] = np.array([18,  80, 60])
    HSV_KANGKUNG["kuning"]["upper"] = np.array([27, 255, 255])
    print("[WARN] Mode SINTETIS aktif — threshold HSV dioverride untuk citra AI.")

# ─── Konfigurasi path ─────────────────────────────────────────────────────────
IMAGE_DIR  = Path(__file__).resolve().parent.parent / "dataset1"   # gambar bed kangkung
OUTPUT_DIR = (Path(__file__).resolve().parent.parent
              / "output" / "segmentasi_batch")
VALID_EXT  = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

IMAGE_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── Label deskriptif default (opsional) ─────────────────────────────────────
FILE_LABELS = {
    "bed_01_seedling": "Benih (3-5 Hari)",
    "bed_02_young":    "Muda (7-10 Hari)",
    "bed_03_growing":  "Tumbuh (14-18 Hari)",
    "bed_04_ready":    "Siap Panen (25-30 Hari)",
    "bed_05_mixed":    "Campuran Multi-stage",
}


# ─── DISCOVERY ───────────────────────────────────────────────────────────────

def discover_images(image_dir=IMAGE_DIR):
    """
    Scan IMAGE_DIR dan kembalikan list file gambar yang ditemukan.
    Mendukung semua format umum: jpg, png, bmp, tiff, webp.
    """
    files = sorted([
        p for p in Path(image_dir).iterdir()
        if p.is_file()
        and p.suffix.lower() in VALID_EXT
        and not p.stem.endswith("_segmentasi")   # exclude hasil output sendiri
        and not p.stem.endswith("_gt")           # exclude ground truth mask
    ])
    return files


def get_pending_images(image_dir=IMAGE_DIR, output_dir=OUTPUT_DIR):
    """
    Kembalikan hanya gambar yang BELUM diproses
    (tidak ada file _segmentasi.png-nya di output/).
    """
    all_imgs = discover_images(image_dir)
    pending  = []
    for f in all_imgs:
        expected = output_dir / f"{f.stem}_segmentasi.png"
        if not expected.exists():
            pending.append(f)
    return pending


def get_label(fpath):
    return FILE_LABELS.get(Path(fpath).stem, Path(fpath).stem.replace("_", " ").title())


def status_color(status):
    return {
        "belum_siap":  "#3498db",
        "hampir_siap": "#f39c12",
        "siap_panen":  "#2ecc71",
        "harus_panen": "#e74c3c",
    }.get(status, "#aaaaaa")


# ─── PROSES SATU GAMBAR ───────────────────────────────────────────────────────

def proses_gambar(fpath, output_dir=OUTPUT_DIR, show_laporan=True):
    """
    Jalankan segmentasi lengkap pada satu file gambar.
    Returns: analyzer object, atau None jika gagal.
    """
    fpath = Path(fpath)
    stem  = fpath.stem

    try:
        analyzer = KangkungAnalyzer(source=str(fpath))
        analyzer.load_image()
        analyzer.segment()
        analyzer.analyze_grid()

        if show_laporan:
            analyzer.print_laporan()

        viz_path  = output_dir / f"{stem}_segmentasi.png"
        json_path = output_dir / f"{stem}_laporan.json"

        analyzer.visualisasi(save_path=str(viz_path))
        analyzer.export_json(str(json_path))

        return analyzer

    except Exception as e:
        print(f"[ERROR] Gagal memproses {fpath.name}: {e}")
        import traceback; traceback.print_exc()
        return None


# ─── RINGKASAN BATCH ─────────────────────────────────────────────────────────

def buat_zona_grid(ax, analyzer, title=""):
    rows = BED_CONFIG["grid_rows"]
    cols = BED_CONFIG["grid_cols"]
    for r in range(rows):
        for c in range(cols):
            z   = analyzer.zone_results[f"R{r+1}C{c+1}"]
            cov = z["coverage"]
            col = status_color(z["status"])
            ax.add_patch(plt.Rectangle(
                (c/cols, 1-(r+1)/rows), 1/cols-0.01, 1/rows-0.01,
                color=col, alpha=0.85
            ))
            ax.text((c+0.5)/cols, 1-(r+0.5)/rows, f"{cov:.0f}",
                    ha="center", va="center",
                    fontsize=7, fontweight="bold", color="white")
    ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=9, color="#e8f4f8", pad=4)


def buat_ringkasan_batch(results, output_dir=OUTPUT_DIR):
    n   = len(results)
    fig = plt.figure(figsize=(max(4*n+1, 12), 18), facecolor="#1a1a2e")
    gs  = GridSpec(5, n, figure=fig, hspace=0.45, wspace=0.15,
                   left=0.04, right=0.97, top=0.94, bottom=0.05)

    title_c = "#e8f4f8"
    label_c = "#b0c4de"

    fig.suptitle(
        f"KOMPARASI BATCH — Segmentasi Kelebatan Kangkung ({n} Gambar)",
        color=title_c, fontsize=14, fontweight="bold", y=0.97
    )

    legend_patches = [
        mpatches.Patch(color="#3498db", label="Belum Siap  (0-25%)"),
        mpatches.Patch(color="#f39c12", label="Hampir Siap (25-55%)"),
        mpatches.Patch(color="#2ecc71", label="Siap Panen  (55-80%)"),
        mpatches.Patch(color="#e74c3c", label="Harus Panen (>80%)"),
    ]

    for i, (fpath, analyzer) in enumerate(results):
        label   = get_label(fpath)
        gs_stat = analyzer.global_stats

        # Baris 0: Gambar asli
        ax0 = fig.add_subplot(gs[0, i])
        ax0.imshow(analyzer.image_rgb)
        ax0.set_title(label, color=title_c, fontsize=9, pad=4)
        ax0.axis("off")

        # Baris 1: Overlay segmentasi
        ax1 = fig.add_subplot(gs[1, i])
        ov  = analyzer.image_rgb.copy()
        ov[analyzer.mask_muda   > 0] = [80,  220, 120]
        ov[analyzer.mask_mature > 0] = [40,  180,  80]
        ov[analyzer.mask_kuning > 0] = [220, 200,  60]
        ax1.imshow(cv2.addWeighted(analyzer.image_rgb, 0.35, ov, 0.65, 0))
        ax1.set_title("Segmentasi HSV", color=label_c, fontsize=8.5, pad=4)
        ax1.axis("off")
        if i == 0:
            ax1.legend(handles=legend_patches, loc="lower left",
                       fontsize=6, facecolor="#1a1a2e", labelcolor="white",
                       framealpha=0.8)

        # Baris 2: Peta zona
        ax2 = fig.add_subplot(gs[2, i])
        buat_zona_grid(ax2, analyzer, "Peta Zona Coverage")

        # Baris 3: Heatmap
        ax3 = fig.add_subplot(gs[3, i])
        rows_g = BED_CONFIG["grid_rows"]
        cols_g = BED_CONFIG["grid_cols"]
        hmap   = np.array([
            [analyzer.zone_results[f"R{r+1}C{c+1}"]["coverage"]
             for c in range(cols_g)]
            for r in range(rows_g)
        ])
        im = ax3.imshow(hmap, cmap="RdYlGn", vmin=0, vmax=100,
                        aspect="auto", interpolation="bilinear")
        for r in range(rows_g):
            for c in range(cols_g):
                ax3.text(c, r, f"{hmap[r,c]:.0f}",
                         ha="center", va="center",
                         fontsize=6.5, fontweight="bold", color="black")
        ax3.axis("off")
        ax3.set_title("Heatmap Kelebatan", color=label_c, fontsize=8.5, pad=4)

        # Baris 4: Metrik
        ax4 = fig.add_subplot(gs[4, i])
        ax4.set_facecolor("#16213e")
        ax4.axis("off")
        sc   = gs_stat["status_distribusi"]
        vals = [sc[k] for k in sc if sc[k] > 0]
        cols_pie = [status_color(k) for k in sc if sc[k] > 0]
        if vals:
            ax4.pie(vals, colors=cols_pie, radius=0.55, center=(0.5, 0.65),
                    frame=False,
                    wedgeprops={"edgecolor": "#1a1a2e", "linewidth": 0.8})
        ax4.text(0.5, 0.18, f"Cov: {gs_stat['coverage_rata']:.1f}%",
                 ha="center", color="#2ecc71", fontsize=9.5,
                 fontweight="bold", transform=ax4.transAxes)
        ax4.text(0.5, 0.06,
                 f"Skor: {gs_stat['skor_panen_rata']:.0f}/100  |  Siap: {gs_stat['persen_siap']:.0f}%",
                 ha="center", color="#b0c4de", fontsize=7.5,
                 transform=ax4.transAxes)

    out_path = output_dir / "RINGKASAN_BATCH.png"
    plt.savefig(str(out_path), dpi=130, bbox_inches="tight", facecolor="#1a1a2e")
    print(f"[INFO] Ringkasan batch disimpan: {out_path}")
    plt.close(fig)


def export_csv(results, output_dir=OUTPUT_DIR):
    csv_path = output_dir / "ringkasan_batch.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Gambar", "Waktu_Proses", "Coverage_Rata(%)",
                    "Coverage_Std(%)", "Skor_Panen", "Zona_Siap",
                    "Total_Zona", "Persen_Siap(%)",
                    "Belum_Siap", "Hampir_Siap", "Siap_Panen", "Harus_Panen",
                    "Rekomendasi"])
        for fpath, analyzer in results:
            g  = analyzer.global_stats
            sc = g["status_distribusi"]
            w.writerow([
                Path(fpath).name,
                g["timestamp"],
                g["coverage_rata"], g["coverage_std"],
                g["skor_panen_rata"],
                g["zona_siap_panen"], g["total_zona"], g["persen_siap"],
                sc["belum_siap"], sc["hampir_siap"],
                sc["siap_panen"], sc["harus_panen"],
                g["rekomendasi"][:80] + "...",
            ])
    print(f"[INFO] CSV disimpan: {csv_path}")


def cetak_tabel(results):
    sep = "=" * 72
    print(f"\n{sep}")
    print("  TABEL PERBANDINGAN HASIL BATCH")
    print(sep)
    print(f"  {'Gambar':<26} {'Cov%':>6} {'Skor':>5} {'Siap%':>7}  {'Status Dominan'}")
    print("-" * 72)
    for fpath, analyzer in results:
        g  = analyzer.global_stats
        sc = g["status_distribusi"]
        dom = max(sc, key=sc.get)
        print(f"  {Path(fpath).name:<26} {g['coverage_rata']:>5.1f}%"
              f" {g['skor_panen_rata']:>5.0f} {g['persen_siap']:>6.0f}%"
              f"  {dom}")
    print(sep)


# ─── MODE WATCH ──────────────────────────────────────────────────────────────

def watch_mode(image_dir=IMAGE_DIR, output_dir=OUTPUT_DIR, interval=5):
    """
    Monitor folder images/ dan otomatis proses file baru yang ditambahkan.
    Tekan Ctrl+C untuk berhenti.
    """
    print(f"\n[WATCH] Mode monitor aktif — memantau: {image_dir.resolve()}")
    print(f"[WATCH] Interval cek: {interval} detik. Tekan Ctrl+C untuk berhenti.\n")

    known = set(p.name for p in discover_images(image_dir))
    if known:
        print(f"[WATCH] {len(known)} gambar sudah ada: {', '.join(sorted(known))}")

    try:
        while True:
            time.sleep(interval)
            current = set(p.name for p in discover_images(image_dir))
            new_files = current - known

            for fname in sorted(new_files):
                fpath = image_dir / fname
                print(f"\n[WATCH] File baru terdeteksi: {fname}")
                result = proses_gambar(fpath, output_dir)
                if result:
                    g = result.global_stats
                    print(f"[WATCH] Selesai: coverage={g['coverage_rata']:.1f}%, "
                          f"skor={g['skor_panen_rata']:.0f}, "
                          f"siap={g['persen_siap']:.0f}%")
                known.add(fname)

    except KeyboardInterrupt:
        print("\n[WATCH] Monitor dihentikan.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Batch segmentasi kelebatan kangkung aquaponik"
    )
    parser.add_argument("--new-only",  action="store_true",
                        help="Hanya proses gambar yang belum ada outputnya")
    parser.add_argument("--file",      type=str, default=None,
                        help="Proses satu file spesifik saja")
    parser.add_argument("--watch",     action="store_true",
                        help="Mode monitor: auto-proses file baru di images/")
    parser.add_argument("--interval",  type=int, default=5,
                        help="Interval cek watch mode dalam detik (default: 5)")
    parser.add_argument("--no-summary", action="store_true",
                        help="Skip pembuatan RINGKASAN_BATCH.png")
    parser.add_argument("--synthetic", action="store_true",
                        help="Aktifkan override HSV untuk gambar sintetis/AI "
                             "(jangan dipakai untuk foto nyata)")
    parser.add_argument("--image-dir", type=str, default=str(IMAGE_DIR),
                        help=f"Folder gambar input (default: {IMAGE_DIR})")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR),
                        help=f"Folder output (default: {OUTPUT_DIR})")
    args = parser.parse_args()

    # ── Mode sintetis (override HSV) ──────────────────────────────────────────
    if args.synthetic:
        apply_synthetic_hsv()

    img_dir = Path(args.image_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Mode watch ────────────────────────────────────────────────────────────
    if args.watch:
        watch_mode(img_dir, out_dir, args.interval)
        return

    # ── Satu file spesifik ────────────────────────────────────────────────────
    if args.file:
        fpath = Path(args.file)
        if not fpath.exists():
            # Coba cari di IMAGE_DIR
            fpath = img_dir / args.file
        if not fpath.exists():
            print(f"[ERROR] File tidak ditemukan: {args.file}")
            sys.exit(1)
        proses_gambar(fpath, out_dir)
        return

    # ── Batch: semua atau hanya yang baru ─────────────────────────────────────
    if args.new_only:
        image_files = get_pending_images(img_dir, out_dir)
        mode_label  = "gambar BARU (belum diproses)"
    else:
        image_files = discover_images(img_dir)
        mode_label  = "semua gambar"

    if not image_files:
        if args.new_only:
            print("[INFO] Semua gambar sudah diproses. Tidak ada yang baru.")
            print("       Tambahkan foto baru ke folder images/ lalu jalankan ulang.")
        else:
            print(f"[ERROR] Tidak ada gambar ditemukan di '{img_dir}/'")
            print("        Format didukung: .jpg .jpeg .png .bmp .tiff .webp")
        return

    print("=" * 68)
    print(f"  BATCH SEGMENTASI KANGKUNG — {len(image_files)} {mode_label}")
    print(f"  Input : {img_dir.resolve()}")
    print(f"  Output: {out_dir.resolve()}")
    print("=" * 68)

    results = []
    t_start = time.time()

    for idx, fpath in enumerate(image_files, 1):
        print(f"\n[{idx}/{len(image_files)}] {fpath.name}")
        print("-" * 46)
        analyzer = proses_gambar(fpath, out_dir)
        if analyzer:
            results.append((fpath, analyzer))

    elapsed = time.time() - t_start

    if not results:
        print("\n[ERROR] Tidak ada gambar yang berhasil diproses.")
        return

    # ── Output ringkasan ──────────────────────────────────────────────────────
    if not args.no_summary and len(results) > 1:
        print("\n[INFO] Membuat ringkasan komparasi batch...")
        buat_ringkasan_batch(results, out_dir)

    export_csv(results, out_dir)
    cetak_tabel(results)

    print(f"\n  Selesai dalam {elapsed:.1f} detik")
    print(f"  {len(results)} gambar diproses → {out_dir.resolve()}/")
    n_out = len(results) * 2 + (2 if len(results) > 1 else 0)
    print(f"  Total file output: {n_out}")


if __name__ == "__main__":
    main()
