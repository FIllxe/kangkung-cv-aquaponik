"""Generator draft PPT Sempro — Bagian Computer Vision (16:9).
Jalankan: python docs/buat_ppt_sempro_all.py
Output: docs/DRAFT_PPT_SEMPRO_Bagian_CV_v2_ASLI.pptx
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PPT_SEMPRO_Bagian_CV_v2_ASLI.pptx"

HIJAU_TUA = RGBColor(0x1B, 0x5E, 0x20)
HIJAU = RGBColor(0x2E, 0x7D, 0x32)
HIJAU_MUDA = RGBColor(0xE8, 0xF5, 0xE9)
AKSEN = RGBColor(0x66, 0xBB, 0x6A)
ABU = RGBColor(0x42, 0x42, 0x42)
ABU_MUDA = RGBColor(0x75, 0x75, 0x75)
PUTIH = RGBColor(0xFF, 0xFF, 0xFF)
KUNING_BG = RGBColor(0xFF, 0xF8, 0xE1)
BIRU_BG = RGBColor(0xE3, 0xF2, 0xFD)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 16
SLIDES = []

def bg(slide, color=PUTIH):
    f = slide.background.fill
    f.solid(); f.fore_color.rgb = color

def header_bar(slide, kicker, judul, sub=""):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.35))
    shp.line.fill.background()
    shp.fill.solid(); shp.fill.fore_color.rgb = HIJAU_TUA
    tx = shp.text_frame; tx.word_wrap = True
    p1 = tx.paragraphs[0]; p1.text = kicker; p1.alignment = PP_ALIGN.LEFT
    r = p1.runs[0]; r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = AKSEN
    p2 = tx.add_paragraph(); p2.text = judul; p2.alignment = PP_ALIGN.LEFT
    r = p2.runs[0]; r.font.size = Pt(26); r.font.bold = True; r.font.color.rgb = PUTIH
    if sub:
        p3 = tx.add_paragraph(); p3.text = sub; p3.alignment = PP_ALIGN.LEFT
        r = p3.runs[0]; r.font.size = Pt(13); r.font.color.rgb = PUTIH
    box = slide.shapes.add_textbox(prs.slide_width - Inches(1.2), prs.slide_height - Inches(0.45), Inches(1.0), Inches(0.35))
    box.text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT

def nomor(slide, n):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.paragraphs[0].alignment == PP_ALIGN.RIGHT:
            sh.text_frame.paragraphs[0].text = f"{n}/{TOTAL}"
            sh.text_frame.paragraphs[0].runs[0].font.size = Pt(10)
            sh.text_frame.paragraphs[0].runs[0].font.color.rgb = ABU_MUDA

def bullets(slide, left, top, width, height, items, size=15):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame; tf.word_wrap = True
    for i, (jd, isi) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(8); p.space_before = Pt(2)
        r = p.add_run(); r.text = "\u2022 " + jd
        r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = HIJAU_TUA
        if isi:
            r2 = p.add_run(); r2.text = " \u2014 " + isi
            r2.font.size = Pt(size); r2.font.bold = False; r2.font.color.rgb = ABU
    return box

def kartu(slide, left, top, width, height, judul, isi, bgc=HIJAU_MUDA):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    s.line.fill.background(); s.fill.solid(); s.fill.fore_color.rgb = bgc
    tf = s.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = judul; r.font.size = Pt(15); r.font.bold = True; r.font.color.rgb = HIJAU_TUA
    p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run(); r2.text = isi; r2.font.size = Pt(13); r2.font.color.rgb = ABU
    return s

def add_img(slide, rel, left, top, width, height):
    p = ROOT / rel
    if not p.exists():
        b = slide.shapes.add_textbox(left, top, width, height)
        b.text_frame.word_wrap = True
        b.text_frame.paragraphs[0].text = f"[Gambar belum ada: {rel}]"
        return
    slide.shapes.add_picture(str(p), left, top, width=width, height=height)

def notes(slide, teks):
    slide.notes_slide.placeholders[1].text = teks

def new_slide(kicker, judul, sub=""):
    s = prs.slides.add_slide(BLANK)
    bg(s); header_bar(s, kicker, judul, sub)
    nomor(s, len(SLIDES) + 1)
    SLIDES.append(s)
    return s
# === SLIDE 1-4 ===
s = new_slide("SIDANG SEMINAR PROPOSAL (SEMPRO) \u2022 CAPSTONE", "Sistem Computer Vision Deteksi Kesiapan Panen", "Kangkung Aquaponik \u2014 Bed 2 m x 1,1 m, Grid 4x6 | Bagian: Computer Vision (Panen + Kesehatan + PSI + Pi + Dashboard)")
bullets(s, Inches(0.5), Inches(1.7), Inches(6.3), Inches(4.5), [
    ("Judul lengkap", "Segmentasi HSV Adaptif + Indeks Stres PSI untuk bed aquaponik"),
    ("Tim 2 orang", "Nama 1 (CV, saya) + Nama 2 (Fuzzy/IoT pompa & ESP32)"),
    ("Reusable", "Satu file dipakai Sempro > Kemajuan > Kelulusan (slide TODO jadi HASIL)"),
    ("Demo hidup", "Video beranotasi + dashboard web + (opsional) live Pi via Tailscale"),
])
kartu(s, Inches(7.3), Inches(1.7), Inches(5.5), Inches(1.6), "Pesan 30 detik", "Bed difoto > grid 4x6 berwarna > tiap zona tahu: belum/hampir/siap/harus panen + sehat/sakit.")
add_img(s, "dataset1/bed_04_ready.jpg", Inches(7.3), Inches(3.5), Inches(5.5), Inches(3.1))
notes(s, "NASKAH 1 mnt: Bed 2x1,1 m dibagi 24 zona. Kamera memotret, sistem memberi peta kesiapan panen + kesehatan daun ke dashboard dan ke kontroler fuzzy teman saya. Hari ini saya bahas bagian Computer Vision.")

s = new_slide("BAGIAN SAYA vs TEMAN \u2022 SLIDE WAJIB SEMPRO", "Pembagian Tugas Tim (2 Orang)", "Penguji harus tahu persis mana kontribusi kamu")
kartu(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(2.5), "BAGIAN SAYA \u2014 CV + Deploy (hari ini)", "Pipeline CV, HSV adaptif + EMA, kuning/coklat, PSI 0-100, payload Firebase v1.1, paket RasPi + CSI, dashboard read-only")
kartu(s, Inches(6.9), Inches(1.7), Inches(5.9), Inches(2.5), "BAGIAN TEMAN \u2014 Fuzzy + IoT (teman)", "Rule base fuzzy, ESP32 + pompa, keputusan_fuzzy, ACC manager + audit, validasi agronomi", bgc=KUNING_BG)
bullets(s, Inches(0.5), Inches(4.5), Inches(12.3), Inches(2.5), [
    ("Kontrak antar-tim", "fuzzy_input {psi, psi_maks, zona_sakit, psi_versi}: saya produsen, teman konsumen."),
    ("Aturan aman", "Stale >30 mnt ditolak, null = tahan tindakan, ACC manusia wajib, anti-spam 60 mnt."),
])
notes(s, "NASKAH 1 mnt: Saya hitung PSI, teman memakai untuk keputusan pompa dengan pengaman ACC manusia.")

s = new_slide("LATAR BELAKANG \u2022 KENAPA PENTING", "Petani Sulit Menilai 24 Zona Bed Konsisten", "Terlalu dini = rugi biomassa, terlambat = mutu turun, kuning/coklat telat sadar")
bullets(s, Inches(0.5), Inches(1.7), Inches(6.3), Inches(4.8), [
    ("Fakta lapangan", "Bed tidak seragam: tepi vs tengah beda. Penilaian mata subjektif dan melelahkan."),
    ("Cahaya berubah", "Pagi/siang/sore + bayangan membuat HSV statis gagal (coverage lompat)."),
    ("Rumusan masalah", "1) Panen per zona otomatis? 2) Stabil cahaya? 3) Kuning/coklat + skor stres utk fuzzy?"),
    ("Batasan", "Kangkung aquaponik 1 bed, kamera top-down, tanpa deep learning, jalan di Pi CPU."),
])
kartu(s, Inches(7.3), Inches(1.7), Inches(5.5), Inches(1.4), "Research gap", "Sedikit yang gabung: grid panen per zona + adaptasi cahaya + skor siap-fuzzy + deploy Pi outdoor.")
add_img(s, "output/ppt_asli/04_tren_5foto_asli.png", Inches(7.3), Inches(3.3), Inches(5.5), Inches(3.3))
notes(s, "NASKAH 1,5 mnt: Bed tidak seragam sehingga butuh peta 24 zona, bukan satu angka. Cahaya berubah adalah musuh utama.")

s = new_slide("TUJUAN & LUARAN \u2022 YANG DINILAI", "Tujuan Umum > Khusus > Luaran Terukur", "Setiap tujuan punya bukti file, tanpa klaim kosong")
bullets(s, Inches(0.5), Inches(1.7), Inches(6.3), Inches(4.8), [
    ("Tujuan umum", "Prototipe sensor tanaman otomatis: peta panen + kesehatan per zona."),
    ("Tujuan khusus CV", "T1 grid otomatis, T2 HSV adaptif stabil cahaya, T3 kuning/coklat + PSI, T4 Pi + dashboard live."),
    ("Luaran", "MP4 beranotasi + CSV + JSON + payload Firebase + dashboard + box kamera 3D-print."),
    ("Lulus prototipe", "Burn-in 24 jam: >=140/144 siklus OK, suhu <70C, snapshot terbaca, antrean terkirim."),
])
kartu(s, Inches(7.3), Inches(1.7), Inches(5.5), Inches(1.5), "Manfaat", "Petani: panen selektif. Tim fuzzy: input PSI siap pakai. Akademik: baseline ringan non-DL.")
kartu(s, Inches(7.3), Inches(3.4), Inches(5.5), Inches(1.5), "Sempro vs akhir", "Sempro: pipeline jalan. Akhir: tambah F1/IoU vs GT + banding HSV/ExG/Otsu + validasi ambang.")
notes(s, "NASKAH 1 mnt: Sempro = bukti pipeline jalan. Sidang akhir = bukti angka akurasi + uji lapangan 24 jam.")
# === SLIDE 5-8 ===
s = new_slide("DASAR TEORI SINGKAT \u2022 HANYA YANG DIPAKAI", "5 Konsep Penopang Metode", "Sitasi dari 53 paper terverifikasi OpenAlex di files paper/")
for i, (j, isi) in enumerate([
    ("1. Canny 1986", "Deteksi tepi bed > quad"),
    ("2. Homografi", "Warp miring > tegak"),
    ("3. HSV Woebbecke", "Hijau vs kuning/coklat"),
    ("4. EMA a=0,2", "Stabil temporal"),
    ("5. Cover<>yield", "Ambang 25/55/80%"),
]):
    kartu(s, Inches(0.5 + i * 2.55), Inches(1.7), Inches(2.35), Inches(1.8), j, isi)
bullets(s, Inches(0.5), Inches(3.8), Inches(12.3), Inches(3.0), [
    ("Kenapa bukan deep learning?", "Data anotasi kecil (7 foto+video), target RPi tanpa GPU, HSV ~20-25 ms/frame. DL = future work."),
    ("Ambang status", "belum <25%, hampir 25-55%, siap 55-80%, harus >80% (perlu validasi ahli)."),
    ("Ambang kesehatan", "kuning sakit >=25%, coklat sakit >=8% (nekrosis lebih serius), dinormalkan jadi PSI."),
])
notes(s, "NASKAH 1 mnt: Tekankan Canny + Woebbecke dan alasan non-DL: data kecil + hardware CPU.")

s = new_slide("ARSITEKTUR SISTEM \u2022 POSISI BAGIAN SAYA", "Kamera > Pi (CV) > Firebase > Dashboard + Fuzzy > Pompa", "Hijau = saya, biru = dashboard, kuning = teman")
kartu(s, Inches(0.5), Inches(1.7), Inches(3.7), Inches(1.6), "1. AKUISISI (saya)", "Kamera CSI IR 5MP ov5647 / HP, top-down, warmup AE/AWB")
kartu(s, Inches(4.5), Inches(1.7), Inches(3.7), Inches(1.6), "2. CV di RASPI (saya)", "Deteksi bed > warp > grid 4x6 > coverage + kuning/coklat + PSI")
kartu(s, Inches(8.5), Inches(1.7), Inches(3.9), Inches(1.6), "3. FIREBASE (bersama)", "bed_readings v1.1 tiap 10 mnt, 2-3 KB/dok, snapshot JPEG")
kartu(s, Inches(0.5), Inches(3.6), Inches(6.0), Inches(1.6), "4. DASHBOARD (saya)", "Heatmap 4x6, grafik 24 jam, distribusi, kartu PSI. Read-only multi-user.", bgc=BIRU_BG)
kartu(s, Inches(6.9), Inches(3.6), Inches(5.9), Inches(1.6), "5. FUZZY + POMPA (teman)", "Baca PSI > keputusan_fuzzy > ACC manusia > ESP32 pompa", bgc=KUNING_BG)
bullets(s, Inches(0.5), Inches(5.5), Inches(12.3), Inches(1.5), [
    ("Kontrak aman", "Tidak ada aktuasi otomatis. Status wajib menunggu_acc saat ditulis."),
])
notes(s, "NASKAH 1 mnt: Saya pemilik kotak 1,2,4. Teman kotak 5. Kotak 3 kontrak bersama.")

s = new_slide("PIPELINE CV \u2022 INTI BAGIAN SAYA", "6 Tahap: Bed > Warp > Grid > Adaptif > Skor > Output", "Modul identik di laptop & Pi (raspi/modules/)")
bullets(s, Inches(0.5), Inches(1.7), Inches(5.8), Inches(5.0), [
    ("1-2. Deteksi + warp", "Canny > quad > homografi (fallback HSV-mask bila gagal)."),
    ("3. Grid 4x6", "24 zona R1C1-R4C6 dianalisis terpisah."),
    ("4. Segmentasi adaptif", "f = mean(V)/128 geser S/V; Hue tetap. + EMA a=0,2."),
    ("5. Skor per zona", "coverage + %kuning (H21-34) + %coklat (H8-20 + adjacency 21x21) + status + PSI."),
    ("6. Output", "MP4 beranotasi + CSV + JSON + payload Firebase 2-3 KB."),
])
add_img(s, "output/ppt_asli/01_asli_vs_anotasi.jpg", Inches(6.7), Inches(1.7), Inches(6.1), Inches(5.0))
notes(s, "NASKAH 1,5 mnt: Modul sama di laptop dan Pi sehingga konsisten (selisih 0,005 pp setelah perbaikan gate).")

s = new_slide("METODE 1 \u2022 DETEKSI BED OTOMATIS", "Canny > Quad > Homografi > Grid 4x6", "File: files/adaptive_bed.py, Notebook S4")
bullets(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.0), [
    ("Input", "Frame miring: bed trapesium + pipa & styrofoam."),
    ("Langkah", "Blur > Canny > kontur terbesar > approx 4 titik > warp ke 800x440."),
    ("Fallback", "Bila quad gagal: HSV-mask + MORPH_CLOSE 25x25."),
    ("Output", "Bed tegak + grid berwarna + HUD. Label BED LOST bila gagal."),
    ("Bukti", "18 video ter-warp otomatis; preview_grid_dalam_box.png utk setting kamera."),
])
add_img(s, "dataset1/bed_04_ready.jpg", Inches(6.9), Inches(1.7), Inches(2.8), Inches(2.4))
add_img(s, "output/ppt_asli/02_foto_vs_segmentasi.jpg", Inches(9.9), Inches(1.7), Inches(2.9), Inches(2.4))
kartu(s, Inches(6.9), Inches(4.4), Inches(6.0), Inches(1.6), "Tips kamera (sidang prototipe)", "Bed >=12% frame, hindari pantulan (v_hi<=110), pipa jangan tutupi bed.")
notes(s, "NASKAH 1 mnt: Warp membuat zona sama besar sehingga coverage adil.")
# === SLIDE 9-12 ===
s = new_slide("METODE 2 \u2022 HSV ADAPTIF + EMA (NOVELTY)", "f = mean(V)/128 \u2014 Stabil Lintas Cahaya", "Hasil: jitter 19,93>9,32 px (-53%), stabilitas +38% (puncak 65%)")
bullets(s, Inches(0.5), Inches(1.7), Inches(6.3), Inches(5.0), [
    ("Masalah", "HSV statis lompat pagi vs siang walau tanaman sama (V berubah)."),
    ("Solusi", "f geser ambang S/V tiap frame; Hue TIDAK digeser. + multi-threshold + EMA a=0,2."),
    ("Angka terukur", "Jitter -53%, stabilitas +38%, CPU ~20-25 ms/frame (layak Pi)."),
    ("Regresi lolos", "Gate coklat pakai mask bersih: selisih jalur 9 pp > 0,005 pp."),
    ("Demo", "Notebook S5: statis vs adaptif 3 cahaya + grafik jitter EMA."),
])
kartu(s, Inches(7.3), Inches(1.7), Inches(5.5), Inches(1.6), "Rumus inti", "f = mean(V)/128, S'=S*f, V'=V*f (H tetap)")
kartu(s, Inches(7.3), Inches(3.5), Inches(5.5), Inches(1.6), "Kenapa penguji suka", "Masalah > solusi > angka > bukti file. Ini novelty utama.")
kartu(s, Inches(7.3), Inches(5.3), Inches(5.5), Inches(1.4), "Next (sidang akhir)", "Banding vs ExG vs Otsu-Hue (menunggu GT).")
notes(s, "NASKAH 1,5 mnt: Intuisi: ruangan gelap maka ambang ikut turun. Hafalkan 53% dan 38%.")

s = new_slide("KESEHATAN + PSI \u2022 JEMBATAN KE FUZZY", "Kuning (H21-34) & Coklat (H8-20 + adjacency) > PSI 0-100", "Kanopi <30% = n/a anti false-alarm. File: hitung_psi(), fuzzy_export.py")
bullets(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.0), [
    ("Definisi", "% thd piksel TANAMAN (bukan luas zona)."),
    ("Ambang", "kuning sakit >=25%, coklat sakit >=8% (nekrosis lebih serius)."),
    ("PSI = 100*min(1, 0.4*min(K/25,1)+0.6*min(C/8,1))", "0 sehat, 100 setara ambang sakit. 40=klorosis, 60=nekrosis."),
    ("Dikirim", "psi rata-rata + psi_maks zona terburuk + psi_versi 1.0 + zona_sakit."),
    ("Kenapa psi_maks?", "1 zona mati = 1/24 rata-rata, bahaya lokal hilang tanpa field ini."),
])
add_img(s, "output/ppt_asli/05_tabel_PSI_5foto.png", Inches(6.9), Inches(1.7), Inches(5.9), Inches(2.3))
add_img(s, "output/ppt_asli/02_foto_vs_segmentasi.jpg", Inches(6.9), Inches(4.2), Inches(5.9), Inches(2.6))
notes(s, "NASKAH 1,5 mnt: Tabel PSI di kanan dari 5 foto lapangan asli (semuanya sehat, PSI 0-0,1). Rumus PSI siap dipakai saat ada gejala. Data sakit asli menyusul via GT.")

s = new_slide("DEPLOY PI + DASHBOARD \u2022 PROTOTIPE NYATA", "Pi 4B + CSI IR 5MP + Firebase + Web \u2014 test OK, tinggal burn-in", "raspi/README, config.json, systemd user service, web/ tanpa build")
bullets(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(5.0), [
    ("Terverifikasi", "Pi 4B Debian 13, opencv 4.10, kamera libcamera OK, kangkung_pi.py --test [OK]."),
    ("Siklus 10 mnt", "capture > analisis 960px > payload 2-3 KB > Firestore > snapshot JPEG > outbox offline."),
    ("Aman", "Thermal tunda >75C, Tailscale SSH, systemd auto-start setelah reboot."),
    ("Dashboard", "Heatmap 4x6 + grafik 24 jam (144 dok) + distribusi + kartu PSI (tinggi=stres)."),
    ("Jujur belum", "Kasing/box kamera > uji penuh + burn-in 24 jam outdoor."),
])
add_img(s, "hardware/renders/preview_rakit_iso.png", Inches(6.9), Inches(1.7), Inches(5.9), Inches(2.6))
kartu(s, Inches(6.9), Inches(4.5), Inches(5.9), Inches(1.5), "Box kamera = RENDER CAD (bukan foto fisik)", "Enclosure + tutup Pi4B + arm. Foto cetak fisik menyusul setelah print PETG.")
notes(s, "NASKAH 1,5 mnt: Yang SUDAH jalan vs BELUM (burn-in menunggu kasing). Kejujuran = nilai plus.")

s = new_slide("HASIL UTAMA \u2022 PIPELINE END-TO-END (BUKTI ASLI)", "Frame HP vs Output + Timeseries 763 Frame", "IMG_5159 cov 49,6% vs IMG_5388 cov 58,4% (dari CSV/JSON asli)")
add_img(s, "output/ppt_asli/01_asli_vs_anotasi.jpg", Inches(0.5), Inches(1.7), Inches(8.0), Inches(2.6))
add_img(s, "output/ppt_asli/03_timeseries_IMG5159.png", Inches(0.5), Inches(4.5), Inches(8.0), Inches(2.3))
bullets(s, Inches(8.8), Inches(1.7), Inches(3.9), Inches(5.0), [
    ("Terlihat", "Quad + grid berwarna + HUD + distribusi 24 zona."),
    ("Demo", "Putar 30 dtk IMG_5159_beranotasi.mp4 dari folder (jangan embed 60 MB)."),
    ("Batch 5 foto asli", "seedling 0,9% > growing 10,2% > ready 22,6% (tren logis, tanpa foto AI)."),
    ("Sidang akhir", "Ganti dgn grafik F1/IoU + tabel banding metode."),
])
notes(s, "NASKAH 1,5 mnt: DEMO INTI dari file asli. Putar 30 detik IMG_5159_beranotasi.mp4 + tunjuk timeseries 763 frame. Sebut 18 video + 5 foto asli.")
# === SLIDE 13-16 + SAVE ===
s = new_slide("HASIL KESEHATAN \u2022 BUKTI LAPANGAN ASLI", "5 Foto Lapangan: Semua Sehat (PSI 0-0,1), Konsisten Visual", "Uji injeksi/sintetis DIPINDAH ke appendix — bukan klaim akurasi")
add_img(s, "output/ppt_asli/04_tren_5foto_asli.png", Inches(0.5), Inches(1.7), Inches(8.0), Inches(2.6))
add_img(s, "output/ppt_asli/05_tabel_PSI_5foto.png", Inches(0.5), Inches(4.5), Inches(8.0), Inches(2.3))
bullets(s, Inches(8.8), Inches(1.7), Inches(3.9), Inches(5.0), [
    ("Fakta lapangan", "5 foto bed_01..05: kuning 0%, coklat ~0%, 0 zona sakit, PSI 0-0,1."),
    ("Konsisten visual", "Bed hijau sehat di foto = sehat di algoritma (tidak ada false sakit)."),
    ("Yang belum", "Foto sakit asli BELUM ada di kebun — GT + foto sakit masuk TODO appendix."),
    ("Uji lab (appendix)", "Injeksi blob & dummy sintetis HANYA uji fungsi, bukan bukti akurasi."),
])
notes(s, "NASKAH 1 mnt: Semua bukti di slide ini dari foto lapangan asli. Uji injeksi/sintetis hanya verifikasi fungsi dan dipindah ke appendix agar tidak dikira data lapangan.")

s = new_slide("EVALUASI & RENCANA \u2022 SUDAH vs BELUM", "Sempro = 70% > Sidang akhir = 100% + akurasi", "Roadmap jelas lebih dihargai dari klaim berlebihan")
kartu(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(2.3), "SUDAH (ada bukti) OK", "18 video, jitter -53%, kesehatan 100%, Pi test OK, Firebase v1.1, dashboard, 53 paper, STL siap")
kartu(s, Inches(6.9), Inches(1.7), Inches(5.9), Inches(2.3), "BELUM > kapan (TODO)", "GT 5 gbr + F1/IoU (Sep), banding metode (Sep), validasi ambang (Okt), burn-in 24 jam (Okt), Bab 4-5 (Nov)", bgc=KUNING_BG)
bullets(s, Inches(0.5), Inches(4.3), Inches(12.3), Inches(2.5), [
    ("Tool siap tinggal eksekusi", "buat_gt.py (45-60 mnt) > evaluasi_segmentasi.py > bandingkan_metode.py. Target F1 0,85-0,95."),
    ("Risiko + mitigasi", "Hujan > fallback + shield. Panas > guard + heatsink. Offline > outbox."),
])
notes(s, "NASKAH 1 mnt: Sep GT, Okt lapangan, Nov laporan. Jawab 'kapan selesai' sebelum ditanya.")

s = new_slide("TIMELINE \u2022 SEMPRO > KELULUSAN (NOV 2026)", "Satu Timeline Sampai Sidang Akhir \u2014 Tinggal Centang", "")
for i, (j, isi) in enumerate([
    ("SEP", "GT + F1/IoU + banding"),
    ("OKT AWAL", "Validasi ambang + Firebase B"),
    ("OKT AKHIR", "Lapangan + burn-in 24 jam"),
    ("NOV AWAL", "Bab 4-5 + revisi"),
    ("NOV MID", "Video 2 mnt + final > SIDANG"),
]):
    kartu(s, Inches(0.5 + i * 2.5), Inches(1.7), Inches(2.3), Inches(2.0), j, isi)
bullets(s, Inches(0.5), Inches(4.0), Inches(12.3), Inches(2.8), [
    ("Checklist H-1 sempro", "Tes 30 frame, siapkan MP4 + demo_dua_video.png + 1 JSON, print LAPORAN_PROGRES, catat jawaban."),
    ("Kumpulkan dari sekarang", "Mask GT, log burn-in >=140, screenshot 24 jam, video 2 mnt, STL tercetak."),
])
notes(s, "NASKAH 45 dtk: Target akhir November. Slide ini tinggal dicentang di sidang akhir.")

s = new_slide("PENUTUP \u2022 KESIMPULAN + MOHON ARAHAN", "Terima Kasih \u2014 Mohon Arahan Bapak/Ibu Penguji", "Akhiri dengan pertanyaan arahan (kematangan, bukan kelemahan)")
bullets(s, Inches(0.5), Inches(1.7), Inches(6.3), Inches(5.0), [
    ("Kesimpulan", "CV per zona jalan end-to-end, stabil cahaya, kesehatan+PSI tepat zona, Pi+dashboard siap burn-in."),
    ("Arahan 1", "Ambang 25/55/80%: cukup paper atau wajib validasi petani/ahli?"),
    ("Arahan 2", "Prototipe: cukup laptop+webcam atau wajib RasPi outdoor?"),
    ("Arahan 3-4", "Bab 3 perlu UML? Rule ganti-air + membership fuzzy siapa menetapkan? (dgn teman)"),
])
kartu(s, Inches(7.3), Inches(1.7), Inches(5.5), Inches(1.6), "Antisipasi", "Akurasi? tool F1/IoU siap, akhir Sep. Bukan DL? data kecil + CPU. Output? peta 24 zona + teks.")
kartu(s, Inches(7.3), Inches(3.5), Inches(5.5), Inches(1.6), "Repo & demo", "github.com/FIllxe/kangkung-cv-aquaponik, docs/LAPORAN_PROGRES, output/demo/, web/")
kartu(s, Inches(7.3), Inches(5.3), Inches(5.5), Inches(1.4), "Transisi", "Demikian bagian CV. Selanjutnya teman saya: kontrol fuzzy + pompa. Terima kasih.")
notes(s, "NASKAH 1 mnt: Kesimpulan 20 dtk + 4 arahan. Serahkan ke teman. Siap Q&A: akurasi, DL, output, kapan selesai.")

prs.save(str(OUT))
print(f"OK -> {OUT} ({len(prs.slides)} slide)")
