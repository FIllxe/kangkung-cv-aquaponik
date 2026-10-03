# 💻 files/ — Pipeline Computer Vision (laptop)

Skrip Python analisis video & gambar kangkung. Dijalankan dari folder ini:

```bash
cd files
pip install -r requirements.txt
python proses_video.py ..\data\videos\VIDEO_ANDA.MOV --adaptive --no-gui --save
```

> `raspi/modules/` adalah **salinan** `adaptive_bed.py` + `kangkung_cv.py` —
> edit di sini, lalu kirim ulang ke Pi (lihat `../raspi/README.md` § Perbarui kode).

## Inti pipeline (jangan dipindah)

| File | Peran | Dipakai oleh |
|---|---|---|
| `kangkung_cv.py` | Segmentasi HSV + skor zona + `hitung_psi()` (sumber tunggal PSI) | semua skrip + `web/` + `raspi/` |
| `adaptive_bed.py` | Deteksi bed, warp, grid 4×6, `CornerSmoother`, `mask_tanaman_warna()` | `proses_video.py`, `kalibrasi_kamera.py`, `live_monitor.py` |
| `proses_video.py` | End-to-end video → MP4 beranotasi + CSV + JSON | CLI utama laptop |
| `kalibrasi_kamera.py` | Simpan/muat `kalibrasi_kamera.json` (mode FIXED) | `proses_video.py` |

## Kalibrasi & ground truth

| File | Peran |
|---|---|
| `kalibrasi_hsv.py` | Tune ambang hijau ke kamera/cahaya lapangan |
| `buat_gt.py` | Anotasi mask GT → `../gt/` (lihat `../docs/PANDUAN_GT.md`) |
| `evaluasi_segmentasi.py` | P/R/F1/IoU vs GT (Bab 4) |
| `bandingkan_metode.py` | HSV vs ExG vs Otsu-Hue (Bab 4) |

## Utilitas / demo (sekali pakai, output ke `../output/`)

| File | Peran |
|---|---|
| `batch_segmentasi.py` | Proses semua gambar `../dataset1/` sekaligus |
| `live_monitor.py` | Preview webcam laptop (bukan service Pi) |
| `cek_psi.py` | Regression test paritas 2 jalur + tabel PSI |
| `buat_payload_dashboard.py` | JSON laporan → payload `bed_readings` (Tahap A, tanpa Firebase) |
| `buat_dummy_sakit.py` | Gambar uji sintetis (verifikasi fungsi, bukan klaim akurasi) |
| `buat_demo_dua_video.py` | Panel demo 2 video |
| `panel_kesehatan_daun.py` | Panel demo injeksi blob (appendix, bukan bukti lapangan) |
| `requirements.txt` | `opencv-python`, `numpy`, `matplotlib` (laptop saja) |
