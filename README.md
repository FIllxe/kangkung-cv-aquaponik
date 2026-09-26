# 🌿 Kangkung CV Aquaponik — Sistem Computer Vision Deteksi Kesiapan Panen

Deteksi kesiapan panen kangkung **per zona** pada bed aquaponik 2 m × 1,1 m
(grid 4×6 = 24 zona) dari video HP/kamera, plus **kesehatan daun** (% kuning =
klorosis, % coklat = nekrosis) — output siap dikonsumsi dashboard Firebase dan
kontroler fuzzy pompa air.

![status](https://img.shields.io/badge/status-prototype%20capstone-green)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![deploy](https://img.shields.io/badge/deploy-Raspberry%20Pi%204B-c51a4a)

## Status terverifikasi

| Lingkungan | Yang sudah diverifikasi |
|---|---|
| Laptop (Windows, Python 3.12) | pipeline video end-to-end, evaluasi, notebook presentasi |
| Raspberry Pi 4B + Debian 13 *trixie* (aarch64, Python 3.13) | akses remote (SSH + Tailscale), venv Pi (`opencv 4.10.0`, `numpy 1.26.4`, `firebase-admin 6.5.0`), **kamera CSI IR 5MP (ov5647) terbaca lewat libcamera/Picamera2** |
| Lapangan (outdoor permanen) | ⏳ menunggu kasing/box kamera → uji pipeline penuh + burn-in 24 jam |

Langkah deploy, konfigurasi, dan troubleshooting: [`raspi/README.md`](raspi/README.md).

## Arsitektur

```
Video/Kamera → Deteksi Bed (Canny edge / HSV) → Warp Perspektif → Grid 4×6
→ Segmentasi HSV Adaptif (f = mean(V)/128) → Coverage + Kesehatan per Zona
→ CSV Timeseries + JSON + MP4 Beranotasi → Dashboard Firebase (multi-user)
                                                    ↘ fuzzy_input (PSI 0-100) → Kontroler Fuzzy
```

## Isi Repo

| Folder | Isi |
|---|---|
| `files/` | Pipeline utama: `proses_video.py`, `adaptive_bed.py`, `kangkung_cv.py`, evaluasi, kalibrasi, GT tool |
| `raspi/` | Paket **ready-to-use Raspberry Pi**: `install.sh`, `kangkung_pi.py`, `camera_pi.py` (kamera CSI), systemd, thermal guard, Firebase uplink |
| `web/` | **Dashboard web statis** (live monitoring, tanpa build) — lihat [`web/README.md`](web/README.md) |
| `notebooks/` | Notebook presentasi (`presentasi_kangkung_cv.ipynb`, tereksekusi) |
| `docs/` | Indeks dokumen, laporan progres, skema Firebase `bed_readings`, panduan GT, laporan PDF — lihat [`docs/README.md`](docs/README.md) |
| `gt/` | Mask ground truth hasil anotasi (`buat_gt.py`) — belum diisi, lihat [`docs/PANDUAN_GT.md`](docs/PANDUAN_GT.md) |
| `files paper/` | **53 referensi paper** terverifikasi (OpenAlex) dalam markdown |
| `data/`, `dataset1/`, `output/` | Video mentah, foto lapangan, hasil proses — *tidak di-commit* (lihat `.gitignore`) |

## Quickstart — Laptop (analisis video)

```bash
git clone https://github.com/FIllxe/kangkung-cv-aquaponik.git
cd kangkung-cv-aquaponik
pip install -r files/requirements.txt

cd files
python proses_video.py ..\data\videos\VIDEO_ANDA.MOV --adaptive --no-gui --save
# output: output/video/<nama>_beranotasi.mp4 + timeseries.csv + ringkasan.json
```

## Quickstart — Raspberry Pi (live monitoring outdoor)

```bash
git clone https://github.com/FIllxe/kangkung-cv-aquaponik.git ~/kangkung_pi_src
cd ~/kangkung_pi_src/raspi
bash install.sh                      # copy → venv → deps (+libcamera) → systemd
cd ~/kangkung_pi
./venv/bin/python camera_pi.py       # cek kamera: 1 frame → /tmp/camera_pi_test.jpg
./venv/bin/python kangkung_pi.py --test
sudo systemctl start kangkung
journalctl -u kangkung -f
```

Detail lengkap (persiapan hardware, kamera CSI/IR, Tailscale remote, multi-user
tanpa login, troubleshooting, burn-in test 24 jam): lihat
[`raspi/README.md`](raspi/README.md).

## Output per Sesi

| File | Isi |
|---|---|
| `*_beranotasi.mp4` | Video side-by-side + grid berwarna + HUD |
| `*_timeseries.csv` | Coverage + %kuning (Y_) + %coklat (B_) per zona per frame |
| `*_laporan.json` / `ringkasan_*.json` | Statistik global + 24 zona + distribusi |
| Payload `bed_readings` | Skema v1.0 + `fuzzy_input` untuk pompa — [skema](docs/SKEMA_FIREBASE_BED_READINGS.md) |

## Metode

1. **Deteksi bed**: Canny edge → approx quad → homografi 4-titik (fallback HSV-mask)
2. **HSV adaptif**: `f = mean(V)/128` menggeser S/V per frame — stabilisasi coverage
   lintas kondisi cahaya **rata-rata 38%** (puncak 65%); Hue tidak digeser
3. **Kesehatan daun**: kuning (klorosis, H 21–34) & coklat (nekrosis, H 8–20 +
   adjacency kanopi) — % terhadap piksel tanaman, bukan luas zona
4. **Stabilisasi temporal**: EMA α=0,2 — jitter sudut −53%

## Dokumentasi

| Dokumen | Isi |
|---|---|
| [`docs/README.md`](docs/README.md) | **Indeks dokumentasi** (mulai dari sini) |
| [`docs/SKEMA_FIREBASE_BED_READINGS.md`](docs/SKEMA_FIREBASE_BED_READINGS.md) | Kontrak data `bed_readings` v1.0 untuk dashboard |
| [`docs/PANDUAN_GT.md`](docs/PANDUAN_GT.md) | Anotasi ground truth (Bab 4) + **checklist deploy Raspberry Pi** |
| [`docs/LAPORAN_PROGRES_BIMBINGAN.md`](docs/LAPORAN_PROGRES_BIMBINGAN.md) | Laporan progres & timeline bimbingan |
| [`raspi/README.md`](raspi/README.md) | Deploy Pi, kamera CSI, remote Tailscale, troubleshooting, burn-in |
| [`web/README.md`](web/README.md) | **Dashboard web live monitoring**: fitur, mode demo, sambung Firebase, hosting |
| [`gt/README.md`](gt/README.md) | Konvensi nama mask ground truth |
| [`files paper/REFERENSI_METHOD_BARU.md`](files%20paper/REFERENSI_METHOD_BARU.md) · [`REFERENSI_KESEHATAN_DAUN.md`](files%20paper/REFERENSI_KESEHATAN_DAUN.md) | 53 referensi terverifikasi (OpenAlex) |

## Lisensi

[MIT](LICENSE) — dataset video/foto **tidak** disertakan di repo (unduh
terpisah); struktur folder yang diharapkan ada di `.gitignore`.
