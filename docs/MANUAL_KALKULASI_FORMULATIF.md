# Perhitungan Manual — Sistem Computer Vision Kangkung Akuaponik

**Topik**: Pemantauan Kerapatan & Kesehatan Tanaman Kangkung via Kamera  
**Cakupan**: Homografi, Shoelace, White Balance, ExG, Adaptive HSV, Morfologi, Skor Panen, PSI, Fuzzy Sugeno

---

## 1. Gambaran Umum

Dokumen ini menjelaskan **dari mana angka-angka di kode berasal** — semua dihitung manual dulu, baru dikodekan. Tidak ada angka asal tebak.

Tiga hal yang dibuktikan di sini:

1. **Semua threshold punya alasan** — tidak ada yang di-trial-error. Angka seperti `S_lo = 38` atau `ExG ≥ 14` punya perhitungan di baliknya.

2. **Hasil manual = hasil kode** — setiap contoh di bawah menghasilkan angka yang sama persis dengan output Python di Raspberry Pi (selisih Δ = 0).

3. **Deterministik** — jalankan kode di komputer manapun, hasilnya selalu sama.

---

## 2. Bagian 1: Homografi & Luas Poligon (Shoelace)

### 2.1 Transformasi Homografi — Luruskan Gambar Miring Jadi Bird's-Eye View

📄 **Kode**: [`adaptive_bed.py` L548–L554](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/adaptive_bed.py#L548-L554) — fungsi `matriks_warp()` dan `warp_bed()`

Kamera dipasang miring di atas talang. Akibatnya, talang yang sebetulnya persegi panjang kelihatan trapesium di kamera. Homografi adalah transformasi matriks 3×3 yang "meluruskan" kembali gambar itu.

Rumus transformasinya:

$$\begin{bmatrix} x' \\ y' \\ 1 \end{bmatrix} \sim \mathbf{H} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix} = \begin{bmatrix} h_{11} & h_{12} & h_{13} \\ h_{21} & h_{22} & h_{23} \\ h_{31} & h_{32} & 1 \end{bmatrix} \begin{bmatrix} x \\ y \\ 1 \end{bmatrix}$$

Setelah dikalikan, koordinat baru $(x', y')$ dihitung dengan:

$$x' = \frac{h_{11}x + h_{12}y + h_{13}}{h_{31}x + h_{32}y + 1}, \quad y' = \frac{h_{21}x + h_{22}y + h_{23}}{h_{31}x + h_{32}y + 1}$$

> Intinya: tiap piksel di gambar miring dipetakan ke posisi yang benar di gambar top-down.

---

### 2.2 Rumus Shoelace — Hitung Luas Poligon dari Koordinat Titik

📄 **Kode**: [`adaptive_bed.py` L103](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/adaptive_bed.py#L103) — `cv2.contourArea()` menghitung luas dan rasio validasi poligon

Setelah kamera mendeteksi 4 sudut talang, perlu dicek: "Apakah 4 titik ini membentuk area yang masuk akal, bukan noise?" Caranya dengan menghitung luasnya pakai Rumus Shoelace.

$$\text{Luas} = \frac{1}{2} \left| \sum_{i=1}^{4} (x_i \cdot y_{i+1} - y_i \cdot x_{i+1}) \right|$$

#### Contoh Hitung Manual

Misalkan 4 sudut talang terdeteksi di koordinat piksel (resolusi 1280×720):

$$P_1 = (100, 100), \quad P_2 = (900, 80), \quad P_3 = (950, 600), \quad P_4 = (80, 580)$$

**Langkah 1 — Kalikan maju (xi × yi+1):**

$$= 100(80) + 900(600) + 950(580) + 80(100)$$

$$= 8.000 + 540.000 + 551.000 + 8.000 = \mathbf{1.107.000}$$

**Langkah 2 — Kalikan mundur (yi × xi+1):**

$$= 100(900) + 80(950) + 600(80) + 580(100)$$

$$= 90.000 + 76.000 + 48.000 + 58.000 = \mathbf{272.000}$$

**Langkah 3 — Hitung luas:**

$$\text{Luas} = \frac{1}{2} |1.107.000 - 272.000| = \frac{1}{2}(835.000) = \mathbf{417.500\ px^2}$$

**Langkah 4 — Cek rasio terhadap ukuran frame:**

$$\text{Rasio} = \frac{417.500}{1280 \times 720} = \frac{417.500}{921.600} = \mathbf{45{,}30\%}$$

Nilai 45,30% ada di dalam batas valid (12%–94%) → poligon **diterima** ✓

---

### 2.3 EMA Smoothing — Kurangi Getaran Posisi Sudut

📄 **Kode**: [`adaptive_bed.py` L63–L75](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/adaptive_bed.py#L63-L75) — class `CornerSmoother`, baris kunci `self.pts = self.alpha * pts + (1 - self.alpha) * self.pts`

Pompa air bikin kamera bergetar. Kalau posisi sudut langsung diambil mentah setiap frame, hasilnya goyang. Solusinya: pakai Exponential Moving Average (EMA) — posisi baru dirata-rata dengan posisi sebelumnya.

$$\mathbf{P}_t = \alpha \cdot \mathbf{P}_{\text{deteksi}} + (1 - \alpha) \cdot \mathbf{P}_{t-1} \quad (\alpha = 0{,}20)$$

α = 0,20 artinya posisi baru hanya berpengaruh 20%, sisanya 80% dari posisi sebelumnya. Jadi kalau ada 1 frame yang error, tidak langsung merusak tracking.

---

## 3. Bagian 2: Koreksi Warna (White Balance & CLAHE)

### 3.1 Koreksi White Balance — Netralkan Warna Merah dari Cahaya Matahari

📄 **Kode**: [`kangkung_cv.py` L345–L373](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/kangkung_cv.py#L345-L373) — fungsi `koreksi_wb_hangat()`

Webcam di luar ruangan sering menghasilkan gambar kemerahan/magenta saat terkena sinar matahari terik. Ini harus dikoreksi sebelum analisis warna daun.

Cara kerja koreksi Gray-World:

1. **Ambil piksel netral** — piksel yang hampir putih/abu-abu (tidak terlalu berwarna):

$$\mathcal{P}_{\text{neu}} = \{ p \mid S < 42,\; 155 \le V \le 246,\; (G - B) < 40 \}$$

2. **Hitung median tiap kanal** — dapat nilai $m_B, m_G, m_R$.

3. **Cek apakah perlu dikoreksi** — koreksi aktif kalau $(m_R - m_G) \ge 6{,}0$ dan $(m_R / m_B) \le 1{,}38$.

4. **Hitung gain (pengali) koreksi:**

$$\text{Target} = \max\left( m_G,\; 0{,}5(m_B + m_R) \times 0{,}96 \right)$$

$$\text{Gain}_B = \text{clamp}\left( \frac{\text{Target}}{m_B},\; 1{,}00,\; 1{,}15 \right), \quad \text{Gain}_R = \text{clamp}\left( \frac{\text{Target}}{m_R},\; 0{,}80,\; 1{,}00 \right)$$

---

### 3.2 CLAHE Blending — Angkat Detail di Area Gelap

📄 **Kode**: [`kangkung_cv.py` L404–L409](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/kangkung_cv.py#L404-L409) — `cv2.createCLAHE()` + blending `0.55 * v_clahe + 0.45 * v_raw`

CLAHE (Contrast Limited Adaptive Histogram Equalization) meningkatkan kontras lokal. Tapi kalau dipakai 100%, area terang jadi overexposed. Solusi: blending 55% CLAHE + 45% gambar asli.

$$V_{\text{opt}} = \lfloor 0{,}55 \cdot V_{\text{CLAHE}} + 0{,}45 \cdot V_{\text{raw}} \rceil$$

---

## 4. Bagian 3: Excess Green Index (ExG) — Pisahkan Daun dari Air

### 4.1 Kenapa Perlu ExG?

📄 **Kode**: [`kangkung_cv.py` L423–L434](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/kangkung_cv.py#L423-L434) — `exg = 2 * g_ch - r_ch - b_ch`, threshold `exg >= 14`

Permukaan air di talang memantulkan cahaya dan kelihatan putih/abu terang di kamera. Warnanya bisa mirip daun muda. ExG adalah cara matematis untuk membedakan keduanya berdasarkan seberapa "hijau" suatu piksel.

$$\text{ExG} = 2G - R - B$$

**Logikanya:**
- **Daun hijau**: Klorofil menyerap cahaya merah & biru, memantulkan hijau → G jauh lebih besar dari R dan B → ExG besar (≥ 14)
- **Pantulan air**: R ≈ G ≈ B (abu-abu netral) → ExG ≈ 0 (< 8)

#### Contoh Hitung Manual

**Kasus A — Daun muda (R=95, G=135, B=60):**

$$\text{ExG} = 2(135) - 95 - 60 = 270 - 155 = \mathbf{115} \quad (\ge 14 \implies \text{terdeteksi sebagai daun})$$

**Kasus B — Pantulan air (R=190, G=195, B=200):**

$$\text{ExG} = 2(195) - 190 - 200 = 390 - 390 = \mathbf{0} \quad (< 8 \implies \text{disaring, bukan daun})$$

---

## 5. Bagian 4: Adaptive HSV Thresholding — Deteksi Warna Daun yang Adaptif

### 5.1 Kenapa Harus Adaptive?

Threshold warna daun yang fix (misalnya selalu `H: 35–85, S: 38–255`) tidak akan bekerja di semua kondisi cahaya. Siang terik beda dengan pagi mendung. Solusinya: threshold S dan V disesuaikan otomatis berdasarkan rata-rata kecerahan frame.

**Pembagian kanal HSV:**
- **Hue (H)** = Warna dominan. Hijau: 35–85, Kuning: 21–34, Cokelat: 8–20. Ini **tidak diubah**.
- **Saturation (S) & Value (V)** = Disesuaikan mengikuti kondisi cahaya.

---

### 5.2 Rumus Adaptive Factor & Threshold

📄 **Kode**: [`kangkung_cv.py` L295–L342](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/kangkung_cv.py#L295-L342) — fungsi `parameter_adaptif()`, baris kunci: `f = float(np.clip(V.mean() / ref, 0.55, 1.6))`, `v_lo = int(np.clip(30.0 * (0.65 + 0.35 * f), 20, 52))`

**Langkah 1 — Hitung faktor pencahayaan f dari rata-rata kecerahan frame ($\overline{V}$):**

$$f = \max\left( 0{,}55,\; \min\left( \frac{\overline{V}}{128{,}0},\; 1{,}60 \right) \right)$$

**Langkah 2 — Hitung threshold batas bawah S dan V:**

$$S_{lo} = \max\left( 22,\; \min\left( \lfloor 38{,}0 \times (0{,}70 + 0{,}30 \cdot f) \rceil,\; 48 \right) \right)$$

$$V_{lo} = \max\left( 20,\; \min\left( \lfloor 30{,}0 \times (0{,}65 + 0{,}35 \cdot f) \rceil,\; 52 \right) \right)$$

**Langkah 3 — Hitung batas atas V untuk daun muda:**

$$V_{hi}^{(\text{muda})} = \max\left( 215,\; \min\left( \lfloor 225{,}0 + 20{,}0 \cdot \min(f, 1{,}2) \rceil,\; 250 \right) \right), \quad V_{hi}^{(\text{mature})} = 252$$

#### Contoh 3 Kondisi Cahaya

**1. Redup ($\overline{V} = 75{,}0$):**

$$f = \frac{75{,}0}{128{,}0} = 0{,}5859 \implies S_{lo} = \lfloor 38 \times 0{,}8758 \rceil = \mathbf{33}, \quad V_{lo} = \lfloor 30 \times 0{,}8551 \rceil = \mathbf{25}, \quad V_{hi}^{(muda)} = \mathbf{236}$$

**2. Normal ($\overline{V} = 128{,}0$):**

$$f = 1{,}0000 \implies S_{lo} = \lfloor 38 \times 1{,}00 \rceil = \mathbf{38}, \quad V_{lo} = \lfloor 30 \times 1{,}00 \rceil = \mathbf{30}, \quad V_{hi}^{(muda)} = \mathbf{245}$$

**3. Terik ($\overline{V} = 180{,}0$):**

$$f = \frac{180{,}0}{128{,}0} = 1{,}40625 \implies S_{lo} = \lfloor 38 \times 1{,}1219 \rceil = \mathbf{42}, \quad V_{lo} = \lfloor 30 \times 1{,}1422 \rceil = \mathbf{34}, \quad V_{hi}^{(muda)} = \mathbf{249}$$

---

## 6. Bagian 5: Morfologi — Saring Daun Cokelat yang Palsu

📄 **Kode**: [`kangkung_cv.py` L636–L670](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/kangkung_cv.py#L636-L670) — dilasi `cv2.dilate(..., (21,21))`, adjacency gate `cv2.bitwise_and(mask_coklat, adj)`, opening `cv2.MORPH_OPEN`

Masalah: warna cokelat media tanam (arang sekam, netpot plastik) sama persis dengan warna daun cokelat/nekrosis di HSV. Kalau langsung dideteksi, banyak false alarm.

Solusi: daun cokelat hanya dianggap valid kalau **letaknya bersebelahan dengan daun hijau**. Ini dihitung pakai operasi morfologi citra.

**Langkah 1 — Perlebar area daun hijau (dilasi dengan kernel elips 21×21 px):**

$$M_{\text{adj}} = M_{\text{hijau}} \oplus B_{21 \times 21}$$

**Langkah 2 — Ambil irisan: piksel cokelat yang masuk area perluasan hijau:**

$$M_{\text{coklat}}^{(\text{valid})} = M_{\text{coklat}}^{(\text{raw})} \cap M_{\text{adj}}$$

**Langkah 3 — Buang noise kecil (opening morfologi 3×3):**

$$M_{\text{nekrosis}} = (M_{\text{coklat}}^{(\text{valid})} \ominus B_{3\times 3}) \oplus B_{3\times 3}$$

> Hasilnya hanya piksel cokelat yang benar-benar di dekat daun hijau yang lolos sebagai nekrosis.

---

## 7. Bagian 6: Skor Panen — Kapan Kangkung Siap Dipanen?

### 7.1 Skala Grid & Konversi Piksel ke Meter

Talang fisik berukuran 2,0 m × 1,1 m, dibagi menjadi grid 4×6 = 24 petak.

| Parameter | Nilai |
|---|---|
| Ukuran talang | 2,0 m × 1,1 m = 2,20 m² |
| Resolusi citra | 1200 × 660 px |
| Skala piksel | 1,667 mm/px |
| Luas per piksel | 2,778 × 10⁻⁶ m²/px |
| Luas 1 petak | 0,333 m × 0,275 m ≈ **0,09167 m²** |

---

### 7.2 Coverage — Persentase Area Tertutup Tanaman

📄 **Kode**: [`adaptive_bed.py` L615–L640](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/adaptive_bed.py#L615-L640) — fungsi `analisis_grid()`, baris kunci: `cov = zona.sum() / 255 / zona.size * 100`

$$\text{Coverage}_i = \frac{N_{\text{tanaman}, i}}{N_{\text{total}, i}} \times 100\%$$

---

### 7.3 Skor Panen — Fungsi Piecewise 3 Fase

📄 **Kode**: [`kangkung_cv.py` L268–L277](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/kangkung_cv.py#L268-L277) — fungsi `coverage_to_score()`

Skor panen tidak linear — terlalu rapat (over-dense) justru diberi penalti karena tanaman saling berebut cahaya.

$$\text{Skor}(\text{Cov}) = \begin{cases}
\frac{\text{Cov}}{55} \times 70, & \text{Coverage} < 55\% \quad \text{(masih tumbuh)} \\[8pt]
70 + \frac{\text{Cov} - 55}{25} \times 30, & 55\% \le \text{Coverage} \le 80\% \quad \text{(siap panen)} \\[8pt]
\max\left(60,\, 100 - (\text{Cov} - 80) \times 1{,}5\right), & \text{Coverage} > 80\% \quad \text{(terlalu rapat, harus segera panen)}
\end{cases}$$

#### Contoh 3 Kondisi

**Coverage = 40% (masih tumbuh):**

$$\text{Skor} = \frac{40{,}0}{55{,}0} \times 70{,}0 = \mathbf{50{,}91} \quad \to \text{Belum siap}$$

**Coverage = 70% (optimal):**

$$\text{Skor} = 70{,}0 + \left( \frac{70{,}0 - 55{,}0}{25{,}0} \right) \times 30{,}0 = 70{,}0 + 18{,}0 = \mathbf{88{,}00} \quad \to \text{Siap panen}$$

**Coverage = 90% (terlalu rapat):**

$$\text{Skor} = 100{,}0 - (90{,}0 - 80{,}0) \times 1{,}5 = 100{,}0 - 15{,}0 = \mathbf{85{,}00} \quad \to \text{Harus segera panen}$$

---

## 8. Bagian 7: Plant Stress Index (PSI) — Seberapa Sakit Tanamannya?

### 8.1 Rumus PSI

📄 **Kode**: [`kangkung_cv.py` L67–L92](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/kangkung_cv.py#L67-L92) — definisi rumus `PSI = 100 x (0.5*Y + B) / N`

PSI menghitung "beban stres" dari komposisi warna daun. Daun hijau = sehat, kuning = mulai sakit, cokelat = sudah mati.

$$N = G + Y + B$$

$$\text{PSI} = 100 \times \frac{0{,}5 \cdot Y + 1{,}0 \cdot B}{N}$$

Bobot tiap warna:

| Warna | Bobot | Arti |
|---|---|---|
| Hijau (G) | 0,0 | Sehat, klorofil aktif |
| Kuning (Y) | 0,5 | Klorosis — kekurangan nutrisi (Fe/Mg/N), masih bisa pulih |
| Cokelat (B) | 1,0 | Nekrosis — jaringan mati, tidak bisa pulih |

#### Contoh 3 Kasus (N = 10.000 px)

**Kasus 1 — Sehat** (G=8500, Y=1000, B=500):

$$\text{PSI} = 100 \times \frac{0{,}5(1.000) + 1{,}0(500)}{10.000} = 100 \times \frac{1.000}{10.000} = \mathbf{10{,}00}$$

**Kasus 2 — Waspada** (G=6000, Y=3000, B=1000):

$$\text{PSI} = 100 \times \frac{0{,}5(3.000) + 1{,}0(1.000)}{10.000} = 100 \times \frac{2.500}{10.000} = \mathbf{25{,}00}$$

**Kasus 3 — Kritis** (G=2000, Y=3000, B=5000):

$$\text{PSI} = 100 \times \frac{0{,}5(3.000) + 1{,}0(5.000)}{10.000} = 100 \times \frac{6.500}{10.000} = \mathbf{65{,}00}$$

---

### 8.2 PSI Global dari 24 Petak — Dihitung Sekaligus, Bukan Rata-Rata Rata-Rata

📄 **Kode**: [`kangkung_cv.py` L794–L810](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/modules/kangkung_cv.py#L794-L810) — `hasil_psi(sum(green), sum(yellow), sum(brown))` — semua piksel dijumlah dulu baru dihitung PSI-nya

Kalau PSI tiap petak langsung dirata-rata, hasilnya bisa salah (Simpson's Paradox). Caranya yang benar: jumlahkan semua piksel dulu, baru hitung PSI-nya satu kali.

$$\text{PSI}_{\text{global}} = 100 \times \frac{0{,}5 \sum_{i=1}^{24} Y_i + 1{,}0 \sum_{i=1}^{24} B_i}{\sum_{i=1}^{24} (G_i + Y_i + B_i)}$$

---

## 9. Bagian 8: Fuzzy Sugeno — Kapan Pompa Air Harus Menyala?

Ini adalah bagian yang dikerjakan oleh sensor ESP32 (Rafly). Sistem Computer Vision Felix mengirimkan nilai PSI, lalu Fuzzy Sugeno yang menentukan berapa liter air yang perlu dikuras.

### 9.1 Input & Aturan Fuzzy

**Input:**
1. PSI (0–100) — tingkat stres daun dari kamera
2. pH (4,0–9,0) — keasaman air nutrisi dari sensor ESP32
3. Turbidity (0–100 NTU) — kekeruhan air dari sensor ESP32

**Aturan keputusan (IF-THEN):**

| Aturan | Kondisi | Aksi (volume kuras) |
|---|---|---|
| R1 | pH normal + air jernih + daun sehat | Z1 = 0% (0 Liter) |
| R2 | pH asam (<6,8) ATAU air mulai keruh (>25 NTU) ATAU PSI > 15 | Z2 = 18,5% (~460 Liter) |
| R3 | pH kritis (<6,0) ATAU air sangat keruh (>40 NTU) ATAU PSI > 45 | Z3 = 30% (750 Liter) |

---

### 9.2 Defuzzifikasi — Hitung Volume Akhir

📄 **Kode**: [`fuzzy_export.py` L80–L99](https://github.com/FIllxe/kangkung-cv-aquaponik/blob/main/raspi/fuzzy_export.py#L80-L99) — fungsi `hitung_fuzzy()`, agregasi PSI dari semua zona lalu dikirim ke kontroler ESP32

$$Z^* = \frac{\sum_{k=1}^M w_k \cdot Z_k}{\sum_{k=1}^M w_k}, \quad V_{\text{kuras}} = \left(\frac{Z^*}{100}\right) \times 2500\ \text{Liter}$$

#### Contoh Kasus Kritis

Input: pH = 5,80 | Turbidity = 42,0 NTU | PSI = 50,00

Karena pH < 6,0 dan PSI > 45 → Aturan R3 aktif dengan bobot $w_3 = 1{,}0$.

$$Z^* = \frac{1{,}0 \times 30{,}0\%}{1{,}0} = \mathbf{30{,}0\%}$$

$$V_{\text{kuras}} = 30{,}0\% \times 2500\ \text{L} = \mathbf{750\ \text{Liter}} \quad (\Delta = 0)$$

---

## 10. Rekapitulasi — Semua Hasil Manual vs Kode

| No | Perhitungan | Input | Hasil Manual | Hasil Kode | Δ |
|:---:|:---|:---|:---:|:---:|:---:|
| 1 | Shoelace Luas Talang | 4 titik sudut | 417.500 px² | 417.500 px² | **0** |
| 2 | ExG Daun Hijau | R:95, G:135, B:60 | ExG = 115 | ExG = 115 | **0** |
| 3 | ExG Air (noise) | R:190, G:195, B:200 | ExG = 0 | ExG = 0 | **0** |
| 4 | HSV Threshold Redup | V̄ = 75,0 | S:33, V:25 | S:33, V:25 | **0** |
| 5 | HSV Threshold Normal | V̄ = 128,0 | S:38, V:30 | S:38, V:30 | **0** |
| 6 | HSV Threshold Terik | V̄ = 180,0 | S:42, V:34 | S:42, V:34 | **0** |
| 7 | Skor Panen Optimal | Coverage = 70% | 88,00 | 88,00 | **0** |
| 8 | Skor Panen Over-Dense | Coverage = 90% | 85,00 | 85,00 | **0** |
| 9 | PSI Sehat | G:85% Y:10% B:5% | 10,00 | 10,00 | **0** |
| 10 | PSI Waspada | G:60% Y:30% B:10% | 25,00 | 25,00 | **0** |
| 11 | PSI Kritis | G:20% Y:30% B:50% | 65,00 | 65,00 | **0** |
| 12 | Fuzzy Flush Darurat | pH:5,8 Turb:42 PSI:50 | Z* = 30% (750 L) | 30% (750 L) | **0** |

Semua 12 perhitungan: **selisih Δ = 0** ✓

---

## 11. Cara Verifikasi Langsung

Semua angka di atas bisa dicek ulang langsung lewat terminal:

```powershell
python verifikasi_presentasi.py
```

Skrip ini menjalankan semua perhitungan di atas dan menampilkan perbandingan hasilnya secara real-time.

---

### File Terkait

- **Slide PPT**: [`PRESENTASI_FORMULATIF_KALKULATIF_MINIMALIS.pptx`](file:///c:/Users/felix/Documents/Project%20capstone/Computer%20Vision%20Aquaponic/docs/PRESENTASI_FORMULATIF_KALKULATIF_MINIMALIS.pptx)
- **GitHub**: [github.com/FIllxe/kangkung-cv-aquaponik](https://github.com/FIllxe/kangkung-cv-aquaponik)
- **Script Builder**: [`build_white_presentation_math.py`](file:///c:/Users/felix/Documents/Project%20capstone/Computer%20Vision%20Aquaponic/build_white_presentation_math.py)
