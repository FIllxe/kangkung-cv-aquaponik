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
       PSI baru = 100*min(1, 0.4*min(kuning/25,1) + 0.6*min(coklat/8,1))
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
from kangkung_cv import KangkungAnalyzer, BED_CONFIG, KESEHATAN, hitung_psi
from adaptive_bed import mask_tanaman_warna

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DUMMY = ROOT / "output" / "dummy"
TOLERANSI_PP = 0.5


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
    """Ambil (kuning, coklat, zona_sakit, label) dari laporan atau payload."""
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
    return kuning, coklat, int(zs), path.stem


def cetak_tabel(sumber):
    lebar = 88
    print("\n" + "=" * lebar)
    print(f"{'sumber':<30}{'kuning %':>10}{'coklat %':>10}{'sakit':>7}"
          f"{'PSI':>8}{'PSI lama':>10}{'jenuh?':>8}")
    print("=" * lebar)
    for kuning, coklat, zs, label in sumber:
        psi = hitung_psi(kuning, coklat)
        lama = min(100.0, kuning * 2.0 + coklat * 5.0)
        print(f"{label[:29]:<30}{kuning:>10.2f}{coklat:>10.2f}{zs:>7}"
              f"{psi:>8.1f}{lama:>10.1f}{'YA' if lama >= 100 else '-':>8}")
    print("=" * lebar)
    print(f"PSI baru = 100*min(1, 0.4*min(kuning/{KESEHATAN['kuning_sakit']:.0f},1)"
          f" + 0.6*min(coklat/{KESEHATAN['coklat_sakit']:.0f},1))  "
          f"-> kangkung_cv.hitung_psi()")
    print("PSI lama = min(100, 2*kuning + 5*coklat) -> mentok di 20% coklat")
    print("'jenuh? = YA' = rumus lama sudah 100, sehingga fuzzy tidak bisa")
    print("                membedakan 20% vs 80% nekrosis.")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Validasi PSI & paritas segmentasi")
    ap.add_argument("--gambar", type=Path, nargs="*", default=None,
                    help="gambar untuk uji paritas (default: 2 dummy sakit)")
    ap.add_argument("--laporan", type=Path, nargs="*", default=None,
                    help="laporan/payload JSON untuk tabel PSI")
    args = ap.parse_args()

    gambar = args.gambar or [DUMMY / "dummy_kuning_30.png",
                             DUMMY / "dummy_coklat_40.png"]
    ok_semua = True
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
