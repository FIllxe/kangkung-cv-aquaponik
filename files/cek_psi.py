"""
=============================================================================
  CEK PSI — validasi indeks stres & konsistensi antar jalur segmentasi
=============================================================================
  CARA PAKAI:
    python cek_psi.py                          # paritas 2 dummy + tabel PSI
    python cek_psi.py --gambar <img>           # uji paritas pada 1 gambar
    python cek_psi.py --laporan a.json b.json  # tabel PSI dari laporan/payload
=============================================================================
  Yang dicek:

  1) PARITAS SEGMENTASI (regression test). Dua jalur resmi harus memberi
     angka IDENTIK pada gambar yang sama:
       - kangkung_cv.KangkungAnalyzer.segment()  -> gate adjacency via mask_clean
       - adaptive_bed.mask_tanaman_warna()      -> gate adjacency via mask_tanaman
     Dulunya jalur CLI memakai hijau RAW untuk gate adjacency, sehingga
     %coklat terbaca 48% sedangkan jalur live/Pi 39% (beda 9 poin persentase).
     Angka inilah yang menjadi PSI, jadi selisih > 0,5 pp = FAIL.

  2) TABEL PSI per sumber (laporan pipeline / payload Firebase):
       PSI v2.0 = 100*(0.5*Y + B)/N  dari jumlah piksel mentah
       PSI lama = min(100, 2*kuning + 5*coklat)   -> kolom "jenuh?"
     Kolom "jenuh?" menandai sumber yang sudah mentok di 100 sehingga kontroler
     fuzzy kehilangan gradien di area paling penting.
=============================================================================
"""

import argparse
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kangkung_cv import (KangkungAnalyzer, BED_CONFIG, PSI_VERSION,
                         PSI_BOBOT, hitung_psi, hitung_psi_persen,
                         hasil_psi, gabung_psi)
from adaptive_bed import mask_tanaman_warna

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DUMMY = ROOT / "output" / "dummy"
TOLERANSI_PP = 0.5
TOL_RUMUS = 1e-9          # toleransi absolut unit test rumus (spesifikasi §9)


# ─── 1) Unit test rumus PSI (spesifikasi PSI v2.0) ───────────────────────────

# (G, Y, B) -> PSI yang diharapkan — 8 kasus wajib dari spesifikasi §4
KASUS_PSI = [
    ((1000, 0, 0),     0.0),
    ((0, 1000, 0),    50.0),
    ((0, 0, 1000),   100.0),
    ((800, 150, 50),  12.5),
    ((600, 300, 100), 25.0),
    ((400, 400, 200), 40.0),
    ((0, 500, 500),   75.0),
    ((300, 400, 300), 50.0),
]


def uji_rumus() -> bool:
    """Uji rumus, agregasi, invariansi, dan kontrak validitas. True = lolos."""
    ok = True

    print("\nUNIT TEST RUMUS PSI  "
          f"(PSI = 100*(0.5*Y + B)/N, toleransi {TOL_RUMUS:g})")
    print(f"  {'G':>6}{'Y':>6}{'B':>6}{'N':>7}{'harapan':>10}"
          f"{'hasil':>12}{'selisih':>12}  status")
    for (g, y, b), harap in KASUS_PSI:
        psi = hitung_psi(g, y, b)
        selisih = abs(psi - harap)
        lolos = psi is not None and selisih <= TOL_RUMUS
        ok &= lolos
        print(f"  {g:>6}{y:>6}{b:>6}{g+y+b:>7}{harap:>10.4f}"
              f"{psi:>12.6f}{selisih:>12.1e}  {'OK' if lolos else 'FAIL'}")

    # ── N = 0: PSI tidak tersedia, BUKAN 0 ────────────────────────────────
    cek = [
        ("N=0 -> None (bukan PSI 0)", hitung_psi(0, 0, 0) is None),
        ("masukan negatif -> None", hitung_psi(-10, 5, 5) is None),
        ("masukan pecahan -> None", hitung_psi(10.5, 5, 5) is None),
        ("masukan non-angka -> None", hitung_psi("x", 5, 5) is None),
        ("hasil selalu 0-100", all(0.0 <= hitung_psi(*c) <= 100.0
                                   for c, _ in KASUS_PSI)),
        # skala: semua jumlah piksel x konstanta -> PSI tak berubah
        ("invarian skala x7", all(
            abs(hitung_psi(g * 7, y * 7, b * 7) - harap) <= TOL_RUMUS
            for (g, y, b), harap in KASUS_PSI)),
        # gradien linier pada N tetap: 1 px hijau->kuning naik 50/N, dst
        ("hijau->kuning naik 50/N", abs(
            hitung_psi(999, 1, 0) - hitung_psi(1000, 0, 0) - 0.05) <= TOL_RUMUS),
        ("hijau->coklat naik 100/N", abs(
            hitung_psi(999, 0, 1) - hitung_psi(1000, 0, 0) - 0.1) <= TOL_RUMUS),
        ("kuning->coklat naik 50/N", abs(
            hitung_psi(0, 999, 1) - hitung_psi(0, 1000, 0) - 0.05) <= TOL_RUMUS),
        # bentuk persentase setara bentuk piksel
        ("paritas piksel vs persentase", abs(
            hitung_psi(800, 150, 50) -
            hitung_psi_persen(15.0, 5.0)) <= TOL_RUMUS),
        ("persentase tak sah -> None", hitung_psi_persen(-1, 0) is None),
        ("bobot kategori 0 / 0,5 / 1",
         (PSI_BOBOT["hijau"], PSI_BOBOT["kuning"], PSI_BOBOT["coklat"])
         == (0.0, 0.5, 1.0)),
    ]

    # ── Agregasi grid: jumlahkan piksel, JANGAN rata-rata PSI (§4) ─────────
    psi_grid, (g, y, b) = gabung_psi([
        {"green": 900, "yellow": 0, "brown": 0},    # PSI zona = 0
        {"green": 0, "yellow": 0, "brown": 100},    # PSI zona = 100
    ])
    cek += [
        ("agregasi grid = 10 (bukan rata-rata 50)",
         abs(psi_grid - 10.0) <= TOL_RUMUS),
        ("grid kosong semua -> None",
         gabung_psi([{"green": 0, "yellow": 0, "brown": 0}])[0] is None),
        ("total piksel terhitung benar", (g, y, b) == (900, 0, 100)),
    ]

    # ── Kontrak validitas ─────────────────────────────────────────────────
    # Catatan: plant_mask_pixels harus >= PSI_MIN_TANAMAN_PX agar lolos ke
    # pemeriksaan berikutnya (kecuali kasus yang memang menguji ambang itu).
    v_ok = hasil_psi(900, 50, 50, plant_mask_pixels=1000,
                     captured_at_ms=1_760_000_000_000, frame_id="f-001")
    # varian luas memadai (>= PSI_MIN_TANAMAN_PX) untuk kasus hasil valid
    v_valid = hasil_psi(9000, 500, 500, plant_mask_pixels=10000,
                        frame_id="f-006")
    v_nol = hasil_psi(500, 0, 0, plant_mask_pixels=500, frame_id="f-002")
    v_kosong = hasil_psi(0, 0, 0, plant_mask_pixels=0, frame_id="f-003")
    v_kecil = hasil_psi(10, 0, 0, plant_mask_pixels=10, frame_id="f-004")
    v_uncl = hasil_psi(800, 0, 0, plant_mask_pixels=4000,
                       unclassified_pixels=3000, frame_id="f-005")
    cek += [
        # (0.5*50 + 50)/1000*100 = 7,5  — rasio sama dengan kasus (900,50,50)
        ("hasil valid: psi + valid + reason ok",
         v_valid["valid"] and v_valid["reason"] == "ok"
         and abs(v_valid["psi"] - 7.5) <= TOL_RUMUS),
        ("invarian skala juga berlaku di kontrak hasil",
         abs(v_valid["psi"] - hitung_psi(900, 50, 50)) <= TOL_RUMUS),
        ("luas di bawah ambang walau N > 0 -> tidak valid",
         not v_ok["valid"] and v_ok["reason"] == "insufficient_plant_area"),
        ("N=0 -> reason no_plant_pixels, psi None",
         v_kosong["reason"] == "no_plant_pixels" and v_kosong["psi"] is None),
        # 500 px hijau masih di bawah ambang minimum area -> tidak valid,
        # jadi PSI 0 yang SAH diuji dengan luas di atas ambang:
        ("PSI 0 tetap valid bila luas cukup",
         hasil_psi(3000, 0, 0, plant_mask_pixels=3000)["psi"] == 0.0),
        ("luas tanaman kurang -> insufficient_plant_area",
         v_kecil["reason"] == "insufficient_plant_area"),
        ("tak terklasifikasi berlebih -> excessive_unclassified",
         v_uncl["reason"] == "excessive_unclassified"),
        ("psi None pada hasil tidak valid (bukan 0)",
         all(r["psi"] is None for r in (v_kosong, v_kecil, v_uncl))),
        ("NaN/Infinity tidak lolos sebagai psi",
         all(r["psi"] is None or 0.0 <= r["psi"] <= 100.0
             for r in (v_valid, v_nol, v_kosong, v_kecil, v_uncl))),
        ("captured_at_ms & frame_id diteruskan",
         v_ok["captured_at_ms"] == 1_760_000_000_000
         and v_ok["frame_id"] == "f-001"),
    ]

    for nama, lolos in cek:
        ok &= bool(lolos)
        print(f"  {'OK  ' if lolos else 'FAIL'} {nama}")

    print(f"  {'LOLOS SEMUA' if ok else 'ADA KEGAGALAN'} — "
          f"rumus PSI v{PSI_VERSION}")
    return ok


# ─── 1) Paritas antar jalur segmentasi ────────────────────────────────────────

def _sel(masks, r, c):
    """%kuning & %coklat zona (r, c) — sama persis rumus analyze_grid()
    (kangkung_cv.py) dan analisis() (kangkung_pi.py)."""
    rows, cols = BED_CONFIG["grid_rows"], BED_CONFIG["grid_cols"]
    h, w = masks["tanaman"].shape[:2]
    ch, cw = h // rows, w // cols
    y1, x1 = r * ch, c * cw
    y2 = (r + 1) * ch if r < rows - 1 else h
    x2 = (c + 1) * cw if c < cols - 1 else w
    t = int(masks["tanaman"][y1:y2, x1:x2].sum()) // 255
    k = int(masks["kuning"][y1:y2, x1:x2].sum()) // 255
    ck = int(masks["coklat"][y1:y2, x1:x2].sum()) // 255
    return (k / t * 100 if t else 0.0), (ck / t * 100 if t else 0.0)


def cek_paritas(gambar: Path):
    """Bandingkan pct_kuning/pct_coklat dari 2 jalur resmi pada 1 gambar."""
    rows, cols = BED_CONFIG["grid_rows"], BED_CONFIG["grid_cols"]

    an = KangkungAnalyzer(source=str(gambar))
    an.load_image()
    an.segment(adaptif=True)
    an.analyze_grid()
    cli = {zid: (z["pct_kuning"], z["pct_coklat"])
           for zid, z in an.zone_results.items()}

    mw = mask_tanaman_warna(cv2.imread(str(gambar)))
    live = {f"R{r+1}C{c+1}": _sel(mw, r, c)
            for r in range(rows) for c in range(cols)}

    dk = max(abs(cli[z][0] - live[z][0]) for z in live)
    dc = max(abs(cli[z][1] - live[z][1]) for z in live)
    ok = dk <= TOLERANSI_PP and dc <= TOLERANSI_PP
    print(f"\nPARITAS  {gambar.name}")
    print(f"  zone    : {len(live)}  (maks selisih {TOLERANSI_PP} poin persentase)")
    print(f"  kuning  : selisih maks {dk:.3f} pp")
    print(f"  coklat  : selisih maks {dc:.3f} pp")
    print(f"  hasil   : {'OK - kedua jalur identik' if ok else 'FAIL - tidak konsisten'}")
    return ok


# ─── 2) Tabel PSI per sumber ──────────────────────────────────────────────────

def _ambil(path: Path):
    """Ambil (kuning, coklat, zona_sakit, piksel, label) dari laporan/payload."""
    d = json.loads(path.read_text(encoding="utf-8"))
    d = d.get("payload", d)                    # file payload dibungkus "payload"
    g = d.get("global") or d.get("kesehatan") or {}
    if not g:
        return None
    kuning = float(g.get("kuning_rata", 0.0))
    coklat = float(g.get("coklat_rata", 0.0))
    zs = g.get("zona_sakit")
    if zs is None:
        zona = d.get("zona", {})
        zs = sum(1 for z in zona.values() if z.get("kesehatan") == "sakit")
    # Jumlah piksel mentah kalau laporan sudah memuatnya (kangkung_cv v2.0)
    gy = g.get("green_pixels")
    yy = g.get("yellow_pixels")
    bb = g.get("brown_pixels")
    px = (int(gy), int(yy), int(bb)) if None not in (gy, yy, bb) else None
    return kuning, coklat, int(zs), px, path.stem


def _psi_sumber(kuning, coklat, px):
    """PSI v2.0 untuk satu sumber: piksel mentah bila ada, jika tidak
    direkonstruksi dari persentase (Y,B % ; G = 100 - Y - B)."""
    if px is not None:
        return hitung_psi(*px)
    y = max(0.0, min(kuning, 100.0))
    b = max(0.0, min(coklat, 100.0 - y))
    return hitung_psi_persen(y, b)


def cetak_tabel(sumber):
    lebar = 96
    print("\n" + "=" * lebar)
    print(f"{'sumber':<28}{'kuning %':>9}{'coklat %':>9}{'sakit':>7}"
          f"{'PSI v2.0':>10}{'PSI lama':>10}{'jenuh?':>8}{'valid':>8}")
    print("=" * lebar)
    for kuning, coklat, zs, px, label in sumber:
        psi = _psi_sumber(kuning, coklat, px)
        lama = min(100.0, kuning * 2.0 + coklat * 5.0)
        print(f"{label[:27]:<28}{kuning:>9.2f}{coklat:>9.2f}{zs:>7}"
              f"{(f'{psi:.1f}' if psi is not None else 'n/a'):>10}"
              f"{lama:>10.1f}{('YA' if lama >= 100 else '-'):>8}"
              f"{('ya' if psi is not None else 'TIDAK'):>8}")
    print("=" * lebar)
    print(f"PSI v2.0 = 100*(0.5*Y + B)/N dari jumlah piksel mentah "
          f"(PSI_BOBOT {PSI_BOBOT})")
    print("PSI lama = min(100, 2*kuning + 5*coklat) -> mentok di 20% coklat")
    print("'jenuh? = YA' = rumus lama sudah 100, sehingga fuzzy tidak bisa")
    print("                membedakan 20% vs 80% nekrosis.")
    print("PSI v2.0 linear: gradien tetap ada sampai 100% piksel coklat.")
    print("'valid = TIDAK' -> hasil tidak valid, nilai PSI tidak boleh dibaca "
          "pembaca (bukan PSI 0).")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Validasi PSI & paritas segmentasi")
    ap.add_argument("--gambar", type=Path, nargs="*", default=None,
                    help="gambar untuk uji paritas (default: 2 dummy sakit)")
    ap.add_argument("--laporan", type=Path, nargs="*", default=None,
                    help="laporan/payload JSON untuk tabel PSI")
    ap.add_argument("--hanya-rumus", action="store_true",
                    help="jalankan unit test rumus saja (tanpa segmentasi)")
    args = ap.parse_args()

    # Unit test rumus selalu dijalankan lebih dulu — murah dan tanpa dependensi
    # gambar; kalau gagal, paritas segmentasi tidak perlu dilanjutkan.
    ok_semua = uji_rumus()
    if args.hanya_rumus:
        return 0 if ok_semua else 1

    gambar = args.gambar or [DUMMY / "dummy_kuning_30.png",
                             DUMMY / "dummy_coklat_40.png"]
    for g in gambar:
        g = Path(g)
        if g.exists():
            ok_semua &= cek_paritas(g)
        else:
            print(f"[WARN] gambar tidak ada: {g}")

    laporan = args.laporan or sorted(
        (ROOT / "output" / "firebase").glob("*_payload.json"))
    sumber = [s for s in (_ambil(Path(p)) for p in laporan if Path(p).exists())
              if s is not None]
    if sumber:
        cetak_tabel(sumber)
    else:
        print("[WARN] tidak ada laporan/payload untuk tabel PSI")
    return 0 if ok_semua else 1


if __name__ == "__main__":
    sys.exit(main())
