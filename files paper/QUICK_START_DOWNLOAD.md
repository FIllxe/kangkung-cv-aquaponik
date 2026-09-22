# 🚀 Quick Start — Cara Download Paper Referensi

## Option A: Otomatis (Python Script)

### **Requirement:**
```bash
pip install requests --break-system-packages
```

### **Jalankan:**
```bash
# Lihat semua paper
python3 download_papers.py --list

# Download hanya PRIORITY 1 (recommended)
python3 download_papers.py --download-priority 1

# Download SEMUA paper (takes ~1-2 hours)
python3 download_papers.py --download

# Buka folder result
python3 download_papers.py --open
```

---

## Option B: Manual (Copy-Paste Links)

### **PRIORITY 1 Papers (Download Dulu):**

#### 1️⃣ Aquaponics IoT System
**Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9739085/pdf/sensors-22-09260.pdf
**Cara:** Langsung klik link → PDF download otomatis
**Size:** ~2.5 MB

#### 2️⃣ HSV + Morphology Crop Detection  
**Link:** https://www.sciencedirect.com/science/article/pii/S0168169916303714
**Cara:** 
- Buka link
- Jika ada login popup → buka via ResearchGate (bawah): https://www.researchgate.net/publication/312084190
- Klik "Request PDF" atau "Full-text available"

#### 3️⃣ Vegetation Segmentation (Hue Histogram)
**Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC5948827/pdf/sensors-18-01258.pdf
**Cara:** Langsung klik → PDF download
**Size:** ~1.8 MB

#### 4️⃣ Advanced HSV (Leaf Disease Detection)
**Link:** https://www.acadlore.com/article/ATAIML/2024_3_3/ataiml030305
**Cara:** Buka link → scroll down → ada PDF button, atau copy artikel ke offline

---

### **PRIORITY 2 Papers (Deep Learning - Untuk Fase U-Net):**

#### 5️⃣ LSTM Plant Growth Prediction
**Link:** https://arxiv.org/pdf/1907.00624.pdf
**Cara:** Langsung download PDF
**Size:** ~1.2 MB

#### 6️⃣ Deep Learning Review (Comprehensive)
**Link:** https://www.researchgate.net/publication/361567510_Deep_Learning_for_Image-Based_Plant_Growth_Monitoring_A_Review
**Cara:** 
- Buka link ResearchGate
- Klik "Request full-text"
- Author akan approve (biasanya <24 jam)

#### 7️⃣ LSTM + GRU untuk Plant Height Prediction
**Link:** https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11213942/pdf/s41598-024-59643-8.pdf
**Cara:** Langsung download PDF
**Size:** ~2.1 MB

#### 8️⃣ Autoencoder + Attention (Advanced)
**Link:** https://arxiv.org/pdf/2012.04041.pdf
**Cara:** Langsung download PDF
**Size:** ~0.9 MB

---

### **PRIORITY 3 & 4 (Supporting):**

#### 9️⃣ Water IoT Monitoring
**Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9565948/pdf/sensors-22-07679.pdf
**Cara:** Langsung download
**Size:** ~2.2 MB

#### 🔟 CV Trends in Aquaponics
**Link:** https://www.academia.edu/55554307
**Cara:** Daftar di Academia.edu → Search paper → Download gratis

#### 1️⃣1️⃣ 2025 Smart Aquaponics Review
**Link:** https://link.springer.com/article/10.1186/s42834-025-00255-z
**Cara:** 
- Buka link
- Jika tidak bisa (paywalled) → coba universitas library proxy
- Atau search Google Scholar + click "Free PDF" link

#### 1️⃣2️⃣ PBM + Deep Learning (Latest)
**Link:** https://arxiv.org/pdf/2504.16141.pdf
**Cara:** Langsung download
**Size:** ~1.5 MB

---

## Option C: Pakai Universitas Library

Jika Felix adalah mahasiswa UNNES:

### **Steps:**
1. Buka website perpustakaan UNNES
2. Login dengan credentials mahasiswa
3. Cari paper via search bar
4. Most papers (IEEE, Springer, ScienceDirect) available gratis via university proxy

### **Universitas UNNES Library:**
- Website: https://lib.unnes.ac.id
- Database: IEEE, Springer, Wiley, ScienceDirect (usually available)

---

## Option D: Pakai ResearchGate

Paling reliable untuk papers academic yang tidak tersedia gratis:

### **Steps:**
1. Daftar gratis: https://www.researchgate.net/signup
2. Search paper by title/DOI
3. Klik "Request full-text" → author dapat notifikasi
4. Author approve (usually <24 jam)

### **Tips:**
- Follow authors untuk notification cepat
- Banyak author yang balas dalam hitungan jam
- Alternatif: cari contact author di paper, email langsung request

---

## Option E: Google Scholar Trick

### **Cara:**
1. Google Scholar: https://scholar.google.com
2. Search: `"[paper title]" filetype:pdf`
3. Cari link "Free PDF" atau `[pdf]` di hasil search
4. Sering ada hosted di repository author/universitas

---

## 📊 Summary — Mana yang Harus Download Duluan?

### **Minimum (Absolutely Essential):**
- ✅ Paper #1 (Aquaponics IoT)
- ✅ Paper #3 (Hue Histogram)
- ✅ Paper #4 (HSV Advanced)

**Time:** 30 minutes  
**Result:** Sudah bisa mulai implementasi HSV segmentation

### **Recommended (Foundation + Theory):**
- ✅ Paper #1, #3, #4 (above)
- ✅ Paper #2 (HSV Morphology) — CRITICAL untuk metodologi
- ✅ Paper #9 (Water IoT) — untuk architecture

**Time:** 1-2 hours  
**Result:** Complete understanding untuk current phase (HSV-based)

### **Full Package (Research-Grade):**
- ✅ Paper #1-9 (semua di atas)
- ✅ Paper #5, #6, #7 (Deep Learning)
- ✅ Paper #10, #12, #14 (State-of-art)

**Time:** 4-6 hours (reading) + 2 hours (download)  
**Result:** Production-grade knowledge untuk publication

---

## ❓ Troubleshooting

### **Problem: Link error 403 / Access Denied**
**Solution:** 
- Coba via universitas library proxy
- Coba ResearchGate request
- Coba email author langsung

### **Problem: PDF corrupt atau tidak terbuka**
**Solution:**
- Download ulang (mungkin gagal)
- Coba buka via web viewer dulu sebelum save lokal
- Chrome bisa langsung view PDF tanpa download

### **Problem: Download timeout / Terlalu lambat**
**Solution:**
- Gunakan `wget` atau `curl` dengan resume:
  ```bash
  wget -c "https://[pdf-link]"  # -c = resume jika terputus
  ```

### **Problem: Tidak punya akses universitas**
**Solution:**
- ResearchGate request (paling reliable)
- Email author langsung + explain project
- Coba alternatiw free version (preprint via arXiv)

---

## 💾 Recommended Folder Structure

Setelah download, organize begini:

```
kangkung_project/
├── papers/
│   ├── [PRIORITY 1]/
│   │   ├── 01_Aquaponics_IoT_EdgeComputing_Wan2022.pdf
│   │   ├── 02_HSV_CropDetection_Morphology_Searson2017.pdf
│   │   ├── 03_VegetationSegmentation_HueHistogram_Hameed2018.pdf
│   │   └── 04_HSV_LeafDisease_Detection_Raza2024.pdf
│   │
│   ├── [PRIORITY 2 - Deep Learning]/
│   │   ├── 05_DeepLearning_PlantGrowth_LSTM_Perez2019.pdf
│   │   ├── 06_DL_PlantMonitoring_Review_Liu2022.pdf
│   │   ├── 07_LSTM_PlantHeight_CrownArea_Mane2024.pdf
│   │   └── 08_Autoencoder_Attention_PlantGrowth_Athanasiadis2020.pdf
│   │
│   └── [PRIORITY 3 - Supporting]/
│       ├── 09_WaterIoT_Aquaponics_Variyar2022.pdf
│       ├── 10_CVTrends_Aquaponics_Bayas2021.pdf
│       └── 12_SmartAquaponics_Analysis_2025.pdf
│
├── images/                  (input photos)
├── output/                  (segmentation results)
├── batch_segmentasi.py
└── README.md
```

---

## 📚 Reading Notes Template

Untuk setiap paper, catat:

```markdown
## Paper: [Title]
- **Authors:** 
- **Year:** 
- **Key Method:** 
- **Relevant for:** 
- **Main Findings:** 
- **Code/Implementation:** 
- **References to Follow:** 
```

Contoh:
```markdown
## Paper: Automatic crop detection using HSV colour space
- **Authors:** Dominic Searson, et al.
- **Year:** 2017
- **Key Method:** HSV color space + morphological erosion/dilation
- **Relevant for:** Main segmentation methodology
- **Main Findings:** 
  - HSV robust under natural illumination (cloudy, sunny, shadow)
  - Morphological operations improve connectivity
  - Better than RGB for agriculture
- **Code/Implementation:** Can adapt their threshold ranges for kangkung
- **References to Follow:** Woebbecke et al. (color indices), Kataoka et al. (crop detection)
```

---

## ✅ Final Checklist

- [ ] Download PRIORITY 1 papers (4 papers)
- [ ] Create folder structure
- [ ] Baca Paper #1 (IoT architecture)
- [ ] Baca Paper #3 (HSV method)
- [ ] Baca Paper #4 (Advanced HSV)
- [ ] Take notes untuk setiap paper
- [ ] Identify 2-3 key papers untuk sitasi di skripsi
- [ ] Save bibliography di Mendeley/Zotero

---

**Questions?** Check DAFTAR_PAPER_REFERENSI.md untuk info lengkap.

Good luck! 📖🌱
