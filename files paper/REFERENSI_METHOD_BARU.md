# 📚 Referensi untuk 2 Method Baru — Edge Detection Grid & HSV Adaptif

**Project:** Sistem Computer Vision Deteksi Kesiapan Panen Kangkung Aquaponik
**Dibuat:** September 2026
**Total Paper:** 13 (semua terverifikasi via OpenAlex — judul, tahun, DOI, sitasi valid)
**Catatan:** Melengkapi `DAFTAR_PAPER_REFERENSI.md` (14) + `REFERENSI_TAMBAHAN_20.md` (20).
Total daftar pustaka gabungan: **47 referensi**.

**Pemetaan ke notebook `presentasi_kangkung_cv.ipynb`:**
| Elemen Method | Didukung oleh |
|---|---|
| §4 Canny edge → kontur quad → homografi → grid | Paper A1–A6 |
| §5 HSV adaptif-iluminasi + multi-threshold | Paper B1–B4 (+ B5, B6 existing) |
| §5b EMA smoothing & coverage per zona 4×6 → status panen | Paper C1–C4 |

---

## 🔵 A. CANNY EDGE DETECTION → GRID BED KELAYAKAN PANEN

### A1. **A Computational Approach to Edge Detection** ⭐ FUNDAMENTAL
- **Authors:** John Canny (MIT AI Lab)
- **Tahun:** 1986
- **Jurnal:** IEEE Transactions on Pattern Analysis and Machine Intelligence, Vol. 8, No. 6, pp. 679–698
- **Sitasi:** 29.443 (paper paling fundamental untuk seluruh metode edge proyek ini)
- **Relevance:** ⭐⭐⭐⭐⭐ — dasar teori Canny operator (multi-scale gradient,
  non-maximum suppression, hysteresis threshold) yang dipakai di §4 notebook
- **DOI:** 10.1109/TPAMI.1986.4767851
- **Link:** https://doi.org/10.1109/tpami.1986.4767851

### A2. **Automated robust crop-row detection in maize fields based on position clustering algorithm and shortest path method**
- **Authors:** Xiya Zhang, Xiaona Li, Baohua Zhang, Jun Zhou, Guangzhao Tian, Yingjun Xiong, Baoxing Gu (Nanjing Agricultural University)
- **Tahun:** 2018
- **Jurnal:** Computers and Electronics in Agriculture (Elsevier)
- **Sitasi:** 115
- **Relevance:** ⭐⭐⭐⭐⭐ — deteksi struktur baris/lajur tanam dari citra
  top-down via thresholding + clustering; analogi langsung untuk deteksi
  polygon bed + grid 4×6 pada video handheld
- **DOI:** 10.1016/j.compag.2018.09.014
- **Link:** https://doi.org/10.1016/j.compag.2018.09.014

### A3. **A New Leaf Venation Detection Technique for Plant Species Classification**
- **Tahun:** 2018
- **Jurnal:** Arabian Journal for Science and Engineering (Springer)
- **Sitasi:** 42
- **Relevance:** ⭐⭐⭐⭐ — pipeline Canny + morphology + contour yang identik
  dengan alur `Canny → dilate → findContours → approxPolyDP` di §4
- **DOI:** 10.1007/s13369-018-3504-8

### A4. **Advanced Plant Leaf Classification Through Image Enhancement and Canny Edge Detection**
- **Tahun:** 2018
- **Konferensi:** IEEE ICRITO
- **Sitasi:** 24
- **Relevance:** ⭐⭐⭐⭐ — Gaussian blur → Canny (parameter hysteresis)
  sebagai feature extraction; referensi pemilihan `canny_lo/canny_hi`
- **DOI:** 10.1109/ICRITO.2018.8748587

### A5. **Edge detection algorithm of plant leaf image based on improved Canny**
- **Tahun:** 2021
- **Konferensi:** IEEE ICSP
- **Sitasi:** 9
- **Relevance:** ⭐⭐⭐ — perbaikan Canny untuk citra tanaman (denoising
  sebelum edge); mendukung langkah GaussianBlur(5,5) di implementasi
- **DOI:** 10.1109/ICSP51882.2021.9408929

### A6. **An Effective Algorithm for Edges and Veins Detection in Leaf Images**
- **Tahun:** 2014
- **Konferensi:** IEEE WCCCT
- **Sitasi:** 18
- **Relevance:** ⭐⭐⭐ — dilate/morphological closing untuk menyambung garis
  tepi putus-putus (langkah `cv2.dilate(iterations=2)` di §4)
- **DOI:** 10.1109/WCCCT.2014.1

---

## 🟠 B. SEGMENTASI HSV ADAPTIF (ILUMINASI)

### B1. **Color Indices for Weed Identification Under Various Soil, Residue, and Lighting Conditions** ⭐ FUNDAMENTAL
- **Authors:** D. M. Woebbecke, G. E. Meyer, K. Von Bargen, D. A. Mortensen
- **Tahun:** 1995
- **Publikasi:** Transactions of the ASAE (ASAE Paper No. 93-4017)
- **Sitasi:** 1.543
- **Relevance:** ⭐⭐⭐⭐⭐ — paper fondasi segmentasi tanaman berbasis indeks
  warna yang **diuji lintas kondisi pencahayaan/latar** (persis masalah yang
  diselesaikan faktor adaptif `f = mean(V)/128` di §5)
- **DOI:** 10.13031/2013.27838

### B2. **A Training-Free Leaf Disease Lesion Segmentation Method Using HSV Color and Adaptive Thresholding**
- **Tahun:** 2026
- **Konferensi:** IEEE ICCRAIDS
- **Relevance:** ⭐⭐⭐⭐⭐ — paling dekat dengan method §5: range HSV yang
  **disesuaikan adaptif per-frame tanpa pelatihan ulang**
- **DOI:** 10.1109/ICCRAIDS67816.2026.11519661

### B3. **Illumination-invariant Morphology-aware Dual-branch Segmentation with CNN Feature Fusion for Robust Cotton Weed Classification**
- **Tahun:** 2025
- **Jurnal:** International Journal of Intelligent Engineering and Systems (IJIES)
- **Relevance:** ⭐⭐⭐⭐ — menangani perubahan iluminasi pada segmentasi
  gulma; pembanding robustness HSV adaptif vs CNN
- **DOI:** 10.22266/ijies2025.1231.27
- **Link (open access):** https://ijies.pes.edu/

### B4. **Development of a vision system to evaluate greenhouse crop condition**
- **Tahun:** 2026
- **Relevance:** ⭐⭐⭐⭐ — sistem visi HSV untuk kondisi tanaman greenhouse
  (cahaya berubah-ubah) — konteks deploy sama seperti webcam RPi proyek ini
- **DOI:** 10.53083/1996-4277-2026-256-2-70-78

### B5. 🔁 **(Sudah ada di daftar existing)** Searson et al. 2017 — HSV + morphological operations, robust natural illumination → dasar `mask_tanaman()`.
### B6. 🔁 **(Sudah ada di daftar existing)** Hameed et al. 2018 — threshold adaptif dari Hue histogram → kerabat terdekat faktor adaptif `f`.

---

## 🟢 C. COVERAGE PER ZONA → KESIAPAN PANEN

### C1. **The estimation of crop emergence in potatoes by UAV RGB imagery**
- **Tahun:** 2019
- **Jurnal:** Plant Methods (BMC, open access)
- **Sitasi:** 141
- **Relevance:** ⭐⭐⭐⭐⭐ — estimasi tahap pertumbuhan dari **fractional
  vegetation cover** citra RGB murah; validasi ide coverage % → status panen
- **DOI:** 10.1186/s13007-019-0399-7
- **PDF (FREE):** https://plantmethods.biomedcentral.com/articles/10.1186/s13007-019-0399-7

### C2. **Comparative canopy cover estimation using RGB images from UAV and ground**
- **Tahun:** 2018
- **Publikasi:** Proceedings SPIE
- **Relevance:** ⭐⭐⭐⭐ — perbandingan canopy cover citra RGB ground vs UAV;
  mendukung pendekatan kamera statis RPi (ground-based)
- **DOI:** 10.1117/12.2501531

### C3. **Corn Grain Yield Estimation from Vegetation Indices, Canopy Cover, Plant Density, and a Neural Network Using Multispectral and RGB Images Acquired with Unmanned Aerial Vehicles**
- **Tahun:** 2020
- **Jurnal:** Agriculture (MDPI, open access)
- **Sitasi:** 165
- **Relevance:** ⭐⭐⭐⭐ — korelasi canopy cover (RGB) terhadap hasil panen;
  dasar empiris relasi coverage ↔ yield
- **DOI:** 10.3390/agriculture10070277
- **PDF (FREE):** https://www.mdpi.com/2077-0472/10/7/277/pdf

### C4. **Yield estimation in cotton using UAV-based multi-sensor imagery**
- **Tahun:** 2020
- **Jurnal:** Biosystems Engineering (Elsevier)
- **Sitasi:** 220
- **Relevance:** ⭐⭐⭐⭐ — estimasi yield dari citra; pembanding prediksi
  kesiapan panen berbasis coverage per zona
- **DOI:** 10.1016/j.biosystemseng.2020.02.014

---

## ✅ Ringkasan

- **13 paper baru** (A1–A6, B1–B4, C1–C4) + 2 paper existing dipakai ulang (B5, B6)
- Semua DOI terverifikasi via OpenAlex per September 2026
- 3 paper fundamental bersitasi tinggi: **Canny 1986** (29.443), **Woebbecke 1995** (1.543), **Zhang 2018** (115)
- 4 paper open access full-text gratis: B3, C1, C3 (+ existing: Wan 2022, Hameed 2018, dll.)

## 📖 Contoh Sitasi di Notebook (BibTeX)

```bibtex
@article{canny1986,
  author  = {Canny, John},
  title   = {A Computational Approach to Edge Detection},
  journal = {IEEE Trans. Pattern Anal. Mach. Intell.},
  volume  = {PAMI-8}, number = {6}, pages = {679--698}, year = {1986},
  doi     = {10.1109/TPAMI.1986.4767851}
}
@article{woebbecke1995,
  author  = {Woebbecke, D. M. and Meyer, G. E. and Von Bargen, K. and Mortensen, D. A.},
  title   = {Color Indices for Weed Identification Under Various Soil, Residue, and Lighting Conditions},
  journal = {Transactions of the ASAE},
  year    = {1995}, doi = {10.13031/2013.27838}
}
@article{zhang2018croprow,
  author  = {Zhang, Xiya and Li, Xiaona and Zhang, Baohua and Zhou, Jun and Tian, Guangzhao and Xiong, Yingjun and Gu, Baoxing},
  title   = {Automated robust crop-row detection in maize fields based on position clustering algorithm and shortest path method},
  journal = {Computers and Electronics in Agriculture},
  year    = {2018}, doi = {10.1016/j.compag.2018.09.014}
}
```

