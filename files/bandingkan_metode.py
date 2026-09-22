"""
=============================================================================
  PERBANDINGAN METODE SEGMENTASI — untuk Bab 4 skripsi
  HSV (pipeline utama)  vs  ExG (Excess Green)  vs  Otsu-Hue
=============================================================================
  CARA PAKAI:
    python bandingkan_metode.py                       # semua gambar di images/
    python bandingkan_metode.py --file bed_04_ready.jpg
    python bandingkan_metode.py --gt gt               # hitung metrik vs GT juga

  Output:
    output/perbandingan_metode.csv   → tabel metrik per metode per gambar
    output/perbandingan_<stem>.png   → visual perbandingan mask 3 metode
    output/perbandingan_metode.png   → grafik summary (jika GT tersedia)

  Referensi:
    - ExG: Woebbecke et al. (1995), "Color indices for weed identification
      under field conditions" — 2G-R-B pada RGB ternormalisasi + Otsu.
    - Otsu-Hue: thresholding otomatis pada channel Hue (piksel vegetasi),
      Otsu (1979) + seleksi saturasi.
=============================================================================
"""

import cv2
import numpy as np
import csv
import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kangkung_cv import HSV_KANGKUNG
from evaluasi_segmentasi import compute_metrics, find_gt_total, load_mask

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ─── METODE 1: HSV (pipeline utama kangkung_cv.py) ───────────────────────────

def segment_hsv(img_bgr):
    """Segmentasi HSV 3 kelas + morfologi — sama dengan pipeline utama."""
    t0 = time.perf_counter()
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    mask_muda   = cv2.inRange(hsv, HSV_KANGKUNG["muda"]["lower"],
                                    HSV_KANGKUNG["muda"]["upper"])
    mask_mature = cv2.inRange(hsv, HSV_KANGKUNG["mature"]["lower"],
                                    HSV_KANGKUNG["mature"]["upper"])
    mask = cv2.bitwise_or(mask_muda, mask_mature)

    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k7 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k3)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k7)

    return mask, (time.perf_counter() - t0) * 1000


# ─── METODE 2: ExG (Excess Green + Otsu) ─────────────────────────────────────

def segment_exg(img_bgr):
    """
    ExG = 2g - r - b (RGB ternormalisasi, Woebbecke 1995) + threshold Otsu.
    Metode pembanding klasik untuk deteksi vegetasi.
    """
    t0 = time.perf_counter()
    b, g, r = cv2.split(img_bgr.astype(np.float32))
    total = b + g + r + 1e-6
    r_n, g_n, b_n = r / total, g / total, b / total

    exg = 2.0 * g_n - r_n - b_n
    exg_u8 = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    _, mask = cv2.threshold(exg_u8, 0, 255,
                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k7 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k3)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k7)

    return mask, (time.perf_counter() - t0) * 1000


# ─── METODE 3: Otsu-Hue (threshold otomatis pada Hue) ────────────────────────

def segment_otsu_hue(img_bgr):
    """
    Otsu pada channel Hue, hanya untuk piksel kandidat vegetasi
    (S & V cukup tinggi). Threshold otomatis — tidak perlu kalibrasi manual.
    """
    t0 = time.perf_counter()
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # Kandidat vegetasi: hue hijau-kuning (20–100), saturasi & value cukup
    base = cv2.inRange(hsv, np.array([20, 40, 40]), np.array([100, 255, 255]))

    cand_hues = h[base > 0]
    if cand_hues.size == 0:
        return np.zeros_like(h), (time.perf_counter() - t0) * 1000

    # Otsu pada histogram hue kandidat
    _, _ = cv2.threshold(cand_hues, 0, 255,
                         cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    t_otsu = float(np.mean([cv2.threshold(cand_hues, 0, 255,
                                          cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]]))

    mask = np.where((base > 0) & (h >= t_otsu), 255, 0).astype(np.uint8)

    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k7 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  k3)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k7)

    return mask, (time.perf_counter() - t0) * 1000


METODE = {
    "HSV":      segment_hsv,
    "ExG":      segment_exg,
    "Otsu-Hue": segment_otsu_hue,
}


# ─── EVALUASI SATU GAMBAR ────────────────────────────────────────────────────

def coverage_pct(mask):
    return mask.sum() / 255 / mask.size * 100


def evaluate_all_methods(fpath, gt_dir=None):
    """Jalankan 3 metode pada satu gambar. Returns list record per metode."""
    img = cv2.imread(str(fpath))
    if img is None:
        print(f"[ERROR] Tidak bisa membaca: {fpath}")
        return []

    gt_mask = None
    if gt_dir is not None:
        gt_path = find_gt_total(gt_dir, Path(fpath).stem)
        if gt_path is not None:
            probe = METODE["HSV"](img)[0]
            gt_mask = load_mask(gt_path, probe.shape)

    records = []
    for nama, fn in METODE.items():
        mask, ms = fn(img)
        rec = {
            "gambar":       Path(fpath).name,
            "metode":       nama,
            "waktu":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "coverage_pct": round(coverage_pct(mask), 2),
            "waktu_ms":     round(ms, 1),
        }
        if gt_mask is not None:
            m = compute_metrics(gt_mask, mask)
            rec.update({k: m[k] for k in
                        ("precision", "recall", "f1", "iou", "accuracy")})
            rec["gt_coverage_pct"] = m["gt_coverage_pct"]
        records.append(rec)
        line = (f"  {nama:<9} coverage={rec['coverage_pct']:>6.2f}%  "
                f"waktu={rec['waktu_ms']:>6.1f} ms")
        if gt_mask is not None:
            line += (f"  P={rec['precision']:.3f} R={rec['recall']:.3f} "
                     f"F1={rec['f1']:.3f} IoU={rec['iou']:.3f}")
        print(line)

    # ── Visual perbandingan ──
    simpan_visual(img, fpath, records)
    return records


def simpan_visual(img_bgr, fpath, records):
    """Panel perbandingan: gambar asli + hasil 3 metode."""
    n = len(records)
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    fig, axes = plt.subplots(1, n + 1, figsize=(4 * (n + 1), 4.5),
                             facecolor="#1a1a2e")
    fig.suptitle(f"Perbandingan Metode — {Path(fpath).name}",
                 color="white", fontsize=12, fontweight="bold")

    axes[0].imshow(rgb)
    axes[0].set_title("Asli", color="white", fontsize=10)
    axes[0].axis("off")

    for ax, rec in zip(axes[1:], records):
        mask, _ = METODE[rec["metode"]](img_bgr)
        ov = rgb.copy()
        ov[mask > 0] = [80, 220, 120]
        ax.imshow(cv2.addWeighted(rgb, 0.4, ov, 0.6, 0))
        judul = f"{rec['metode']} ({rec['coverage_pct']:.1f}%)"
        if "f1" in rec:
            judul += f"\nF1={rec['f1']:.3f} IoU={rec['iou']:.3f}"
        ax.set_title(judul, color="white", fontsize=9)
        ax.axis("off")

    fig.tight_layout()
    out = OUTPUT_DIR / f"perbandingan_{Path(fpath).stem}.png"
    fig.savefig(out, dpi=130, facecolor="#1a1a2e")
    plt.close(fig)
    print(f"  [INFO] Visual disimpan: {out}")


# ─── EXPORT ──────────────────────────────────────────────────────────────────

def export_csv(records, out_path):
    if not records:
        return
    fields = list(records[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(records)
    print(f"[INFO] CSV disimpan: {out_path}")


def buat_grafik_summary(all_records, out_path):
    """Bar chart F1 & IoU rata-rata per metode (hanya jika GT tersedia)."""
    if not all_records or "f1" not in all_records[0]:
        return
    metodes = list(METODE.keys())
    rata = {m: {"f1": [], "iou": []} for m in metodes}
    for rec in all_records:
        if "f1" in rec and rec["metode"] in rata:
            rata[rec["metode"]]["f1"].append(rec["f1"])
            rata[rec["metode"]]["iou"].append(rec["iou"])

    x = np.arange(len(metodes))
    wdt = 0.35
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")
    f1_vals  = [np.mean(rata[m]["f1"])  if rata[m]["f1"]  else 0 for m in metodes]
    iou_vals = [np.mean(rata[m]["iou"]) if rata[m]["iou"] else 0 for m in metodes]
    b1 = ax.bar(x - wdt / 2, f1_vals,  wdt, label="F1-Score", color="#2ecc71")
    b2 = ax.bar(x + wdt / 2, iou_vals, wdt, label="IoU",      color="#3498db")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.01,
                    f"{b.get_height():.3f}", ha="center", va="bottom",
                    fontsize=9, color="white")
    ax.set_xticks(x)
    ax.set_xticklabels(metodes, color="white", fontsize=11)
    ax.set_ylim(0, 1.15)
    ax.set_title("Rata-rata F1 & IoU per Metode Segmentasi",
                 color="white", fontsize=12, fontweight="bold")
    ax.tick_params(colors="white")
    ax.legend(facecolor="#1a1a2e", labelcolor="white")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor="#1a1a2e")
    plt.close(fig)
    print(f"[INFO] Grafik summary disimpan: {out_path}")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Perbandingan metode segmentasi: HSV vs ExG vs Otsu-Hue")
    parser.add_argument("--images", type=str, default="../dataset1",
                        help="Folder gambar atau satu file (default: ../dataset1/)")
    parser.add_argument("--gt", type=str, default=None,
                        help="Folder ground truth (opsional — untuk metrik)")
    args = parser.parse_args()

    img_path = Path(args.images)
    gt_dir   = Path(args.gt) if args.gt else None

    if img_path.is_file():
        image_files = [img_path]
    elif img_path.is_dir():
        exts = {".jpg", ".jpeg", ".png", ".bmp"}
        image_files = sorted(p for p in img_path.iterdir()
                             if p.is_file() and p.suffix.lower() in exts
                             and not p.stem.endswith("_gt")
                             and not p.stem.endswith("_segmentasi"))
    else:
        print(f"[ERROR] Path tidak ditemukan: {img_path}")
        sys.exit(1)

    if not image_files:
        print(f"[ERROR] Tidak ada gambar di {img_path}/")
        sys.exit(1)

    print("=" * 68)
    print(f"  PERBANDINGAN METODE SEGMENTASI — {len(image_files)} gambar")
    print("  Metode: HSV | ExG | Otsu-Hue")
    if gt_dir:
        print(f"  GT    : {gt_dir.resolve()}")
    print("=" * 68)

    all_records = []
    for f in image_files:
        print(f"\n{f.name}")
        print("-" * 46)
        try:
            all_records.extend(evaluate_all_methods(f, gt_dir))
        except Exception as e:
            print(f"[ERROR] {f.name}: {e}")

    if all_records:
        export_csv(all_records, OUTPUT_DIR / "perbandingan_metode.csv")
        buat_grafik_summary(all_records, OUTPUT_DIR / "perbandingan_metode.png")
        print("\n[SELESAI] Buka output/perbandingan_metode.csv untuk tabel Bab 4.")


if __name__ == "__main__":
    main()