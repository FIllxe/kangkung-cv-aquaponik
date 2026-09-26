# LAPORAN PROGRES CAPSTONE — BIMBINGAN

**Nama / NIM** : _________________
**Tanggal** : 15 September 2026
**Judul** : Sistem Computer Vision Deteksi Kesiapan Panen Kangkung Aquaponik —
Grid 4×6 dengan Segmentasi HSV Adaptif (Jalur Prototype)
**Target selesai** : akhir November 2026

---

## 1. Ringkasan Satu Paragraf

Sistem computer vision untuk menilai kesiapan panen kangkung per zona pada bed
aquaponik 2 m × 1,1 m sudah **berjalan end-to-end**: video HP → deteksi tepi bed →
warp perspektif → grid 4×6 → segmentasi HSV → coverage & status panen per zona →
timeseries CSV + JSON + video beranotasi. Dua method dikembangkan: (1) deteksi edge
Canny → quad → homografi untuk grid otomatis, (2) HSV adaptif-iluminasi + EMA yang
menurunkan jitter sudut deteksi **53%** (19,93 → 9,32 px). Sistem sudah diuji pada
**18 video lapangan** dan 7 foto batch. Sisa pekerjaan: evaluasi kuantitatif vs
ground truth, validasi ambang, dan finalisasi laporan.

---

## 2. Yang Sudah Selesai ✅

| # | Item | Bukti |
|---|---|---|
| 1 | Pipeline end-to-end berjalan (deteksi bed → warp → grid → status) | 18 video diproses, output di `output\video\` (timeseries + ringkasan + 4 MP4 beranotasi) |
| 2 | **Method 1** — Canny edge → approx quad → homografi → grid 4×6 | Notebook §4; `adaptive_bed.py` |
| 3 | **Method 2** — HSV adaptif-iluminasi (`f = mean(V)/128`) + multi-threshold + EMA | Jitter sudut **19,93 → 9,32 px (−53%)**; Notebook §5 |
| 4 | Demo dua video lapangan | `output\demo\demo_dua_video.png` — IMG_5159 cov 49,6% vs IMG_5388 cov 58,4% |
| 5 | Batch 7 foto bed tahap seedling → ready | `output\segmentasi_batch\RINGKASAN_BATCH.png` + CSV |
| 6 | Notebook presentasi 16 cell, semua tereksekusi | `notebooks\presentasi_kangkung_cv.ipynb` |
| 7 | Tinjauan pustaka: **53 paper terverifikasi** (OpenAlex: 14 + 20 + 13 + 6), termasuk Canny 1986 (29.443 sitasi) & Woebbecke 1995 (1.543) | `files paper\` (DAFTAR + TAMBAHAN_20 + METHOD_BARU + KESEHATAN_DAUN) |
| 8 | Kontrak skema dashboard Firebase (mengikuti dashboard yang sudah ada) | `docs\SKEMA_FIREBASE_BED_READINGS.md` + payload contoh siap upload |
| 9 | **Deteksi kesehatan daun per zona** — kuning/klorosis (H 21–34) & coklat/nekrosis (H 8–20 + adjacency kanopi 21×21), ambang 10/25% & 3/8% | `files\kangkung_cv.py`; uji positif: `output\evaluasi\uji_kuning_coklat.jpg` |
| 10 | **Panel demo kesehatan daun (before/after)** — blob kuning 58%K & coklat 20,5%C terdeteksi `sakit` tepat di zona injeksi; zona kanopi <30% otomatis `n/a`; heatmap 4×6 deteksi = target 100% | `files\panel_kesehatan_daun.py` → `output\evaluasi\panel_kesehatan_daun.png` |
| 11 | **Paket deploy Raspberry Pi siap jalan** — Debian 13 aarch64 (Python 3.13), remote admin via Tailscale (tanpa buka port), kamera **CSI IR 5MP (ov5647)** terbaca lewat libcamera/Picamera2, `kangkung_pi.py --test` berjalan (venv: opencv 4.10.0, numpy 1.26.4, firebase-admin 6.5.0) | `raspi/README.md`, `raspi/camera_pi.py` |
| 12 | **Indeks stres PSI (Plant Stress Index) 0–100 sebagai input tim fuzzy** — `PSI = 100·min(1, 0.4·min(kuning/25,1) + 0.6·min(coklat/8,1))`, normalisasi ke ambang `KESEHATAN`; dikirim lengkap dengan `psi_maks` (zona terburuk) + `psi_versi`; skema Firebase naik ke **v1.1** + kontrak loop fuzzy (koleksi `keputusan_fuzzy`, aturan stale/null/cooldown) | `files/kangkung_cv.py::hitung_psi`, `raspi/fuzzy_export.py`, `files/cek_psi.py`, `docs/SKEMA_FIREBASE_BED_READINGS.md` |
| 13 | **Perbaikan konsistensi antar jalur segmentasi** — gate adjacency coklat di `KangkungAnalyzer.segment()` kini memakai mask hijau **sudah dibersihkan** (bukan raw), sama persis dengan `mask_tanaman_warna()`; selisih CLI vs live/Pi pada gambar yang sama turun dari **9 pp → 0,005 pp** (dummy coklat: 48,05% → **39,18%**, sesuai target generator) | `files/kangkung_cv.py`, `files/cek_psi.py` (regression test) |

## 3. Yang Sedang / Akan Dikerjakan 🔄

| # | Item | Target | Status |
|---|---|---|---|
| 1 | Mask ground truth 5 gambar (`buat_gt.py`) → metrik **P/R/F1/IoU** | akhir Sep | Tool siap, `gt/` belum dibuat |
| 2 | Perbandingan metode: HSV vs ExG vs Otsu-Hue (`bandingkan_metode.py`) | akhir Sep | Tool siap, menunggu GT |
| 3 | Validasi ambang 25/55/80% (ahli/petani atau justifikasi paper) | awal Okt | Menunggu arahan dosen |
| 4 | Uji live lapangan (`live_monitor.py --no-gui` di laptop + `kangkung_pi.py` di Pi) + uji cahaya pagi/siang/sore | akhir Okt | Paket Pi siap; menunggu kasing/box kamera |
| 5 | Finalisasi Bab 4 (hasil) + Bab 5 (kesimpulan) | awal Nov | — |
| 6 | Revisi + README + video demo 2 menit + slide | mid Nov | — |
| 7 | Integrasi upload otomatis Firebase (Tahap B) | Okt (opsional) | Skrip siap (`firebase_uplink.py` + offline queue); tinggal kredensial & `storage_bucket` |

---

## 4. Rencana Demo (±5 menit)

1. **30 detik** `output\demo\IMG_5159_beranotasi.mp4` — quad bed + grid berwarna + HUD coverage.
2. `output\demo\demo_dua_video.png` — perbandingan dua bed (49,6% vs 58,4%; distribusi status).
3. Notebook §5 — HSV statis vs adaptif pada 3 kondisi cahaya + grafik jitter EMA.
4. `output\evaluasi\panel_kesehatan_daun.png` — demo deteksi kesehatan daun: bed asli →
   injeksi blob kuning/coklat → zona sakit terdeteksi otomatis + heatmap validasi 24 zona.

## 5. Pertanyaan — Mohon Arahan

1. **Ambang status panen 25/55/80%**: cukup justifikasi paper (canopy cover ↔ yield),
   atau wajib validasi penilaian petani/ahli?
2. **Prototype akhir**: uji laptop + webcam di lapangan cukup, atau wajib deploy Raspberry Pi?
3. **Bab 3 laporan**: perlu UML lengkap atau cukup diagram alur pipeline + arsitektur?
4. **PSI → fuzzy**: apakah "ganti air" memang respons yang tepat untuk klorosis?
   Secara agronomi klorosis umumnya defisiensi N/Fe atau pH lockout, sedangkan
   mengganti air di aquaponik berisiko mengganggu bakteri nitrifikasi + ikan.
   Perlu validasi rule base oleh dosen/ahli, atau cukup landasan pustaka?
5. **Rule base fuzzy**: berapa anteseden yang dipakai (PSI saja, atau PSI +
   `psi_maks` + `zona_sakit`), dan siapa yang menetapkan membership set-nya?

## 6. Jawaban Antisipasi Pertanyaan Dosen

| Kemungkinan pertanyaan | Jawaban singkat |
|---|---|
| "Akurasi berapa?" | Tool evaluasi sudah siap (P/R/F1/IoU + pembanding 2 metode lain); mask GT sedang dikerjakan, angka final akhir Sep. Yang sudah terukur: jitter −53%, coverage konsisten antar video. |
| "Kenapa bukan deep learning?" | Dataset anotasi kecil (7 foto + video); target deploy ringan (RPi tanpa GPU); HSV+kontur ~20–25 ms/frame di CPU. DL dicantumkan sebagai pengembangan lanjutan. |
| "Output-nya apa untuk petani?" | Peta status 24 zona (belum/hampir/siap/harus panen) **+ status kesehatan daun per zona (sehat/waspada/sakit karena kuning/coklat)** + rekomendasi teks + timeseries; siap dikirim ke dashboard web (skema Firebase sudah disepakati). |
| "Kapan selesai?" | Target akhir November. Coding inti selesai; sisa evaluasi + validasi + laporan (timeline di §3). |

## 7. Checklist H-1 Bimbingan

- [ ] Tes offline (aman, output terpisah): `python proses_video.py ..\data\videos\IMG_5159.MOV --adaptive --max-frames 30 --no-gui --save --out-dir ..\output\evaluasi`
- [ ] Siapkan 3 file demo: MP4 beranotasi, `demo_dua_video.png`, 1 JSON ringkasan
- [ ] Print dokumen ini (1–2 halaman) + timeline November
- [ ] Catat jawaban 3 pertanyaan arahan di tempat
