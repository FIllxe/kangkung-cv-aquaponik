"""
=============================================================================
  BUAT PAYLOAD DASHBOARD — Konversi <stem>_laporan.json → skema Firestore
  Tahap A: TANPA dependensi Firebase. Murni konversi JSON lokal.
=============================================================================
  Skema dokumen (collection "bed_readings", v1.1):
    device_id          string   ID perangkat (mis. "pi-bed-01")
    timestamp          string   ISO-8601 + zona waktu ("...+07:00")
    mode               string   STANDARD | ADAPTIVE | MANUAL | AUTO
    coverage_rata      float    rata-rata coverage 24 zona (%)
    coverage_std       float    simpangan baku coverage
    zona_siap_panen    int      jumlah zona siap/harus panen
    persen_siap        float    persen zona siap (0-100)
    status_distribusi  object   {"belum_siap":n,"hampir_siap":n,
                                 "siap_panen":n,"harus_panen":n}
    rekomendasi        string   teks rekomendasi (emoji dilepas)
    zona               object   24 entri: {coverage, status, pct_kuning,
                                  pct_coklat, kesehatan}
    fuzzy_input        object   input crisp untuk kontroler fuzzy (rekan tim):
                                  {kuning_pct, coklat_pct, zona_sakit,
                                  psi, psi_maks, psi_versi, indeks_sehat}
                                  psi = Plant Stress Index 0-100 (TINGGI =
                                  makin stres) = 100*(0.5*Y + B)/N dari
                                  jumlah piksel mentah; agregasi bed
                                  menjumlahkan piksel DULU, bukan rata-rata
                                  PSI per zona
    snapshot_url       string?  URL Storage snapshot (null jika belum ada)
    suhu_pi_c          float?   suhu SoC Pi saat capture (null jika n/a)

  ID dokumen disarankan: "<device_id>_<timestamp-compact>"
  Contoh: pi-bed-01_20260903T211532

  CARA PAKAI:
    python buat_payload_dashboard.py                       # semua laporan
    python buat_payload_dashboard.py --file <path.json>
    python buat_payload_dashboard.py --device pi-bed-01 --mode ADAPTIVE

  OUTPUT: <root>/output/firebase/<stem>_payload.json
=============================================================================
"""

import json
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Pastikan output terminal UTF-8 (Windows cp1252 aman)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kangkung_cv import PSI_VERSION, hitung_psi, hasil_psi

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "output" / "segmentasi_batch"
OUT_DIR = ROOT / "output" / "firebase"
ZONA_URUT = [f"R{r}C{c}" for r in range(1, 5) for c in range(1, 7)]

# Status yang dianggap "siap" (konsisten dengan THRESHOLD di kangkung_cv.py)
def _iso_timestamp(ts_lokal: str) -> str:
    """'2026-09-03 21:15:32' → '2026-09-03T21:15:32+07:00' (WIB)."""
    try:
        dt = datetime.strptime(ts_lokal, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        dt = datetime.now()
    return dt.isoformat(timespec="seconds") + "+07:00"


def _id_dokumen(device_id: str, ts_lokal: str) -> str:
    """ID dokumen idempotent: '<device>_<YYYYmmddTHHMMSS>'."""
    try:
        dt = datetime.strptime(ts_lokal, "%Y-%m-%d %H:%M:%S")
        compact = dt.strftime("%Y%m%dT%H%M%S")
    except (ValueError, TypeError):
        compact = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"{device_id}_{compact}"


def buat_payload(path_laporan: Path, device_id: str = "pi-bed-01",
                 mode: str = "STANDARD", snapshot_url=None,
                 suhu_pi_c=None) -> dict:
    """Konversi satu file *_laporan.json menjadi payload ramping."""
    with open(path_laporan, encoding="utf-8") as f:
        lap = json.load(f)

    glob = lap.get("global", {})
    zona_src = lap.get("zona", {})

    # Rekomendasi tanpa emoji (aman untuk Firestore & tampilan web)
    rekom = " ".join(glob.get("rekomendasi", "").split())
    rekom = rekom.encode("ascii", "ignore").decode("ascii").strip()

    zona = {}
    for zid in ZONA_URUT:
        z = zona_src.get(zid)
        if z is None:
            continue
        zona[zid] = {
            "coverage": round(float(z.get("coverage", 0.0)), 2),
            "status": z.get("status", "belum_siap"),
            "pct_kuning": round(float(z.get("pct_kuning", 0.0)), 2),
            "pct_coklat": round(float(z.get("pct_coklat", 0.0)), 2),
            "kesehatan": z.get("kesehatan", "sehat"),
        }

    # Input untuk kontroler fuzzy (rekan tim): crisp 0-100.
    # PSI v2.0 = 100*(0.5*Y + B)/N dari jumlah piksel mentah, DAN agregasi bed
    # menjumlahkan piksel dulu (bukan rata-rata PSI per zona) — spesifikasi §4.
    #
    # Laporan v2.0 sudah memuat green/yellow/brown_pixels -> dipakai langsung.
    # Laporan lama hanya punya persentase zona -> dijadikan piksel sintetis
    # bulat; hasil PSI identik karena PSI linear & invarian skala. Skala
    # sintetis dikali 1000 agar melewati PSI_MIN_TANAMAN_PX (ambang absolut
    # yang bermakna untuk piksel citra nyata, bukan untuk data persentase).
    zona_px = [{"green": 100.0 - z["pct_kuning"] - z["pct_coklat"],
                "yellow": z["pct_kuning"], "brown": z["pct_coklat"]}
               for z in zona.values()]
    sintetik = []
    for p in zona_px:
        y = int(round(max(0.0, min(p["yellow"], 100.0))))
        b = int(round(max(0.0, min(p["brown"], 100.0 - y))))
        g = max(0, 100 - y - b)
        sintetik.append({"green": g, "yellow": y, "brown": b})

    if glob.get("green_pixels") is not None:
        hasil = hasil_psi(int(glob["green_pixels"]),
                          int(glob["yellow_pixels"]),
                          int(glob["brown_pixels"]),
                          plant_mask_pixels=int(glob.get(
                              "plant_mask_pixels", 0)),
                          unclassified_pixels=int(glob.get(
                              "unclassified_pixels", 0)))
    else:
        tg, ty = sum(p["green"] for p in sintetik), \
            sum(p["yellow"] for p in sintetik)
        tb = sum(p["brown"] for p in sintetik)
        if tg + ty + tb == 0:
            hasil = hasil_psi(0, 0, 0, plant_mask_pixels=0)
        else:
            hasil = hasil_psi(tg * 1000, ty * 1000, tb * 1000,
                              plant_mask_pixels=(tg + ty + tb) * 1000)
    psi = round(hasil["psi"], 1) if hasil["psi"] is not None else None

    # psi_maks = PSI zona terburuk, dari piksel zona itu sendiri
    psi_zona = [hitung_psi(p["green"], p["yellow"], p["brown"])
                for p in sintetik]
    psi_zona = [p for p in psi_zona if p is not None]
    if glob.get("psi_maks") is not None:
        psi_maks = round(float(glob["psi_maks"]), 1)
    else:
        psi_maks = round(max(psi_zona), 1) if psi_zona else None

    zona_sakit = int(glob.get("zona_sakit",
                              sum(1 for z in zona.values()
                                  if z["kesehatan"] == "sakit")))
    fuzzy_input = {
        "green_pixels": hasil["green_pixels"],
        "yellow_pixels": hasil["yellow_pixels"],
        "brown_pixels": hasil["brown_pixels"],
        "classified_pixels": hasil["classified_pixels"],
        "kuning_pct": round(float(glob.get("kuning_rata", 0.0)), 2),
        "coklat_pct": round(float(glob.get("coklat_rata", 0.0)), 2),
        "zona_sakit": zona_sakit,
        "psi": psi,
        "psi_maks": psi_maks,
        "valid": hasil["valid"],
        "reason": hasil["reason"],
        "psi_versi": PSI_VERSION,
        "frame_id": None,
        "captured_at_ms": None,
        "indeks_sehat": round(100.0 - psi, 1) if psi is not None else None,
    }

    return {
        "device_id": device_id,
        "timestamp": _iso_timestamp(glob.get("timestamp", "")),
        "doc_id": _id_dokumen(device_id, glob.get("timestamp", "")),
        "mode": mode,
        "coverage_rata": round(float(glob.get("coverage_rata", 0.0)), 2),
        "coverage_std": round(float(glob.get("coverage_std", 0.0)), 2),
        "zona_siap_panen": int(glob.get(
            "zona_siap_panen",
            sum(1 for v in zona.values() if v["status"] in SIAP))),
        "persen_siap": round(float(glob.get("persen_siap", 0.0)), 1),
        "status_distribusi": glob.get("status_distribusi", {
            "belum_siap": 0, "hampir_siap": 0,
            "siap_panen": 0, "harus_panen": 0}),
        "kesehatan": {
            "kuning_rata": fuzzy_input["kuning_pct"],
            "coklat_rata": fuzzy_input["coklat_pct"],
            "distribusi": glob.get("kesehatan_distribusi", {
                "sehat": 0, "waspada": 0, "sakit": 0}),
            "rekomendasi": " ".join(
                glob.get("rekomendasi_kesehatan", "").split()),
        },
        "fuzzy_input": fuzzy_input,
        "rekomendasi": rekom,
        "zona": zona,
        "snapshot_url": snapshot_url,
        "suhu_pi_c": suhu_pi_c,
    }

SIAP = ("siap_panen", "harus_panen")


def validasi_payload(p: dict) -> list:
    """Cek konsistensi skema. Return daftar peringatan (kosong = OK)."""
    warn = []
    if len(p.get("zona", {})) != 24:
        warn.append(f"zona: {len(p.get('zona', {}))} entri (harus 24)")
    dist = p.get("status_distribusi", {})
    if sum(dist.values()) != len(p.get("zona", {})):
        warn.append("status_distribusi tidak cocok dengan jumlah zona")
    if not p.get("timestamp", "").endswith("+07:00"):
        warn.append("timestamp bukan ISO-8601 +07:00")
    for zid, z in p.get("zona", {}).items():
        if not (0.0 <= z["coverage"] <= 100.0):
            warn.append(f"{zid}: coverage di luar 0-100")

    # Kontrak PSI: hasil valid wajib punya psi 0-100; hasil tidak valid wajib
    # psi None (JANGAN 0 — 0 adalah hasil sah untuk kanopi hijau).
    fz = p.get("fuzzy_input")
    if fz is None:
        warn.append("fuzzy_input tidak ada")
    else:
        if fz.get("psi_versi") != PSI_VERSION:
            warn.append(f"psi_versi {fz.get('psi_versi')} != {PSI_VERSION}")
        psi = fz.get("psi")
        if fz.get("valid"):
            if not isinstance(psi, (int, float)) or not (0.0 <= psi <= 100.0):
                warn.append(f"psi valid tapi bukan 0-100: {psi}")
        elif psi is not None:
            warn.append(f"hasil tidak valid tapi psi tetap terisi: {psi}")
        else:
            pass  # benar: invalid -> psi None
        pm = fz.get("psi_maks")
        if pm is not None and not (0.0 <= pm <= 100.0):
            warn.append(f"psi_maks di luar 0-100: {pm}")
    return warn


def main():
    ap = argparse.ArgumentParser(
        description="Konversi laporan.json → payload skema bed_readings")
    ap.add_argument("--file", default=None,
                    help="satu file laporan (default: semua di "
                         "output/segmentasi_batch)")
    ap.add_argument("--device", default="pi-bed-01", help="device_id")
    ap.add_argument("--mode", default="STANDARD",
                    help="STANDARD | ADAPTIVE | MANUAL | AUTO")
    ap.add_argument("--snapshot-url", default=None,
                    help="URL Storage snapshot (opsional)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(SOURCE_DIR.glob("*_laporan.json"))

    if not files:
        print(f"[ERROR] Tidak ada file laporan di {SOURCE_DIR}")
        sys.exit(1)

    print("=" * 68)
    print(f"  BUAT PAYLOAD DASHBOARD — {len(files)} file")
    print(f"  Skema  : bed_readings v1.0 "
          f"(device={args.device}, mode={args.mode})")
    print(f"  Output : {OUT_DIR}")
    print("=" * 68)

    n_ok = 0
    for f in files:
        try:
            payload = buat_payload(f, device_id=args.device,
                                   mode=args.mode,
                                   snapshot_url=args.snapshot_url)
            warn = validasi_payload(payload)
            out = OUT_DIR / f"{f.stem.replace('_laporan', '')}_payload.json"
            with open(out, "w", encoding="utf-8") as fp:
                json.dump({"versi_skema": "1.0", "payload": payload},
                          fp, indent=2, ensure_ascii=False)
            ukuran = out.stat().st_size / 1024
            status = "OK" if not warn else "WARN: " + "; ".join(warn)
            print(f"[OK] {f.name} → {out.name} ({ukuran:.1f} KB) [{status}]")
            n_ok += 1
        except Exception as e:
            print(f"[ERROR] {f.name}: {e}")

    print(f"\n[SELESAI] {n_ok}/{len(files)} payload dibuat.")
    print("Upload manual ke Firestore Console → collection 'bed_readings', "
          "doc_id = payload.doc_id")


if __name__ == "__main__":
    main()
