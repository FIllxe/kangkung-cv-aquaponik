"""
=============================================================================
  BUAT DEMO DUA VIDEO — IMG_5159 vs IMG_5388
  Panel demo: frame beranotasi kedua video + perbandingan coverage 24 zona
              + distribusi status panen + JSON statistik gabungan
=============================================================================
  CARA PAKAI (jalankan dari folder files):
    python buat_demo_dua_video.py
  INPUT  (output/demo/):  ringkasan_IMG_5159.json, ringkasan_IMG_5388.json,
                          IMG_5159_beranotasi.mp4, IMG_5388_beranotasi.mp4
  OUTPUT (output/demo/):  demo_dua_video.png, demo_dua_video.json
=============================================================================
"""

import cv2
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(ROOT, "output", "demo")

VIDEOS = [
    ("IMG_5159", "IMG_5159 (12.7s, 763 frame)"),
    ("IMG_5388", "IMG_5388 (7.1s, 425 frame)"),
]
ZONA_IDS = [f"R{r}C{c}" for r in range(1, 5) for c in range(1, 7)]
STATUS_LABEL = {
    "belum_siap":   ("Belum siap", "#b04a3a"),
    "hampir_siap":  ("Hampir siap", "#d9a03c"),
    "siap_panen":   ("Siap panen", "#4a9b4f"),
    "harus_panen":  ("Harus panen", "#2f7d32"),
}


def muat_ringkasan(stem):
    path = os.path.join(DEMO_DIR, f"ringkasan_{stem}.json")
    with open(path, encoding="utf-8") as f:
        rk = json.load(f)
    n = max(1, int(rk["n"]))
    cov_global = rk["tot_cov"] / n
    cov_zona = np.array(rk["sum_coverage"]) / n
    status = rk["status_count"]
    return {
        "stem": stem, "n": int(rk["n"]),
        "cov_global": round(cov_global, 1),
        "cov_zona": [round(float(x), 1) for x in cov_zona],
        "status": status,
        "tot_status": sum(status.values()),
    }


def ekstrak_frame(stem):
    """Ambil frame tengah dari video beranotasi (BGR -> RGB)."""
    path = os.path.join(DEMO_DIR, f"{stem}_beranotasi.mp4")
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, n // 2))
    ok, frame = cap.read()
    if not ok:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Gagal membaca frame dari {path}")
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def main():
    print("=" * 62)
    print("  DEMO DUA VIDEO — IMG_5159 vs IMG_5388")
    print("=" * 62)

    data = [muat_ringkasan(stem) for stem, _ in VIDEOS]
    frames = [ekstrak_frame(stem) for stem, _ in VIDEOS]
    for d in data:
        print(f"[OK] {d['stem']}: n={d['n']}  cov_global={d['cov_global']}%  "
              f"status={d['status']}")

    fig = plt.figure(figsize=(16, 9), facecolor="#f4f4f0")
    fig.suptitle("Demo Computer Vision Aquaponik — Dua Video (Mode Adaptive)",
                 fontsize=17, fontweight="bold", y=0.975)

    # ─── Baris 1: frame beranotasi kedua video ───
    for i, (d, frame) in enumerate(zip(data, frames)):
        ax = fig.add_axes([0.045 + i * 0.475, 0.47, 0.44, 0.40])
        ax.imshow(frame)
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_title(f"{VIDEOS[i][1]}  —  coverage rata-rata {d['cov_global']}%",
                     fontsize=11.5, pad=6)
        for spine in ax.spines.values():
            spine.set_color("#888")

    # ─── Baris 2 kiri: perbandingan coverage per zona ───
    ax1 = fig.add_axes([0.055, 0.07, 0.42, 0.30])
    x = np.arange(len(ZONA_IDS))
    w = 0.38
    ax1.bar(x - w / 2, data[0]["cov_zona"], w, label=data[0]["stem"],
            color="#3d7ab5", edgecolor="white", linewidth=0.4)
    ax1.bar(x + w / 2, data[1]["cov_zona"], w, label=data[1]["stem"],
            color="#c97b3d", edgecolor="white", linewidth=0.4)
    ax1.set_xticks(x[::3]), ax1.set_xticklabels(ZONA_IDS[::3], fontsize=7.5)
    ax1.set_ylabel("Coverage rata-rata (%)", fontsize=9.5)
    ax1.set_title("Coverage per zona (grid 4x6)", fontsize=11.5, pad=6)
    ax1.legend(fontsize=9), ax1.grid(axis="y", alpha=0.3, linewidth=0.5)
    ax1.set_axisbelow(True)

    # ─── Baris 2 kanan: distribusi status panen ───
    ax2 = fig.add_axes([0.53, 0.07, 0.40, 0.30])
    keys = ["belum_siap", "hampir_siap", "siap_panen", "harus_panen"]
    tot = np.array([d["tot_status"] for d in data])
    y = np.arange(2)
    bottom = np.zeros(2)
    for k in keys:
        val = np.array([d["status"].get(k, 0) for d in data]) / tot * 100
        label, warna = STATUS_LABEL[k]
        ax2.barh(y, val, left=bottom, height=0.5, label=label,
                 color=warna, edgecolor="white", linewidth=0.8)
        for j in range(2):
            if val[j] >= 7:
                ax2.text(bottom[j] + val[j] / 2, y[j], f"{val[j]:.0f}%",
                         ha="center", va="center", fontsize=8.5,
                         color="white", fontweight="bold")
        bottom += val
    ax2.set_yticks(y)
    ax2.set_yticklabels([d["stem"] for d in data], fontsize=9.5)
    ax2.set_xlim(0, 100), ax2.set_xlabel("Distribusi status (%)", fontsize=9.5)
    ax2.set_title("Distribusi status panen", fontsize=11.5, pad=6)
    ax2.legend(fontsize=8.5, ncol=2, loc="upper center",
               bbox_to_anchor=(0.5, -0.22), frameon=False)

    out_png = os.path.join(DEMO_DIR, "demo_dua_video.png")
    fig.savefig(out_png, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] Panel demo tersimpan: {out_png}")

    out_json = os.path.join(DEMO_DIR, "demo_dua_video.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "deskripsi": "Demo dua video: IMG_5159 vs IMG_5388, mode ADAPTIVE",
            "mode": "ADAPTIVE", "jumlah_zona": 24, "zona": ZONA_IDS,
            "video": data,
        }, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON demo tersimpan: {out_json}")


if __name__ == "__main__":
    main()

