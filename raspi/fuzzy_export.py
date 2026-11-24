"""fuzzy_export — bangun input crisp untuk kontroler fuzzy pompa air (rekan tim).

Input  : jumlah piksel MENTAH per zona (hijau/kuning/cokelat) — BUKAN persentase.
         Bentuk lama (dua list persentase) masih didukung otomatis.
Output : dict crisp yang dikirim ke dashboard (field 'fuzzy_input'):
          - green/yellow/brown_pixels : total piksel mentah seluruh bed
          - classified_pixels         : N = G + Y + B
          - kuning_pct  : % klorosis thd piksel tanaman (tampilan)
          - coklat_pct  : % nekrosis thd piksel tanaman (tampilan)
          - zona_sakit  : jumlah zona berstatus 'sakit' (0-24)
          - psi         : Plant Stress Index 0-100 (TINGGI = makin stres)
          - psi_maks    : PSI zona terburuk 0-100
          - valid       : apakah PSI boleh dibaca pembaca
          - reason      : kode alasan bila tidak valid
          - psi_versi   : versi rumus PSI (kontrak ke tim fuzzy)
          - indeks_sehat: 0-100 (tinggi = makin sehat) = 100 - psi (legacy)

Definisi PSI v2.0 (sumber tunggal: hitung_psi() di kangkung_cv.py):
    N   = G + Y + B
    PSI = 100 * (0.5*Y + B) / N
  - bobot kategori: hijau 0, kuning 0,5, cokelat 1 (urutan kategori pada
    indeks, BUKAN "stres fisiologis sebesar 50%")
  - LINIER: tidak jenuh di tengah rentang, gradien tetap ada sampai 100%
    piksel cokelat (rumus lama 2*kuning + 5*coklat mentok di 20% coklat atau
    50% kuning sehingga fuzzy kehilangan gradien di area paling penting)
  - PSI 0 hanya bila semua piksel hijau; PSI 100 hanya bila semua cokelat
  - agregasi bed: jumlahkan piksel DULU, baru hitung PSI. Rata-rata PSI per
    zona salah karena luas tanaman tiap zona berbeda.
  - mengapa perlu psi_maks: 1 zona mati di 24 hanya menyumbang 1/24 ke
    agregat, jadi ikut dikirim sebagai anteseden kedua
  - hasil tidak valid -> psi None + reason; JANGAN disamakan dengan PSI 0
  - "PSI" = Plant Stress Index (istilah proyek), BUKAN Photosystem I
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kangkung_cv import PSI_VERSION, hitung_psi, hasil_psi


def hitung_fuzzy(piksel_zona, status_kesehatan_list, captured_at_ms=None,
                 frame_id=None):
    """Bangun `fuzzy_input` untuk kontroler fuzzy.

    Bentuk baru (disarankan):
        hitung_fuzzy(piksel_zona, status_kesehatan_list,
                     captured_at_ms=..., frame_id=...)
        piksel_zona: list of dict {"green", "yellow", "brown",
                                   "plant_mask", "unclassified"} per zona.

    Bentuk lama (masih didukung, untuk kompatibilitas):
        hitung_fuzzy(pct_kuning_list, pct_coklat_list, status_kesehatan_list)
    Dideteksi otomatis dari tipe argumen; persentase diubah jadi 100 px
    sintetis per zona. Hasil PSI identik karena PSI linear & invarian skala,
    TAPI captured_at_ms/frame_id tidak tersedia di bentuk lama.
    """
    # ── Deteksi bentuk lama: 3 argumen posisional ───────────────────────────
    # Lama: hitung_fuzzy(pct_kuning_list, pct_coklat_list, status_list)
    # Baru: hitung_fuzzy(piksel_zona, status_list, captured_at_ms, frame_id)
    # Ciri bentuk lama: argumen ke-3 berisi status (string), bukan angka.
    dari_persen = False
    if captured_at_ms is not None and not _adalah_angka(captured_at_ms):
        # captured_at_ms sebenarnya berisi list status -> bentuk lama
        piksel_zona = _dari_persen(piksel_zona, status_kesehatan_list)
        status_kesehatan_list = captured_at_ms
        captured_at_ms = None
        dari_persen = True
    elif not _adalah_daftar_dict(piksel_zona) \
            and _adalah_daftar_angka(piksel_zona):
        # hitung_fuzzy(kuns, coks) tanpa daftar status
        piksel_zona = _dari_persen(piksel_zona, status_kesehatan_list)
        status_kesehatan_list = []
        dari_persen = True

    zona = _normalisasi_masukan(piksel_zona)
    zona_sakit = sum(1 for s in (status_kesehatan_list or []) if s == "sakit")

    G = sum(z["green"] for z in zona)
    Y = sum(z["yellow"] for z in zona)
    B = sum(z["brown"] for z in zona)
    PM = sum(z["plant_mask"] for z in zona)
    UN = sum(z["unclassified"] for z in zona)

    # PSI agregat: satu perhitungan dari total piksel (spesifikasi §4).
    # Pada bentuk lama (persentase -> 100 px sintetis), ambang luas absolut
    # tidak bermakna (100 px < PSI_MIN_TANAMAN_PX), jadi cukup hitung psi-nya.
    if dari_persen:
        psi = hitung_psi(G, Y, B)
        hasil = {"psi": psi,
                 "valid": psi is not None,
                 "reason": "ok" if psi is not None else "no_plant_pixels",
                 "captured_at_ms": None, "frame_id": None}
    else:
        hasil = hasil_psi(G, Y, B, plant_mask_pixels=PM,
                          unclassified_pixels=UN,
                          captured_at_ms=captured_at_ms, frame_id=frame_id)
    psi = hasil["psi"]

    # Persentase gejala untuk tampilan (bukan masukan rumus)
    kuning_pct = round(100.0 * Y / PM, 2) if PM else 0.0
    coklat_pct = round(100.0 * B / PM, 2) if PM else 0.0

    # PSI zona terburuk — zona kosong (psi None) tidak menyumbang
    psi_zona = [p for p in (hitung_psi(z["green"], z["yellow"], z["brown"])
                            for z in zona) if p is not None]
    psi_maks = round(max(psi_zona), 1) if psi_zona else None

    return {
        "green_pixels": G,
        "yellow_pixels": Y,
        "brown_pixels": B,
        "classified_pixels": G + Y + B,
        "kuning_pct": kuning_pct,
        "coklat_pct": coklat_pct,
        "zona_sakit": int(zona_sakit),
        "psi": round(psi, 1) if psi is not None else None,
        "psi_maks": psi_maks,
        "valid": hasil["valid"],
        "reason": hasil["reason"],
        "psi_versi": PSI_VERSION,
        "captured_at_ms": hasil["captured_at_ms"],
        "frame_id": hasil["frame_id"],
        # legacy: arah berlawanan (tinggi = sehat), dipertahankan agar
        # dashboard/Firestore lama tidak breaking. Setara 100 - psi.
        "indeks_sehat": round(100.0 - psi, 1) if psi is not None else None,
    }


def _adalah_angka(x):
    """True bila x adalah angka tunggal (bukan list/dict/string)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _adalah_daftar_dict(x):
    """True bila x adalah list/tuple yang elemen pertamanya dict."""
    return isinstance(x, (list, tuple)) and len(x) > 0 \
        and isinstance(x[0], dict)


def _adalah_daftar_angka(x):
    """True bila x adalah list/tuple/array yang elemennya angka (bukan dict)."""
    if isinstance(x, dict) or not hasattr(x, "__len__"):
        return False
    if len(x) == 0:
        return False
    return all(isinstance(v, (int, float)) and not isinstance(v, bool)
               for v in x)


def _dari_persen(pct_kuning, pct_coklat):
    """Persentase zona -> 100 px sintetis per zona (untuk pemanggil lama).

    PSI linear dan invarian skala, jadi PSI dari 100 px sintetis identik
    dengan PSI dari jumlah piksel sebenarnya.
    """
    kuns = np.atleast_1d(np.asarray(pct_kuning, dtype=float))
    coks = np.atleast_1d(np.asarray(pct_coklat, dtype=float))
    zona = []
    for k, c in zip(kuns, coks):
        # Dibulatkan ke piksel bulat: hitung_psi() menolak jumlah pecahan.
        y = int(round(max(0.0, min(float(k), 100.0))))
        b = int(round(max(0.0, min(float(c), 100.0 - y))))
        g = max(0, 100 - y - b)
        zona.append({"green": g, "yellow": y, "brown": b,
                     "plant_mask": g + y + b, "unclassified": 0})
    return zona


def _normalisasi_masukan(masukan):
    """Pastikan bentuk list-of-dict dengan kunci lengkap."""
    return [{"green": float(z.get("green", 0)),
             "yellow": float(z.get("yellow", 0)),
             "brown": float(z.get("brown", 0)),
             "plant_mask": float(z.get("plant_mask",
                                       z.get("green", 0) + z.get("yellow", 0)
                                       + z.get("brown", 0))),
             "unclassified": float(z.get("unclassified", 0))}
            for z in masukan]