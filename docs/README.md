# 📚 Indeks Dokumentasi — Kangkung CV Aquaponik

Peta dokumen proyek Computer Vision Kangkung Aquaponik.

---

## 📌 Dokumen Utama Proyek (Production & Rujukan)

| Dokumen | Jenis | Isi Ringkas |
|---|---|---|
| [`MANUAL_KALKULASI_FORMULATIF.md`](MANUAL_KALKULASI_FORMULATIF.md) | **Rujukan Matematis** | Penurunan matematis lengkap 8 pilar (Homografi, Shoelace, WB, ExG, Adaptive HSV, Morfologi, Skor Panen, PSI, Fuzzy) + tautan kode sumber & verifikasi numerik ($\Delta = 0$) |
| [`PRESENTASI_FORMULATIF_KALKULATIF_MINIMALIS.pptx`](PRESENTASI_FORMULATIF_KALKULATIF_MINIMALIS.pptx) | **Slide Resmi** | Slide presentasi 32 slide paritas perhitungan manual vs kode |
| [`SKEMA_FIREBASE_BED_READINGS.md`](SKEMA_FIREBASE_BED_READINGS.md) | Kontrak Data | Skema `bed_readings` v1.0: field, tipe, ID dokumen, batas ukuran, dan contoh payload untuk dashboard |
| [`DASHBOARD_SPEC.md`](DASHBOARD_SPEC.md) | Spesifikasi UI | Spesifikasi tampilan dan interaksi dashboard web |
| [`PANDUAN_PRESENTASI_CV.md`](PANDUAN_PRESENTASI_CV.md) | Panduan Presentasi | Panduan alur penyampaian materi computer vision |
| [`PANDUAN_GT.md`](PANDUAN_GT.md) | Prosedur Evaluasi | Prosedur anotasi ground truth, evaluasi metrik (P/R/F1/IoU), dan checklist Raspberry Pi |
| [`RENCANA_KONEKSI_ESP32_RASPI.md`](RENCANA_KONEKSI_ESP32_RASPI.md) | Integrasi Hardware | Protokol komunikasi serial/BLE antara ESP32 dan Raspberry Pi 4B |
| [`../raspi/README.md`](../raspi/README.md) | Panduan Operasional | Setup runtime Raspberry Pi 4B, kamera CSI/IR, service systemd, dan troubleshooting |
| [`../web/README.md`](../web/README.md) | Panduan Dashboard | Panduan penggunaan dan deployment web dashboard monitoring |

---

## 📂 Berkas Pendukung & Draf Proposal (`_support/`)

Seluruh draf proposal, draf slide seminar, lembar bimbingan, dan skrip otomasi penunjang telah dipisahkan ke dalam folder [`../_support/`](../_support/):

- **[`../_support/drafts/`](../_support/drafts/)**: Berkas DOCX proposal, draf presentasi awal, surat keputusan pembimbing, dan berkas bimbingan dosen.
- **[`../_support/scripts/`](../_support/scripts/)**: Skrip pembantu pembuat draf proposal, utilitas rendering visual 3D, dan skrip formatting laporan.
