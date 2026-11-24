# 🌿 SISTEM COMPUTER VISION DETEKSI KESIAPAN PANEN KANGKUNG AQUAPONIK

> Bed Aquaponik 2 m × 1,1 m • Grid 4×6 (24 Zona) • Segmentasi HSV Adaptif • PSI 0–100  
> Raspberry Pi 4B + Kamera CSI IR 5MP • Firebase Dashboard • Enclosure 3D-Print PETG

---

## 📌 MASALAH
Petani sulit menilai masa panen & kesehatan daun **per zona** secara konsisten.  
Bed tidak seragam (tepi vs tengah berbeda), cahaya berubah tiap hari, dan penilaian mata subjektif.

---

## 🎯 SOLUSI
Sistem sensor tanaman otomatis berbasis **Computer Vision** yang memotret bed setiap 10 menit, membagi jadi 24 zona, dan memberi peta kesiapan panen + kesehatan daun secara real-time ke dashboard.

---

## ⚙️ METODE (PIPELINE CV)

| Tahap | Teknik | Fungsi |
|-------|--------|--------|
| 1 | Canny Edge + Homografi | Deteksi otomatis tepi bed & warp perspektif |
| 2 | Grid 4×6 | Pembagian bed jadi 24 zona pemrosesan |
| 3 | HSV Adaptif (`f = mean(V)/128`) | Stabilisasi coverage lintas kondisi cahaya (±38%) |
| 4 | Segmentasi Warna | Hijau = tanaman, Kuning = klorosis, Coklat = nekrosis |
| 5 | EMA α = 0,2 | Stabilisasi temporal (jitter turun −53%) |
| 6 | PSI = 100×(0,5·Y + B)/N | Indeks stres tanaman sebagai input kontroler fuzzy |

---

## 🛠️ HARDWARE

| Komponen | Spesifikasi |
|----------|-------------|
| Komputer | Raspberry Pi 4B (2 GB), Debian 13, Python 3.13 |
| Kamera | CSI IR 5MP (ov5647) via libcamera/Picamera2 |
| Enclosure | PETG 3D-Print, IP65, sun shield, cable gland, silica gel |
| Mounting | Lengan miring, top-down ~2,5 m di atas bed |
| Daya | Adaptor 5 V / 3 A, microSD high-endurance 16 GB |
| Jaringan | WiFi + Tailscale (remote tanpa buka port) |

---

## 📊 ARSITEKTUR SISTEM

```
Kamera CSI → CV (OpenCV) → Grid 4×6 → PSI → JSON (2–3 KB)
      ↓                              ↓
Firebase Firestore ←─────────────── Web Dashboard (heatmap 4×6 + grafik 24 jam)
      ↓
Kontroler Fuzzy (teman) → Pompa Air (ESP32)
```

*Pi hanya mengirim data (tidak melayani koneksi masuk). Outbox antrean saat offline.*

---

## ✅ HASIL & BUKTI REAL

- **18 video** MP4 beranotasi dari lapangan asli
- **5 foto bed** (bed_01–05): semua sehat, PSI 0–0,1, 0 zona sakit
- **Timeseries 763 frame** per video
- **Pi test OK**: capture → analisis 960 px → payload → Firebase
- **Dashboard live**: heatmap zona + distribusi + kartu PSI
- **53 referensi paper** terverifikasi (OpenAlex)

---

## 🗺️ CONTOH OUTPUT ZONA (4×6)

```
┌────┬────┬────┬────┐
│ C1 │ C2 │ C3 │ C4 │  ← sehat (hijau)
├────┼────┼────┼────┤
│ C5 │ C6 │ C7 │ C8 │  ← waspada (orange)
├────┼────┼────┼────┤
│ C9 │ C10│ C11│ C12│  ← sakit (merah)
├────┼────┼────┼────┤
│ C13│ C14│ C15│ C16│
├────┼────┼────┼────┤
│ C17│ C18│ C19│ C20│
├────┼────┼────┼────┤
│ C21│ C22│ C23│ C24│
└────┴────┴────┴────┘
```

Legend: 🟢 Sehat  🟡 Waspada  🔴 Sakit  ⚫ n/a

---

## 📅 ROADMAP

| Bulan | Target |
|-------|--------|
| Sep 2026 | Ground Truth 5 gambar + F1/IoU + banding metode |
| Okt 2026 | Validasi ambang + burn-in 24 jam outdoor |
| Nov 2026 | Bab 4–5 + revisi + video final sidang |

---

## 📂 REPOSITORI & DEMO

**GitHub:** `github.com/FIllxe/kangkung-cv-aquaponik`  
**Dokumen:** `docs/LAPORAN_PROGRES_BIMBINGAN.md`  
**Output:** `output/` (video beranotasi, CSV, JSON, render 3D)

---

> Proyek Capstone — Teknik Komputer  
> Komponen Computer Vision (panen + kesehatan + PSI + Pi + dashboard)  
> *Tidak ada nama pribadi — konten teknis siap pameran*