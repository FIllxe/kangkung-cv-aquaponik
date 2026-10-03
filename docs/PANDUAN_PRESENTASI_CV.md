# Panduan Presentasi Sempro — Bagian Computer Vision (pendamping PPT v2 ASLI)

File PPT: `docs/DRAFT_PPT_SEMPRO_Bagian_CV_v2_ASLI.pptx` (16 slide, 16:9).
Regenerasi gambar: `python docs/buat_gambar_ppt_asli.py` lalu `python docs/buat_ppt_sempro_all.py`
(v1 `DRAFT_PPT_SEMPRO_Bagian_CV.pptx` = versi lama berisi gambar simulasi/injeksi — JANGAN dipakai.)
Durasi: ±15 menit bagian CV + 5 menit bagian teman + 10 menit Q&A.

## Daftar slide + apa diomongkan + file bukti

| # | Slide | Naskah inti (±) | Bukti ASLI / demo |
|---|---|---|---|
| 1 | Judul | Bed 2×1,1 m → 24 zona → peta panen + kesehatan → dashboard + fuzzy teman | `dataset1/bed_04_ready.jpg` (foto lapangan) |
| 2 | Pembagian tugas | Saya = CV+deploy, teman = fuzzy+pompa, kontrak = `fuzzy_input` | `docs/SKEMA_FIREBASE_BED_READINGS.md` |
| 3 | Latar belakang | Bed tak seragam + cahaya berubah = butuh peta zona + adaptif | `output/ppt_asli/04_tren_5foto_asli.png` |
| 4 | Tujuan & luaran | Tiap tujuan ada file bukti; lulus = burn-in 24 jam | `output/demo/`, `output/firebase/` |
| 5 | Teori | Canny 1986 + Woebbecke 1995; non-DL karena data kecil + RPi CPU | `files paper/` (53 paper) |
| 6 | Arsitektur | Saya kotak 1,2,4; teman kotak 5; bersama kotak 3; tanpa aktuasi otomatis | skema v1.1 |
| 7 | Pipeline CV | 6 tahap; modul identik laptop & Pi | `output/ppt_asli/01_asli_vs_anotasi.jpg` (frame HP vs output) |
| 8 | Metode 1 bed | Canny→quad→homografi + fallback; warp bikin zona adil | `bed_04_ready.jpg` + `02_foto_vs_segmentasi.jpg` |
| 9 | Metode 2 adaptif (NOVELTY) | f=mean(V)/128, Hue tetap; jitter −53%, stabilitas +38% | Notebook §5 |
| 10 | Kesehatan + PSI | Rumus PSI; tabel 5 foto asli: semua sehat PSI 0–0,1 | `05_tabel_PSI_5foto.png` + `02_foto_vs_segmentasi.jpg` |
| 11 | Deploy Pi + dashboard | Test [OK], siklus 10 mnt; box = RENDER CAD (bukan foto fisik) | `hardware/renders/preview_rakit_iso.png` + label jujur |
| 12 | Hasil utama (DEMO) | Frame HP vs output + timeseries 763 frame; putar 30 dtk MP4 | `01_asli_vs_anotasi.jpg` + `03_timeseries_IMG5159.png` |
| 13 | Hasil kesehatan lapangan | 5 foto: kuning 0%, coklat ~0%, 0 sakit, PSI 0–0,1; injeksi/dummy di appendix | `04_tren_5foto_asli.png` + `05_tabel_PSI_5foto.png` |
| 14 | Evaluasi vs TODO | Sudah vs belum + risiko/mitigasi; tool GT siap (45–60 mnt) | `files/buat_gt.py` |
| 15 | Timeline Nov 2026 | Sep GT, Okt lapangan+burn-in, Nov Bab 4–5 + sidang | checklist H-1 |
| 16 | Penutup | Kesimpulan + 4 mohon arahan + transisi ke teman | antisipasi Q&A |

## Yang DIKELUARKAN dari v2 (pindah appendix, bukan badan presentasi)

| File | Sebab |
|---|---|
| `output/evaluasi/panel_kesehatan_daun.png` | Bed asli + blob injeksi digital (semi-simulasi) |
| `output/evaluasi/uji_kuning_coklat.jpg` | Citra uji sintetis |
| `output/dummy/*`, `demo_dummy_*`, `laporan_dummy_*` | 100% sintetis |
| `output/segmentasi_batch/RINGKASAN_BATCH.png`, `dataset1/Image_*.png` | Tercampur 2 file asal tak terverifikasi (pola nama AI) |

## Kalimat kejujuran (ucapkan di slide 13)

> "Semua gambar di presentasi ini adalah foto/video lapangan asli dan output
> langsung pipeline. Uji blob injeksi dan gambar dummy sintetis hanya verifikasi
> fungsi dan saya simpan di appendix — bukan klaim akurasi lapangan.
> Akurasi lapangan (F1/IoU) menyusul setelah ground truth 5 gambar akhir September."

## Cara pakai sampai kelulusan (tanpa buat ulang)

- Sempro: pakai apa adanya. Slide 14–15 yang berisi TODO adalah bukti kejujuran.
- Kemajuan: tambah centang di slide 14–15 + selipkan grafik F1/IoU di slide 12.
- Kelulusan: ubah judul slide 14 jadi "Hasil Evaluasi Kuantitatif",
  ganti kartu TODO dengan tabel P/R/F1/IoU + foto box tercetak + log burn-in ≥140.

## Checklist H-1

- [ ] Tes offline 30 frame: `python proses_video.py ..\data\videos\IMG_5159.MOV --adaptive --max-frames 30 --no-gui --save --out-dir ..\output\evaluasi`
- [ ] Copy ke laptop presentasi: MP4 30-detik + `output/ppt_asli/` + 1 JSON + screenshot dashboard
- [ ] Internet cadangan: hotspot HP + screenshot dashboard offline + video lokal
- [ ] Print `docs/LAPORAN_PROGRES_BIMBINGAN.md` 1–2 lembar
- [ ] Hafalkan angka: −53%, +38%, 49,6 vs 58,4 (763 vs 425 frame), 18 video, 5 foto asli, 24 zona, ambang 25/55/80 & 25/8

## Jawaban Q&A (hafalkan)

- Akurasi? → GT 5 gambar akhir Sep (`buat_gt.py` 45–60 mnt → `evaluasi_segmentasi.py`), target F1 0,85–0,95. Terukur kini: jitter −53%, tren 5 foto logis, 5 foto sehat PSI 0–0,1 tanpa false sakit.
- Foto sakit asli mana? → Belum ada di kebun (semua bed sehat saat pengambilan). Rumus PSI sudah siap; GT + foto sakit masuk TODO.
- Panel injeksi/dummy kemarin? → Itu uji fungsi di appendix, bukan bukti lapangan. Sudah saya keluarkan dari badan presentasi.
- Kenapa bukan DL? → Data kecil, RPi tanpa GPU, HSV 20–25 ms/frame. DL = future work.
- Output petani? → Peta 24 zona + status kesehatan + rekomendasi teks + timeseries; ke dashboard + fuzzy.
- Kapan selesai? → Akhir Nov: Sep GT, Okt lapangan+burn-in, Nov laporan+sidang.
- Ganti air untuk klorosis? → Pertanyaan bagus, dibahas bersama teman + dosen (risiko bakteri/ikan); sementara butuh ACC manusia.
