# -*- coding: utf-8 -*-
"""Generator notebook NASKAH presentasi video - Bagian Computer Vision.
Jalankan : python notebooks/buat_naskah_presentasi.py
Output   : notebooks/naskah_presentasi_video.ipynb
Isi      : peta segmen -> slide, 'yang harus dijelaskan', naskah kata-per-kata,
           file bukti, angka kunci, checker bukti, lampiran Q&A + checklist H-1.
Konvensi : mengikuti docs/buat_ppt_sempro_all.py (16 slide v2_ASLI).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'notebooks' / 'naskah_presentasi_video.ipynb'

def md(text, cid):
    return {'cell_type': 'markdown', 'id': cid, 'metadata': {},
            'source': [l + '\n' for l in text.splitlines()]}

def code(text, cid):
    return {'cell_type': 'code', 'execution_count': None, 'id': cid,
            'metadata': {}, 'outputs': [],
            'source': [l + '\n' for l in text.splitlines()]}

C = []

C.append(md("""# \U0001f3ac NASKAH Presentasi Video \u2014 Bagian Computer Vision
**Judul:** Sistem Computer Vision Deteksi Kesiapan Panen Kangkung Aquaponik (Segmentasi HSV Adaptif + PSI, Grid 4\u00d76)
**Pasangan:** `docs/DRAFT_PPT_SEMPRO_Bagian_CV_v2_ASLI.pptx` (16 slide) \u2014 naskah ini mengikuti urutan slide itu.
**Bukti visual:** `notebooks/presentasi_kangkung_cv.ipynb` (16 sel, tereksekusi) + file di `output/`.

## Cara pakai notebook ini
1. Baca **Peta Segmen** di sel berikut untuk alur dan durasi total **\u00b110 menit**.
2. Setiap segmen punya pola tetap: **Slide \u2192 Durasi \u2192 \u2705 Yang harus dijelaskan \u2192 \U0001f399 Naskah \u2192 \U0001f4c1 Bukti \u2192 \U0001f522 Angka kunci**.
3. Jalankan sel **Checker Bukti** sekali sebelum merekam; semua baris harus `[OK]`.
4. Saat merekam: tampilkan slide PPT sesuai nomor, lalu pindah ke file bukti (gambar/MP4/dashboard).
5. Ganti semua `[NAMA]`, `[NIM]`, `[NAMA TEMAN]` sebelum merekam.
""", 'md-00'))

C.append(md("""## \U0001f4cc Peta Segmen \u2192 Slide \u2192 Durasi (total \u00b1 10 menit)

| Segmen | Slide PPT | Durasi | Isi |
|---|---|---|---|
| 1. Pembuka | 1. Judul | 0:40 | Elevator pitch 30 detik |
| 2. Pembagian tugas | 2. Pembagian Tugas Tim | 0:50 | Bagian saya vs teman + kontrak data |
| 3. Masalah & tujuan | 3. Latar Belakang, 4. Tujuan & Luaran | 1:30 | Rumusan masalah, tujuan, manfaat, **batasan** |
| 4. Teori | 5. 5 Konsep Penopang | 1:00 | Sitasi inti + alasan non-DL |
| 5. Arsitektur | 6. Arsitektur, 7. Pipeline CV | 1:20 | Alur end-to-end + 6 tahap pipeline |
| 6. Metode | 8. Metode 1, 9. Metode 2 (novelty) | 1:40 | Canny/homografi + HSV adaptif/EMA + angka |
| 7. Kesehatan + PSI | 10. Kesehatan + PSI | 1:00 | Rumus PSI + jembatan ke fuzzy |
| 8. Demo | 11. Deploy Pi, 12. Hasil Utama | 1:30 | Pi test OK + **putar MP4 30 detik** |
| 9. Hasil & evaluasi | 13. Hasil Kesehatan, 14. Sudah vs Belum | 1:00 | Fakta lapangan + kalimat kejujuran + TODO |
| 10. Rencana & penutup | 15. Timeline, 16. Penutup | 1:10 | Timeline Nov + kriteria lulus + mohon arahan |

## Aturan narasi (dibaca sekali sebelum merekam)
- Satu klaim = satu bukti yang ditunjuk di layar. Jangan menyebut angka tanpa menunjuk file/grafiknya.
- Bedakan tegas **data lapangan asli** vs **uji fungsi sintetis** (injeksi blob/dummy hanya di appendix, bukan klaim akurasi).
- Ucapkan istilah persis seperti di laporan: *coverage*, *warp*, *quad*, *burn-in*, *PSI (Plant Stress Index)*.
- Tempo santai \u00b1 130 kata/menit; jeda 1 detik tiap ganti slide.
""", 'md-01'))
C.append(md("""---
## Segmen 1 \u2014 Pembuka & Elevator Pitch (0:40) \u2502 Slide 1
**Slide:** `1/16` \u2014 SIDANG SEMINAR PROPOSAL (SEMPRO) \u2022 CAPSTONE / \u201cSistem Computer Vision Deteksi Kesiapan Panen\u201d.

### \u2705 Yang harus dijelaskan
- Identitas: nama, NIM, dan bahwa ini **bagian Computer Vision** dari tim 2 orang.
- Judul lengkap prototipe + objek (bed 2 m \u00d7 1,1 m) + output (peta 24 zona + kesehatan + PSI).
- Elevator pitch 30 detik: bed difoto \u2192 grid 4\u00d76 berwarna \u2192 tiap zona tahu status panen dan kesehatannya.

### \U0001f399 Naskah (\u00b1 90 kata)
> \u201cSelamat pagi Bapak/Ibu. Saya [NAMA], NIM [NIM], dari tim Computer Vision capstone kami.
> Judul prototipe kami: Sistem Computer Vision Deteksi Kesiapan Panen Kangkung Aquaponik Berbasis Segmentasi HSV Adaptif dan Indeks Stres Tanaman pada Grid 4 kali 6.
> Bed aquaponik ukuran 2 meter kali 1,1 meter kami bagi menjadi 24 zona.
> Kamera memotret bed dari atas, lalu sistem memberi peta kesiapan panen per zona \u2014 belum, hampir, siap, atau harus panen \u2014 sekaligus status kesehatan daun tiap zona dan skor stres untuk kontroler fuzzy.
> Video ini membahas bagian saya, yaitu Computer Vision dan deploy-nya.\u201d

### \U0001f4c1 Bukti yang ditunjuk
- Foto `dataset1/bed_04_ready.jpg` (bed siap panen, lapangan asli).

### \U0001f522 Angka kunci
- 2 orang tim \u2022 24 zona (4\u00d76) \u2022 bed 2 \u00d7 1,1 m.
""", 'md-seg1'))

C.append(md("""---
## Segmen 2 \u2014 Pembagian Tugas & Kontrak (0:50) \u2502 Slide 2
**Slide:** `2/16` \u2014 BAGIAN SAYA vs TEMAN \u2022 SLIDE WAJIB SEMPRO / \u201cPembagian Tugas Tim (2 Orang)\u201d.

### \u2705 Yang harus dijelaskan
- Mana kotak milik saya (akuisisi, CV di Pi, dashboard) vs milik teman (fuzzy + ESP32 + pompa) vs kontrak bersama (Firebase).
- **Kontrak data**: saya produsen `fuzzy_input` berisi `psi`, `psi_maks`, `zona_sakit`, `psi_versi`; teman konsumen.
- **Aturan aman**: tidak ada aktuasi otomatis; status baru ditulis `menunggu_acc` oleh manusia; data basi > 30 menit ditolak; nilai hilang = tahan tindakan; anti-spam 60 menit.
- Kontrak tertulis di `docs/SKEMA_FIREBASE_BED_READINGS.md` (skema v1.1).

### \U0001f399 Naskah (\u00b1 100 kata)
> \u201cAgar jelas, ini pembagian tugas kami berdua.
> Bagian saya: akuisisi kamera, seluruh pipeline computer vision di Raspberry Pi \u2014 deteksi bed, warp, grid 4 kali 6, coverage, deteksi kuning dan coklat, dan skor PSI \u2014 plus payload Firebase dan dashboard web.
> Bagian [NAMA TEMAN]: rule base fuzzy, ESP32 dan pompa, keputusan fuzzy, serta ACC dan audit oleh manusia.
> Kami bertemu di satu kontrak data: skema bed_readings versi 1.1.
> Saya mengirim fuzzy_input berisi PSI rata-rata bed, PSI zona terburuk, jumlah zona sakit, dan versi rumus.
> Aturannya: tidak ada aktuasi otomatis; setiap usulan tindakan wajib menunggu persetujuan manusia, data basi dan data hilang ditolak.\u201d

### \U0001f4c1 Bukti yang ditunjuk
- Slide 2 (kartu hijau/biru/kuning) + `docs/SKEMA_FIREBASE_BED_READINGS.md`.

### \U0001f522 Angka kunci
- Payload \u00b1 2\u20133 KB/dok \u2022 upload 1\u00d7/10 menit \u2022 stale > 30 menit \u2022 cooldown 60 menit.
""", 'md-seg2'))
C.append(md("""---
## Segmen 3 \u2014 Masalah, Tujuan & Batasan (1:30) \u2502 Slide 3\u20134
**Slide:** `3/16` LATAR BELAKANG / \u201cPetani Sulit Menilai 24 Zona Bed Konsisten\u201d dan `4/16` TUJUAN & LUARAN / \u201cTujuan Umum > Khusus > Luaran Terukur\u201d.

### \u2705 Yang harus dijelaskan
- **Fakta lapangan (slide 3):** bed tidak tumbuh seragam (tepi vs tengah beda); penilaian mata subjektif, melelahkan, antarpenilai tidak konsisten.
- **Musuh utama:** cahaya pagi/siang/sore dan bayangan \u2192 HSV statis gagal, coverage melompat walau tanamannya sama. Tunjuk `output/ppt_asli/04_tren_5foto_asli.png`.
- **Rumusan masalah (3 butir):** (1) panen per zona otomatis? (2) stabil lintas cahaya? (3) skor kuning/coklat siap-fuzzy?
- **Tujuan:** umum = sensor tanaman otomatis; khusus T1 grid otomatis, T2 HSV adaptif stabil cahaya, T3 kuning/coklat + PSI, T4 Pi + dashboard live.
- **Manfaat:** petani (panen selektif), tim fuzzy (input PSI siap pakai), akademik (baseline ringan non-DL).
- **Batasan (wajib diucapkan):** kangkung aquaponik 1 bed, kamera top-down, tanpa deep learning, jalan di CPU Pi.
- **Research gap (kartu kanan slide 3):** sedikit yang menggabungkan grid panen per zona + adaptasi cahaya + skor siap-fuzzy + deploy Pi outdoor.

### \U0001f399 Naskah (\u00b1 190 kata)
> \u201cBed tidak tumbuh seragam: bagian tepi dan tengah beda. Penilaian kesiapan panen yang masih mengandalkan mata bersifat subjektif dan melelahkan, sehingga bed yang sama bisa dinilai berbeda.
> Panen terlalu dini menurunkan biomassa, panen terlambat menurunkan mutu daun. Karena itu kami butuh peta kesiapan per zona, bukan satu angka untuk seluruh bed.
> Masalah keduanya adalah cahaya. Foto pagi, siang, dan sore mengubah komponen terang citra, sehingga segmentasi warna statis menghasilkan liputan yang melompat walaupun tanamannya sama \u2014 grafik tren lima foto lapangan di kanan menunjukkan tantangannya.
> Rumusan masalah kami tiga: bagaimana menilai panen per zona otomatis; bagaimana membuatnya stabil lintas cahaya; dan bagaimana mendeteksi gejala kuning dan coklat plus skor stres untuk kontroler fuzzy.
> Tujuannya: T1 grid otomatis, T2 HSV adaptif yang stabil cahaya, T3 deteksi kuning-coklat dan PSI, T4 deploy Pi plus dashboard live.
> Manfaatnya untuk petani berupa panen selektif, untuk tim fuzzy berupa input PSI siap pakai, dan untuk akademik berupa baseline ringan non-deep-learning.
> Batasannya jelas: satu bed kangkung aquaponik, kamera top-down, tanpa deep learning, berjalan di CPU Raspberry Pi.
> Celah yang kami isi: gabungan grid panen 4 kali 6, adaptasi iluminasi tanpa pembelajaran mendalam, dan skor stres siap kendali dalam satu paket lapangan.\u201d

### \U0001f4c1 Bukti yang ditunjuk
- `output/ppt_asli/04_tren_5foto_asli.png` (slide 3 kanan) \u2022 kartu Tujuan/Luaran slide 4 (`output/demo/`, `output/firebase/`).

### \U0001f522 Angka kunci
- 3 rumusan masalah \u2022 4 tujuan khusus \u2022 5 foto lapangan tren liputan logis.
""", 'md-seg3'))

C.append(md("""---
## Segmen 4 \u2014 Dasar Teori Singkat (1:00) \u2502 Slide 5
**Slide:** `5/16` DASAR TEORI SINGKAT / \u201c5 Konsep Penopang Metode\u201d (sitasi dari 53 paper di `files paper/`).

### \u2705 Yang harus dijelaskan \u2014 hanya 5 kartu, satu kalimat tiap kartu
1. **Canny 1986** \u2192 deteksi tepi bed menjadi quad (29.443 sitasi).
2. **Homografi 4-titik** \u2192 warp miring menjadi tegak agar zona adil.
3. **HSV Woebbecke 1995** \u2192 hijau vs kuning/coklat (1.543 sitasi); Hue menyimpan identitas warna.
4. **EMA \u03b1=0,2** \u2192 perata temporal, menekan jitter sudut.
5. **Coverage \u2194 yield** \u2192 dasar ambang status 25/55/80% (perlu validasi ahli).
- **Kenapa bukan deep learning** (kartu bawah slide): data anotasi kecil (7 foto + video), target RPi tanpa GPU, HSV \u00b1 20\u201325 ms/frame di CPU. DL = future work.
- Ambang kesehatan: kuning sakit \u226525%, coklat sakit \u22658% (nekrosis lebih serius), dinormalkan menjadi PSI.

### \U0001f399 Naskah (\u00b1 125 kata)
> \u201cLima konsep menopang metode kami.
> Pertama, Canny tahun 1986 untuk mendeteksi tepi bed menjadi segiempat \u2014 dirujuk lebih dari 29 ribu kali.
> Kedua, homografi empat titik untuk meluruskan bed miring menjadi tampak atas, sehingga tiap zona sama besar dan adil dinilai.
> Ketiga, ruang warna HSV dari Woebbecke 1995 untuk memisahkan hijau, kuning, dan coklat; komponen Hue menyimpan identitas warna sehingga tidak kami geser.
> Keempat, perata temporal EMA alfa 0,2 untuk menstabilkan deteksi antarframe.
> Kelima, hubungan tutupan kanopi dengan hasil panen sebagai dasar ambang status 25, 55, dan 80 persen \u2014 yang masih perlu validasi ahli.
> Kami tidak memakai deep learning karena data anotasi kecil dan targetnya Raspberry Pi tanpa GPU; HSV hanya butuh sekitar 20 sampai 25 milidetik per frame di CPU. Deep learning kami catat sebagai pengembangan lanjutan.\u201d

### \U0001f4c1 Bukti yang ditunjuk
- Slide 5 (5 kartu) + folder `files paper/` (53 referensi terverifikasi OpenAlex).

### \U0001f522 Angka kunci
- Canny 1986 (29.443 sitasi) \u2022 Woebbecke 1995 (1.543) \u2022 53 paper \u2022 HSV 20\u201325 ms/frame \u2022 ambang 25/55/80 dan 25/8.
""", 'md-seg4'))
C.append(md("""---
## Segmen 5 \u2014 Arsitektur & Pipeline (1:20) \u2502 Slide 6\u20137
**Slide:** `6/16` ARSITEKTUR SISTEM / \u201cKamera > Pi (CV) > Firebase > Dashboard + Fuzzy > Pompa\u201d dan `7/16` PIPELINE CV / \u201c6 Tahap: Bed > Warp > Grid > Adaptif > Skor > Output\u201d.

### \u2705 Yang harus dijelaskan
- Lima kotak dan pemiliknya: 1 Akuisisi (saya) \u2014 kamera CSI IR 5MP ov5647 atau HP, top-down, warmup AE/AWB; 2 CV di Pi (saya); 3 Firebase (bersama) \u2014 bed_readings v1.1 tiap 10 menit, 2\u20133 KB/dok, snapshot JPEG; 4 Dashboard (saya) \u2014 heatmap 4\u00d76, grafik 24 jam, distribusi, kartu PSI, read-only multi-user; 5 Fuzzy+pompa (teman).
- **Tanpa aktuasi otomatis**: status ditulis `menunggu_acc` oleh manusia (aturan aman slide 6).
- 6 tahap pipeline (slide 7): 1\u20132 deteksi + warp (Canny > quad > homografi, fallback HSV-mask bila gagal); 3 grid 4\u00d76 (24 zona R1C1\u2013R4C6); 4 segmentasi adaptif f = mean(V)/128, Hue tetap, + EMA \u03b1=0,2; 5 skor per zona (coverage + %kuning H21\u201334 + %coklat H8\u201320 + adjacency 21\u00d721 + status + PSI); 6 output (MP4 beranotasi + CSV + JSON + payload Firebase).
- Modul identik di laptop dan Pi (`raspi/modules/`) sehingga konsisten antarjalur (selisih CLI vs live turun 9 pp \u2192 0,005 pp).

### \U0001f399 Naskah (\u00b1 170 kata)
> \u201cArsitekturnya lima kotak. Kotak satu milik saya: akuisisi kamera CSI IR 5 megapiksel atau HP, dari atas, dengan pemanasan auto-exposure.
> Kotak dua milik saya: seluruh CV di Raspberry Pi \u2014 deteksi bed, warp, grid 4 kali 6, coverage, kuning-coklat, dan PSI.
> Kotak tiga kontrak bersama: Firebase bed_readings versi 1.1, diunggah tiap 10 menit, hanya 2 sampai 3 kilobyte per dokumen plus snapshot JPEG.
> Kotak empat milik saya: dashboard web berisi heatmap 4 kali 6, grafik 24 jam, distribusi status, dan kartu PSI \u2014 read-only untuk banyak pengguna.
> Kotak lima milik teman: fuzzy membaca PSI menjadi keputusan pompa.
> Prinsip amannya: tidak ada aktuasi otomatis; setiap usulan wajib menunggu persetujuan manusia.
> Pipeline CV-nya enam tahap: deteksi bed, warp perspektif, grid 24 zona, segmentasi adaptif dengan f sama dengan rata-rata Value dibagi 128 tanpa menggeser Hue, skor per zona, lalu output berupa MP4 beranotasi, CSV timeseries, JSON ringkasan, dan payload Firebase.
> Modulnya identik di laptop dan Pi, sehingga konsisten: selisih antarjalur turun dari 9 poin persen menjadi 0,005 poin persen.\u201d

### \U0001f4c1 Bukti yang ditunjuk
- `output/ppt_asli/01_asli_vs_anotasi.jpg` (frame HP vs output, slide 7 kanan) \u2022 `docs/SKEMA_FIREBASE_BED_READINGS.md`.

### \U0001f522 Angka kunci
- 5 kotak arsitektur \u2022 6 tahap pipeline \u2022 payload 2\u20133 KB \u2022 konsistensi 9 pp \u2192 0,005 pp.
""", 'md-seg5'))

C.append(md("""---
## Segmen 6 \u2014 Metode 1 & 2 + Angka (1:40) \u2502 Slide 8\u20139
**Slide:** `8/16` METODE 1 / \u201cCanny > Quad > Homografi > Grid 4x6\u201d dan `9/16` METODE 2 / \u201cHSV Adaptif + EMA (NOVELTY)\u201d.

### \u2705 Yang harus dijelaskan \u2014 Metode 1 (slide 8)
- Input: frame miring (bed trapesium + pipa & styrofoam).
- Langkah: blur > Canny > kontur terbesar > aproksimasi 4 titik > warp ke 800\u00d7440; fallback HSV-mask + MORPH_CLOSE 25\u00d725 bila quad gagal; label BED LOST bila gagal total.
- Bukti: 18 video ter-warp otomatis; bandingkan `dataset1/bed_04_ready.jpg` vs `output/ppt_asli/02_foto_vs_segmentasi.jpg`; `output/video/preview_grid_dalam_box.png` untuk setting kamera.
- Intuisi untuk dosbing: warp membuat zona sama besar sehingga coverage adil.

### \u2705 Yang harus dijelaskan \u2014 Metode 2 / NOVELTY (slide 9)
- Masalah: HSV statis melompat pagi vs siang walau tanaman sama (komponen V berubah).
- Solusi: faktor `f = mean(V)/128` menggeser ambang S/V tiap frame; **Hue TIDAK digeser** (identitas warna tetap); + multi-threshold + EMA \u03b1=0,2.
- Analogi: ruangan gelap \u2192 ambang ikut turun.
- Angka terukur: jitter \u221253% (19,93 \u2192 9,32 px), stabilitas +38% (puncak 65%), CPU \u00b1 20\u201325 ms/frame (layak Pi).
- Regresi lolos: gate coklat kini memakai mask hijau bersih \u2192 selisih 9 pp menjadi 0,005 pp.
- Demo: Notebook S5 (statis vs adaptif 3 kondisi cahaya + grafik jitter EMA); sidang akhir: banding HSV vs ExG vs Otsu-Hue (menunggu GT).

### \U0001f399 Naskah (\u00b1 210 kata)
> \u201cMetode pertama: deteksi bed otomatis. Inputnya frame miring berisi bed trapesium, pipa, dan styrofoam.
> Langkahnya: blur, Canny, ambil kontur terbesar, aproksimasi empat titik, lalu warp ke 800 kali 440.
> Bila segiempat gagal, ada cadangan berupa HSV-mask plus morfologi; bila gagal total muncul label BED LOST.
> Delapan belas video ter-warp otomatis dengan cara ini. Tujuannya: bed menjadi tegak dan tiap zona sama besar, sehingga coverage adil dibandingkan.
> Metode kedua adalah kebaruan kami: HSV adaptif plus EMA.
> Masalahnya: ambang statis melompat antara pagi dan siang walaupun tanamannya sama, karena komponen terang berubah.
> Solusinya: faktor f sama dengan rata-rata Value dibagi 128 menggeser ambang Saturation dan Value tiap frame, tetapi Hue tidak digeser karena Hue menyimpan identitas warna daun.
> Analoginya: ruangan gelap, ambang ikut turun.
> Hasil terukurnya: jitter sudut turun 53 persen, dari 19,93 menjadi 9,32 piksel; stabilitas naik rata-rata 38 persen; dan hanya butuh sekitar 20 sampai 25 milidetik per frame sehingga layak di Pi.
> Perbaikan konsistensi membuat selisih antarjalur turun dari 9 poin persen menjadi 0,005 poin persen.
> Bukti grafiknya ada di notebook section 5; perbandingan melawan ExG dan Otsu-Hue menyusul setelah ground truth.\u201d

### \U0001f4c1 Bukti yang ditunjuk
- Slide 8 (`bed_04_ready.jpg` vs `02_foto_vs_segmentasi.jpg`) \u2022 kartu rumus slide 9 (f = mean(V)/128) \u2022 Notebook \u00a75 \u2022 `files/cek_psi.py` (regresi).

### \U0001f522 Angka kunci
- jitter \u221253% (19,93 \u2192 9,32 px) \u2022 stabilitas +38% \u2022 f = mean(V)/128 \u2022 \u03b1=0,2 \u2022 20\u201325 ms/frame \u2022 9 pp \u2192 0,005 pp \u2022 18 video.
""", 'md-seg6'))

C.append(md("""---
## Segmen 7 \u2014 Kesehatan Daun & PSI (1:00) \u2502 Slide 10
**Slide:** `10/16` KESEHATAN + PSI / \u201cKuning (H21-34) & Coklat (H8-20 + adjacency) > PSI 0-100\u201d.

### \u2705 Yang harus dijelaskan
- Definisi: persen **terhadap piksel tanaman**, bukan luas zona; kanopi < 30% = `n/a` (anti false-alarm).
- Ambang: kuning sakit \u2265 25% (klorosis), coklat sakit \u2265 8% (nekrosis lebih serius; coklat hanya valid bila menempel kanopi lewat gate adjacency 21\u00d721 \u2192 false-positive media tanam 76% \u2192 0%).
- **Rumus PSI**: `PSI = 100 \u00d7 min(1, 0,4\u00b7min(kuning/25,1) + 0,6\u00b7min(coklat/8,1))`; 0 sehat, 100 setara ambang sakit; 40 = dominan klorosis, 60 = dominan nekrosis, \u2248 0 saat bed sehat.
- Dikirim: `psi` rata-rata + `psi_maks` zona terburuk (1 zona mati hanya 1/24 rata-rata, jadi dikirim terpisah) + `psi_versi` 1.0 + `zona_sakit`.
- Tabel kanan slide dari **5 foto lapangan asli**: semuanya sehat, PSI 0\u20130,1. Rumus siap saat ada gejala; foto sakit asli menyusul via GT.
- Terminologi: PSI = Plant Stress Index, **bukan** Photosystem I.

### \U0001f399 Naskah (\u00b1 130 kata)
> \u201cKesehatan dihitung terhadap piksel tanaman, bukan luas zona; zona berkanopi di bawah 30 persen otomatis tidak dinilai agar tidak false-alarm.
> Kuning pada rentang Hue 21 sampai 34 menandai klorosis, coklat pada 8 sampai 20 menandai nekrosis \u2014 coklat hanya valid bila menempel kanopi lewat gate ketetanggaan, sehingga media tanam yang juga coklat tidak ikut terhitung.
> Keduanya dinormalkan ke ambang sakit \u2014 kuning 25 persen, coklat 8 persen \u2014 menjadi satu skor: PSI sama dengan 100 kali minimum dari 1 dan 0,4 kali kuning per 25 tambah 0,6 kali coklat per 8.
> Nol berarti sehat, 100 setara ambang sakit; 40 berarti dominan klorosis, 60 dominan nekrosis.
> Kami kirim PSI rata-rata plus PSI zona terburuk, karena satu zona mati hanya menyumbang seperdua-puluh-empat ke rata-rata.
> Tabel di kanan dari lima foto lapangan asli: semuanya sehat, PSI 0 sampai 0,1. Rumusnya siap dipakai saat ada gejala.\u201d

### \U0001f4c1 Bukti yang ditunjuk
- `output/ppt_asli/05_tabel_PSI_5foto.png` + `output/ppt_asli/02_foto_vs_segmentasi.jpg` (slide 10 kanan).

### \U0001f522 Angka kunci
- H kuning 21\u201334, H coklat 8\u201320, adjacency 21\u00d721 \u2022 ambang 25/8 \u2022 PSI 0\u2013100 (40/60) \u2022 5 foto PSI 0\u20130,1.
""", 'md-seg7'))
C.append(md("""---
## Segmen 8 \u2014 Demo: Deploy Pi + Hasil Utama (1:30) \u2502 Slide 11\u201312
**Slide:** `11/16` DEPLOY PI + DASHBOARD / \u201cPi 4B + CSI IR 5MP + Firebase + Web \u2014 test OK, tinggal burn-in\u201d dan `12/16` HASIL UTAMA / \u201cFrame HP vs Output + Timeseries 763 Frame\u201d.

### \u2705 Yang harus dijelaskan \u2014 Deploy (slide 11)
- Terverifikasi: Pi 4B Debian 13, opencv 4.10, kamera libcamera OK, `kangkung_pi.py --test` [OK].
- Siklus 10 menit: capture \u2192 analisis 960px \u2192 payload 2\u20133 KB \u2192 Firestore \u2192 snapshot JPEG \u2192 outbox offline.
- Aman: thermal tunda > 75\u00b0C, Tailscale SSH, systemd auto-start setelah reboot.
- Dashboard: heatmap 4\u00d76 + grafik 24 jam (144 dok) + distribusi + kartu PSI (tinggi = stres).
- **Jujur belum:** kasing/box kamera \u2192 uji penuh + burn-in 24 jam outdoor. Gambar box = **RENDER CAD, bukan foto fisik** (`hardware/renders/preview_rakit_iso.png`).

### \u2705 Yang harus dijelaskan \u2014 Hasil + PUTAR VIDEO (slide 12)
- Tunjuk `output/ppt_asli/01_asli_vs_anotasi.jpg`: quad + grid berwarna + HUD + distribusi 24 zona.
- **Putar 30 detik** `output/demo/IMG_5159_beranotasi.mp4` langsung dari folder (jangan embed file 60 MB ke PPT).
- Tunjuk `output/ppt_asli/03_timeseries_IMG5159.png` (timeseries 763 frame) + `output/demo/demo_dua_video.png`.
- Bandingkan dua bed: IMG_5159 cov 49,6% (763 frame) vs IMG_5388 cov 58,4% (425 frame) \u2014 bed kedua lebih lebat.

### \U0001f399 Naskah (\u00b1 195 kata)
> \u201cPaket deploy Raspberry Pi sudah terverifikasi: Pi 4B, kamera CSI IR 5 megapiksel terbaca lewat libcamera, dan uji mandiri lolos.
> Siklusnya tiap 10 menit: capture, analisis, kirim payload 2 sampai 3 kilobyte ke Firestore, plus snapshot JPEG, dengan antrean offline bila koneksi putus.
> Pengamannya: tunda capture bila suhu di atas 75 derajat, remote via Tailscale, dan service otomatis jalan setelah reboot.
> Dashboard web menampilkan heatmap 4 kali 6, grafik 24 jam, distribusi status, dan kartu PSI.
> Yang jujur belum: kasing kamera \u2014 gambar di kanan adalah render CAD, bukan foto fisik \u2014 sehingga uji penuh dan burn-in 24 jam outdoor menunggu kasing.
> Sekarang buktinya. Kiri adalah frame HP, kanan output pipeline: segiempat bed, grid berwarna, dan HUD.
> Saya putar 30 detik video beranotasinya \u2026 Terlihat grid mengikuti bed dan status tiap zona berubah konsisten.
> Grafik di bawah adalah timeseries 763 frame video pertama dengan coverage global 49,6 persen.
> Bed kedua lebih lebat: 58,4 persen dari 425 frame. Tren lima foto dari seedling sampai ready juga logis, tanpa foto buatan.\u201d

### \U0001f4c1 Bukti yang ditunjuk
- `hardware/renders/preview_rakit_iso.png` (label RENDER) \u2022 `output/demo/IMG_5159_beranotasi.mp4` (putar 30 dtk) \u2022 `output/ppt_asli/01_asli_vs_anotasi.jpg`, `03_timeseries_IMG5159.png` \u2022 `output/demo/demo_dua_video.png`.

### \U0001f522 Angka kunci
- 10 menit/siklus \u2022 payload 2\u20133 KB \u2022 49,6% (763 frame) vs 58,4% (425 frame) \u2022 18 video.
""", 'md-seg8'))

C.append(md("""---
## Segmen 9 \u2014 Hasil Kesehatan & Evaluasi (1:00) \u2502 Slide 13\u201314
**Slide:** `13/16` HASIL KESEHATAN / \u201c5 Foto Lapangan: Semua Sehat (PSI 0-0,1)\u201d dan `14/16` EVALUASI & RENCANA / \u201cSUDAH vs BELUM\u201d.

### \u2705 Yang harus dijelaskan
- Fakta lapangan (slide 13): 5 foto bed_01..05 \u2192 kuning 0%, coklat \u2248 0%, 0 zona sakit, PSI 0\u20130,1; konsisten visual (bed hijau sehat di foto = sehat di algoritma, tanpa false sakit).
- **Kalimat kejujuran \u2014 WAJIB diucapkan kata-per-kata:** \u201cSemua gambar di presentasi ini adalah foto/video lapangan asli dan output langsung pipeline. Uji blob injeksi dan gambar dummy sintetis hanya verifikasi fungsi dan saya simpan di appendix \u2014 bukan klaim akurasi lapangan. Akurasi lapangan (F1/IoU) menyusul setelah ground truth 5 gambar akhir September.\u201d
- Slide 14: SUDAH (18 video, jitter \u221253%, kesehatan tepat zona, Pi test OK, Firebase v1.1, dashboard, 53 paper, STL siap) vs BELUM + kapan (GT 5 gambar + F1/IoU Sep; banding metode Sep; validasi ambang Okt; burn-in 24 jam Okt; Bab 4\u20135 Nov).
- Tool siap tinggal eksekusi: `buat_gt.py` (45\u201360 menit) \u2192 `evaluasi_segmentasi.py` \u2192 `bandingkan_metode.py`; target F1 0,85\u20130,95.
- Risiko + mitigasi: hujan \u2192 fallback + shield; panas \u2192 guard + heatsink; offline \u2192 outbox.

### \U0001f399 Naskah (\u00b1 135 kata)
> \u201cLima foto lapangan dari seedling sampai ready semuanya sehat: kuning nol persen, coklat mendekati nol, nol zona sakit, PSI 0 sampai 0,1.
> Artinya konsisten visual: bed yang hijau sehat di foto juga sehat menurut algoritma, tanpa false sakit.
> Yang belum ada: foto sakit asli di kebun \u2014 saat pengambilan semua bed memang sehat \u2014 sehingga ground truth dan foto sakit masuk rencana.
> [BACA KALIMAT KEJUJURAN]
> Posisi kami jujur: sempro membuktikan pipeline jalan; sidang akhir membuktikan angka akurasi.
> Yang sudah: 18 video, jitter minus 53 persen, kesehatan tepat zona, Pi test OK, skema Firebase 1.1, dashboard, 53 paper, dan desain box siap cetak.
> Yang belum terjadwal: ground truth dan F1/IoU September, perbandingan metode September, validasi ambang dan burn-in 24 jam Oktober, Bab 4 dan 5 November.
> Alatnya siap, tinggal eksekusi: anotasi 45 sampai 60 menit lalu evaluasi.\u201d

### \U0001f4c1 Bukti yang ditunjuk
- `output/ppt_asli/04_tren_5foto_asli.png` + `05_tabel_PSI_5foto.png` \u2022 kartu SUDAH/BELUM slide 14 \u2022 `files/buat_gt.py`.

### \U0001f522 Angka kunci
- 5 foto: kuning 0%, PSI 0\u20130,1 \u2022 GT 5 gambar \u2192 F1 target 0,85\u20130,95 \u2022 anotasi 45\u201360 menit.
""", 'md-seg9'))

C.append(md("""---
## Segmen 10 \u2014 Timeline, Penutup & Mohon Arahan (1:10) \u2502 Slide 15\u201316
**Slide:** `15/16` TIMELINE / \u201cSEMPRO > KELULUSAN (NOV 2026)\u201d dan `16/16` PENUTUP / \u201cKESIMPULAN + MOHON ARAHAN\u201d.

### \u2705 Yang harus dijelaskan
- Timeline 5 kartu (slide 15): SEP = GT + F1/IoU + banding metode; OKT AWAL = validasi ambang + Firebase Tahap B; OKT AKHIR = lapangan + burn-in 24 jam; NOV AWAL = Bab 4\u20135 + revisi; NOV MID = video 2 menit + final \u2192 SIDANG.
- Kriteria lulus prototipe: burn-in 24 jam \u2265 140 siklus OK + F1/IoU terukur + box tercetak.
- Kumpulkan dari sekarang: mask GT, log burn-in, screenshot 24 jam, video 2 menit, STL tercetak.
- Kesimpulan (slide 16): CV per zona jalan end-to-end, stabil lintas cahaya, kesehatan + PSI tepat zona, Pi + dashboard siap burn-in.
- **4 mohon arahan (ucapkan sebagai pertanyaan, bukan pernyataan):** (1) ambang 25/55/80% cukup justifikasi paper atau wajib validasi petani/ahli? (2) prototipe cukup laptop + webcam atau wajib RasPi outdoor? (3) Bab 3 perlu UML lengkap atau cukup diagram alir + arsitektur? (4, bersama teman) rule ganti-air dan membership fuzzy siapa yang menetapkan \u2014 ganti air berisiko bagi bakteri nitrifikasi dan ikan.
- Transisi: \u201cDemikian bagian CV. Selanjutnya teman saya: kontrol fuzzy + pompa. Terima kasih.\u201d + repo `github.com/FIllxe/kangkung-cv-aquaponik`.

### \U0001f399 Naskah (\u00b1 150 kata)
> \u201cTarget kami akhir November. September: ground truth, F1/IoU, dan perbandingan metode.
> Awal Oktober: validasi ambang dan Firebase tahap B. Akhir Oktober: uji lapangan dan burn-in 24 jam.
> Awal November: Bab 4, Bab 5, dan revisi. Pertengahan November: video 2 menit dan final menuju sidang.
> Kriteria lulusnya: burn-in 24 jam dengan minimal 140 siklus OK, F1 dan IoU terukur, dan box tercetak.
> Kesimpulannya: CV per zona berjalan end-to-end, stabil lintas cahaya, kesehatan dan PSI tepat zona, dan Pi plus dashboard siap burn-in.
> Mohon arahan Bapak/Ibu, empat hal: pertama, ambang 25, 55, 80 persen \u2014 cukup justifikasi paper atau wajib validasi petani dan ahli?
> Kedua, prototipe cukup laptop plus webcam atau wajib Raspberry Pi outdoor?
> Ketiga, Bab 3 perlu UML lengkap atau cukup diagram alir dan arsitektur?
> Keempat, bersama teman saya: apakah ganti air respons yang tepat untuk klorosis, dan siapa menetapkan membership fuzzy-nya?
> Demikian bagian Computer Vision. Selanjutnya teman saya menjelaskan kontrol fuzzy dan pompa. Terima kasih.\u201d

### \U0001f4c1 Bukti yang ditunjuk
- Slide 15 (5 kartu timeline) \u2022 slide 16 (kartu antisipasi + repo + transisi) \u2022 `docs/LAPORAN_PROGRES_BIMBINGAN.md` (print 1\u20132 lembar sebagai lampiran video).

### \U0001f522 Angka kunci
- Akhir Nov 2026 \u2022 burn-in \u2265 140 siklus/24 jam \u2022 4 mohon arahan.
""", 'md-seg10'))
C.append(md("""---
## \U0001f50d Checker Bukti (jalankan sekali sebelum merekam)
Sel code berikut memverifikasi setiap file bukti yang disebut naskah benar-benar ada di repo.
Semua baris harus `[OK]`; bila ada `[HILANG]`, perbaiki path atau siapkan file pengganti sebelum merekam.
""", 'md-check'))

C.append(code("""import os
from pathlib import Path
ROOT = Path.cwd()
if (ROOT / 'notebooks' / 'buat_naskah_presentasi.py').exists():
    pass
elif (ROOT.parent / 'notebooks' / 'buat_naskah_presentasi.py').exists():
    ROOT = ROOT.parent
else:
    raise SystemExit('Jalankan dari root repo atau dari folder notebooks/')
BUKTI = [
    'dataset1/bed_04_ready.jpg',
    'docs/SKEMA_FIREBASE_BED_READINGS.md',
    'docs/LAPORAN_PROGRES_BIMBINGAN.md',
    'docs/DRAFT_PPT_SEMPRO_Bagian_CV_v2_ASLI.pptx',
    'notebooks/presentasi_kangkung_cv.ipynb',
    'output/ppt_asli/01_asli_vs_anotasi.jpg',
    'output/ppt_asli/02_foto_vs_segmentasi.jpg',
    'output/ppt_asli/03_timeseries_IMG5159.png',
    'output/ppt_asli/04_tren_5foto_asli.png',
    'output/ppt_asli/05_tabel_PSI_5foto.png',
    'output/demo/IMG_5159_beranotasi.mp4',
    'output/demo/demo_dua_video.png',
    'output/demo/ringkasan_IMG_5159.json',
    'output/demo/IMG_5159_timeseries.csv',
    'hardware/renders/preview_rakit_iso.png',
    'files/buat_gt.py',
    'files/cek_psi.py',
]
gagal = 0
for b in BUKTI:
    ok = (ROOT / b).exists()
    gagal += (not ok)
    print(('[OK]     ' if ok else '[HILANG] ') + b)
print()
print('HASIL: semua bukti ada' if gagal == 0 else f'HASIL: {gagal} bukti HILANG - perbaiki dulu')
""", 'code-check'))

C.append(md("""---
## \U0001f4ce Lampiran A \u2014 Daftar Angka yang Dihafal
- \u221253% jitter sudut (19,93 \u2192 9,32 px) \u2022 stabilitas +38% (puncak 65%)
- 49,6% cov global IMG_5159 (763 frame) vs 58,4% IMG_5388 (425 frame)
- 18 video lapangan \u2022 5 foto asli (seedling \u2192 ready) \u2022 24 zona (4\u00d76)
- Ambang status 25/55/80% \u2022 ambang kesehatan kuning 25% / coklat 8%
- f = mean(V)/128 \u2022 EMA \u03b1=0,2 \u2022 H kuning 21\u201334, H coklat 8\u201320, adjacency 21\u00d721
- PSI 0\u2013100 (40 = dominan klorosis, 60 = dominan nekrosis, \u2248 0 saat sehat)
- Payload 2\u20133 KB/dok \u2022 upload 1\u00d7/10 menit \u2022 stale > 30 menit \u2022 cooldown 60 menit
- Burn-in 24 jam \u2265 140 siklus OK \u2022 GT 5 gambar (anotasi 45\u201360 menit) \u2192 target F1 0,85\u20130,95
- Konsistensi antarjalur 9 pp \u2192 0,005 pp \u2022 HSV 20\u201325 ms/frame
- Canny 1986 (29.443 sitasi) \u2022 Woebbecke 1995 (1.543) \u2022 53 paper

## \U0001f4ce Lampiran B \u2014 Jawaban Q&A (di balik video, hafalkan)
- **Akurasi?** \u2192 Tool evaluasi siap (P/R/F1/IoU + 2 metode pembanding); mask GT dikerjakan, angka final akhir Sep. Terukur kini: jitter \u221253%, tren 5 foto logis, 5 foto sehat PSI 0\u20130,1 tanpa false sakit.
- **Foto sakit asli mana?** \u2192 Belum ada di kebun (semua bed sehat saat pengambilan). Rumus PSI siap; GT + foto sakit masuk rencana.
- **Panel injeksi/dummy kemarin?** \u2192 Itu uji fungsi di appendix, bukan bukti lapangan; sudah dikeluarkan dari badan presentasi.
- **Kenapa bukan DL?** \u2192 Data kecil, RPi tanpa GPU, HSV 20\u201325 ms/frame. DL = future work.
- **Output petani?** \u2192 Peta 24 zona + status kesehatan + rekomendasi teks + timeseries; ke dashboard + fuzzy.
- **Kapan selesai?** \u2192 Akhir Nov: Sep GT, Okt lapangan + burn-in, Nov laporan + sidang.
- **Ganti air untuk klorosis?** \u2192 Dibahas bersama teman + dosen (risiko bakteri nitrifikasi/ikan); sementara butuh ACC manusia.

## \U0001f4ce Lampiran C \u2014 Checklist H-1 Merekam
- [ ] Jalankan sel Checker Bukti di atas \u2192 semua `[OK]`.
- [ ] Ganti semua `[NAMA]`, `[NIM]`, `[NAMA TEMAN]` di naskah.
- [ ] Tes offline 30 frame: `python proses_video.py ..\\data\\videos\\IMG_5159.MOV --adaptive --max-frames 30 --no-gui --save --out-dir ..\\output\\evaluasi` (dijalankan dari `files/`).
- [ ] Siapkan MP4 30-detik + `output/ppt_asli/` + 1 JSON ringkasan + screenshot dashboard di laptop rekaman.
- [ ] Internet cadangan: hotspot HP + screenshot dashboard offline + video lokal.
- [ ] Print `docs/LAPORAN_PROGRES_BIMBINGAN.md` 1\u20132 lembar sebagai lampiran.
- [ ] Baca keras seluruh naskah sekali (\u00b110 menit) \u2192 tandai bagian yang terbata-bata, sederhanakan.
""", 'md-lamp'))

NB = {
    'cells': C,
    'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': '3.12.2', 'file_extension': '.py',
                          'mimetype': 'text/x-python', 'nbconvert_exporter': 'python',
                          'pygments_lexer': 'ipython3',
                          'codemirror_mode': {'name': 'ipython', 'version': 3}},
    },
    'nbformat': 4,
    'nbformat_minor': 5,
}
OUT.write_text(json.dumps(NB, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'OK -> {OUT} ({len(C)} sel)')
