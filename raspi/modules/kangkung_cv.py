"""
=============================================================================
  SISTEM COMPUTER VISION - SEGMENTASI KELEBATAN TANAMAN KANGKUNG
  Bed Aquaponik | Ukuran: 2 m x 1.1 m
  Mengukur kesiapan panen berdasarkan densitas & morfologi tanaman
=============================================================================
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import json
import os
import sys
from datetime import datetime

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
    Range HSV per kelas ADAPTIF-ILUMINASI (method 2 proyek).
    f = mean(V)/ref menggeser S_lo/V_lo & V_hi; Hue TIDAK digeser
    (identitas warna hijau/kuning/coklat tetap). Nilai statis HSV_KANGKUNG
    dipakai sebagai seed; pergeseran dibatasi clip agar tidak liar.
    Rujukan: notebook section 5; Woebbecke (1995); Hameed (2018).
    """
    V = cv2.split(hsv)[2]
    f = float(np.clip(V.mean() / ref, 0.6, 1.6))
    s_lo = int(np.clip(base * f, 20, 120))
    v_lo = int(np.clip(base * f, 20, 120))
    v_hi = int(np.clip(200 * f, 150, 255))
    rng = {}
    for k in HSV_KANGKUNG:
        lo = HSV_KANGKUNG[k]["lower"].copy()
        hi = HSV_KANGKUNG[k]["upper"].copy()
        if f >= 1.0:
            # Terang: naikkan floor + cap V atas (buang glare)
            lo[1] = max(int(lo[1]), s_lo)
            lo[2] = max(int(lo[2]), v_lo)
            hi[2] = min(int(hi[2]), v_hi)
        else:
            # Gelap: turunkan floor seed secara proporsional (recover daun
            # gelap) — tetap konservatif agar media tanam tidak ikut masuk
            lo[1] = int(lo[1] * (0.5 + 0.5 * f))
            lo[2] = int(lo[2] * (0.4 + 0.6 * f))
        rng[k] = {"lower": lo, "upper": hi}
    # Kelas diagnostik (kuning/coklat) TIDAK ikut dilonggarkan — tetap seed
    # statis agar status kesehatan deterministik (terbukti: pelonggaran
    # memicu false-positive nekrosis hingga 21/24 zona pada bed sehat).
    for k in ("kuning", "coklat"):
        rng[k] = {"lower": HSV_KANGKUNG[k]["lower"].copy(),
                  "upper": HSV_KANGKUNG[k]["upper"].copy()}
    rng["info"] = {"f": round(f, 2), "s_lo": s_lo,
                   "v_lo": v_lo, "v_hi": v_hi}
    return rng


def pixel_to_meter(px, total_px, real_m):
    return px / total_px * real_m


# ─────────────────────────────────────────────────────────────────────────────
# KELAS UTAMA
# ─────────────────────────────────────────────────────────────────────────────

class KangkungAnalyzer:
    def __init__(self, source=None):
        """
        source: path file gambar / index kamera (int) / None → buat gambar demo
        """
        self.source = source
        self.image_orig = None
        self.image_rgb  = None
        self.h, self.w  = 0, 0

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
        """Segmentasi HSV — range ADAPTIF (f = mean(V)/128) secara default."""
        hsv = cv2.cvtColor(self.image_orig, cv2.COLOR_BGR2HSV)

        if adaptif:
            rng = parameter_adaptif(hsv)
        else:
            rng = {k: {"lower": HSV_KANGKUNG[k]["lower"],
                       "upper": HSV_KANGKUNG[k]["upper"]}
                   for k in HSV_KANGKUNG}
        self.info_adaptif = rng["info"] if adaptif else {
            "f": 1.0, "s_lo": 40, "v_lo": 40, "v_hi": 255}

        # Buat mask per kategori (range hasil adaptasi)
        self.mask_muda   = cv2.inRange(hsv, rng["muda"]["lower"],
                                       rng["muda"]["upper"])
        self.mask_mature = cv2.inRange(hsv, rng["mature"]["lower"],
                                       rng["mature"]["upper"])
        self.mask_kuning = cv2.inRange(hsv, rng["kuning"]["lower"],
                                       rng["kuning"]["upper"])
        self.mask_coklat = cv2.inRange(hsv, rng["coklat"]["lower"],
                                       rng["coklat"]["upper"])

        # Media tanam/bed juga coklat → coklat hanya valid bila BERDEKATAN
        # dengan kanopi hijau (daun mati muncul di dalam/tepi kanopi, bukan
        # di seluruh permukaan media). Adjacency via dilasi hijau 21x21.
        hijau_raw = cv2.bitwise_or(self.mask_muda, self.mask_mature)
        adj = cv2.dilate(hijau_raw,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)))
        self.mask_coklat = cv2.bitwise_and(self.mask_coklat, adj)

        # Gabung semua tanaman (hijau muda + tua)
        mask_raw = cv2.bitwise_or(self.mask_muda, self.mask_mature)

        # ── Post-processing morfologi ──────────────────────────────────────
        kernel3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel7 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

        # Hilangkan noise kecil
        mask_clean = cv2.morphologyEx(mask_raw, cv2.MORPH_OPEN,  kernel3)
        # Tutup lubang kecil di dalam daun
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel7)

        # Bercak kuning/coklat: cukup open (bercak kecil justru informasi
        # penting — jangan di-close agar tidak menyatu dengan kanopi hijau)
        self.mask_kuning = cv2.morphologyEx(self.mask_kuning,
                                            cv2.MORPH_OPEN, kernel3)
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
