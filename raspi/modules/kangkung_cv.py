"""
=============================================================================
  SISTEM COMPUTER VISION - SEGMENTASI KELEBATAN TANAMAN KANGKUNG
  Bed Aquaponik | Ukuran: 2 m x 1.1 m
  Mengukur kesiapan panen berdasarkan densitas & morfologi tanaman
=============================================================================
"""

import cv2
import math
import numpy as np
# Catatan: matplotlib TIDAK di-import di sini. Hanya dipakai untuk
# visualisasi() (debug/plot di laptop) -> import dilakukan di dalam fungsi
# tersebut agar Raspberry Pi tetap ringan tanpa paket matplotlib.
import json
import os
import sys
import time
from datetime import datetime, timezone

# Pastikan output terminal UTF-8 (karakter box-drawing & emoji aman di Windows)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────────────────────────────────────
# KONFIGURASI SISTEM
# ─────────────────────────────────────────────────────────────────────────────

BED_CONFIG = {
    "panjang_m": 2.0,       # meter
    "lebar_m": 1.1,          # meter
    "grid_rows": 4,           # baris zona analisis
    "grid_cols": 6,           # kolom zona analisis
}

# Parameter HSV untuk deteksi warna hijau kangkung
# (dapat di-tune lewat mode kalibrasi)
HSV_KANGKUNG = {
    # Hijau muda – tanaman masih kecil / daun baru
    "muda":   {"lower": np.array([35, 40,  40]),
               "upper": np.array([75, 255, 200])},
    # Hijau tua – tanaman sudah mature, siap panen
    "mature": {"lower": np.array([36, 60,  60]),
               "upper": np.array([85, 255, 255])},
    # Kuning / menguning (klorosis) – defisiensi N/Fe/Mg atau stres; H 20–34
    "kuning": {"lower": np.array([21, 60,  80]),
               "upper": np.array([34, 255, 255])},
    # Coklat / nekrosis – jaringan mati (busuk/kering); H 8–20, V 85–220:
    # cukup terang agar tidak tertukar media tanam gelap, tidak terlalu terang
    # agar tidak tertukar pantulan cahaya di permukaan air
    "coklat": {"lower": np.array([8,  70,  85]),
               "upper": np.array([20, 255, 220])},
}

# Ambang kesehatan daun per zona (% terhadap piksel TANAMAN di zona, bukan
# luas zona). Rujukan: Barbedo (2013) SpringerPlus — segmentasi area sakit
# daun berbasis warna; klorosis = dapat dipulihkan, nekrosis = jaringan mati.
KESEHATAN = {
    "kuning_waspada": 10.0,   # % tanaman menguning
    "kuning_sakit":   25.0,
    "coklat_waspada": 3.0,    # % tanaman coklat (lebih serius)
    "coklat_sakit":   8.0,
}


# ─── Indeks stres PSI (Plant Stress Index) ────────────────────────────────────
# Kontrak ke kontroler fuzzy (rekan tim, Bab 5): skalar 0-100, TINGGI = makin
# stres. Definisi mengikuti spesifikasi bersama (Rafly, 13 Oktober 2026):
#
#   N   = G + Y + B                                  (piksel tanaman terklasifikasi)
#   PSI = 100 x (0.5*Y + B) / N                      (presisi float64)
#
# Bobot kategori: hijau 0, kuning 0,5, coklat 1. Bobot itu HANYA urutan kategori
# pada indeks — bobot 0,5 TIDAK berarti daun kuning stres fisiologis 50%.
# Karena linear, rumus ini TIDAK jenuh di tengah rentang: gradien tetap ada
# sampai 100% piksel cokelat (rumus lama 2*K+5*C sudah mentok di 20% coklat /
# 50% kuning sehingga fuzzy kehilangan gradien di area paling penting).
#   - PSI 0   hanya bila SEMUA piksel hijau
#   - PSI 50  bila semua piksel kuning (campuran lain bisa juga 50)
#   - PSI 100 hanya bila SEMUA piksel cokelat
#
# PSI tinggi TIDAK membuktikan kualitas air sebagai penyebab — tetap dibaca
# bersama pH dan kekeruhan oleh Sugeno, bukan pemicu tunggal ganti air.
#
# CATATAN TERMINOLOGI: "PSI" di proyek ini = Plant Stress Index (istilah tim),
# BUKAN Photosystem I (fisiologi tumbuhan). Selalu tulis lengkap di laporan.
PSI_VERSION = "2.0"
PSI_BOBOT = {"hijau": 0.0, "kuning": 0.5, "coklat": 1.0}

# Batas kalibrasi validitas pengamatan (disesuaikan dari citra instalasi nyata)
PSI_MIN_TANAMAN_PX = 2000      # batas minimum piksel tanaman yang teramati
PSI_MAKS_UNCLASSIFIED = 0.15   # batas proporsi piksel tanaman tak terklasifikasi


def _ke_piksel(nilai):
    """Validasi jumlah piksel: bilangan bulat TIDAK NEGATIF.

    Mengembalikan int, atau None bila bukan angka terbatas, negatif, pecahan,
    atau boolean. NaN/Infinity juga ditolak (spesifikasi §7: jangan kirim
    NaN atau Infinity sebagai hasil).
    """
    if isinstance(nilai, bool):
        return None
    try:
        f = float(nilai)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(f) or f < 0 or f != int(f):
        return None
    return int(f)


def hitung_psi(green, yellow, brown):
    """PSI 0-100 dari JUMLAH PIKSEL MENTAH (hijau, kuning, cokelat).

        N   = G + Y + B
        PSI = 100 x (0.5*Y + B) / N        (presisi float64)

    Mengembalikan `None` bila N = 0 (tidak ada piksel terklasifikasi) atau
    masukan tidak sah (negatif, pecahan, non-angka) — JANGAN mengembalikan 0,
    karena 0 adalah hasil SAH untuk kanopi hijau dan tidak boleh tertukar
    dengan "tidak ada tanaman".

    Tak ada pembulatan di sini: presisi float64 dijaga sampai tampilan.
    """
    g, y, b = _ke_piksel(green), _ke_piksel(yellow), _ke_piksel(brown)
    if g is None or y is None or b is None:
        return None
    n = g + y + b
    if n <= 0:
        return None
    return 100.0 * (PSI_BOBOT["kuning"] * y + PSI_BOBOT["coklat"] * b) / n


def hitung_psi_persen(pct_kuning, pct_coklat):
    """Bentuk persentase PSI = 0,5*Y + B (Y,B dalam 0-100, G+Y+B = 100).

    Setara `hitung_psi()` bila masukan adalah persentase yang sama. Hanya
    untuk tampilan/penelusuran — perhitungan resmi memakai piksel mentah.
    """
    try:
        y = float(pct_kuning); b = float(pct_coklat)
    except (TypeError, ValueError):
        return None
    if y < 0 or b < 0 or y + b > 100:
        return None
    return PSI_BOBOT["kuning"] * y + PSI_BOBOT["coklat"] * b


def gabung_psi(daftar_piksel):
    """PSI global dari gabungan beberapa area (grid 4x6).

    Menerima iterable dict `{"green": int, "yellow": int, "brown": int}`.
    WAJIB menjumlahkan piksel DULU baru menghitung PSI — rata-rata PSI per
    area salah karena tiap area punya luas tanaman berbeda (spesifikasi §4).
    """
    g = y = b = 0
    for p in daftar_piksel:
        pg = _ke_piksel(p.get("green", 0))
        py = _ke_piksel(p.get("yellow", 0))
        pb = _ke_piksel(p.get("brown", 0))
        if pg is None or py is None or pb is None:
            return None, (None, None, None)
        g += pg; y += py; b += pb
    return hitung_psi(g, y, b), (g, y, b)


def hasil_psi(green, yellow, brown, *, plant_mask_pixels=0,
              unclassified_pixels=0, quality_flags=None, frame_id=None,
              captured_at_ms=None):
    """Bungkus PSI jadi satu objek kontrak untuk pembaca ESP32/tim fuzzy.

    Kontrak: `psi` numerik 0-100 pada hasil valid, `valid` boolean, `reason`
    kode alasan, `captured_at_ms` Unix epoch milidetik, `frame_id`.
    Nilai 0 adalah hasil SAH (kanopi hijau) — dibedakan lewat `reason`.
    Pada hasil tidak valid `psi` bernilai None supaya pembaca tidak salah pakai.
    """
    flags = dict(quality_flags or {})
    g = _ke_piksel(green)
    y = _ke_piksel(yellow)
    b = _ke_piksel(brown)
    pm = _ke_piksel(plant_mask_pixels) or 0
    up = _ke_piksel(unclassified_pixels) or 0
    # Kunci kontrak selalu lengkap di SEMUA jalur kembalian supaya pembaca
    # tidak perlu memakai .get() untuk setiap field.
    dasar = {
        "psi": None,
        "valid": False,
        "reason": "ok",
        "captured_at_ms": _ke_piksel(captured_at_ms),
        "frame_id": frame_id,
        "green_pixels": g,
        "yellow_pixels": y,
        "brown_pixels": b,
        "classified_pixels": None if g is None else g + (y or 0) + (b or 0),
        "plant_mask_pixels": pm,
        "unclassified_pixels": up,
        "quality_flags": flags,
        "formula_version": PSI_VERSION,
    }
    if g is None or y is None or b is None:
        dasar["reason"] = "invalid_counts"
        return dasar

    # Urutan pemeriksaan mengikuti spesifikasi §7
    if g < 0 or y < 0 or b < 0:
        reason = "invalid_counts"
    elif flags.get("camera_error"):
        reason = "camera_error"
    elif flags.get("empty_frame"):
        reason = "empty_frame"
    elif flags.get("bad_frame_quality"):
        reason = "bad_frame_quality"
    elif flags.get("mask_overlap"):
        reason = "mask_overlap"
    elif g + y + b == 0:
        reason = "no_plant_pixels"
    elif pm < PSI_MIN_TANAMAN_PX:
        reason = "insufficient_plant_area"
    elif pm > 0 and up / pm > PSI_MAKS_UNCLASSIFIED:
        reason = "excessive_unclassified"
    else:
        reason = "ok"

    psi = hitung_psi(g, y, b) if reason == "ok" else None
    if psi is not None and not (0.0 <= psi <= 100.0):
        reason, psi = "invalid_psi", None

    dasar["psi"] = psi
    dasar["reason"] = reason
    dasar["valid"] = reason == "ok"
    return dasar


def sekarang_ms():
    """Unix epoch milidetik (UTC) untuk penanda waktu pengambilan frame."""
    return int(time.time() * 1000)


# Ambang batas kesiapan panen (dalam % coverage per zona)
THRESHOLD = {
    "belum_siap":    (0,   25),   # 0–25%
    "hampir_siap":   (25,  55),   # 25–55%
    "siap_panen":    (55,  80),   # 55–80%
    "harus_panen":   (80, 100),   # >80% (over-dense, segera panen!)
}

WARNA_STATUS = {
    "belum_siap":  "#3498db",   # biru
    "hampir_siap": "#f39c12",   # oranye
    "siap_panen":  "#2ecc71",   # hijau
    "harus_panen": "#e74c3c",   # merah
}


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAS
# ─────────────────────────────────────────────────────────────────────────────

def get_status(coverage_pct: float) -> str:
    for status, (lo, hi) in THRESHOLD.items():
        if lo <= coverage_pct < hi:
            return status
    return "harus_panen"


def coverage_to_score(coverage_pct: float) -> float:
    """Konversi coverage ke skor 0–100 kesiapan panen."""
    # Skor panen optimal di 65–75% coverage
    if coverage_pct < 55:
        return coverage_pct / 55 * 70
    elif coverage_pct <= 80:
        return 70 + (coverage_pct - 55) / 25 * 30
    else:
        # Over-dense: skor turun (risiko penyakit, kompetisi nutrisi)
        return max(60, 100 - (coverage_pct - 80) * 1.5)


def get_kesehatan(pct_kuning: float, pct_coklat: float) -> str:
    """
    Status kesehatan zona dari % tanaman menguning & coklat.
    Coklat (nekrosis / jaringan mati) diprioritaskan lebih serius daripada
    kuning (klorosis — masih dapat dipulihkan via nutrisi/pompa air).
    """
    if pct_coklat >= KESEHATAN["coklat_sakit"] or \
            pct_kuning >= KESEHATAN["kuning_sakit"]:
        return "sakit"
    if pct_coklat >= KESEHATAN["coklat_waspada"] or \
            pct_kuning >= KESEHATAN["kuning_waspada"]:
        return "waspada"
    return "sehat"


def parameter_adaptif(hsv, base=40.0, ref=128.0):
    """
    Range HSV per kelas ADAPTIF-ILUMINASI (optimasi S & V).
    - Ambang S_lo memakai persentil ke-15 piksel kandidat hijau (tidak ikut
      melonjak ketika V tinggi/terik agar daun muda & area glare tidak terpotong).
    - V_lo diadaptasi halus dan V_hi diperlebar hingga 245-252 untuk memulihkan
      daun di area terang; Hue tidak digeser.
    - Kuning & cokelat dipertahankan pada seed statis agar PSI konsisten.
    """
    H, S, V = cv2.split(hsv)
    f = float(np.clip(V.mean() / ref, 0.55, 1.6))

    kand = (H >= 35) & (H <= 85) & (S >= 22) & (V >= 28)
    if int(kand.sum()) >= 200:
        s_p15 = float(np.percentile(S[kand], 15))
        s_lo = int(np.clip(min(base, max(24.0, s_p15 * 0.85)), 22, 48))
    else:
        s_lo = int(np.clip(38.0 * (0.7 + 0.3 * f), 22, 48))

    v_lo = int(np.clip(30.0 * (0.65 + 0.35 * f), 20, 52))
    v_hi_muda = int(np.clip(225.0 + 20.0 * min(f, 1.2), 215, 250))
    v_hi_mat = 252

    rng = {}
    for k in ("muda", "mature"):
        lo = HSV_KANGKUNG[k]["lower"].copy()
        hi = HSV_KANGKUNG[k]["upper"].copy()
        lo[1] = max(s_lo, 40) if k == "mature" else s_lo
        lo[2] = max(v_lo, 35) if k == "mature" else v_lo
        hi[2] = v_hi_muda if k == "muda" else v_hi_mat
        rng[k] = {"lower": lo, "upper": hi}

    # Kelas diagnostik (kuning/coklat) tetap memakai seed statis agar status
    # kesehatan deterministik (mencegah false-positive nekrosis pada bed sehat).
    for k in ("kuning", "coklat"):
        rng[k] = {"lower": HSV_KANGKUNG[k]["lower"].copy(),
                  "upper": HSV_KANGKUNG[k]["upper"].copy()}
    rng["info"] = {
        "f": round(f, 2),
        "s_lo": s_lo,
        "v_lo": v_lo,
        "v_hi": v_hi_mat,
        "v_hi_muda": v_hi_muda,
        "v_mean": round(float(V.mean()), 1),
        "s_mean": round(float(S.mean()), 1),
        "clahe": True,
    }
    return rng


def koreksi_wb_hangat(bgr):
    """Koreksi cast hangat/magenta (AWB webcam) berbasis piksel netral terang.

    Hanya aktif bila sorotan netral (PVC/air terang) benar-benar mengalami bias
    merah (med_R - med_G >= 6), sehingga foto dengan AWB normal tidak berubah.
    Tidak menekan kanal G dan menjaga warna daun kuning/cokelat sejati.
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    s, v = hsv[:, :, 1], hsv[:, :, 2]
    b, g, r = cv2.split(bgr.astype(np.int16))
    neu = (s < 42) & (v >= 155) & (v <= 246) & ((g - b) < 40)
    min_px = max(600, int(0.004 * bgr.shape[0] * bgr.shape[1]))
    if int(neu.sum()) < min_px:
        return bgr, (1.0, 1.0, 1.0), False

    med = np.median(bgr[neu].astype(np.float32), axis=0)
    mb, mg, mr = float(med[0]), float(med[1]), float(med[2])
    if (mr - mg) < 6.0 or (mr / max(mb, 1.0)) > 1.38:
        return bgr, (1.0, 1.0, 1.0), False

    target = max(mg, (mb + mr) * 0.5 * 0.96)
    gains = (
        float(np.clip(target / max(mb, 1.0), 1.0, 1.15)),
        float(np.clip(target / max(mg, 1.0), 1.0, 1.08)),
        float(np.clip(target / max(mr, 1.0), 0.80, 1.0)),
    )
    arr = np.array(gains, dtype=np.float32)
    out = np.clip(bgr.astype(np.float32) * arr[None, None, :], 0, 255).astype(np.uint8)
    return out, tuple(round(g_val, 3) for g_val in gains), True


def segmentasi_hijau_adaptif(bgr, adaptif=True):
    """Segmentasi mask daun hijau (muda + mature) dengan optimasi WB, CLAHE V, & glare S.

    Menghasilkan dict {mask_muda, mask_mature, mask_hijau, hsv_raw, rng, info}
    agar KangkungAnalyzer.segment() dan adaptive_bed.mask_tanaman_warna() selalu identik.
    """
    if not adaptif:
        hsv_raw = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        rng = {k: {"lower": HSV_KANGKUNG[k]["lower"].copy(),
                   "upper": HSV_KANGKUNG[k]["upper"].copy()}
               for k in HSV_KANGKUNG}
        info = {"f": 1.0, "s_lo": 40, "v_lo": 40, "v_hi": 255, "clahe": False, "wb_cast": False}
        mask_muda = cv2.inRange(hsv_raw, rng["muda"]["lower"], rng["muda"]["upper"])
        mask_mature = cv2.inRange(hsv_raw, rng["mature"]["lower"], rng["mature"]["upper"])
        mask_raw = cv2.bitwise_or(mask_muda, mask_mature)
        return {
            "mask_muda": mask_muda,
            "mask_mature": mask_mature,
            "mask_hijau": mask_raw,
            "hsv_raw": hsv_raw,
            "rng": rng,
            "info": info,
        }

    bgr_work, wb_gains, wb_aktif = koreksi_wb_hangat(bgr)
    hsv_raw = cv2.cvtColor(bgr_work, cv2.COLOR_BGR2HSV)

    h_raw, s_raw, v_raw = cv2.split(hsv_raw)
    clahe = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8))
    v_clahe = clahe.apply(v_raw)
    v_opt = np.clip(
        0.55 * v_clahe.astype(np.float32) + 0.45 * v_raw.astype(np.float32),
        0, 255
    ).astype(np.uint8)
    hsv_opt = cv2.merge([h_raw, s_raw, v_opt])

    rng = parameter_adaptif(hsv_opt)
    info = rng["info"]
    info["wb_cast"] = wb_aktif
    if wb_aktif:
        info["wb_gains"] = wb_gains
    s_lo = int(info["s_lo"])

    mask_muda = cv2.inRange(hsv_opt, rng["muda"]["lower"], rng["muda"]["upper"])
    mask_mature = cv2.inRange(hsv_opt, rng["mature"]["lower"], rng["mature"]["upper"])

    b_ch, g_ch, r_ch = cv2.split(bgr_work.astype(np.int16))
    exg = 2 * g_ch - r_ch - b_ch

    # Pemulihan daun hijau pada area glare / terang ketika S memudar (< s_lo)
    glare_leaf = (
        (
            ((h_raw >= 37) & (s_raw >= 18)) |
            ((h_raw >= 36) & (v_raw >= 175) & (s_raw >= 12) & (exg >= 14))
        ) &
        (h_raw <= 84) &
        (s_raw < s_lo) &
        (v_raw >= 165) & (v_raw <= 252) &
        (exg >= 12)
    )
    if glare_leaf.any():
        mask_muda[glare_leaf] = 255

    # Pemulihan daun hijau-lime muda dominan klorofil (G > R, H 31..34)
    # tanpa mengganggu daun kuning klorosis sejati (R >= G / ExG rendah).
    lime_leaf = (
        (h_raw >= 31) & (h_raw <= 34) &
        (s_raw >= max(s_lo, 40)) &
        (v_raw >= 60) &
        ((g_ch - r_ch) >= 4) &
        (exg >= 24)
    )
    if lime_leaf.any():
        mask_muda[lime_leaf] = 255

    # Penjaga anti-false-positive pada pantulan air putih/abu-abu & noise saturasi rendah
    noise_glare = (v_raw >= 220) & (s_raw < 24) & (exg < 8)
    noise_low_s = (s_raw < 38) & (exg <= 4)
    suppress = noise_glare | noise_low_s
    if suppress.any():
        mask_muda[suppress] = 0
        mask_mature[suppress] = 0

    mask_raw = cv2.bitwise_or(mask_muda, mask_mature)
    return {
        "mask_muda": mask_muda,
        "mask_mature": mask_mature,
        "mask_hijau": mask_raw,
        "hsv_raw": hsv_raw,
        "rng": rng,
        "info": info,
    }


def pixel_to_meter(px, total_px, real_m):
    return px / total_px * real_m


# ─────────────────────────────────────────────────────────────────────────────
# KELAS UTAMA
# ─────────────────────────────────────────────────────────────────────────────

class KangkungAnalyzer:
    def __init__(self, source=None, frame_id=None):
        """
        source: path file gambar / index kamera (int) / None → buat gambar demo
        frame_id: identitas unik frame (kontrak PSI). None → dibuat otomatis
                  dari timestamp saat analyze_grid() dijalankan.
        """
        self.source = source
        self.image_orig = None
        self.image_rgb  = None
        self.h, self.w  = 0, 0
        self.frame_id = frame_id

        # Hasil analisis
        self.mask_muda   = None
        self.mask_mature = None
        self.mask_kuning = None
        self.mask_coklat = None
        self.mask_sehat  = None   # union semua jaringan tanaman
        self.mask_total  = None
        self.zone_results = {}
        self.global_stats = {}

    # ── Load / Demo ──────────────────────────────────────────────────────────

    def load_image(self):
        if self.source is None:
            print("[INFO] Tidak ada sumber gambar → membuat citra simulasi...")
            self.image_orig = self._buat_citra_simulasi()
        elif isinstance(self.source, int):
            cap = cv2.VideoCapture(self.source)
            ret, frame = cap.read()
            cap.release()
            if not ret:
                raise IOError(f"Tidak bisa membuka kamera index {self.source}")
            self.image_orig = frame
            print(f"[INFO] Frame dari kamera {self.source} berhasil diambil.")
        else:
            img = cv2.imread(self.source)
            if img is None:
                raise FileNotFoundError(f"File tidak ditemukan: {self.source}")
            self.image_orig = img
            print(f"[INFO] Gambar '{self.source}' berhasil dimuat.")

        self.image_rgb = cv2.cvtColor(self.image_orig, cv2.COLOR_BGR2RGB)
        self.h, self.w = self.image_orig.shape[:2]
        print(f"[INFO] Resolusi: {self.w}x{self.h} piksel "
              f"(~{pixel_to_meter(self.w, self.w, BED_CONFIG['panjang_m']):.2f} m × "
              f"{pixel_to_meter(self.h, self.h, BED_CONFIG['lebar_m']):.2f} m)")

    def _buat_citra_simulasi(self, w=1200, h=660):
        """Buat citra simulasi bed kangkung aquaponik."""
        np.random.seed(42)
        img = np.zeros((h, w, 3), dtype=np.uint8)

        # Latar air / media tanam (biru-abu)
        img[:] = [60, 80, 70]

        # ── Cluster tanaman kangkung ──────────────────────────────────────
        # Setiap cluster = satu rumpun tanaman
        clusters = [
            # (cx, cy, radius, density, stage)
            # stage: 0=muda, 1=mature, 2=over
            ( 80,  80, 65, 0.7, 0),
            (220,  90, 75, 0.8, 0),
            (380, 100, 85, 0.9, 1),
            (550,  85, 90, 0.85,1),
            (720,  95, 80, 0.75,1),
            (880,  80, 70, 0.6, 0),
            (1040, 90, 60, 0.5, 0),
            (1150, 70, 55, 0.4, 0),

            ( 90, 220, 70, 0.65,1),
            (240, 230, 95, 0.95,2),
            (430, 210, 90, 0.88,1),
            (600, 225, 85, 0.82,1),
            (760, 215, 75, 0.7, 1),
            (920, 205, 65, 0.6, 1),
            (1080,220, 55, 0.5, 0),

            (100, 360, 80, 0.75,1),
            (280, 350, 90, 0.9, 2),
            (470, 365, 95, 0.92,2),
            (650, 355, 85, 0.8, 1),
            (820, 345, 70, 0.65,1),
            (980, 360, 60, 0.55,0),
            (1120,350, 50, 0.4, 0),

            ( 85, 500, 60, 0.55,0),
            (210, 490, 70, 0.7, 1),
            (360, 505, 85, 0.85,1),
            (530, 495, 90, 0.9, 2),
            (700, 510, 80, 0.78,1),
            (860, 500, 65, 0.6, 0),
            (1010,490, 55, 0.45,0),
            (1140,505, 50, 0.35,0),

            (150, 590, 55, 0.5, 0),
            (300, 580, 65, 0.6, 0),
            (450, 595, 75, 0.7, 1),
            (620, 585, 70, 0.65,1),
            (780, 575, 60, 0.55,0),
            (940, 590, 50, 0.4, 0),
            (1090,580, 45, 0.3, 0),
        ]

        # Warna per stage (BGR)
        stage_colors = [
            ([50, 160, 50],  [70, 200, 80]),   # muda: hijau muda
            ([30, 120, 30],  [50, 160, 60]),   # mature: hijau tua
            ([20,  90, 80],  [35, 130,100]),   # over: agak kuning
        ]

        for cx, cy, r, dens, stage in clusters:
            n_daun = int(r * r * dens / 8)
            c_lo, c_hi = stage_colors[stage]
            for _ in range(n_daun):
                angle  = np.random.uniform(0, 2 * np.pi)
                dist   = np.random.uniform(0, r * 0.9)
                px = int(cx + dist * np.cos(angle))
                py = int(cy + dist * np.sin(angle))
                leaf_r = np.random.randint(6, 18)
                color  = [int(np.random.uniform(c_lo[i], c_hi[i])) for i in range(3)]
                # Gambar elips agar mirip daun
                axes = (leaf_r, max(3, leaf_r // 2))
                rot  = int(np.degrees(angle))
                cv2.ellipse(img, (px, py), axes, rot, 0, 360, color, -1)
                # Sedikit highlight
                cv2.ellipse(img, (px-2, py-2), (max(2,axes[0]-3), max(1,axes[1]-2)),
                            rot, 0, 360,
                            [min(255, c+40) for c in color], -1)

        # Tambah noise organik
        noise = np.random.randint(-12, 12, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        # Label watermark
        cv2.putText(img, "SIMULASI - Bed Aquaponik Kangkung 2m x 1.1m",
                    (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (200, 200, 200), 1, cv2.LINE_AA)
        return img

    # ── Segmentasi HSV ───────────────────────────────────────────────────────

    def segment(self, adaptif=True):
        """Segmentasi HSV — optimasi S & V adaptif (CLAHE V + glare recovery)."""
        seg = segmentasi_hijau_adaptif(self.image_orig, adaptif=adaptif)
        hsv = seg["hsv_raw"]
        rng = seg["rng"]
        self.info_adaptif = seg["info"]

        self.mask_muda = seg["mask_muda"]
        self.mask_mature = seg["mask_mature"]
        self.mask_kuning = cv2.inRange(hsv, rng["kuning"]["lower"],
                                       rng["kuning"]["upper"])
        self.mask_coklat = cv2.inRange(hsv, rng["coklat"]["lower"],
                                       rng["coklat"]["upper"])

        # Gate adjacency coklat dijalankan SETELAH mask_clean di bawah, karena
        # harus memakai hijau yang sudah dibersihkan (paritas dengan
        # mask_tanaman_warna() di adaptive_bed.py).

        # Gabung semua tanaman (hijau muda + tua)
        mask_raw = seg["mask_hijau"]

        # ── Post-processing morfologi ──────────────────────────────────────
        kernel3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel7 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

        # Hilangkan noise kecil
        mask_clean = cv2.morphologyEx(mask_raw, cv2.MORPH_OPEN,  kernel3)
        # Tutup lubang kecil di dalam daun
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel7)

        # Media tanam/bed juga coklat → coklat hanya valid bila BERDEKATAN
        # dengan kanopi hijau (daun mati muncul di dalam/tepi kanopi, bukan
        # di seluruh permukaan media). Adjacency via dilasi hijau 21x21.
        # WAJIB memakai mask_clean (bukan hijau raw): dengan mask raw, speck
        # noise hijau ikut melegitimasi coklat di luar kanopi sehingga
        # %coklat CLI (48%) dan jalur live/Pi (39%) berbeda pada gambar yang
        # sama. Angka inilah yang menjadi PSI → harus konsisten antar jalur.
        adj = cv2.dilate(mask_clean,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)))
        self.mask_coklat = cv2.bitwise_and(self.mask_coklat, adj)

        # Bercak kuning/coklat: cukup open (bercak kecil justru informasi
        # penting — jangan di-close agar tidak menyatu dengan kanopi hijau)
        self.mask_kuning = cv2.morphologyEx(self.mask_kuning,
                                            cv2.MORPH_OPEN, kernel3)
        self.mask_kuning = cv2.bitwise_and(self.mask_kuning,
                                           cv2.bitwise_not(mask_clean))
        self.mask_coklat = cv2.morphologyEx(self.mask_coklat,
                                            cv2.MORPH_OPEN, kernel3)

        # Union seluruh jaringan tanaman = denominator % kesehatan daun
        union = cv2.bitwise_or(mask_clean, self.mask_kuning)
        self.mask_sehat = cv2.bitwise_or(union, self.mask_coklat)

        self.mask_total = mask_clean
        print(f"[INFO] Segmentasi selesai. "
              f"Coverage global: {self._hitung_coverage(mask_clean):.1f}%")

    def _hitung_coverage(self, mask):
        return mask.sum() / 255 / mask.size * 100

    # ── Analisis Grid ─────────────────────────────────────────────────────────

    def analyze_grid(self):
        """Bagi bed menjadi grid zona dan hitung kelebatan per zona."""
        rows = BED_CONFIG["grid_rows"]
        cols = BED_CONFIG["grid_cols"]

        cell_h = self.h // rows
        cell_w = self.w // cols

        m_per_row = BED_CONFIG["lebar_m"]  / rows
        m_per_col = BED_CONFIG["panjang_m"] / cols

        self.zone_results = {}
        total_panen = 0

        # frame_id wajib ada untuk kontrak PSI: diisi otomatis bila tidak diberikan
        if not self.frame_id:
            self.frame_id = f"{self.source or 'cam'}-{sekarang_ms()}"

        for r in range(rows):
            for c in range(cols):
                y1 = r * cell_h
                y2 = y1 + cell_h if r < rows - 1 else self.h
                x1 = c * cell_w
                x2 = x1 + cell_w if c < cols - 1 else self.w

                zona_id = f"R{r+1}C{c+1}"
                mask_zona  = self.mask_total [y1:y2, x1:x2]
                muda_zona  = self.mask_muda  [y1:y2, x1:x2]
                mtr_zona   = self.mask_mature[y1:y2, x1:x2]
                kng_zona   = self.mask_kuning[y1:y2, x1:x2]
                cok_zona   = self.mask_coklat[y1:y2, x1:x2]
                tan_zona   = self.mask_sehat [y1:y2, x1:x2]

                cov      = self._hitung_coverage(mask_zona)
                cov_muda = self._hitung_coverage(muda_zona)
                cov_mtr  = self._hitung_coverage(mtr_zona)
                cov_kng  = self._hitung_coverage(kng_zona)
                cov_cok  = self._hitung_coverage(cok_zona)
                status   = get_status(cov)
                skor     = coverage_to_score(cov)

                # Kesehatan daun: % terhadap piksel TANAMAN (union hijau +
                # kuning + coklat). Zona tanpa tanaman → 0% & "sehat".
                tan_px = int(tan_zona.sum()) // 255
                if tan_px > 0:
                    pct_kng = kng_zona.sum() / 255 / tan_px * 100
                    pct_cok = cok_zona.sum() / 255 / tan_px * 100
                else:
                    pct_kng = pct_cok = 0.0
                kesehatan = get_kesehatan(pct_kng, pct_cok)

                # ── Jumlah piksel mentah untuk PSI (spesifikasi §3) ──────────
                # Setiap piksel WAJIB masuk tepat satu kategori. Ketiga mask
                # dibuat saling lepas secara KONSTRUKSI (bukan dikurangi
                # perkiraan): kuning dikurangi coklat, hijau dikurangi kuning
                # maupun coklat. Dengan begini G+Y+B selalu = |mask tanaman|,
                # sehingga unclassified_pixels otomatis 0 dan hasilnya bisa
                # diperiksa silang oleh pembaca ESP32.
                kng_bukan_cok = cv2.bitwise_and(kng_zona,
                                                cv2.bitwise_not(cok_zona))
                px_kuning = int(kng_bukan_cok.sum()) // 255
                px_coklat = int(cok_zona.sum()) // 255
                px_hijau = int(cv2.bitwise_and(
                    mask_zona, cv2.bitwise_not(
                        cv2.bitwise_or(kng_zona, cok_zona))).sum()) // 255
                px_klasifikasi = px_hijau + px_kuning + px_coklat
                px_unclassified = max(0, tan_px - px_klasifikasi)

                if status in ("siap_panen", "harus_panen"):
                    total_panen += 1

                self.zone_results[zona_id] = {
                    "bbox":        (x1, y1, x2, y2),
                    "coverage":    round(cov, 2),
                    "cov_muda":    round(cov_muda, 2),
                    "cov_mature":  round(cov_mtr, 2),
                    "cov_kuning":  round(cov_kng, 2),
                    "cov_coklat":  round(cov_cok, 2),
                    "pct_kuning":  round(pct_kng, 2),   # % thd tanaman
                    "pct_coklat":  round(pct_cok, 2),   # % thd tanaman
                    "kesehatan":   kesehatan,
                    "status":      status,
                    "skor":        round(skor, 1),
                    "luas_m2":     round(m_per_row * m_per_col, 3),
                    "green_pixels":  px_hijau,
                    "yellow_pixels": px_kuning,
                    "brown_pixels":  px_coklat,
                    "plant_mask_pixels": tan_px,
                    "unclassified_pixels": px_unclassified,
                }

        # Statistik global
        all_cov   = [v["coverage"] for v in self.zone_results.values()]
        all_skor  = [v["skor"]     for v in self.zone_results.values()]
        n_zona    = rows * cols

        status_count = {s: 0 for s in THRESHOLD}
        for z in self.zone_results.values():
            status_count[z["status"]] += 1

        # Agregat kesehatan daun (kuning = klorosis, coklat = nekrosis)
        kes_count = {"sehat": 0, "waspada": 0, "sakit": 0}
        for z in self.zone_results.values():
            kes_count[z["kesehatan"]] += 1
        kuning_rata = float(np.mean([z["pct_kuning"]
                                     for z in self.zone_results.values()]))
        coklat_rata = float(np.mean([z["pct_coklat"]
                                     for z in self.zone_results.values()]))

        # Indeks stres PSI. WAJIB dijumlah per piksel dulu (spesifikasi §4):
        # rata-rata PSI antar zona salah karena luas tanaman tiap zona beda.
        # Contoh: zona A 900 px hijau (PSI 0) + zona B 100 px coklat (PSI 100)
        # → global 10, bukan 50.
        psi_hasil = hasil_psi(
            sum(z["green_pixels"] for z in self.zone_results.values()),
            sum(z["yellow_pixels"] for z in self.zone_results.values()),
            sum(z["brown_pixels"] for z in self.zone_results.values()),
            plant_mask_pixels=sum(z["plant_mask_pixels"]
                                  for z in self.zone_results.values()),
            unclassified_pixels=sum(z["unclassified_pixels"]
                                    for z in self.zone_results.values()),
            captured_at_ms=sekarang_ms(),
            frame_id=self.frame_id,
        )
        psi_rata = round(psi_hasil["psi"], 1) if psi_hasil["psi"] is not None \
            else None
        # psi_maks = PSI zona terburuk, dihitung dari piksel zona itu sendiri.
        # Dikirim terpisah agar 1 zona mati tidak hilang di agregat bed.
        psi_maks = max((hitung_psi(z["green_pixels"], z["yellow_pixels"],
                                   z["brown_pixels"]) or 0.0
                        for z in self.zone_results.values()), default=None)
        psi_maks = round(psi_maks, 1) if psi_maks is not None else None

        self.global_stats = {
            "total_zona":           n_zona,
            "coverage_rata":        round(np.mean(all_cov),  2),
            "coverage_std":         round(np.std(all_cov),   2),
            "coverage_min":         round(np.min(all_cov),   2),
            "coverage_max":         round(np.max(all_cov),   2),
            "skor_panen_rata":      round(np.mean(all_skor), 1),
            "zona_siap_panen":      status_count["siap_panen"] + status_count["harus_panen"],
            "persen_siap":          round((status_count["siap_panen"] +
                                           status_count["harus_panen"]) / n_zona * 100, 1),
            "status_distribusi":    status_count,
            "kesehatan_distribusi": kes_count,
            "kuning_rata":          round(kuning_rata, 2),
            "coklat_rata":          round(coklat_rata, 2),
            "zona_sakit":           kes_count["sakit"],
            "psi":                  psi_rata,
            "psi_maks":             psi_maks,
            "psi_versi":            PSI_VERSION,
            "psi_valid":            psi_hasil["valid"],
            "psi_reason":           psi_hasil["reason"],
            "captured_at_ms":       psi_hasil["captured_at_ms"],
            "frame_id":             self.frame_id,
            "green_pixels":         psi_hasil["green_pixels"],
            "yellow_pixels":        psi_hasil["yellow_pixels"],
            "brown_pixels":         psi_hasil["brown_pixels"],
            "classified_pixels":    psi_hasil["classified_pixels"],
            "plant_mask_pixels":    psi_hasil["plant_mask_pixels"],
            "unclassified_pixels":  psi_hasil["unclassified_pixels"],
            "rekomendasi_kesehatan": self._buat_rekomendasi_kesehatan(
                                        kes_count, kuning_rata, coklat_rata),
            "rekomendasi":          self._buat_rekomendasi(
                                        status_count, np.mean(all_cov), n_zona),
            "timestamp":            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _buat_rekomendasi(self, sc, rata_cov, n):
        siap = sc["siap_panen"] + sc["harus_panen"]
        pct  = siap / n * 100
        if pct >= 75:
            return ("🌿 SEGERA PANEN — Lebih dari 75% bed sudah siap panen. "
                    "Tunda panen berisiko over-density dan persaingan nutrisi.")
        elif pct >= 50:
            return ("✅ PANEN PARSIAL — Panen zona merah dan hijau terlebih dahulu. "
                    "Sisakan zona biru-oranye untuk pertumbuhan berikutnya.")
        elif pct >= 25:
            return ("⏳ TUNGGU 3–5 HARI — Tanaman belum merata matang. "
                    "Pantau zona yang hampir siap dan pastikan nutrisi cukup.")
        else:
            return ("🌱 MASIH DALAM PERTUMBUHAN — Coverage rata-rata "
                    f"{rata_cov:.0f}%. Perkiraan panen: 7–14 hari ke depan.")

    def _buat_rekomendasi_kesehatan(self, kes_count, kuning_rata, coklat_rata):
        """Rekomendasi kesehatan — sinyal untuk kontrol pompa/nutrisi."""
        if coklat_rata >= KESEHATAN["coklat_sakit"] or kes_count["sakit"] >= 6:
            return ("DEAD ZONES — Coklat (nekrosis) dominan: buang/panen "
                    "selektif zona sakit dan cek akar. Tanaman coklat tidak "
                    "dapat dipulihkan.")
        if kuning_rata >= KESEHATAN["kuning_sakit"] or kes_count["sakit"] >= 3:
            return ("NUTRISI KRITIS — Klorosis luas: cek nitrogen/besi dan pH "
                    "air segera. Sinyal untuk kontroler pompa (fuzzy).")
        if kuning_rata >= KESEHATAN["kuning_waspada"] or \
                kes_count["waspada"] >= 4:
            return ("WASPADA — Gejala menguning awal di beberapa zona. "
                    "Pantau harian dan kalibrasi nutrisi.")
        return "SEHAT — Kanopi dominan hijau, tidak ada gejala klorosis/nekrosis."

    # ── Visualisasi ───────────────────────────────────────────────────────────

    def visualisasi(self, save_path=None):
        # Import di dalam fungsi: matplotlib hanya dibutuhkan untuk plot debug,
        # sehingga pipeline di Raspberry Pi (kangkung_pi.py) tidak memerlukannya.
        try:
            import matplotlib
            matplotlib.use("Agg")            # aman tanpa display (headless)
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            from matplotlib.gridspec import GridSpec
        except ImportError as e:
            raise ImportError(
                "visualisasi() butuh matplotlib "
                "(laptop: pip install matplotlib)") from e

        fig = plt.figure(figsize=(22, 14), facecolor="#1a1a2e")
        fig.patch.set_facecolor("#1a1a2e")

        gs = GridSpec(3, 4, figure=fig,
                      hspace=0.38, wspace=0.35,
                      left=0.04, right=0.97, top=0.93, bottom=0.06)

        title_color   = "#e8f4f8"
        label_color   = "#b0c4de"
        cell_alpha     = 0.45

        # ── 0: Gambar Asli ─────────────────────────────────────────────────
        ax0 = fig.add_subplot(gs[0, :2])
        ax0.imshow(self.image_rgb)
        ax0.set_title("📷  Citra Input — Bed Aquaponik Kangkung",
                      color=title_color, fontsize=11, pad=8)
        ax0.axis("off")

        # ── 1: Overlay Segmentasi ──────────────────────────────────────────
        ax1 = fig.add_subplot(gs[0, 2:])
        overlay = self.image_rgb.copy()
        # Warnai mask: muda=cyan, mature=lime, kuning=yellow, coklat=brown
        overlay[self.mask_muda   > 0] = [80, 220, 120]
        overlay[self.mask_mature > 0] = [40, 180,  80]
        overlay[self.mask_kuning > 0] = [220, 200,  60]
        overlay[self.mask_coklat > 0] = [90, 60, 30]
        blended = cv2.addWeighted(self.image_rgb, 0.4, overlay, 0.6, 0)
        ax1.imshow(blended)
        ax1.set_title("🎨  Hasil Segmentasi HSV",
                      color=title_color, fontsize=11, pad=8)
        ax1.axis("off")
        legend_elem = [
            mpatches.Patch(color=[80/255,220/255,120/255], label="Hijau Muda"),
            mpatches.Patch(color=[40/255,180/255, 80/255], label="Hijau Mature"),
            mpatches.Patch(color=[220/255,200/255,60/255], label="Kuning (Klorosis)"),
            mpatches.Patch(color=[90/255,60/255,30/255],   label="Coklat (Nekrosis)"),
        ]
        ax1.legend(handles=legend_elem, loc="lower right",
                   fontsize=8, framealpha=0.5,
                   facecolor="#1a1a2e", labelcolor="white")

        # ── 2: Peta Zona Kelebatan ─────────────────────────────────────────
        ax2 = fig.add_subplot(gs[1, :2])
        ax2.imshow(self.image_rgb, alpha=0.35)
        ax2.set_title("🗺️  Peta Zona Kelebatan & Status Panen",
                      color=title_color, fontsize=11, pad=8)

        status_hex = {
            "belum_siap":  "#3498db",
            "hampir_siap": "#f39c12",
            "siap_panen":  "#2ecc71",
            "harus_panen": "#e74c3c",
        }

        for zona_id, z in self.zone_results.items():
            x1, y1, x2, y2 = z["bbox"]
            cw, ch = x2 - x1, y2 - y1
            color_hex = status_hex[z["status"]]
            # RGB 0–1
            r_c = int(color_hex[1:3], 16) / 255
            g_c = int(color_hex[3:5], 16) / 255
            b_c = int(color_hex[5:7], 16) / 255

            rect = plt.Rectangle((x1, y1), cw, ch,
                                  linewidth=1.2, edgecolor="white",
                                  facecolor=(r_c, g_c, b_c), alpha=cell_alpha)
            ax2.add_patch(rect)
            ax2.text(x1 + cw * 0.5, y1 + ch * 0.4,
                     f"{z['coverage']:.0f}%",
                     ha="center", va="center",
                     color="white", fontsize=7.5, fontweight="bold")
            ax2.text(x1 + cw * 0.5, y1 + ch * 0.75,
                     f"S:{z['skor']:.0f}",
                     ha="center", va="center",
                     color="lightyellow", fontsize=6.5)

        ax2.set_xlim(0, self.w); ax2.set_ylim(self.h, 0)
        ax2.axis("off")
        leg2 = [mpatches.Patch(color=v, label=k.replace("_", " ").title())
                for k, v in status_hex.items()]
        ax2.legend(handles=leg2, loc="lower right", fontsize=7.5,
                   framealpha=0.55, facecolor="#1a1a2e", labelcolor="white")

        # ── 3: Heatmap Coverage ───────────────────────────────────────────
        ax3 = fig.add_subplot(gs[1, 2:])
        rows = BED_CONFIG["grid_rows"]
        cols = BED_CONFIG["grid_cols"]
        heatmap = np.zeros((rows, cols))
        for r in range(rows):
            for c in range(cols):
                heatmap[r, c] = self.zone_results[f"R{r+1}C{c+1}"]["coverage"]

        im = ax3.imshow(heatmap, cmap="RdYlGn", vmin=0, vmax=100,
                        aspect="auto", interpolation="bilinear")
        for r in range(rows):
            for c in range(cols):
                ax3.text(c, r, f"{heatmap[r,c]:.0f}%",
                         ha="center", va="center",
                         color="black", fontsize=8, fontweight="bold")
        plt.colorbar(im, ax=ax3, label="Coverage (%)",
                     shrink=0.85).ax.yaxis.label.set_color(label_color)
        ax3.set_title("🌡️  Heatmap Kelebatan Kanopi",
                      color=title_color, fontsize=11, pad=8)
        ax3.set_xticks(range(cols))
        ax3.set_xticklabels([f"K{i+1}" for i in range(cols)], color=label_color, fontsize=8)
        ax3.set_yticks(range(rows))
        ax3.set_yticklabels([f"B{i+1}" for i in range(rows)], color=label_color, fontsize=8)
        ax3.tick_params(colors=label_color)

        # ── 4: Distribusi Coverage Histogram ─────────────────────────────
        ax4 = fig.add_subplot(gs[2, 0])
        all_cov = [z["coverage"] for z in self.zone_results.values()]
        ax4.hist(all_cov, bins=12, color="#2ecc71", edgecolor="#1a1a2e",
                 alpha=0.85, rwidth=0.85)
        ax4.axvline(np.mean(all_cov), color="#e74c3c", linewidth=1.8,
                    linestyle="--", label=f"Rata: {np.mean(all_cov):.1f}%")
        ax4.set_facecolor("#16213e")
        ax4.set_title("📊  Distribusi Coverage", color=title_color, fontsize=10)
        ax4.set_xlabel("Coverage (%)", color=label_color, fontsize=8)
        ax4.set_ylabel("Jumlah Zona", color=label_color, fontsize=8)
        ax4.tick_params(colors=label_color)
        ax4.legend(fontsize=8, labelcolor=label_color,
                   facecolor="#1a1a2e", framealpha=0.6)
        for spine in ax4.spines.values():
            spine.set_edgecolor("#34495e")

        # ── 5: Pie Status Zona ────────────────────────────────────────────
        ax5 = fig.add_subplot(gs[2, 1])
        sc = self.global_stats["status_distribusi"]
        labels_pie = [k.replace("_", " ").title() for k, v in sc.items() if v > 0]
        vals_pie   = [v for v in sc.values() if v > 0]
        colors_pie = [status_hex[k] for k, v in sc.items() if v > 0]
        wedges, _, autotxts = ax5.pie(
            vals_pie, labels=None, colors=colors_pie,
            autopct="%1.0f%%", startangle=90,
            wedgeprops={"edgecolor": "#1a1a2e", "linewidth": 1.5}
        )
        for t in autotxts:
            t.set_color("white"); t.set_fontsize(9)
        ax5.legend(wedges, labels_pie, loc="upper left",
                   bbox_to_anchor=(-0.15, 1.0), fontsize=7.5,
                   facecolor="#1a1a2e", labelcolor="white")
        ax5.set_title("🥧  Status Distribusi Zona", color=title_color, fontsize=10)
        ax5.set_facecolor("#16213e")

        # ── 6: Skor Panen per Zona (bar) ──────────────────────────────────
        ax6 = fig.add_subplot(gs[2, 2])
        skor_vals = [z["skor"] for z in self.zone_results.values()]
        bar_colors = [status_hex[z["status"]] for z in self.zone_results.values()]
        ax6.bar(range(len(skor_vals)), skor_vals, color=bar_colors,
                edgecolor="#1a1a2e", linewidth=0.5)
        ax6.axhline(70, color="#f39c12", linewidth=1.2, linestyle=":",
                    label="Batas siap panen (70)")
        ax6.set_facecolor("#16213e")
        ax6.set_title("📈  Skor Kesiapan Panen / Zona", color=title_color, fontsize=10)
        ax6.set_xlabel("Zona (index)", color=label_color, fontsize=8)
        ax6.set_ylabel("Skor (0–100)", color=label_color, fontsize=8)
        ax6.set_ylim(0, 105)
        ax6.tick_params(colors=label_color)
        ax6.legend(fontsize=8, labelcolor=label_color,
                   facecolor="#1a1a2e", framealpha=0.6)
        for spine in ax6.spines.values():
            spine.set_edgecolor("#34495e")

        # ── 7: Panel Ringkasan ────────────────────────────────────────────
        ax7 = fig.add_subplot(gs[2, 3])
        ax7.set_facecolor("#0f3460")
        ax7.axis("off")
        gs_stat = self.global_stats
        lines = [
            ("RINGKASAN ANALISIS", None, 12, "bold"),
            (f"Waktu: {gs_stat['timestamp']}", None, 7.5, "normal"),
            ("", None, 8, "normal"),
            (f"Coverage Rata-rata:", f"{gs_stat['coverage_rata']:.1f}%", 9, "normal"),
            (f"Coverage Min / Max:",
             f"{gs_stat['coverage_min']:.0f}% / {gs_stat['coverage_max']:.0f}%", 9, "normal"),
            (f"Skor Panen Rata-rata:", f"{gs_stat['skor_panen_rata']:.0f}/100", 9, "normal"),
            (f"Kuning / Coklat Rata:",
             f"{gs_stat.get('kuning_rata', 0):.1f}% / {gs_stat.get('coklat_rata', 0):.1f}%", 9, "normal"),
            ("", None, 8, "normal"),
            (f"Zona Siap Panen:",
             f"{gs_stat['zona_siap_panen']} / {gs_stat['total_zona']} zona", 9, "bold"),
            (f"Persentase Siap:", f"{gs_stat['persen_siap']:.1f}%", 9, "bold"),
            ("", None, 8, "normal"),
            ("REKOMENDASI:", None, 9, "bold"),
        ]
        y_pos = 0.96
        for item in lines:
            key, val, fs, fw = item
            if val:
                ax7.text(0.05, y_pos, key, transform=ax7.transAxes,
                         color=label_color, fontsize=fs, va="top", fontweight=fw)
                ax7.text(0.97, y_pos, val, transform=ax7.transAxes,
                         color="#2ecc71", fontsize=fs, va="top",
                         fontweight="bold", ha="right")
            else:
                ax7.text(0.5, y_pos, key, transform=ax7.transAxes,
                         color=title_color, fontsize=fs, va="top",
                         fontweight=fw, ha="center")
            y_pos -= 0.09

        # Rekomendasi (wrap teks)
        rek = gs_stat["rekomendasi"]
        words = rek.split()
        lines_rek, line = [], []
        for w in words:
            line.append(w)
            if len(" ".join(line)) > 28:
                lines_rek.append(" ".join(line[:-1]))
                line = [w]
        if line:
            lines_rek.append(" ".join(line))
        for l in lines_rek:
            ax7.text(0.05, y_pos, l, transform=ax7.transAxes,
                     color="#f1c40f", fontsize=8.2, va="top")
            y_pos -= 0.09

        # Judul utama
        fig.suptitle(
            "🌿  SISTEM ANALISIS KELEBATAN KANGKUNG — BED AQUAPONIK  "
            f"({BED_CONFIG['panjang_m']}m × {BED_CONFIG['lebar_m']}m)",
            color=title_color, fontsize=14, fontweight="bold", y=0.975
        )

        plt.tight_layout(rect=[0, 0, 1, 0.97])

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight",
                        facecolor="#1a1a2e")
            print(f"[INFO] Visualisasi disimpan: {save_path}")
        else:
            plt.show()

        return fig

    # ── Export JSON ───────────────────────────────────────────────────────────

    def export_json(self, path="hasil_analisis.json"):
        output = {
            "metadata": {
                "bed_panjang_m": BED_CONFIG["panjang_m"],
                "bed_lebar_m":   BED_CONFIG["lebar_m"],
                "grid":          f"{BED_CONFIG['grid_rows']}x{BED_CONFIG['grid_cols']}",
                "resolusi_px":   f"{self.w}x{self.h}",
            },
            "global": self.global_stats,
            "zona":   {k: {kk: vv for kk, vv in v.items() if kk != "bbox"}
                       for k, v in self.zone_results.items()},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Laporan JSON disimpan: {path}")
        return output

    # ── Cetak Laporan Terminal ────────────────────────────────────────────────

    def print_laporan(self):
        gs = self.global_stats
        sep = "═" * 62
        print(f"\n{sep}")
        print(f"  LAPORAN ANALISIS KELEBATAN KANGKUNG AQUAPONIK")
        print(f"  {gs['timestamp']}")
        print(sep)
        print(f"  Bed           : {BED_CONFIG['panjang_m']} m × {BED_CONFIG['lebar_m']} m "
              f"= {BED_CONFIG['panjang_m']*BED_CONFIG['lebar_m']:.2f} m²")
        print(f"  Grid Analisis : {BED_CONFIG['grid_rows']} baris × "
              f"{BED_CONFIG['grid_cols']} kolom = {gs['total_zona']} zona")
        print(f"  Coverage Rata : {gs['coverage_rata']:.1f}% ± {gs['coverage_std']:.1f}%")
        print(f"  Coverage Range: {gs['coverage_min']:.1f}% — {gs['coverage_max']:.1f}%")
        print(f"  Skor Panen    : {gs['skor_panen_rata']:.1f} / 100")
        print()
        print(f"  Distribusi Status Zona:")
        for s, n in gs["status_distribusi"].items():
            bar = "█" * n + "░" * (gs["total_zona"] - n)
            pct = n / gs["total_zona"] * 100
            print(f"    {s:14s}: {bar}  {n:2d} zona ({pct:.0f}%)")
        print()
        print(f"  Kesehatan Daun (kuning=klorosis, coklat=nekrosis):")
        for s, n in gs.get("kesehatan_distribusi",
                           {"sehat": 0, "waspada": 0, "sakit": 0}).items():
            print(f"    {s:14s}: {n:2d} zona")
        print(f"  Kuning Rata (thd tanaman) : "
              f"{gs.get('kuning_rata', 0):.1f}%")
        print(f"  Coklat Rata (thd tanaman) : "
              f"{gs.get('coklat_rata', 0):.1f}%")
        print(f"  Zona Siap Panen : {gs['zona_siap_panen']} / {gs['total_zona']} "
              f"({gs['persen_siap']:.1f}%)")
        print(f"\n  REKOMENDASI:\n  {gs['rekomendasi']}")
        print(sep)

    # ── Pipeline Utama ────────────────────────────────────────────────────────

    def run(self, save_viz=None, save_json=None):
        self.load_image()
        self.segment()
        self.analyze_grid()
        self.print_laporan()
        self.visualisasi(save_path=save_viz)
        if save_json:
            self.export_json(save_json)
        return self.global_stats


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Gunakan argumen CLI jika ada, atau jalankan demo
    source = sys.argv[1] if len(sys.argv) > 1 else None

    # Jika argumen adalah angka → index kamera
    if source is not None:
        try:
            source = int(source)
        except ValueError:
            pass  # tetap string (path file)

    analyzer = KangkungAnalyzer(source=source)
    analyzer.run(
        save_viz  = "output/hasil_segmentasi.png",
        save_json = "output/laporan.json",
    )
