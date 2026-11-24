"""
Generator PPT Sempro — Bagian Computer Vision: Method & Perhitungan Matematis (PSI).
Hanya isi teknis, tanpa nama penguji/judul lengkap.
Jalankan: python docs/buat_ppt_sempro_math.py
Output: docs/DRAFT_PPT_SEMPRO_MATH_METHOD.pptx
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

HIJAU_TUA = RGBColor(0x1B, 0x5E, 0x20)
HIJAU = RGBColor(0x2E, 0x7D, 0x32)
HIJAU_MUDA = RGBColor(0xE8, 0xF5, 0xE9)
AKSEN = RGBColor(0x66, 0xBB, 0x6A)
ABU = RGBColor(0x42, 0x42, 0x42)
ABU_MUDA = RGBColor(0x75, 0x75, 0x75)
PUTIH = RGBColor(0xFF, 0xFF, 0xFF)
KUNING_BG = RGBColor(0xFF, 0xF8, 0xE1)
BIRU_BG = RGBColor(0xE3, 0xF2, 0xFD)
MERAH = RGBColor(0xB7, 0x1C, 0x1C)
ORANGE = RGBColor(0xE6, 0x51, 0x00)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

def add_bg(slide, color=PUTIH):
    f = slide.background.fill
    f.solid(); f.fore_color.rgb = color

def add_header(slide, kicker, judul, sub=""):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.25))
    shp.line.fill.background()
    shp.fill.solid(); shp.fill.fore_color.rgb = HIJAU_TUA
    tf = shp.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = kicker
    p.alignment = PP_ALIGN.LEFT
    r = p.runs[0]
    r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = AKSEN
    p2 = tf.add_paragraph()
    p2.text = judul
    p2.alignment = PP_ALIGN.LEFT
    r2 = p2.runs[0]
    r2.font.size = Pt(25); r2.font.bold = True; r2.font.color.rgb = PUTIH
    if sub:
        p3 = tf.add_paragraph()
        p3.text = sub
        p3.alignment = PP_ALIGN.LEFT
        r3 = p3.runs[0]
        r3.font.size = Pt(12); r3.font.color.rgb = PUTIH

def add_footer(slide, n):
    box = slide.shapes.add_textbox(prs.slide_width - Inches(1.0), prs.slide_height - Inches(0.45), Inches(0.8), Inches(0.35))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    p.text = str(n)
    r = p.runs[0]
    r.font.size = Pt(10); r.font.color.rgb = ABU_MUDA

def add_bullets(slide, left, top, width, height, items, size=14, space_after=8):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.space_before = Pt(2)
        if isinstance(item, tuple):
            jd, isi = item
            r = p.add_run(); r.text = "\u2022 " + jd
            r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = HIJAU_TUA
            if isi:
                r2 = p.add_run(); r2.text = " \u2014 " + isi
                r2.font.size = Pt(size); r2.font.bold = False; r2.font.color.rgb = ABU
        else:
            r = p.add_run(); r.text = "\u2022 " + item
            r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = HIJAU_TUA
    return box

def add_kartu(slide, left, top, width, height, judul, isi, bgc=HIJAU_MUDA, judul_size=13, isi_size=11):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    s.line.fill.background()
    s.fill.solid(); s.fill.fore_color.rgb = bgc
    tf = s.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = judul
    r.font.size = Pt(judul_size); r.font.bold = True; r.font.color.rgb = HIJAU_TUA
    if isi:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run(); r2.text = isi
        r2.font.size = Pt(isi_size); r2.font.color.rgb = ABU
    return s

def add_text(slide, left, top, width, height, text, size=13, bold=False, color=ABU, align=PP_ALIGN.LEFT, italic=False):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    return box

def add_formula(slide, left, top, width, height, text, size=18, color=HIJAU_TUA, bold=True):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    r.font.name = "Cambria Math"
    return box

SLIDES = []
def new_slide(kicker, judul, sub=""):
    s = prs.slides.add_slide(BLANK)
    add_bg(s)
    add_header(s, kicker, judul, sub)
    SLIDES.append(s)
    return s

# SLIDE 1 — JUDUL / INTRO (umum, tanpa nama)
s = new_slide("SISTEM COMPUTER VISION \u2022 BAGIAN METHOD & PERHITUNGAN",
              "Deteksi Kesiapan Panen & Kesehatan Daun Kangkung Aquaponik",
              "Bed aquaponik 2 m \u00d7 1,1 m \u2022 Grid analisis 4 \u00d7 6 zona \u2022 Output: peta zona + PSI")
add_bullets(s, Inches(0.5), Inches(1.7), Inches(7.5), Inches(5.0), [
    ("Metode utama", "Segmentasi berbasis warna HSV + Indeks Stres Tanaman (PSI)."),
    ("Input", "Citra kamera bed kangkung (daun hijau, kuning, coklat)."),
    ("Output per zona", "Status kesehatan (sehat / waspada / sakit) + nilai PSI 0\u2013100."),
    ("Tujuan", "Identifikasi zona yang perlu perhatian (panen atau penanganan stres)."),
])
add_kartu(s, Inches(8.3), Inches(1.7), Inches(4.5), Inches(1.5), "Fokus Presentasi", "Method, rumus, dan contoh perhitungan matematis saja.", bgc=BIRU_BG)
add_kartu(s, Inches(8.3), Inches(3.4), Inches(4.5), Inches(1.5), "Definisi PSI", "Plant Stress Index (bukan Photosystem I).", bgc=KUNING_BG)
add_kartu(s, Inches(8.3), Inches(5.1), Inches(4.5), Inches(1.5), "Rumus Inti", "PSI = 100 \u00d7 (0,5\u00d7Y + B) / N", bgc=HIJAU_MUDA)
add_footer(s, 1)

# SLIDE 2 — PIPELINE METHOD
s = new_slide("METHOD", "Pipeline Segmentasi Citra Kangkung", "Alur awal sampai akhir dalam satu frame")
steps = [
    ("1. Citra Masuk", "Gambar bed kangkung dari kamera (BGR)."),
    ("2. Konversi Warna", "BGR \u2192 HSV (Hue, Saturation, Value)."),
    ("3. Threshold HSV", "Pisahkan piksel hijau, kuning, coklat per rentang warna."),
    ("4. Morfologi", "Opening (3\u00d73) + Closing (7\u00d77) hapus noise & isi lubang."),
    ("5. Grid Zona", "Bagi citra jadi 4 baris \u00d7 6 kolom = 24 zona."),
    ("6. Hitung Piksel", "Hitung G, Y, B per zona."),
    ("7. Hitung PSI", "Rumus PSI per zona dan global."),
    ("8. Output", "Status zona + nilai PSI ke dashboard / kontroler fuzzy."),
]
y = 1.7
for i, (jd, isi) in enumerate(steps):
    add_kartu(s, Inches(0.5 + (i % 4) * 3.05), Inches(y), Inches(2.85), Inches(1.6), jd, isi, bgc=HIJAU_MUDA if i % 2 == 0 else PUTIH)
    if i % 4 == 3:
        y += 1.85
add_footer(s, 2)

# SLIDE 3 — HSV SEGMENTATION METHOD
s = new_slide("METHOD", "Segmentasi Warna Berbasis HSV", "Konversi citra ke ruang warna HSV sebelum threshold")
add_bullets(s, Inches(0.5), Inches(1.7), Inches(6.2), Inches(5.0), [
    ("Konversi", "Citra BGR diubah ke HSV agar deteksi warna tidak terlalu sensitif kecerahan."),
    ("Kelas warna", "Hijau (daun sehat), Kuning (klorosis/defisiensi nutrisi), Coklat (nekrosis/jaringan mati)."),
    ("Threshold", "Setiap kelas memiliki range lower & upper pada channel H, S, V."),
    ("Operasi morfologi", "Opening (3\u00d73) untuk buang titik noise, Closing (7\u00d77) untuk tutup lubang di dalam daun."),
    ("Hasil", "Mask biner per kelas yang menunjukkan lokasi piksel masing-masing warna."),
])
add_text(s, Inches(7.0), Inches(1.7), Inches(5.8), Inches(2.0), "Contoh range default (dikalibrasi lapangan):", size=13, bold=True, color=HIJAU_TUA)
ranges = [
    ("Hijau muda", "H[35\u201375], S[40\u2013255], V[40\u2013200]"),
    ("Hijau matang", "H[36\u201385], S[60\u2013255], V[60\u2013255]"),
    ("Kuning", "H[21\u201334], S[60\u2013255], V[80\u2013255]"),
    ("Coklat", "H[8\u201320], S[70\u2013255], V[85\u2013220]"),
]
yy = 2.1
for nama, rng in ranges:
    add_kartu(s, Inches(7.0), Inches(yy), Inches(5.8), Inches(0.75), nama, rng, bgc=PUTIH)
    yy += 0.9
add_footer(s, 3)

# SLIDE 4 — PSI FORMULA (CORE MATH)
s = new_slide("PERHITUNGAN MATEMATIS", "Indeks Stres Tanaman (PSI v2.0)", "Rumus utama yang digunakan untuk menilai stres daun per zona")
add_text(s, Inches(0.5), Inches(1.5), Inches(6.0), Inches(0.6), "Definisi variabel:", size=14, bold=True, color=HIJAU_TUA)
add_bullets(s, Inches(0.5), Inches(2.1), Inches(6.0), Inches(4.5), [
    ("G", "Jumlah piksel hijau (daun sehat)."),
    ("Y", "Jumlah piksel kuning (klorosis / stres ringan)."),
    ("B", "Jumlah piksel coklat (nekrosis / stres berat)."),
    ("N", "Total piksel tanaman terklasifikasi: N = G + Y + B."),
])
add_formula(s, Inches(0.5), Inches(4.4), Inches(6.0), Inches(1.0), "PSI = 100 \u00d7 (0,5 \u00d7 Y + B) / N")
add_text(s, Inches(0.5), Inches(5.5), Inches(6.0), Inches(1.0), "Presisi: float64. Hasil dalam skala 0\u2013100. Semakin tinggi PSI, semakin tinggi stres.", size=11, italic=True, color=ABU)
add_kartu(s, Inches(7.0), Inches(1.7), Inches(5.8), Inches(1.2), "Bobot Kategori", "Hijau = 0,0 | Kuning = 0,5 | Coklat = 1,0", bgc=HIJAU_MUDA)
add_kartu(s, Inches(7.0), Inches(3.1), Inches(5.8), Inches(1.2), "Nilai Referens", "PSI 0 = semua hijau | PSI 50 = semua kuning (atau campuran) | PSI 100 = semua coklat", bgc=KUNING_BG)
add_kartu(s, Inches(7.0), Inches(4.5), Inches(5.8), Inches(1.9), "Sifat Rumus", "Linear \u2014 tidak jenuh di tengah rentang. Gradien tetap ada sampai 100% piksel coklat. Rumus lama (2\u00d7K + 5\u00d7C) sudah mentok di 100 ketika coklat \u2265 20%.", bgc=PUTIH)
add_footer(s, 4)

# SLIDE 5 — PSI EXAMPLES
s = new_slide("PERHITUNGAN MATEMATIS", "Contoh Perhitungan PSI per Zona", "Piksel mentah dihitung per zona, lalu masukkan ke rumus PSI")
examples = [
    ("Zona A \u2014 Sehat", "G = 800, Y = 150, B = 50 \u2192 N = 1000", "PSI = 100 \u00d7 (0,5\u00d7150 + 50) / 1000 = 100 \u00d7 125 / 1000 = 12,5", HIJAU),
    ("Zona B \u2014 Sedang", "G = 400, Y = 400, B = 200 \u2192 N = 1000", "PSI = 100 \u00d7 (0,5\u00d7400 + 200) / 1000 = 100 \u00d7 400 / 1000 = 40,0", ORANGE),
    ("Zona C \u2014 Parah", "G = 0, Y = 500, B = 500 \u2192 N = 1000", "PSI = 100 \u00d7 (0,5\u00d7500 + 500) / 1000 = 100 \u00d7 750 / 1000 = 75,0", MERAH),
]
xx = 0.5
for judul, hitung, hasil, warna in examples:
    add_kartu(s, Inches(xx), Inches(1.7), Inches(3.95), Inches(2.6), judul, f"{hitung}\n{hasil}", bgc=HIJAU_MUDA, judul_size=12, isi_size=11)
    xx += 4.15
add_text(s, Inches(0.5), Inches(4.6), Inches(12.3), Inches(1.5), "Catatan: PSI = 50 bisa juga dari campuran lain (mis. G=0, Y=200, B=400 \u2192 N=600 \u2192 PSI = 100\u00d7(100+400)/600 \u2248 83,3). Jadi lihat komposisi G/Y/B, bukan hanya angka PSI sendirian.", size=11, italic=True, color=ABU)
add_footer(s, 5)

# SLIDE 6 — PSI VALIDITY & AGGREGATION
s = new_slide("PERHITUNGAN MATEMATIS", "Kondisi Validitas & Agregasi PSI", "Kapan PSI boleh dihitung dan bagaimana gabungkan 24 zona")
add_bullets(s, Inches(0.5), Inches(1.7), Inches(6.2), Inches(5.0), [
    ("PSI = None (tidak valid)", "Jika N = 0 (tidak ada piksel tanaman), atau masukan negatif / non-angka / NaN / Infinity."),
    ("PSI = 0 adalah valid", "Berarti kanopi sepenuhnya hijau. Tidak boleh dicampur dengan \"tidak ada tanaman\"."),
    ("Batas minimum", "Zona harus memiliki cukup piksel tanaman agar PSI dihitung (filter validitas)."),
    ("Agregasi 24 zona", "Jumlahkan piksel G, Y, B dari semua zona DULU, baru hitung PSI global."),
    ("Jangan rata-rata PSI", "Rata-rata PSI per zona salah karena luas tanaman tiap zona berbeda."),
])
add_kartu(s, Inches(7.0), Inches(1.7), Inches(5.8), Inches(2.5), "PSI Global (Grid 4\u00d76)", "PSI_global = 100 \u00d7 (0,5 \u00d7 \u03a3Y + \u03a3B) / (\u03a3G + \u03a3Y + \u03a3B)", bgc=HIJAU_MUDA)
add_kartu(s, Inches(7.0), Inches(4.4), Inches(5.8), Inches(2.0), "Pembaca data", "Nilai dikirim ke kontroler fuzzy (tim lain) sebagai masukan keputusan pompa / ganti air.", bgc=BIRU_BG)
add_footer(s, 6)

# SLIDE 7 — HEALTH THRESHOLDS
s = new_slide("PERHITUNGAN MATEMATIS", "Ambang Kesehatan Daun per Zona", "Persentase dihitung terhadap piksel tanaman di zona, bukan luas zona")
add_text(s, Inches(0.5), Inches(1.6), Inches(12.3), Inches(0.5), "Referensi: Barbedo (2013), SpringerPlus \u2014 segmentasi area sakit daun berbasis warna.", size=11, italic=True, color=ABU)
headers = ["Kondisi", "Kuning (% tanaman)", "Coklat (% tanaman)", "Status"]
rows = [
    ("Sehat", "< 10%", "< 3%", "Hijau"),
    ("Waspada", "10% \u2013 25%", "3% \u2013 8%", "Kuning"),
    ("Sakit", "> 25%", "> 8%", "Merah"),
]
col_w = [2.2, 2.6, 2.6, 1.8]
xx = 0.5
for i, h in enumerate(headers):
    add_kartu(s, Inches(xx), Inches(2.2), Inches(col_w[i]), Inches(0.6), h, "", bgc=HIJAU_TUA, judul_size=12, isi_size=0)
    xx += col_w[i]
yy = 2.9
for row in rows:
    xx = 0.5
    for i, val in enumerate(row):
        add_kartu(s, Inches(xx), Inches(yy), Inches(col_w[i]), Inches(0.75), val, "", bgc=HIJAU_MUDA if i == 0 else PUTIH, judul_size=11, isi_size=0)
        xx += col_w[i]
    yy += 0.9
add_bullets(s, Inches(0.5), Inches(5.9), Inches(12.3), Inches(1.4), [
    ("Aturan status zona", "Jika coklat \u2265 8% \u2192 zona SAKIT. Else jika kuning \u2265 10% \u2192 WASPADA. Else \u2192 SEHAT."),
])
add_footer(s, 7)

# SLIDE 8 — METHOD COMPARISON
s = new_slide("METHOD", "Perbandingan Tiga Metode Segmentasi", "HSV (utama) dibandingkan dengan ExG dan Otsu-Hue sebagai pembanding")
add_text(s, Inches(0.5), Inches(1.6), Inches(12.3), Inches(0.5), "Semua metode dilewati morfologi Opening (3\u00d73) dan Closing (7\u00d77) yang sama.", size=11, italic=True, color=ABU)
tbl_headers = ["Metode", "Prinsip Kerja", "Kelebihan", "Kekurangan"]
tbl_rows = [
    ("HSV (utama)", "Threshold pada ruang warna HSV (H, S, V)", "Cocok pisahkan kuning & coklat, stabil terhadap cahaya", "Perlu kalibrasi range HSV per kamera/lapangan"),
    ("ExG", "ExG = 2g \u2212 r \u2212 b (RGB ternormalisasi) + Otsu", "Sederhana, tidak perlu kalibrasi warna manual", "Sensitif cahaya, sulit pisahkan kuning vs coklat"),
    ("Otsu-Hue", "Threshold otomatis pada channel Hue", "Otomatis, tidak perlu range manual", "Kurang presisi untuk nuansa warna halus"),
]
col_w = [2.0, 3.6, 3.4, 3.3]
xx = 0.5
for i, h in enumerate(tbl_headers):
    add_kartu(s, Inches(xx), Inches(2.2), Inches(col_w[i]), Inches(0.6), h, "", bgc=HIJAU_TUA, judul_size=11, isi_size=0)
    xx += col_w[i]
yy = 2.9
for row in tbl_rows:
    xx = 0.5
    for i, val in enumerate(row):
        bgc = HIJAU_MUDA if i == 0 else PUTIH
        add_kartu(s, Inches(xx), Inches(yy), Inches(col_w[i]), Inches(1.15), val, "", bgc=bgc, judul_size=10, isi_size=0)
        xx += col_w[i]
    yy += 1.25
add_footer(s, 8)

# SLIDE 9 — EXG FORMULA
s = new_slide("PERHITUNGAN MATEMATIS", "Rumus Excess Green (ExG) \u2014 Metode Pembanding", "Woebbecke et al. (1995), deteksi vegetasi pada citra lapangan")
add_formula(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(1.2), "r_n = R / (R + G + B)")
add_formula(s, Inches(0.5), Inches(2.4), Inches(6.0), Inches(1.2), "g_n = G / (R + G + B)")
add_formula(s, Inches(0.5), Inches(3.1), Inches(6.0), Inches(1.2), "b_n = B / (R + G + B)")
add_formula(s, Inches(0.5), Inches(3.8), Inches(6.0), Inches(1.0), "ExG = 2 \u00d7 g_n \u2212 r_n \u2212 b_n")
add_text(s, Inches(0.5), Inches(4.9), Inches(6.0), Inches(1.5), "Hasil ExG dinormalisasi ke 0\u2013255, lalu dipakai threshold Otsu untuk menghasilkan mask biner tanaman.", size=12, color=ABU)
add_kartu(s, Inches(7.0), Inches(1.7), Inches(5.8), Inches(4.5), "Peran dalam penelitian", "ExG dan Otsu-Hue digunakan sebagai baseline perbandingan performa terhadap metode HSV utama (lihat evaluasi F1 / IoU di slide berikut).", bgc=BIRU_BG)
add_footer(s, 9)

# SLIDE 10 — EVALUATION METRICS
s = new_slide("PERHITUNGAN MATEMATIS", "Evaluasi Segmentasi vs Ground Truth", "Metrik kuantitatif untuk Bab 4 (validasi performa segmentasi)")
add_bullets(s, Inches(0.5), Inches(1.7), Inches(6.2), Inches(5.0), [
    ("TP", "Benar terdeteksi sebagai tanaman."),
    ("FP", "Bukan tanaman tapi terdeteksi tanaman."),
    ("FN", "Tanaman tapi tidak terdeteksi."),
    ("TN", "Benar bukan tanaman."),
])
add_formula(s, Inches(0.5), Inches(4.0), Inches(6.0), Inches(0.5), "Precision = TP / (TP + FP)")
add_formula(s, Inches(0.5), Inches(4.5), Inches(6.0), Inches(0.5), "Recall = TP / (TP + FN)")
add_formula(s, Inches(0.5), Inches(5.0), Inches(6.0), Inches(0.5), "F1 = 2 \u00d7 Precision \u00d7 Recall / (Precision + Recall)")
add_formula(s, Inches(0.5), Inches(5.5), Inches(6.0), Inches(0.5), "IoU = TP / (TP + FP + FN)")
add_kartu(s, Inches(7.0), Inches(1.7), Inches(5.8), Inches(2.0), "Tambahan", "Accuracy = (TP+TN)/Semua | Specificity = TN / (TN+FP)", bgc=HIJAU_MUDA)
add_kartu(s, Inches(7.0), Inches(3.9), Inches(5.8), Inches(2.3), "Target", "F1-score 0,85 \u2013 0,95. Evaluasi menggunakan mask ground truth (GT) buatan manual per gambar.", bgc=KUNING_BG)
add_footer(s, 10)

# SLIDE 11 — KALIBRASI HSV
s = new_slide("METHOD", "Kalibrasi Threshold Warna HSV", "Diselaraskan dengan pencahayaan dan kamera di lokasi bed aquaponik")
add_bullets(s, Inches(0.5), Inches(1.7), Inches(12.3), Inches(4.5), [
    ("Langkah", "Buka citra asli atau live kamera, geser trackbar H/S/V untuk masing-masing kelas (hijau, kuning, coklat)."),
    ("Verifikasi", "Lihat mask hasil secara real-time hingga warna target tertangkap dengan baik."),
    ("Simpan", "Nilai lower & upper disalin ke konfigurasi HSV di kode segmentasi."),
    ("Tujuan", "Agar threshold tidak kaku saat beralih cuaca / waktu pengambilan citra."),
])
add_kartu(s, Inches(0.5), Inches(5.1), Inches(12.3), Inches(1.5), "Output kalibrasi", "Range H, S, V per kelas yang disimpan dan digunakan ulang di setiap frame.", bgc=HIJAU_MUDA)
add_footer(s, 11)

# SLIDE 12 — RINGKASAN
s = new_slide("RINGKASAN METHOD & MATEMATIS", "Hal-Hal Utama yang Diperhatikan Penguji", "Tanpa nama, hanya inti teknis")
add_bullets(s, Inches(0.5), Inches(1.7), Inches(12.3), Inches(5.0), [
    ("Segmentasi", "HSV dengan 3 kelas (hijau/kuning/coklat) + morfologi Opening & Closing."),
    ("PSI", "Plant Stress Index = 100 \u00d7 (0,5\u00d7Y + B) / N, skala 0\u2013100, linear dan tidak jenuh."),
    ("Agregasi", "Jumlahkan piksel semua zona dulu, baru hitung PSI global (jangan rata-rata PSI per zona)."),
    ("Kesehatan zona", "Ambang kuning 10%/25% dan coklat 3%/8% terhadap piksel tanaman per zona."),
    ("Validasi", "Evaluasi segmentasi vs ground truth dengan Precision, Recall, F1, IoU. Target F1 0,85\u20130,95."),
    ("Pembanding", "ExG dan Otsu-Hue sebagai metode pembanding dalam perbandingan performa."),
])
add_kartu(s, Inches(0.5), Inches(5.7), Inches(12.3), Inches(1.2), "PSI = Plant Stress Index", "Bukan Photosystem I. Selalu tulis lengkap di laporan.", bgc=KUNING_BG)
add_footer(s, 12)

# ---------- Simpan ----------
OUT = r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\DRAFT_PPT_SEMPRO_MATH_METHOD.pptx"
prs.save(OUT)
print(f"OK -> {OUT} ({len(prs.slides)} slide)")
