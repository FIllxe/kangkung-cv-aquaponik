# 📚 Indeks Dokumentasi — Kangkung CV Aquaponik

Peta semua dokumen proyek. **Mulai dari sini** kalau baru bergabung.

## "Saya mau …" → dokumen yang dibuka

| Kebutuhan | Buka |
|---|---|
| Menjalankan analisis video di laptop | [`../README.md`](../README.md) § Quickstart Laptop |
| Deploy / merawat Raspberry Pi (kamera, service, remote) | [`../raspi/README.md`](../raspi/README.md) |
| Mengirim data ke dashboard Firebase | [`SKEMA_FIREBASE_BED_READINGS.md`](SKEMA_FIREBASE_BED_READINGS.md) |
| Melihat data live di browser (dashboard) | [`../web/README.md`](../web/README.md) |
| Membuat mask ground truth & metrik Bab 4 | [`PANDUAN_GT.md`](PANDUAN_GT.md) |
| Melaporkan progres ke pembimbing | [`LAPORAN_PROGRES_BIMBINGAN.md`](LAPORAN_PROGRES_BIMBINGAN.md) |
| Mencari sitasi paper | [`../files paper/`](../files%20paper/) |

## Daftar dokumen

| Dokumen | Jenis | Isi ringkas |
|---|---|---|
| [`SKEMA_FIREBASE_BED_READINGS.md`](SKEMA_FIREBASE_BED_READINGS.md) | Kontrak data | Skema `bed_readings` v1.0: field, tipe, ID dokumen, batas ukuran, contoh payload, alur Tahap B |
| [`PANDUAN_GT.md`](PANDUAN_GT.md) | Prosedur | (1) Anotasi 5–7 gambar dengan `buat_gt.py` → P/R/F1/IoU; (2) **checklist deploy Raspberry Pi** + burn-in 24 jam |
| [`LAPORAN_PROGRES_BIMBINGAN.md`](LAPORAN_PROGRES_BIMBINGAN.md) | Laporan | Ringkasan capaian, yang sedang dikerjakan, rencana demo, pertanyaan untuk dosen |
| [`Laporan_Computer_Vision_Kangkung_Aquaponik.pdf`](Laporan_Computer_Vision_Kangkung_Aquaponik.pdf) | Laporan | Versi PDF laporan |
| [`../raspi/README.md`](../raspi/README.md) | Panduan operasional | Kebutuhan hardware, setup Pi, tabel konfigurasi, kamera CSI/IR, Tailscale, troubleshooting, burn-in |
| [`../web/README.md`](../web/README.md) | Panduan dashboard | Fitur dashboard live monitoring, mode demo tanpa Firebase, cara sambung ke Firestore/Storage, publikasi (Hosting) |
| [`../gt/README.md`](../gt/README.md) | Referensi | Konvensi nama file mask ground truth |
| [`../files paper/`](../files%20paper/) | Referensi | 53 paper terverifikasi OpenAlex (14 + 20 + 13 + 6) + skrip unduh |

## Konvensi penulisan

- Bahasa Indonesia; istilah teknis dibiarkan asli (warp, coverage, burn-in, quad).
- Perintah ditulis dalam satu blok siap tempel, dan selalu jelas **dijalankan
  di mana** (laptop vs Pi), mis. `ssh aquaponic@<ip-pi> "…"` untuk dari laptop.
- Setiap masalah nyata yang sudah dipecahkan **wajib** dicatat di tabel
  troubleshooting `raspi/README.md` — agar solusinya tidak hilang lagi.
- Semua angka capaian (mis. jitter −53%) harus bisa dirujuk ke file di
  `output/` atau sel notebook terkait.
