"""
=============================================================================
  EVALUASI SEGMENTASI — Precision / Recall / F1 / IoU
  Membandingkan hasil segmentasi HSV dengan ground truth (mask manual).

  Untuk Bab 4 skripsi: validasi kuantitatif performa segmentasi.
=============================================================================
  CARA PAKAI:
    python evaluasi_segmentasi.py                        # images/ vs gt/
    python evaluasi_segmentasi.py --images folder_foto --gt folder_gt
    python evaluasi_segmentasi.py --file bed_04_ready.jpg --gt gt

  KONVENSI NAMA GROUND TRUTH (di folder gt/):
    <stem>_gt.png            → mask biner (putih=tanaman, hitam=bukan)
                             → dievaluasi terhadap mask_total
    <stem>_muda.png          → opsional, mask biner per kelas
    <stem>_mature.png        → opsional
    <stem>_kuning.png        → opsional
  (format .jpg juga diterima)

  TIP: gunakan buat_gt.py untuk membuat mask ground truth secara manual.
=============================================================================
"""

import cv2
import numpy as np
import json
import csv
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kangkung_cv import KangkungAnalyzer

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ─── METRIK BINER ────────────────────────────────────────────────────────────

def compute_metrics(gt_mask, pred_mask):
    """
    Hitung metrik evaluasi biner: TP/FP/FN/TN, Precision, Recall,
    F1 (Dice), IoU, Accuracy, Specificity.
    gt_mask & pred_mask: array 2D (nilai > 127 dianggap positif).
    """
    gt = (np.asarray(gt_mask) > 127).astype(np.uint8).ravel()
    pr = (np.asarray(pred_mask) > 127).astype(np.uint8).ravel()

    if gt.shape != pr.shape:
        raise ValueError(f"Bentuk mask tidak sama: gt={gt.shape} vs pred={pr.shape}")

    tp = int(np.sum((gt == 1) & (pr == 1)))
    fp = int(np.sum((gt == 0) & (pr == 1)))
    fn = int(np.sum((gt == 1) & (pr == 0)))
    tn = int(np.sum((gt == 0) & (pr == 0)))

    precision   = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall      = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1          = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    iou         = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
    accuracy    = (tp + tn) / len(gt) if len(gt) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    return {
        "TP": tp, "FP": fp, "FN": fn, "TN": tn,
        "precision":   round(precision, 4),
        "recall":      round(recall, 4),
        "f1":          round(f1, 4),
        "iou":         round(iou, 4),
        "accuracy":    round(accuracy, 4),
        "specificity": round(specificity, 4),
        "gt_coverage_pct":   round(gt.sum() / len(gt) * 100, 2),
        "pred_coverage_pct": round(pr.sum() / len(pr) * 100, 2),
    }


# ─── PENCARIAN GROUND TRUTH ──────────────────────────────────────────────────

def _find_first(gt_dir, stem, suffixes):
    """Cari file GT pertama yang cocok dengan kombinasi stem × suffix × ekstensi."""
    exts = [".png", ".jpg", ".jpeg", ".bmp"]
    for suffix in suffixes:
        for ext in exts:
            cand = gt_dir / f"{stem}{suffix}{ext}"
            if cand.exists():
                return cand
    return None


def find_gt_total(gt_dir, stem):
    return _find_first(gt_dir, stem, ["_gt", ""])


def find_gt_class(gt_dir, stem, cls):
    return _find_first(gt_dir, stem, [f"_{cls}_gt", f"_{cls}"])


def load_mask(path, target_shape):
    """Load mask GT (grayscale) dan resize ke bentuk mask prediksi."""
    m = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        return None
    if m.shape != target_shape:
        m = cv2.resize(m, (target_shape[1], target_shape[0]),
                       interpolation=cv2.INTER_NEAREST)
    return m


# ─── EVALUASI SATU GAMBAR ────────────────────────────────────────────────────

def evaluate_image(fpath, gt_dir):
    """
    Segmentasi satu gambar + hitung metrik vs ground truth.
    Returns: dict hasil, atau None jika GT tidak ditemukan / gagal.
    """
    fpath = Path(fpath)
    stem  = fpath.stem

    gt_total = find_gt_total(gt_dir, stem)
    if gt_total is None:
        print(f"[SKIP] GT tidak ditemukan untuk {fpath.name}")
        return None

    # ── Segmentasi HSV (pipeline utama) ──
    analyzer = KangkungAnalyzer(source=str(fpath))
    analyzer.load_image()
    analyzer.segment()
    analyzer.analyze_grid()

    pred_total = analyzer.mask_total
    gt_mask    = load_mask(gt_total, pred_total.shape)
    if gt_mask is None:
        print(f"[SKIP] GT tidak bisa dibaca: {gt_total.name}")
        return None

    record = {
        "gambar":    fpath.name,
        "gt_file":   gt_total.name,
        "waktu":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total":     compute_metrics(gt_mask, pred_total),
        "per_kelas": {},
    }

    # ── Per kelas (opsional) ──
    for cls, mask_pred in (("muda", analyzer.mask_muda),
                           ("mature", analyzer.mask_mature),
                           ("kuning", analyzer.mask_kuning),
                           ("coklat", analyzer.mask_coklat)):
        gt_cls_path = find_gt_class(gt_dir, stem, cls)
        if gt_cls_path is None:
            continue
        gt_cls = load_mask(gt_cls_path, pred_total.shape)
        if gt_cls is not None:
            record["per_kelas"][cls] = compute_metrics(gt_cls, mask_pred)

    print(f"[OK] {fpath.name}: "
          f"P={record['total']['precision']:.3f} "
          f"R={record['total']['recall']:.3f} "
          f"F1={record['total']['f1']:.3f} "
          f"IoU={record['total']['iou']:.3f}")
    return record


# ─── LAPORAN ─────────────────────────────────────────────────────────────────

def print_tabel(records):
    sep = "=" * 92
    print(f"\n{sep}")
    print("  HASIL EVALUASI SEGMENTASI (vs Ground Truth)")
    print(sep)
    print(f"  {'Gambar':<28} {'Prec':>6} {'Recall':>6} {'F1':>6} {'IoU':>6} "
          f"{'Acc':>6} {'GT%':>6} {'Pred%':>6}")
    print("-" * 92)
    for rec in records:
        m = rec["total"]
        print(f"  {rec['gambar']:<28} {m['precision']:>6.3f} {m['recall']:>6.3f} "
              f"{m['f1']:>6.3f} {m['iou']:>6.3f} {m['accuracy']:>6.3f} "
              f"{m['gt_coverage_pct']:>6.1f} {m['pred_coverage_pct']:>6.1f}")

    if records:
        keys = ["precision", "recall", "f1", "iou", "accuracy"]
        rata = {k: np.mean([r["total"][k] for r in records]) for k in keys}
        print("-" * 92)
        print(f"  {'RATA-RATA':<28} " +
              " ".join(f"{rata[k]:>6.3f}" for k in keys))

        # Per kelas jika ada
        cls_records = [r for r in records if r["per_kelas"]]
        if cls_records:
            print()
            print("  PER KELAS (jika GT per kelas tersedia):")
            for rec in cls_records:
                for cls, m in rec["per_kelas"].items():
                    print(f"    {rec['gambar']:<24} [{cls:>6}] "
                          f"P={m['precision']:.3f} R={m['recall']:.3f} "
                          f"F1={m['f1']:.3f} IoU={m['iou']:.3f}")
    print(sep)


def export_csv(records, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Gambar", "GT_File", "Waktu",
                    "Precision", "Recall", "F1", "IoU", "Accuracy", "Specificity",
                    "TP", "FP", "FN", "TN",
                    "GT_Coverage(%)", "Pred_Coverage(%)"])
        for rec in records:
            m = rec["total"]
            w.writerow([rec["gambar"], rec["gt_file"], rec["waktu"],
                        m["precision"], m["recall"], m["f1"], m["iou"],
                        m["accuracy"], m["specificity"],
                        m["TP"], m["FP"], m["FN"], m["TN"],
                        m["gt_coverage_pct"], m["pred_coverage_pct"]])
    print(f"[INFO] CSV disimpan: {out_path}")


def export_json(records, out_path):
    if records:
        keys = ["precision", "recall", "f1", "iou", "accuracy"]
        rata = {k: round(float(np.mean([r["total"][k] for r in records])), 4) for k in keys}
    else:
        rata = {}
    data = {
        "metadata": {
            "jumlah_gambar": len(records),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "rata_rata": rata,
        "detail": records,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[INFO] JSON disimpan: {out_path}")


def buat_grafik(records, out_path):
    """Bar chart Precision/Recall/F1/IoU per gambar untuk lampiran skripsi."""
    if not records:
        return
    names = [r["gambar"][:20] for r in records]
    f1s   = [r["total"]["f1"] for r in records]
    ious  = [r["total"]["iou"] for r in records]
    prec  = [r["total"]["precision"] for r in records]
    recl  = [r["total"]["recall"] for r in records]

    x = np.arange(len(records))
    wdt = 0.2
    fig, ax = plt.subplots(figsize=(max(8, len(records) * 2), 6),
                           facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")
    for off, vals, label, color in (
            (0, prec, "Precision", "#3498db"),
            (1, recl, "Recall",    "#f39c12"),
            (2, f1s,  "F1-Score",  "#2ecc71"),
            (3, ious, "IoU",       "#e74c3c")):
        bars = ax.bar(x + off * wdt, vals, wdt, label=label, color=color)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}",
                    ha="center", va="bottom", fontsize=7, color="white")
    ax.set_xticks(x + 1.5 * wdt)
    ax.set_xticklabels(names, rotation=20, ha="right", color="white", fontsize=8)
    ax.set_ylim(0, 1.15)
    ax.set_title("Evaluasi Segmentasi HSV vs Ground Truth",
                 color="white", fontsize=12, fontweight="bold")
    ax.tick_params(colors="white")
    ax.legend(facecolor="#1a1a2e", labelcolor="white")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor="#1a1a2e")
    plt.close(fig)
    print(f"[INFO] Grafik disimpan: {out_path}")


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Evaluasi segmentasi HSV vs ground truth (P/R/F1/IoU)")
    parser.add_argument("--images", type=str, default="../dataset1",
                        help="Folder gambar input atau satu file (default: ../dataset1/)")
    parser.add_argument("--gt", type=str, default="gt",
                        help="Folder ground truth mask (default: gt/)")
    args = parser.parse_args()

    img_path = Path(args.images)
    gt_dir   = Path(args.gt)

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

    if not gt_dir.exists():
        print(f"[ERROR] Folder GT tidak ada: {gt_dir.resolve()}")
        print("        Buat ground truth dulu dengan: python buat_gt.py <gambar>")
        sys.exit(1)

    if not image_files:
        print(f"[ERROR] Tidak ada gambar di {img_path}/")
        sys.exit(1)

    print("=" * 68)
    print(f"  EVALUASI SEGMENTASI — {len(image_files)} gambar vs GT")
    print(f"  Input : {img_path.resolve()}")
    print(f"  GT    : {gt_dir.resolve()}")
    print("=" * 68)

    records = []
    for f in image_files:
        try:
            rec = evaluate_image(f, gt_dir)
            if rec:
                records.append(rec)
        except Exception as e:
            print(f"[ERROR] {f.name}: {e}")

    if not records:
        print("\n[WARN] Tidak ada pasangan gambar-GT yang terevaluasi.")
        return

    print_tabel(records)
    export_csv(records, OUTPUT_DIR / "evaluasi_segmentasi.csv")
    export_json(records, OUTPUT_DIR / "evaluasi_segmentasi.json")
    buat_grafik(records, OUTPUT_DIR / "evaluasi_segmentasi.png")


if __name__ == "__main__":
    main()