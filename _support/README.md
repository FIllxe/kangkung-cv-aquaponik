# 📂 Berkas Pendukung (Support & Drafts)

Folder ini mengelompokkan seluruh berkas draf, materi bimbingan, dan skrip otomasi pendukung pengerjaan skripsi/tugas akhir agar repositori utama tetap bersih dan terfokus pada sistem produksi.

---

## Struktur Folder

```
_support/
├── drafts/       # Draf proposal (DOCX/PDF), materi bimbingan, draf PPT sempro, SK pembimbing
├── scripts/      # Skrip pembantu pembuat draf proposal, diagram bimbingan, dan utilitas penunjang
└── README.md     # Penjelasan direktori pendukung
```

### 1. `drafts/`
Berisi berkas dokumen non-produksi yang digunakan selama proses bimbingan dan penyusunan proposal:
- Draf proposal Bab 1–3 (`DRAFT_PROPOSAL_...docx`, template proposal `kirim felix.docx`)
- Draf proposal final mahasiswa (`PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_...docx`)
- Draf slide seminar proposal awal (`DRAFT_PPT_SEMPRO_...pptx`, `PRESENTASI_PROTOTIPE_FELIX.pptx`)
- Laporan progres dan diagram bimbingan dosen (`BIMBINGAN3_...`)
- Surat Keputusan pembimbing (`SK-Pembimbing_Felix.pdf` / `.png`)

### 2. `scripts/`
Berisi skrip Python pendukung yang digunakan untuk otomasi dokumen dan pembuatan visual:
- Skrip pembangun draf dokumen (`build_proposal.py`, `buat_draf_proposal_cv.py`, `buat_pdf_bimbingan3.py`)
- Skrip diagram alir dan skema bimbingan (`buat_flowchart_bimbingan3.py`, `buat_wiring_bimbingan3.py`)
- Skrip rendering visual 3D & snapshot laporan (`buat_gambar_3d_laporan.py`, `generate_ppt_snapshots.py`)
- Skrip evaluasi format penulisan (`apply_style_fix_and_verify.py`, `style_check_report.txt`, dll.)

---

## 🚀 Kode Produksi Utama (Operational Code)

Untuk kode yang benar-benar dijalankan pada sistem operasional aquaponik, silakan merujuk ke direktori utama:

| Komponen | Lokasi | Keterangan |
|---|---|---|
| **Raspberry Pi Runtime** | [`../raspi/`](../raspi/) | Pipeline visi komputer live, segmentasi adaptif, ExG, kalkulasi PSI, uplink Firebase & jembatan ESP32 |
| **Web Dashboard** | [`../web/`](../web/) | Dashboard antarmuka pengguna pemantauan grid 24 zona secara real-time |
| **Hardware Enclosure** | [`../hardware/`](../hardware/) | Model CAD 3D-printing dudukan kamera & kasing Raspberry Pi 4B |
| **Pengujian Laptop** | [`../files/`](../files/) | Skrip pipeline pengujian OpenCV di PC (`kangkung_cv.py`, `adaptive_bed.py`, dll.) |
| **Manual Kalkulasi** | [`../docs/MANUAL_KALKULASI_FORMULATIF.md`](../docs/MANUAL_KALKULASI_FORMULATIF.md) | Penurunan matematis lengkap 8 pilar + tautan baris kode sumber |
| **Presentasi Utama** | [`../docs/PRESENTASI_FORMULATIF_KALKULATIF_MINIMALIS.pptx`](../docs/PRESENTASI_FORMULATIF_KALKULATIF_MINIMALIS.pptx) | Slide resmi perhitungan manual vs kode |
