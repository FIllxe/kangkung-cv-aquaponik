"""
=============================================================================
  BUAT DUMMY DATASET SAKIT - Kuning ~30% & Coklat ~40% per Zona
  Generator gambar uji sintetis untuk memverifikasi pipeline kesehatan
  daun (mask_tanaman_warna + get_kesehatan) tanpa foto lapangan.
=============================================================================
  CARA PAKAI:
    python buat_dummy_sakit.py
    python buat_dummy_sakit.py --seed 7 --target-kuning 30 --target-coklat 40

  OUTPUT (default: ../output/dummy/):
    dummy_dasar.png               gambar dasar (kanopi hijau, tanpa sakit)
    dummy_kuning_<t>.png          semua zona ~t% kuning thd tanamannya
    dummy_coklat_<t>.png          semua zona ~t% coklat thd tanamannya
    dummy_sakit_pratinjau.png     panel 2x2 + overlay deteksi
    dummy_sakit_ringkasan.json    ringkasan per zona (JSON)

  CATATAN PENTING:
    - % dihitung terhadap piksel TANAMAN per zona (identik rumus produksi:
      analisis_grid / analyze_grid), bukan terhadap luas zona.
    - Pewarnaan bercak divalidasi LOOP-TERTUTUP: setelah tiap iterasi,
      mask detector dijalankan ulang lalu bercak ditambah sampai semua
      zona masuk toleransi (morfologi open membuat % akhir != % awal).
    - Dataset sintetis = alat uji pipeline, BUKAN pengganti mask GT
      untuk evaluasi F1/IoU Bab 4 (lihat docs/PANDUAN_GT.md).
=============================================================================
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kangkung_cv import BED_CONFIG, get_kesehatan
from adaptive_bed import mask_tanaman_warna

# ─── Konfigurasi ─────────────────────────────────────────────────────────────
KANVAS_W, KANVAS_H = 1200, 660          # sama dengan kanvas warp produksi
ROWS = BED_CONFIG["grid_rows"]
COLS = BED_CONFIG["grid_cols"]
CH, CW = KANVAS_H // ROWS, KANVAS_W // COLS

# Rentang HSV daun: selalu lolos mask hijau untuk f adaptif apa pun (0.6-1.6):
#   f>=1 -> floor S/V naik (maks s_lo=v_lo=120); f<1 -> floor diturunkan.
#   muda H 35-75 (V<=200) -> daun V sengaja <=195.
DAUN_H = (40, 70)
DAUN_S = (130, 220)
DAUN_V = (110, 195)
# Air: H 18-30 (di luar hijau 35-85), V <= 70 (di luar kuning V>=80 dan
# coklat V>=85) -> air tidak pernah masuk mask kelas mana pun.
AIR_H = (18, 30)
AIR_S = (15, 60)
AIR_V = (45, 70)

# Warna bercak sakit (di dalam range HSV_KANGKUNG kelas terkait, statis):
SPEC = {
    "kuning": {"h": 27, "s": (180, 230), "v": (200, 235)},  # H21-34, V80-255
    "coklat": {"h": 13, "s": (170, 220), "v": (120, 190)},  # H8-20,  V85-220
}

# Sel zona (batas kiri-atas; sel terakhir memanjang ke tepi kanvas,
# sama seperti analisis_grid)
SEL = []
for _r in range(ROWS):
    for _c in range(COLS):
        _y1 = _r * CH
        _y2 = (_r + 1) * CH if _r < ROWS - 1 else KANVAS_H
        _x1 = _c * CW
        _x2 = (_c + 1) * CW if _c < COLS - 1 else KANVAS_W
        SEL.append((_r, _c, _x1, _y1, _x2, _y2))


# ─── Utilitas ────────────────────────────────────────────────────────────────

def hsv_ke_bgr(h, s, v):
    px = np.uint8([[[int(h), int(s), int(v)]]])
    b, g, r = cv2.cvtColor(px, cv2.COLOR_HSV2BGR)[0, 0]
    return int(b), int(g), int(r)


def buat_dasar(rng):
    """Kanvas bed sintetis: air gelap + kanopi kangkung padat per zona."""
    hsv = np.zeros((KANVAS_H, KANVAS_W, 3), np.uint8)
    hsv[..., 0] = rng.integers(AIR_H[0], AIR_H[1], (KANVAS_H, KANVAS_W))
    hsv[..., 1] = rng.integers(AIR_S[0], AIR_S[1], (KANVAS_H, KANVAS_W))
    hsv[..., 2] = rng.integers(AIR_V[0], AIR_V[1], (KANVAS_H, KANVAS_W))
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    for (_r, _c, x1, y1, x2, y2) in SEL:
        for _ in range(int(rng.integers(26, 34))):
            cx = int(rng.integers(x1 + 10, x2 - 10))
            cy = int(rng.integers(y1 + 10, y2 - 10))
            ax_ = int(rng.integers(12, 38))
            ay = int(rng.integers(8, 24))
            ang = int(rng.integers(0, 180))
            warna = hsv_ke_bgr(rng.integers(*DAUN_H), rng.integers(*DAUN_S),
                               rng.integers(*DAUN_V))
            cv2.ellipse(img, (cx, cy), (ax_, ay), ang, 0, 360, warna, -1)

    img = cv2.GaussianBlur(img, (3, 3), 0.9)
    noise = rng.normal(0.0, 3.0, img.shape)
    return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def ukur(img):
    """% kuning/coklat per zona persis rumus produksi (thd piksel tanaman)."""
    mw = mask_tanaman_warna(img)
    kun, cok, tan = mw["kuning"], mw["coklat"], mw["tanaman"]
    out = []
    for (_r, _c, x1, y1, x2, y2) in SEL:
        tpx = int(tan[y1:y2, x1:x2].sum() // 255)
        if tpx:
            pk = float(kun[y1:y2, x1:x2].sum()) / 255 / tpx * 100
            pc = float(cok[y1:y2, x1:x2].sum()) / 255 / tpx * 100
        else:
            pk = pc = 0.0
        out.append({"zona": f"R{_r+1}C{_c+1}", "pk": pk, "pc": pc,
                    "tpx": tpx, "kes": get_kesehatan(pk, pc)})
    return out


def beri_bercak(img, box, target_px, spec, green_full, rng, maks_titik=400):
    """Warnai ulang piksel HIJAU dalam bercak bulat acak dengan warna sakit.
    Hanya piksel yang saat ini hijau yang diwarnai (luas tanaman tetap,
    denominator % tidak berubah). Return jumlah piksel yang diwarnai."""
    x1, y1, x2, y2 = box
    gz = green_full[y1:y2, x1:x2]
    zh, zw = gz.shape
    patch = np.zeros((zh, zw), np.uint8)
    m = (patch > 0) & (gz > 0)
    for _ in range(maks_titik):
        eff = int(m.sum())
        if eff >= target_px:
            break
        rad = int(np.clip(np.sqrt(max(target_px - eff, 50) / np.pi)
                          * rng.uniform(0.6, 1.4), 6, 26))
        cx = int(rng.integers(rad + 4, max(rad + 5, zw - rad - 4)))
        cy = int(rng.integers(rad + 4, max(rad + 5, zh - rad - 4)))
        cv2.circle(patch, (cx, cy), rad, 255, -1)
        m = (patch > 0) & (gz > 0)

    ys, xs = np.where(m)
    n = len(ys)
    if n == 0:
        return 0
    hs = np.full(n, spec["h"]) + rng.integers(-2, 3, n)
    ss = rng.integers(spec["s"][0], spec["s"][1], n)
    vv = rng.integers(spec["v"][0], spec["v"][1], n)
    hsv_px = np.stack([hs, ss, vv], 1).astype(np.uint8).reshape(-1, 1, 3)
    bgr_px = cv2.cvtColor(hsv_px, cv2.COLOR_HSV2BGR).reshape(-1, 3)
    img[y1:y2, x1:x2][m] = bgr_px
    return n


def jalankan_varian(img, kelas, target, tol, rng, maks_iter=15):
    """Loop-tertutup: ukur -> tambah bercak di zona yang kurang -> ukur ulang."""
    key = "pk" if kelas == "kuning" else "pc"
    iter_dipakai = 0
    for it in range(1, maks_iter + 1):
        hasil = ukur(img)
        green = mask_tanaman_warna(img)["hijau"]
        perlu = []
        for hz, (_r, _c, x1, y1, x2, y2) in zip(hasil, SEL):
            cur_px = hz[key] / 100.0 * hz["tpx"]
            tgt_px = target / 100.0 * hz["tpx"]
            defisit = int(tgt_px - cur_px)
            if defisit > 0 and abs(hz[key] - target) > tol:
                perlu.append(((x1, y1, x2, y2), int(defisit * 0.8)))
        if not perlu:
            break
        for box, px in perlu:
            beri_bercak(img, box, px, SPEC[kelas], green, rng)
        iter_dipakai = it
    return iter_dipakai


# ─── Laporan ─────────────────────────────────────────────────────────────────

def cetak_tabel(judul, hasil):
    print(f"\n  {judul}")
    print("  " + "-" * 64)
    print(f"  {'Zona':<6} {'%Kuning':>8} {'%Coklat':>8} "
          f"{'Tanaman px':>12} {'Kesehatan':>10}")
    print("  " + "-" * 64)
    for hz in hasil:
        print(f"  {hz['zona']:<6} {hz['pk']:>8.1f} {hz['pc']:>8.1f} "
              f"{hz['tpx']:>12,} {hz['kes']:>10}")
    rata_k = float(np.mean([h["pk"] for h in hasil]))
    rata_c = float(np.mean([h["pc"] for h in hasil]))
    print("  " + "-" * 64)
    print(f"  {'RATA':<6} {rata_k:>8.1f} {rata_c:>8.1f}")


def cek_lolos(hasil, kelas, target, tol):
    key = "pk" if kelas == "kuning" else "pc"
    return [(h["zona"], round(h[key], 1))
            for h in hasil if abs(h[key] - target) > tol]


def overlay_deteksi(img):
    """Visual verifikasi: gelapkan gambar, warnai px sesuai mask detector."""
    mw = mask_tanaman_warna(img)
    ov = (img.astype(np.float32) * 0.35).astype(np.uint8)
    ov[mw["hijau"] > 0] = (60, 160, 60)    # BGR hijau
    ov[mw["kuning"] > 0] = (30, 220, 250)  # BGR kuning
    ov[mw["coklat"] > 0] = (30, 80, 160)   # BGR coklat
    return ov


def simpan_pratinjau(out_dir, dasar, img_k, img_c, hasil_k, hasil_c,
                     target_k, target_c):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rk = float(np.mean([h["pk"] for h in hasil_k]))
    rc = float(np.mean([h["pc"] for h in hasil_c]))
    panels = [
        (dasar, "Gambar dasar (sintetis, tanpa sakit)"),
        (img_k, f"Dummy kuning - rata-rata {rk:.1f}%/zona (target {target_k:g}%)"),
        (img_c, f"Dummy coklat - rata-rata {rc:.1f}%/zona (target {target_c:g}%)"),
        (overlay_deteksi(img_k),
         "Verifikasi deteksi (varian kuning): mask hijau/kuning/coklat"),
    ]
    fig, axs = plt.subplots(2, 2, figsize=(16, 9), facecolor="#11141a")
    for ax, (img, judul) in zip(axs.flat, panels):
        ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))   # BGR -> RGB!
        ax.set_title(judul, color="white", fontsize=10.5)
        ax.axis("off")
    fig.suptitle("Dataset Dummy Sakit - Verifikasi Pipeline Kesehatan Daun",
                 color="white", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = out_dir / "dummy_sakit_pratinjau.png"
    fig.savefig(path, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def simpan_json(path, args, hasil_k, hasil_c, it_k, it_c):
    def blok(hasil, kelas, target, it):
        key = "pk" if kelas == "kuning" else "pc"
        vals = [h[key] for h in hasil]
        return {"target_per_zona": target, "iterasi_loop": it,
                "rata": round(float(np.mean(vals)), 2),
                "std": round(float(np.std(vals)), 2),
                "min": round(float(min(vals)), 2),
                "max": round(float(max(vals)), 2),
                "zona": [{"zona": h["zona"],
                          "pct_kuning": round(h["pk"], 2),
                          "pct_coklat": round(h["pc"], 2),
                          "kesehatan": h["kes"]} for h in hasil]}

    data = {
        "dibuat": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "seed": args.seed, "toleransi_persen": args.tol,
        "ukuran_px": f"{KANVAS_W}x{KANVAS_H}", "grid": f"{ROWS}x{COLS}",
        "definisi_persen": "piksel sakit / piksel TANAMAN per zona (produksi)",
        "kuning": blok(hasil_k, "kuning", args.target_kuning, it_k),
        "coklat": blok(hasil_c, "coklat", args.target_coklat, it_c),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Generator dataset dummy sakit (kuning/coklat) per zona")
    ap.add_argument("--out-dir", type=str,
                    default=str(Path(__file__).resolve().parent.parent
                                / "output" / "dummy"))
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--target-kuning", type=float, default=30.0)
    ap.add_argument("--target-coklat", type=float, default=40.0)
    ap.add_argument("--tol", type=float, default=2.0,
                    help="toleransi tiap zona (poin persen)")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    print("=" * 68)
    print(f"  DUMMY DATASET SAKIT - target per zona: "
          f"kuning {args.target_kuning:g}% / coklat {args.target_coklat:g}%")
    print(f"  Kanvas {KANVAS_W}x{KANVAS_H} | grid {ROWS}x{COLS} | "
          f"seed={args.seed} | toleransi +/-{args.tol:g}%")
    print("=" * 68)

    print("\n[1/3] Gambar dasar sintetis (air + kanopi kangkung)...")
    dasar = buat_dasar(rng)
    cv2.imwrite(str(out_dir / "dummy_dasar.png"), dasar)

    print("[2/3] Varian KUNING - loop tertutup per zona...")
    img_k = dasar.copy()
    it_k = jalankan_varian(img_k, "kuning", args.target_kuning, args.tol, rng)
    hasil_k = ukur(img_k)
    f_k = mask_tanaman_warna(img_k)["info_adaptif"]["f"]
    nama_k = f"dummy_kuning_{int(args.target_kuning)}.png"
    cv2.imwrite(str(out_dir / nama_k), img_k)

    print("[3/3] Varian COKLAT - loop tertutup per zona...")
    img_c = dasar.copy()
    it_c = jalankan_varian(img_c, "coklat", args.target_coklat, args.tol, rng)
    hasil_c = ukur(img_c)
    f_c = mask_tanaman_warna(img_c)["info_adaptif"]["f"]
    nama_c = f"dummy_coklat_{int(args.target_coklat)}.png"
    cv2.imwrite(str(out_dir / nama_c), img_c)

    cetak_tabel(f"VARIAN KUNING (f adaptif = {f_k})", hasil_k)
    cetak_tabel(f"VARIAN COKLAT (f adaptif = {f_c})", hasil_c)

    gagal_k = cek_lolos(hasil_k, "kuning", args.target_kuning, args.tol)
    gagal_c = cek_lolos(hasil_c, "coklat", args.target_coklat, args.tol)
    if gagal_k or gagal_c:
        print("\n[GAGAL] Zona di luar toleransi:")
        for z, v in gagal_k:
            print(f"    kuning {z}: {v}% (target {args.target_kuning:g}%)")
        for z, v in gagal_c:
            print(f"    coklat {z}: {v}% (target {args.target_coklat:g}%)")
        sys.exit(1)

    p_pratinjau = simpan_pratinjau(out_dir, dasar, img_k, img_c,
                                   hasil_k, hasil_c,
                                   args.target_kuning, args.target_coklat)
    p_json = simpan_json(out_dir / "dummy_sakit_ringkasan.json",
                         args, hasil_k, hasil_c, it_k, it_c)

    sakit_k = sum(1 for h in hasil_k if h["kes"] == "sakit")
    sakit_c = sum(1 for h in hasil_c if h["kes"] == "sakit")
    rk = float(np.mean([h["pk"] for h in hasil_k]))
    rc = float(np.mean([h["pc"] for h in hasil_c]))

    print("\n[LOLOS] Semua 24 zona dalam toleransi "
          f"+/-{args.tol:g}% -> status 'sakit' di semua zona")
    print(f"  kuning: rata {rk:.1f}% "
          f"(min {min(h['pk'] for h in hasil_k):.1f} / "
          f"max {max(h['pk'] for h in hasil_k):.1f}) | iterasi {it_k} | "
          f"zona sakit {sakit_k}/24")
    print(f"  coklat: rata {rc:.1f}% "
          f"(min {min(h['pc'] for h in hasil_c):.1f} / "
          f"max {max(h['pc'] for h in hasil_c):.1f}) | iterasi {it_c} | "
          f"zona sakit {sakit_c}/24")
    print(f"\n[SELESAI] Output di {out_dir.resolve()}")
    print(f"  - dummy_dasar.png | {nama_k} | {nama_c}")
    print(f"  - {p_pratinjau.name} | {p_json.name}")


if __name__ == "__main__":
    main()



