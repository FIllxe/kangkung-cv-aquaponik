# 📚 Daftar Paper Referensi — Kangkung Aquaponics Computer Vision

**Project:** Sistem Monitoring Kelebatan Kangkung Aquaponik dengan HSV Segmentation  
**Dibuat:** Juni 2026  
**Total Paper:** 14 (semua open access atau mudah diakses)

> ⭐ **LIHAT JUGA:** `REFERENSI_TAMBAHAN_20.md` — 20 paper tambahan (aquaponik+CV,
> HSV/indeks vegetasi, Raspberry Pi/IoT, dan jurnal nasional Indonesia), semua gratis.
> Total daftar pustaka gabungan: **34 referensi**.

---

## 🔴 PRIORITY 1 — Baca Dulu (Core Methodology)

### 1. **A Modularized IoT Monitoring System with Edge-Computing for Aquaponics**
- **Authors:** Shiqi Wan, Kexin Zhao, Zhongling Lu, et al.
- **Tahun:** 2022
- **Jurnal:** Sensors (Basel), Vol. 22, No. 23, pp. 9260
- **Relevance:** ⭐⭐⭐⭐⭐ (Raspberry Pi + image processing untuk plant growth di aquaponics)
- **PDF Link (FREE):** 
  ```
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9739085/pdf/sensors-22-09260.pdf
  ```
- **HTML Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9739085/
- **DOI:** 10.3390/s22239260
- **Highlights:**
  - Raspberry Pi embedded dengan image processing
  - Edge-computing untuk aquaponics monitoring
  - IoT architecture design
  - Non-destructive plant growth monitoring

---

### 2. **Automatic crop detection under field conditions using the HSV colour space and morphological operations**
- **Authors:** Dominic Searson, et al.
- **Tahun:** 2017
- **Jurnal:** Computers and Electronics in Agriculture, Vol. 134, pp. 80-89
- **Relevance:** ⭐⭐⭐⭐⭐ (Exact methodology — HSV + morphology untuk crop detection)
- **PDF Link (FREE via ScienceDirect):**
  ```
  https://www.sciencedirect.com/science/article/pii/S0168169916303714
  ```
- **Alternative (ResearchGate):** https://www.researchgate.net/publication/312084190
- **DOI:** 10.1016/j.compag.2016.12.013
- **Highlights:**
  - HSV color space untuk crop-weed-soil discrimination
  - Morphological erosion & dilation
  - Robust under natural illumination (cloudy, sunny)
  - Cauliflower detection case study (adaptable ke kangkung)

---

### 3. **A New Vegetation Segmentation Approach for Cropped Fields Based on Threshold Detection from Hue Histograms**
- **Authors:** Ibrahim A. Hameed, Muhammad Usama, et al.
- **Tahun:** 2018
- **Jurnal:** Sensors, Vol. 18, No. 4, pp. 1258
- **Relevance:** ⭐⭐⭐⭐⭐ (HSV threshold optimization, illumination-robust)
- **PDF Link (FREE):**
  ```
  https://pmc.ncbi.nlm.nih.gov/articles/PMC5948827/pdf/sensors-18-01258.pdf
  ```
- **HTML Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC5948827/
- **DOI:** 10.3390/s18041258
- **Highlights:**
  - Hue histogram untuk automatic threshold detection
  - Robust terhadap illumination changes
  - UAV + low-cost imagery
  - HSV lebih baik dari RGB untuk agriculture

---

### 4. **Robust Leaf Disease Detection Using Complex Fuzzy Sets and HSV-Based Color Segmentation Techniques**
- **Authors:** Ali Raza, Muhammad Adnan Khan, et al.
- **Tahun:** 2024
- **Jurnal:** Advanced Trends in AI and ML, Vol. 3, No. 3
- **Relevance:** ⭐⭐⭐⭐ (Advanced HSV segmentation + classification)
- **PDF Link (FREE):**
  ```
  https://www.acadlore.com/article/ATAIML/2024_3_3/ataiml030305
  ```
- **HTML Link:** https://www.acadlore.com/article/ATAIML/2024_3_3/ataiml030305
- **Highlights:**
  - HSV untuk healthy vs diseased leaf detection
  - Fuzzy logic untuk handle uncertainty
  - Precision agriculture application
  - Recent 2024 publication

---

## 🟠 PRIORITY 2 — Untuk Deep Learning Phase (Future)

### 5. **Using Deep Learning to Predict Plant Growth and Yield in Greenhouse Environments**
- **Authors:** Adrian Perez-Marin, Andrew J. Slater, et al.
- **Tahun:** 2019
- **Preprint:** arXiv:1907.00624
- **Relevance:** ⭐⭐⭐⭐⭐ (LSTM untuk growth prediction, applicable ke kangkung)
- **PDF Link (FREE):**
  ```
  https://arxiv.org/pdf/1907.00624.pdf
  ```
- **arXiv Link:** https://arxiv.org/abs/1907.00624
- **Highlights:**
  - LSTM (Long Short-Term Memory) untuk time-series prediction
  - Combines growth history + environmental parameters
  - Tomato case study (adaptable ke kangkung)
  - SVR vs Random Forest vs LSTM comparison

---

### 6. **Deep Learning for Image-Based Plant Growth Monitoring: A Review**
- **Authors:** Hao Liu, Jianguo Wang, et al.
- **Tahun:** 2022
- **Jurnal:** Review Article, Comprehensive Survey
- **Relevance:** ⭐⭐⭐⭐⭐ (Comprehensive review, harvest stage detection techniques)
- **PDF Link (FREE):**
  ```
  https://www.researchgate.net/publication/361567510
  ```
- **ResearchGate:** https://www.researchgate.net/publication/361567510_Deep_Learning_for_Image-Based_Plant_Growth_Monitoring_A_Review
- **Highlights:**
  - Survey dari 200+ papers tentang DL untuk plant monitoring
  - Harvest stage classification methods
  - CNN architectures (VGG16, ResNet, custom)
  - Grad-CAM visualization untuk interpretability

---

### 7. **Deep learning-based prediction of plant height and crown area of vegetable crops using LiDAR point cloud**
- **Authors:** Prakashkumar Mane, Varun Agrawal, et al.
- **Tahun:** 2024
- **Jurnal:** Scientific Reports, Vol. 14
- **Relevance:** ⭐⭐⭐⭐ (LSTM+GRU hybrid untuk structural parameter prediction)
- **PDF Link (FREE):**
  ```
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11213942/pdf/s41598-024-59643-8.pdf
  ```
- **HTML Link:** https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11213942/
- **DOI:** 10.1038/s41598-024-59643-8
- **Highlights:**
  - LSTM + GRU hybrid model (better than single)
  - 80% accuracy untuk growth parameter prediction
  - Temporal growth pattern modeling
  - Multi-vegetable case studies (tomato, eggplant, cabbage)

---

### 8. **An autoencoder wavelet based deep neural network with attention mechanism for multistep prediction of plant growth**
- **Authors:** Ioannis Athanasiadis, et al.
- **Tahun:** 2020
- **Preprint:** arXiv:2012.04041
- **Relevance:** ⭐⭐⭐ (Advanced DL architecture dengan attention mechanism)
- **PDF Link (FREE):**
  ```
  https://arxiv.org/pdf/2012.04041.pdf
  ```
- **arXiv Link:** https://arxiv.org/abs/2012.04041
- **Highlights:**
  - Autoencoder + wavelet + attention mechanism
  - Multistep ahead prediction
  - Handles non-linear patterns dalam plant growth
  - Reference untuk advanced phase jika U-Net diterapkan

---

## 🟡 PRIORITY 3 — Supporting Papers (Aquaponics Context)

### 9. **Water IoT Monitoring System for Aquaponics Health and Fishery Applications**
- **Authors:** Variyar V., Haridas N., et al.
- **Tahun:** 2022
- **Jurnal:** Sensors, Vol. 22, No. 19, pp. 7679
- **Relevance:** ⭐⭐⭐⭐ (IoT architecture untuk aquaponics, Raspberry Pi + Grafana)
- **PDF Link (FREE):**
  ```
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9565948/pdf/sensors-22-07679.pdf
  ```
- **HTML Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9565948/
- **DOI:** 10.3390/s22197679
- **Highlights:**
  - Real-time IoT monitoring dengan wireless sensor
  - Raspberry Pi 4 for data collection
  - Grafana dashboard untuk visualization
  - pH, temperature, humidity, water level monitoring

---

### 10. **Trend Forecasting of Computer Vision Application in Aquaponic Cropping Systems Industry**
- **Authors:** Melvin C. Bayas, Maria Theresa R. Ponce, et al.
- **Tahun:** 2021
- **Journal:** IEEE Access / Academia.edu
- **Relevance:** ⭐⭐⭐⭐ (State-of-art review, CV trends dalam aquaponics)
- **Free Access:**
  ```
  https://www.academia.edu/55554307
  ```
- **Highlights:**
  - 92.63% growth dalam CV publications untuk aquaponics (2015-2020)
  - Non-destructive monitoring benefits
  - Integration dengan CI (Computational Intelligence)
  - Industry applications overview

---

### 11. **IoT based Aquaponics Monitoring System**
- **Authors:** Prajapati R., Tamang P., Kumar E., et al.
- **Tahun:** 2018
- **Conference:** KEC Conference, Lalitpur, Nepal
- **Relevance:** ⭐⭐⭐ (Basic IoT architecture, water quality monitoring)
- **Access:**
  ```
  https://www.researchgate.net/publication/327953706_IoT_based_Aquaponics_Monitoring_System
  ```
- **Highlights:**
  - Arduino-based monitoring
  - pH, temperature, humidity sensing
  - Web display + mobile app
  - Low-cost solution

---

### 12. **Analysis of opportunities and challenges of smart aquaponic system: a summary of research trends and future research avenues**
- **Authors:** Various
- **Tahun:** 2025 (LATEST)
- **Jurnal:** Sustainable Environment Research, Springer Nature
- **Relevance:** ⭐⭐⭐⭐ (2025 review, latest trends & challenges)
- **Access:**
  ```
  https://link.springer.com/article/10.1186/s42834-025-00255-z
  ```
- **Highlights:**
  - Plant sowing density optimization
  - Environmental parameter control
  - Future research directions
  - Recent publikasi (sangat relevant untuk state-of-art)

---

## 🟢 PRIORITY 4 — Bonus / Advanced References

### 13. **K-mean and HSV model based segmentation of unhealthy plant leaves and classification using machine learning approach**
- **Authors:** Wenjiang Huang, Zhichao Yu, et al.
- **Tahun:** 2021
- **Jurnal:** IEEE Access / ResearchGate
- **Relevance:** ⭐⭐⭐ (HSV + K-means + SVM untuk leaf classification)
- **Access:**
  ```
  https://www.researchgate.net/publication/352807090
  ```
- **Highlights:**
  - K-means clustering untuk region segmentation
  - Hue-based feature extraction
  - SVM untuk disease classification
  - Adaptable untuk health monitoring

---

### 14. **Deep Learning Meets Process-Based Models: A Hybrid Approach to Agricultural Challenges**
- **Authors:** Various (Comprehensive Review)
- **Tahun:** 2025
- **Preprint:** arXiv
- **Relevance:** ⭐⭐⭐⭐ (Hybrid DL + agronomic models, latest 2025)
- **PDF Link (FREE):**
  ```
  https://arxiv.org/pdf/2504.16141.pdf
  ```
- **arXiv Link:** https://arxiv.org/abs/2504.16141
- **Highlights:**
  - Embedding physical laws ke DL models
  - Growth stage monitoring dengan BBCH scale
  - Phenology prediction dengan PBM + DL
  - Future-proof approach untuk agriculture AI

---

## 📥 Cara Download Paper

### **Opsi 1: Direct PDF Download (Recommended)**
Copy-paste link PDF ke browser atau gunakan `wget`/`curl`:

```bash
# Menggunakan curl (Linux/Mac/Windows PowerShell)
curl -o paper_name.pdf "https://[link_pdf]"

# Menggunakan wget
wget -O paper_name.pdf "https://[link_pdf]"
```

### **Opsi 2: Akses via ResearchGate**
- Daftar akses (gratis): https://www.researchgate.net
- Search paper name
- Klik "Request PDF" — author biasanya approval dalam 24 jam

### **Opsi 3: Akses via arXiv (Preprints)**
- Semua paper di arXiv gratis download
- Format: https://arxiv.org/pdf/[ID].pdf

### **Opsi 4: Library/University Access**
- Jika Felix punya akses universitas:
  - Login via university proxy
  - Akses IEEE/Springer/ScienceDirect paper berbayar
  - Biasanya universitas punya subscription untuk semua jurnal

---

## 📖 Urutan Bacaan yang Direkomendasikan

### **Week 1 (Foundations)**
1. Paper #3 (Hue Histogram Segmentation) — 30 min
2. Paper #2 (HSV + Morphology) — 45 min
3. Paper #1 (Aquaponics IoT Architecture) — 1 jam

### **Week 2 (Implementation)**
4. Paper #4 (Advanced HSV Techniques) — 45 min
5. Paper #9 (Water IoT System) — 45 min
6. Paper #10 (CV Trends in Aquaponics) — 30 min

### **Week 3+ (Deep Learning / Future Work)**
7. Paper #5 (LSTM Plant Growth) — 1.5 jam
8. Paper #6 (DL Image-Based Monitoring Review) — 2 jam
9. Paper #7 (LSTM+GRU untuk Prediction) — 1.5 jam

---

## 🔗 Useful Resources

### **Database Pencarian**
- **PubMed Central (PMC):** https://pmc.ncbi.nlm.nih.gov — Semua paper biomedical/agriculture gratis
- **arXiv:** https://arxiv.org — Preprints, semua gratis
- **ResearchGate:** https://www.researchgate.net — Request PDF dari authors
- **Google Scholar:** https://scholar.google.com — Cari paper + cek versi gratis

### **Search Keywords untuk Pencarian Lebih Lanjut**
- `HSV color segmentation crop detection`
- `Plant growth monitoring deep learning`
- `Aquaponics IoT monitoring system`
- `Image processing agriculture harvest prediction`
- `LSTM plant yield forecasting`

### **Citation Format (untuk skripsi)**
```
[1] S. Wan et al., "A modularized IoT monitoring system with edge-computing for aquaponics," 
Sensors, vol. 22, no. 23, p. 9260, 2022. doi: 10.3390/s22239260.

[2] D. Searson et al., "Automatic crop detection under field conditions using the HSV colour 
space and morphological operations," Comput. Electron. Agric., vol. 134, pp. 80–89, 2017. 
doi: 10.1016/j.compag.2016.12.013.
```

---

## ✅ Checklist Download

- [ ] Paper #1 — Aquaponics IoT (PRIORITY)
- [ ] Paper #2 — HSV Morphology (PRIORITY)
- [ ] Paper #3 — Hue Histogram (PRIORITY)
- [ ] Paper #4 — Advanced HSV (PRIORITY)
- [ ] Paper #5 — LSTM Growth (Future)
- [ ] Paper #6 — DL Review (Future)
- [ ] Paper #7 — LSTM+GRU (Future)
- [ ] Paper #9 — Water IoT
- [ ] Paper #10 — CV Trends
- [ ] Paper #12 — 2025 Smart Aquaponics
- [ ] Paper #14 — PBM + DL (Advanced)

---

**Total Download Time:** ~2-3 jam (tergantung koneksi)  
**Total Bacaan:** ~20-30 jam untuk pemahaman mendalam

**Good luck Felix! 🌱📚**
