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

## Proposal prototipe — Felix Enrique (NIM 2305110019)

| Dokumen | Jenis | Isi ringkas |
|---|---|---|
| [`PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx`](PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx) | **Hasil final** | Proposal prototipe Bab 1–3 + Daftar Pustaka (10 sitasi): monitoring kelayakan panen akuaponik via segmentasi HSV, grid 4×6, indeks PSI |
| [`kirim felix.docx`](kirim%20felix.docx) | Template | Template proposal kampus — **input** build, jangan diubah isinya |
| [`build_proposal.py`](build_proposal.py) | Skrip build | Membangun ulang DOCX final dari template dalam satu run + verifikasi isi |
| [`blok_diagram.png`](blok_diagram.png), [`flowchart_cv.png`](flowchart_cv.png), [`skema_kamera.png`](skema_kamera.png) | Aset gambar | Gambar 3.1–3.3 proposal — **input** build (Gambar 3.4–3.5 diambil dari `../output/ppt_asli/`) |
| [`DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx`](DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx) | Draf kerja | Draf konten Bab 1–3 sebelum diformat ke template (dibuat oleh `buat_draf_proposal_cv.py`; perlu `pip install python-docx`) |
| [`DRAFT_PPT_SEMPRO_Bagian_CV_v2_ASLI.pptx`](DRAFT_PPT_SEMPRO_Bagian_CV_v2_ASLI.pptx) | Presentasi | Slide sempro bagian CV, 16 slide 16:9, gambar asli lapangan (dibuat oleh `buat_ppt_sempro_all.py`; perlu `pip install python-pptx`; gambar bukti oleh `buat_gambar_ppt_asli.py`) |
| [`PANDUAN_PRESENTASI_CV.md`](PANDUAN_PRESENTASI_CV.md) | Panduan | Naskah per slide, kalimat kejujuran, Q&A, checklist H-1 (pendamping PPT v2 ASLI) |

Regenerasi proposal dari nol (hasil harus `IDENTIK` dengan DOCX final):

```powershell
python docs/build_proposal.py --out docs/REGEN_CHECK.docx --regenerate
python docs/build_proposal.py --compare docs/PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx docs/REGEN_CHECK.docx
```

## Konvensi penulisan

- Bahasa Indonesia; istilah teknis dibiarkan asli (warp, coverage, burn-in, quad).
- Perintah ditulis dalam satu blok siap tempel, dan selalu jelas **dijalankan
  di mana** (laptop vs Pi), mis. `ssh aquaponic@<ip-pi> "…"` untuk dari laptop.
- Setiap masalah nyata yang sudah dipecahkan **wajib** dicatat di tabel
  troubleshooting `raspi/README.md` — agar solusinya tidak hilang lagi.
- Semua angka capaian (mis. jitter −53%) harus bisa dirujuk ke file di
  `output/` atau sel notebook terkait.
