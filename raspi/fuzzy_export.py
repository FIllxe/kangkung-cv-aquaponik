"""fuzzy_export — bangun input crisp untuk kontroler fuzzy pompa air (rekan tim).

Input  : daftar pct_kuning & pct_coklat per zona (0-100, % thd tanaman)
Output : dict crisp yang dikirim ke dashboard (field 'fuzzy_input'):
         - kuning_pct  : rata-rata % klorosis seluruh bed
         - coklat_pct  : rata-rata % nekrosis seluruh bed
         - zona_sakit  : jumlah zona berstatus 'sakit'
         - indeks_sehat: 0-100 (semakin tinggi = semakin sehat)
"""
import numpy as np


def hitung_fuzzy(pct_kuning_list, pct_coklat_list, status_kesehatan_list):
    kuns = np.asarray(pct_kuning_list, dtype=float)
    coks = np.asarray(pct_coklat_list, dtype=float)
    zona_sakit = sum(1 for s in status_kesehatan_list if s == "sakit")

    kuning_pct = round(float(np.mean(kuns)) if kuns.size else 0.0, 2)
    coklat_pct = round(float(np.mean(coks)) if coks.size else 0.0, 2)

    # Indeks kesehatan 0-100: 100 = tidak ada gejala sama sekali
    indeks = 100.0 - min(100.0, kuning_pct * 2.0 + coklat_pct * 5.0)
    return {
        "kuning_pct": kuning_pct,
        "coklat_pct": coklat_pct,
        "zona_sakit": int(zona_sakit),
        "indeks_sehat": round(indeks, 1),
    }
