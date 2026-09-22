# 🌿 Kangkung CV Aquaponik — Sistem Computer Vision Deteksi Kesiapan Panen

Deteksi kesiapan panen kangkung **per zona** pada bed aquaponik 2 m × 1,1 m
(grid 4×6 = 24 zona) dari video HP/kamera, plus **kesehatan daun** (% kuning =
klorosis, % coklat = nekrosis) — output siap dikonsumsi dashboard Firebase dan
kontroler fuzzy pompa air.

![status](https://img.shields.io/badge/status-prototype%20capstone-green)
![python](https://img.shields.io/badge/python-3.9%2B-blue)

## Arsitektur

```
Video/Kamera → Deteksi Bed (Canny edge / HSV) → Warp Perspektif → Grid 4×6
→ Segmentasi HSV Adaptif (f = mean(V)/128) → Coverage + Kesehatan per Zona
→ CSV Timeseries + JSON + MP4 Beranotasi → Dashboard Firebase (multi-user)
                                                    ↘ fuzzy_input → Pompa Air
```

## Isi Repo

| Folder | Isi |
|---|---|
| `files/` | Pipeline utama: `proses_video.py`, `adaptive_bed.py`, `kangkung_cv.py`, evaluasi, kalibrasi |
| `raspi/` | Paket **ready-to-use Raspberry Pi** (install.sh, systemd, thermal guard, Firebase uplink) |
| `notebooks/` | Notebook presentasi (16→19 cell, tereksekusi) |
| `docs/` | Laporan progres, skema Firebase `bed_readings`, laporan PDF |
| `files paper/` | 53 referensi paper terverifikasi (OpenAlex) dalam markdown |

## Quickstart — Laptop (analisis video)

```bash
git clone https://github.com/<USER>/kangkung-cv-aquaponik.git
cd kangkung-cv-aquaponik
pip install -r files/requirements.txt

cd files
python proses_video.py ..\data\videos\VIDEO_ANDA.MOV --adaptive --no-gui --save
# output: output/video/<nama>_beranotasi.mp4 + timeseries.csv + ringkasan.json
```

## Quickstart — Raspberry Pi (live monitoring outdoor)

```bash
git clone https://github.com/<USER>/kangkung-cv-aquaponik.git ~/kangkung_pi_src
cd ~/kangkung_pi_src/raspi
bash install.sh          # copy → venv → deps → systemd auto-start
sudo systemctl start kangkung
journalctl -u kangkung -f
```

Detail lengkap (Tailscale remote, multi-user tanpa login, burn-in test 24 jam):
lihat [`raspi/README.md`](raspi/README.md).

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

- [Skema Firebase `bed_readings` v1.0](docs/SKEMA_FIREBASE_BED_READINGS.md)
- [Laporan progres & timeline](docs/LAPORAN_PROGRES_BIMBINGAN.md)
- [Referensi method baru](files%20paper/REFERENSI_METHOD_BARU.md) ·
  [Referensi kesehatan daun](files%20paper/REFERENSI_KESEHATAN_DAUN.md)

## Lisensi

[MIT](LICENSE) — dataset video/foto **tidak** disertakan di repo (unduh
terpisah); struktur folder yang diharapkan ada di `.gitignore`.
