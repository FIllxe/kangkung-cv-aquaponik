"""fuzzy_export — bangun input crisp untuk kontroler fuzzy pompa air (rekan tim).

Input  : daftar pct_kuning & pct_coklat per zona (0-100, % thd tanaman)
Output : dict crisp yang dikirim ke dashboard (field 'fuzzy_input'):
         - kuning_pct  : rata-rata % klorosis seluruh bed
         - coklat_pct  : rata-rata % nekrosis seluruh bed
         - zona_sakit  : jumlah zona berstatus 'sakit' (0-24)
         - psi         : Plant Stress Index 0-100 (TINGGI = makin stres)
         - psi_maks    : PSI zona terburuk 0-100
         - psi_versi   : versi rumus PSI (kontrak ke tim fuzzy)
         - indeks_sehat: 0-100 (tinggi = makin sehat) = 100 - psi (legacy)

Definisi PSI (sumber tunggal: hitung_psi() di kangkung_cv.py):
    PSI = 100 * min(1, 0.4*min(kuning/25,1) + 0.6*min(coklat/8,1))
  - dinormalkan ke ambang KESEHATAN (kuning_sakit 25%, coklat_sakit 8%)
    sehingga PSI = 100 <=> gejala setara ambang "sakit"
  - TIDAK jenuh: rumus lama (2*kuning + 5*coklat) mentok di 20% coklat atau
    50% kuning, sehingga fuzzy kehilangan gradien di area paling penting
  - mengapa perlu psi_maks: 1 zona mati di 24 hanya menyumbang 1/24 ke
    rata-rata, jadi ikut dikirim sebagai anteseden kedua
  - "PSI" = Plant Stress Index (istilah proyek), BUKAN Photosystem I
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kangkung_cv import PSI_VERSION, hitung_psi


def hitung_fuzzy(pct_kuning_list, pct_coklat_list, status_kesehatan_list):
    kuns = np.asarray(pct_kuning_list, dtype=float)
    coks = np.asarray(pct_coklat_list, dtype=float)
    zona_sakit = sum(1 for s in status_kesehatan_list if s == "sakit")

    kuning_pct = round(float(np.mean(kuns)) if kuns.size else 0.0, 2)
    coklat_pct = round(float(np.mean(coks)) if coks.size else 0.0, 2)

    # Indeks stres PSI + indeks kesehatan legacy (arah berlawanan)
    psi = hitung_psi(kuning_pct, coklat_pct)
    psi_maks = 0.0
    for k, c in zip(np.atleast_1d(kuns), np.atleast_1d(coks)):
        psi_maks = max(psi_maks, hitung_psi(k, c))

    return {
        "kuning_pct": kuning_pct,
        "coklat_pct": coklat_pct,
        "zona_sakit": int(zona_sakit),
        "psi": psi,
        "psi_maks": round(psi_maks, 1),
        "psi_versi": PSI_VERSION,
        # legacy: arah berlawanan (tinggi = sehat), dipertahankan agar
        # dashboard/Firestore lama tidak breaking. Setara 100 - psi.
        "indeks_sehat": round(100.0 - psi, 1),
    }
