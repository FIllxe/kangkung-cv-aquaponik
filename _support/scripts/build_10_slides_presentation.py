import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

# --- PALETTE CONFIGURATION ---
BG_COLOR = RGBColor(10, 14, 23)        # #0A0E17 Dark Slate/Navy
CARD_BG = RGBColor(17, 24, 39)        # #111827 Dark Surface
CARD_BORDER = RGBColor(30, 41, 59)    # #1E293B Subtle Border
CYAN = RGBColor(6, 182, 212)          # #06B6D4 Primary Accent
EMERALD = RGBColor(16, 185, 129)      # #10B981 Green Accent
AMBER = RGBColor(245, 158, 11)        # #F59E0B Warning/Problem Accent
ROSE = RGBColor(244, 63, 94)          # #F43F5E Critical/Stress Accent
TEXT_WHITE = RGBColor(248, 250, 252)  # #F8FAFC Heading text
TEXT_GRAY = RGBColor(148, 163, 184)   # #94A3B8 Body text
TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B Secondary text

def set_slide_background(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_COLOR

def add_header(slide, tag_text, title_text):
    tag_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.13), Inches(0.3))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = tag_text.upper()
    p_tag.font.name = "Segoe UI"
    p_tag.font.size = Pt(9.5)
    p_tag.font.bold = True
    p_tag.font.color.rgb = CYAN
    
    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.62), Inches(12.13), Inches(0.55))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = "Segoe UI"
    p_title.font.size = Pt(20)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE
    
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.22), Inches(12.13), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = CARD_BORDER
    line.line.color.rgb = CARD_BORDER

def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1)
    return card

def build_full_deck(output_path):
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    base_dir = r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic"

    # =========================================================================
    # SLIDE 1: LATAR BELAKANG PERMASALAHAN
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    add_header(s1, "01 / Latar Belakang & Urgensi Penelitian", "LATAR BELAKANG PERMASALAHAN")
    
    card1_h = Inches(1.7)
    card_gap = Inches(0.18)
    
    add_card(s1, Inches(0.6), Inches(1.4), Inches(6.8), card1_h)
    tb = s1.shapes.add_textbox(Inches(0.85), Inches(1.5), Inches(6.3), card1_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "Heterogenitas Pertumbuhan Kanopi pada Bed Akuaponik"
    p.font.name = "Segoe UI"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = CYAN
    p2 = tf.add_paragraph()
    p2.text = "Pada bed tanam kangkung Eco Farm UNNES (2,0 m × 1,1 m), pola sirkulasi nutrisi menghasilkan laju pertumbuhan yang tidak seragam antar titik tanam. Evaluasi rata-rata gelondongan satu bed menyamarkan area yang kekurangan nutrisi atau telah mengalami over-dense."
    p2.font.name = "Segoe UI"
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = TEXT_GRAY
    p2.space_before = Pt(4)
    
    top2 = Inches(1.4) + card1_h + card_gap
    add_card(s1, Inches(0.6), top2, Inches(6.8), card1_h)
    tb = s1.shapes.add_textbox(Inches(0.85), top2 + Inches(0.1), Inches(6.3), card1_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "Keterbatasan Pengamatan Visual Petani (Manual & Subjektif)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = AMBER
    p2 = tf.add_paragraph()
    p2.text = "Penilaian kesiapan panen konvensional bersifat kualitatif dan rentan bias mata pengelola. Gejala klorosis (daun kuning) dan nekrosis (daun busuk/cokelat) kerap baru disadari saat patologi tanaman telah meluas, sehingga mitigasi kualitas air terlambat dilakukan."
    p2.font.name = "Segoe UI"
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = TEXT_GRAY
    p2.space_before = Pt(4)
    
    top3 = top2 + card1_h + card_gap
    add_card(s1, Inches(0.6), top3, Inches(6.8), card1_h)
    tb = s1.shapes.add_textbox(Inches(0.85), top3 + Inches(0.1), Inches(6.3), card1_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = "Kebutuhan Sensor Visi Komputer Edge Otomatis & Non-Destruktif"
    p.font.name = "Segoe UI"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = EMERALD
    p2 = tf.add_paragraph()
    p2.text = "Diperlukan sistem monitoring berbasis computer vision pada komputasi tepi (Raspberry Pi 4B) yang mengukur tutupan kanopi 24 zona dan memformulasikan Plant Stress Index (PSI) secara kontinyu (tiap 10 menit), objektif, dan siap diintegrasikan dengan kendali akuator air."
    p2.font.name = "Segoe UI"
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = TEXT_GRAY
    p2.space_before = Pt(4)
    
    add_card(s1, Inches(7.7), Inches(1.4), Inches(5.03), Inches(5.46))
    img_situasi = os.path.join(base_dir, r"docs\images\Situasi 1.jpg")
    if os.path.exists(img_situasi):
        s1.shapes.add_picture(img_situasi, Inches(7.85), Inches(1.55), Inches(4.73), Inches(3.55))
    tb_cap = s1.shapes.add_textbox(Inches(7.85), Inches(5.25), Inches(4.73), Inches(1.4))
    tf_cap = tb_cap.text_frame
    tf_cap.word_wrap = True
    tf_cap.margin_left = tf_cap.margin_top = tf_cap.margin_right = tf_cap.margin_bottom = 0
    pc1 = tf_cap.paragraphs[0]
    pc1.text = "LOKASI RISET: AQUAPONIK ECO FARM UNNES"
    pc1.font.name = "Segoe UI"
    pc1.font.size = Pt(10)
    pc1.font.bold = True
    pc1.font.color.rgb = CYAN
    pc2 = tf_cap.add_paragraph()
    pc2.text = "Instalasi bed kangkung air (Ipomoea aquatica) 2,0 m × 1,1 m dengan pencahayaan alami matahari terbuka. Menjadi basis observasi, kalibrasi algoritma, serta pengujian prototipe lapangan."
    pc2.font.name = "Segoe UI"
    pc2.font.size = Pt(9.5)
    pc2.font.color.rgb = TEXT_GRAY
    pc2.space_before = Pt(3)

    # =========================================================================
    # SLIDE 2: RUMUSAN MASALAH PENELITIAN
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "02 / Rumusan Masalah Rekayasa", "RUMUSAN MASALAH PENELITIAN")
    
    col_w = Inches(3.85)
    col_gap = Inches(0.28)
    col_h = Inches(5.46)
    
    rumusan_data = [
        {
            "num": "01",
            "title": "Deteksi Geometri & Grid Otomatis",
            "question": "Bagaimana mendeteksi bed dan membagi citra menjadi grid 4 × 6 secara otomatis dari kamera tampak atas pada bak tanam akuaponik?",
            "challenge": "Distorsi perspektif kamera miring (tilt) serta jitter posisi akibat getaran mekanis pompa dan hembusan angin luar ruangan.",
            "solution": "Deteksi tepi Canny + aproksimasi quad + penstabilan temporal EMA (alpha = 0,2) + rektifikasi homografi planar ke kanvas 1200 × 660 px.",
            "color": CYAN
        },
        {
            "num": "02",
            "title": "Stabilitas Iluminasi Terbuka",
            "question": "Bagaimana menstabilkan segmentasi warna HSV terhadap perubahan iluminasi pagi, siang, dan sore sehingga liputan kanopi per zona konsisten?",
            "challenge": "Fluktuasi intensitas matahari ekstrem (pagi redup vs siang terik/glare) yang menyebabkan thresholding statis gagal mendeteksi kanopi.",
            "solution": "Faktor adaptasi dinamis f = mean(V)/128 untuk menggeser batas Saturation dan Value secara linier, dengan menjaga rona Hue tetap invarian.",
            "color": AMBER
        },
        {
            "num": "03",
            "title": "Formulasi Sinyal Indeks Stres (PSI)",
            "question": "Bagaimana mengukur persentase kuning dan cokelat per zona serta merumuskannya menjadi Plant Stress Index (PSI) 0–100 yang siap dibaca pengendali?",
            "challenge": "Formula kuantifikasi lama mengalami saturasi dini (mentok di 100) dan noise media tanam gelap yang tertukar sebagai daun mati.",
            "solution": "Model linear tanpa saturasi: PSI = 100 × (0,5Y + B)/N, dilengkapi filter adjasensi nekrosis morfologi kanopi daun hijau.",
            "color": EMERALD
        }
    ]
    
    for idx, r_item in enumerate(rumusan_data):
        l_pos = Inches(0.6) + idx * (col_w + col_gap)
        add_card(s2, l_pos, Inches(1.4), col_w, col_h)
        tb = s2.shapes.add_textbox(l_pos + Inches(0.25), Inches(1.6), col_w - Inches(0.5), col_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p = tf.paragraphs[0]
        p.text = r_item["num"]
        p.font.name = "Segoe UI"
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = r_item["color"]
        
        p = tf.add_paragraph()
        p.text = r_item["title"].upper()
        p.font.name = "Segoe UI"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(8)
        
        p = tf.add_paragraph()
        p.text = f'"{r_item["question"]}"'
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.italic = True
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(12)
        
        p = tf.add_paragraph()
        p.text = "Tantangan Rekayasa:"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = r_item["color"]
        p = tf.add_paragraph()
        p.text = r_item["challenge"]
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_GRAY
        p.space_after = Pt(10)
        
        p = tf.add_paragraph()
        p.text = "Pendekatan Solusi:"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = r_item["color"]
        p = tf.add_paragraph()
        p.text = r_item["solution"]
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_GRAY

    # =========================================================================
    # SLIDE 3: ARSITEKTUR & PIPELINE CARA KERJA SISTEM
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "03 / Arsitektur & Rekayasa Sistem", "PIPELINE CARA KERJA SISTEM PROTOTIPE")
    
    add_card(s3, Inches(0.6), Inches(1.35), Inches(12.13), Inches(2.75))
    img_blok = os.path.join(base_dir, r"docs\images\blok_diagram.png")
    if os.path.exists(img_blok):
        s3.shapes.add_picture(img_blok, Inches(0.85), Inches(1.45), Inches(11.63), Inches(2.55))
        
    step_w = Inches(2.28)
    step_gap = Inches(0.18)
    step_h = Inches(2.65)
    
    steps = [
        ("1. Akuisisi Citra", "Kamera CSI IR 5 MP pada ketinggian 2,5 m mengambil foto tampak atas otomatis tiap siklus 10 menit.", CYAN),
        ("2. Rektifikasi Bed", "Deteksi tepi Canny + sudut quad dengan filter EMA, lalu warp perspektif ke kanvas ortogonal 1200 × 660 px.", CYAN),
        ("3. Segmentasi HSV", "Adaptasi f = mean(V)/128 memisahkan kanopi hijau muda, mature, klorosis kuning, dan nekrosis cokelat.", EMERALD),
        ("4. Ekstraksi Fitur", "Kalkulasi % coverage per zona (4 status panen) dan skalar Plant Stress Index: PSI = 100·(0,5Y+B)/N.", EMERALD),
        ("5. Uplink & Kontrol", "Kirim JSON payload ke Cloud Firestore, update dasbor web, dan kirim masukan PSI ke kontroler fuzzy.", AMBER)
    ]
    
    for idx, (st_title, st_desc, st_color) in enumerate(steps):
        s_left = Inches(0.6) + idx * (step_w + step_gap)
        add_card(s3, s_left, Inches(4.3), step_w, step_h)
        tb = s3.shapes.add_textbox(s_left + Inches(0.15), Inches(4.45), step_w - Inches(0.3), step_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = st_title
        p.font.name = "Segoe UI"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = st_color
        p.space_after = Pt(4)
        p = tf.add_paragraph()
        p.text = st_desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_GRAY

    # =========================================================================
    # SLIDE 4: DETAIL PIPELINE COMPUTER VISION & HASIL IMPLEMENTASI
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "04 / Algoritma Visi Komputer & Bukti Lapangan", "DETAIL PIPELINE COMPUTER VISION & VALIDASI VISUAL")
    
    add_card(s4, Inches(0.6), Inches(1.35), Inches(4.5), Inches(5.6))
    img_flow = os.path.join(base_dir, r"docs\images\flowchart_cv.png")
    if os.path.exists(img_flow):
        s4.shapes.add_picture(img_flow, Inches(0.8), Inches(1.5), Inches(4.1), Inches(5.3))
        
    add_card(s4, Inches(5.3), Inches(1.35), Inches(7.43), Inches(5.6))
    tb_rt = s4.shapes.add_textbox(Inches(5.5), Inches(1.5), Inches(7.0), Inches(0.35))
    tf_rt = tb_rt.text_frame
    tf_rt.word_wrap = True
    tf_rt.margin_left = tf_rt.margin_top = tf_rt.margin_right = tf_rt.margin_bottom = 0
    p = tf_rt.paragraphs[0]
    p.text = "BUKTI REPRODUKSIBILITAS PADA DATA CITRA LAPANGAN NYATA"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = CYAN
    
    img_res1 = os.path.join(base_dir, r"output\ppt_asli\01_asli_vs_anotasi.jpg")
    if os.path.exists(img_res1):
        s4.shapes.add_picture(img_res1, Inches(5.5), Inches(1.9), Inches(7.0), Inches(1.97))
    tb_c1 = s4.shapes.add_textbox(Inches(5.5), Inches(3.92), Inches(7.0), Inches(0.25))
    tf_c1 = tb_c1.text_frame
    tf_c1.margin_left = tf_c1.margin_top = tf_c1.margin_right = tf_c1.margin_bottom = 0
    pc1 = tf_c1.paragraphs[0]
    pc1.text = "Gambar 3.4: Frame Kamera Asli vs Hasil Segmentasi Grid 24 Zona & HUD Informasi (Liputan 71,9% Siap Panen)"
    pc1.font.name = "Segoe UI"
    pc1.font.size = Pt(8.5)
    pc1.font.color.rgb = TEXT_MUTED
    
    img_res2 = os.path.join(base_dir, r"output\ppt_asli\02_foto_vs_segmentasi.jpg")
    if os.path.exists(img_res2):
        s4.shapes.add_picture(img_res2, Inches(5.5), Inches(4.25), Inches(7.0), Inches(1.97))
    tb_c2 = s4.shapes.add_textbox(Inches(5.5), Inches(6.27), Inches(7.0), Inches(0.25))
    tf_c2 = tb_c2.text_frame
    tf_c2.margin_left = tf_c2.margin_top = tf_c2.margin_right = tf_c2.margin_bottom = 0
    pc2 = tf_c2.paragraphs[0]
    pc2.text = "Gambar 3.5: Frame Video Lapangan vs Segmentasi Multi-Kelas: Hijau Sehat, Kuning Klorosis, dan Cokelat Nekrosis"
    pc2.font.name = "Segoe UI"
    pc2.font.size = Pt(8.5)
    pc2.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 5: LANDASAN TEORETIK & FORMULASI MATEMATIS INTI
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "05 / Dasar Teori & Formulasi Matematis", "LANDASAN TEORETIK & FORMULASI MATEMATIS INTI")
    
    math_cards = [
        ("1. Deteksi Tepi Canny (Gradien)", "G = √(Gx² + Gy²)    dan    θ = arctan(Gy / Gx)", "Mengekstraksi tepi kontur bed menggunakan turunan parsial kernel Sobel horizontal dan vertikal, dilanjutkan non-maximum suppression dan hysteresis thresholding.", CYAN),
        ("2. Homografi Projektif 2D", "s · p′ = H · p    dengan    H ∈ ℝ³ˣ³", "Mentransformasikan 4 titik sudut quad sumber p = [x, y, 1]ᵀ ke kanvas ortogonal datar bebas distorsi perspektif p′ = [x′, y′, 1]ᵀ berukuran tetap 1200 × 660 px.", CYAN),
        ("3. Adaptasi Iluminasi Dinamis", "f = clamp( mean(V) / 128,  0.6,  1.6 )", "Faktor iluminasi harian menyesuaikan ambang batas S_lo, V_lo, V_hi secara adaptif terhadap sinar matahari. Komponen Hue (H) dikunci konstan agar rona warna tidak bias.", AMBER),
        ("4. Rasio Tutupan Kanopi (Coverage)", "Coverage = ( ∑ M_tanaman(x, y) / A_ROI ) × 100%", "Mengukur densitas vegetasi aktif terhadap luas petak zona. Menjadi dasar deterministik penentuan 4 kelas kesiapan panen kangkung (0–25%, 25–55%, 55–80%, >80%).", EMERALD),
        ("5. Plant Stress Index (PSI v2.0)", "N = G + Y + B      ;      PSI = 100 · (0,5·Y + 1,0·B) / N", "Formula linier bebas saturasi: bobot ordinal 0 (hijau sehat), 0,5 (kuning klorosis reversibel), dan 1,0 (cokelat nekrosis ireversibel). Menghasilkan gradien halus bagi kontroler fuzzy.", ROSE)
    ]
    
    m_w = Inches(12.13)
    m_h = Inches(1.0)
    m_gap = Inches(0.12)
    m_top = Inches(1.4)
    
    for idx, (m_title, m_formula, m_desc, m_col) in enumerate(math_cards):
        top_pos = m_top + idx * (m_h + m_gap)
        add_card(s5, Inches(0.6), top_pos, m_w, m_h)
        
        tb = s5.shapes.add_textbox(Inches(0.8), top_pos + Inches(0.08), m_w - Inches(0.4), m_h - Inches(0.16))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p = tf.paragraphs[0]
        p.text = m_title
        p.font.name = "Segoe UI"
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = m_col
        
        p = tf.add_paragraph()
        p.text = f"Formulasi: {m_formula}"
        p.font.name = "Consolas"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(2)
        
        p = tf.add_paragraph()
        p.text = m_desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_GRAY
        p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 6: DISKRETISASI SPASIAL GRID 24 ZONA & STRATEGI PANEN SELEKTIF
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "06 / Diskretisasi Spasial & Agronomi", "DISKRETISASI GRID 24 ZONA & STRATEGI PANEN SELEKTIF")
    
    # Left container: 4 Reasons for 24 Zones
    add_card(s6, Inches(0.6), Inches(1.4), Inches(6.0), Inches(5.46))
    tb_z = s6.shapes.add_textbox(Inches(0.85), Inches(1.6), Inches(5.5), Inches(5.0))
    tf_z = tb_z.text_frame
    tf_z.word_wrap = True
    tf_z.margin_left = tf_z.margin_top = tf_z.margin_right = tf_z.margin_bottom = 0
    
    p = tf_z.paragraphs[0]
    p.text = "MENGAPA DIPILIH GRID 4 × 6 (24 ZONA)?"
    p.font.name = "Segoe UI"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = CYAN
    p.space_after = Pt(8)
    
    reasons = [
        ("1. Kesesuaian Geometris Bed (2,0 m × 1,1 m)", "Kanvas 1200 × 660 px dibagi 4 baris × 6 kolom menghasilkan ukuran zona nyata ≈ 33,3 cm × 27,5 cm (200 × 165 px). Zona berbentuk hampir bujur sangkar proporsional tanpa distorsi memanjang."),
        ("2. Pemetaan Gradien Aliran Nutrisi (6 Kolom)", "Air nutrisi mengalir memanjang dari inlet pipa ke outlet. 6 kolom memetakan dinamika gradien serapan pupuk sepanjang 2 meter bed secara presisi dari hulu ke hilir."),
        ("3. Mengatasi Overlapping Kanopi Tanaman Rimbun", "Saat kangkung usia >10 hari, daun saling bertumpuk rapat sehingga mustahil memisahkan per helai batang dengan kamera 2D. Ukuran 33 × 27 cm adalah ukuran klaster optimal (2–4 netpot)."),
        ("4. Granularitas Ideal untuk Logika Fuzzy", "Menghasilkan variabel diskret integer 0 sampai 24 untuk 'zona_sakit', sangat pas bagi fungsi keanggotaan fuzzy Sugeno rekan tim tanpa lonjakan fluktuasi.")
    ]
    for r_title, r_desc in reasons:
        p = tf_z.add_paragraph()
        p.text = r_title
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = EMERALD
        p = tf_z.add_paragraph()
        p.text = r_desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_GRAY
        p.space_after = Pt(6)

    # Right container: 4 Harvest Status Thresholds
    add_card(s6, Inches(6.9), Inches(1.4), Inches(5.83), Inches(5.46))
    tb_h = s6.shapes.add_textbox(Inches(7.15), Inches(1.6), Inches(5.33), Inches(5.0))
    tf_h = tb_h.text_frame
    tf_h.word_wrap = True
    tf_h.margin_left = tf_h.margin_top = tf_h.margin_right = tf_h.margin_bottom = 0
    
    p = tf_h.paragraphs[0]
    p.text = "4 AMBANG STATUS KESIAPAN PANEN PER ZONA"
    p.font.name = "Segoe UI"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = CYAN
    p.space_after = Pt(8)
    
    statuses = [
        ("Belum Siap (Coverage 0 – 25%)", "Fase seedling/vegetatif awal. Kanopi tanaman masih kecil, dominasi latar belakang media tanam. Tindakan: Lanjutkan penyiraman & nutrisi rutin.", CYAN),
        ("Hampir Siap (Coverage 25 – 55%)", "Fase pertumbuhan pesat (vegetatif aktif). Biomassa daun mulai menutup separuh petak. Tindakan: Pemantauan intensif kesehatan daun.", AMBER),
        ("Siap Panen (Coverage 55 – 80%)", "Kondisi panen optimal kangkung air. Daun rimbun, tinggi batang mencukupi, tekstur renyah. Tindakan: Rekomendasi panen terjadwal.", EMERALD),
        ("Harus Panen (Coverage > 80%)", "Kerapatan berlebih (over-dense). Risiko tinggi sirkulasi udara buruk memicu kelembapan berlebih dan pembusukan batang bawah. Tindakan: Wajib segera dipanen!", ROSE)
    ]
    for st_title, st_desc, st_col in statuses:
        p = tf_h.add_paragraph()
        p.text = st_title
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = st_col
        p = tf_h.add_paragraph()
        p.text = st_desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_GRAY
        p.space_after = Pt(6)
        
    p_concl = tf_h.add_paragraph()
    p_concl.text = "Keunggulan Panen Selektif: Petani dapat memanen petak yang sudah mencapai >55% tanpa merusak zona yang masih muda, menjaga kontinuitas pasokan panen."
    p_concl.font.name = "Segoe UI"
    p_concl.font.size = Pt(9)
    p_concl.font.italic = True
    p_concl.font.color.rgb = TEXT_WHITE

    # =========================================================================
    # SLIDE 7: EVALUASI SEGMENTASI FASE TUMBUH & KESEHATAN DAUN
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "07 / Pengujian & Evaluasi Segmentasi", "EVALUASI SEGMENTASI MULTI-FASE PERTUMBUHAN KANGKUNG")
    
    # Left container: Big Batch Segmentation Overview Image
    add_card(s7, Inches(0.6), Inches(1.35), Inches(7.5), Inches(5.6))
    img_batch = os.path.join(base_dir, r"output\segmentasi_batch\RINGKASAN_BATCH.png")
    if os.path.exists(img_batch):
        s7.shapes.add_picture(img_batch, Inches(0.75), Inches(1.5), Inches(7.2), Inches(4.5))
        
    tb_b_cap = s7.shapes.add_textbox(Inches(0.75), Inches(6.1), Inches(7.2), Inches(0.7))
    tf_bc = tb_b_cap.text_frame
    tf_bc.word_wrap = True
    tf_bc.margin_left = tf_bc.margin_top = tf_bc.margin_right = tf_bc.margin_bottom = 0
    p = tf_bc.paragraphs[0]
    p.text = "Hasil Uji Segmentasi Batch Multi-Tahap: Seedling (4,9%), Young (37,4%), Growing (54,5%), Ready (78,4%), dan Mixed Stres."
    p.font.name = "Segoe UI"
    p.font.size = Pt(8.5)
    p.font.color.rgb = TEXT_MUTED

    # Right container: Health Classification Criteria
    add_card(s7, Inches(8.3), Inches(1.35), Inches(4.43), Inches(5.6))
    tb_diag = s7.shapes.add_textbox(Inches(8.5), Inches(1.5), Inches(4.03), Inches(5.2))
    tf_d = tb_diag.text_frame
    tf_d.word_wrap = True
    tf_d.margin_left = tf_d.margin_top = tf_d.margin_right = tf_d.margin_bottom = 0
    
    p = tf_d.paragraphs[0]
    p.text = "KLASIFIKASI KESEHATAN DAUN"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = CYAN
    p.space_after = Pt(6)
    
    diags = [
        ("Klorosis / Daun Kuning (H: 21–34)", "Indikasi defisiensi hara (N/Fe/Mg) atau stres perakaran awal. Bersifat reversibel bila nutrisi air diperbaiki segera.\n• Waspada: ≥ 10% piksel kanopi menguning\n• Sakit: ≥ 25% piksel kanopi menguning", AMBER),
        ("Nekrosis / Daun Cokelat (H: 8–20)", "Jaringan mati seluler permanen (busuk/kering) akibat patogen jamur atau hawar daun. Bersifat ireversibel.\n• Waspada: ≥ 3% piksel kanopi nekrotik\n• Sakit: ≥ 8% piksel kanopi nekrotik", ROSE),
        ("Fitur Brown Adjacency Gate", "Piksel cokelat hanya diakui sebagai nekrosis jika menempel kanopi hijau (dilatasi 21×21 px). Media tanam gelap di luar kanopi otomatis tereliminasi, mencegah alarm palsu.", EMERALD)
    ]
    for d_title, d_desc, d_col in diags:
        p = tf_d.add_paragraph()
        p.text = d_title
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = d_col
        p = tf_d.add_paragraph()
        p.text = d_desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_GRAY
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 8: DESAIN 3D CAD PERANGKAT & SKEMA PENEMPATAN ALAT
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "08 / Desain Mekanikal & Penempatan Perangkat", "DESAIN 3D PERANGKAT & SKEMA PENEMPATAN ALAT")
    
    add_card(s8, Inches(0.6), Inches(1.35), Inches(5.9), Inches(3.6))
    img_3d_rakit = os.path.join(base_dir, r"docs\images\GAMBAR3D_1_RAKITAN.png")
    if os.path.exists(img_3d_rakit):
        s8.shapes.add_picture(img_3d_rakit, Inches(0.75), Inches(1.48), Inches(5.6), Inches(3.2))
    tb_3d_1 = s8.shapes.add_textbox(Inches(0.6), Inches(5.05), Inches(5.9), Inches(0.35))
    tf_3d_1 = tb_3d_1.text_frame
    tf_3d_1.margin_left = tf_3d_1.margin_top = tf_3d_1.margin_right = tf_3d_1.margin_bottom = 0
    p = tf_3d_1.paragraphs[0]
    p.text = "Desain 3D CAD Rakitan Keseluruhan Instalasi Bed & Penempatan Sensor"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = CYAN
    
    add_card(s8, Inches(6.8), Inches(1.35), Inches(5.9), Inches(3.6))
    img_3d_box = os.path.join(base_dir, r"hardware\_diag\uji_rakit_iso.png")
    if os.path.exists(img_3d_box):
        s8.shapes.add_picture(img_3d_box, Inches(7.4), Inches(1.48), Inches(4.7), Inches(3.33))
    tb_3d_2 = s8.shapes.add_textbox(Inches(6.8), Inches(5.05), Inches(5.9), Inches(0.35))
    tf_3d_2 = tb_3d_2.text_frame
    tf_3d_2.margin_left = tf_3d_2.margin_top = tf_3d_2.margin_right = tf_3d_2.margin_bottom = 0
    p = tf_3d_2.paragraphs[0]
    p.text = "Desain 3D CAD Enclosure Box IP65 (Bahan PETG) untuk RPi 4B & Kamera CSI"
    p.font.name = "Segoe UI"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = CYAN
    
    add_card(s8, Inches(0.6), Inches(5.45), Inches(5.9), Inches(1.5))
    tb_b1 = s8.shapes.add_textbox(Inches(0.8), Inches(5.55), Inches(5.5), Inches(1.3))
    tf_b1 = tb_b1.text_frame
    tf_b1.word_wrap = True
    tf_b1.margin_left = tf_b1.margin_top = tf_b1.margin_right = tf_b1.margin_bottom = 0
    p = tf_b1.paragraphs[0]
    p.text = "SPESIFIKASI RANGKA & INTEGRASI SENSOR"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = EMERALD
    p = tf_b1.add_paragraph()
    p.text = "• Dimensi bed tanam: 2,0 m × 1,1 m kapasitas 24 lubang tanam kangkung air.\n• Rangka hollow besi square pipe mendukung tiang kantilever kamera top-down.\n• Penempatan probe sensor air (pH, kekeruhan, suhu) pada kolam bawah."
    p.font.name = "Segoe UI"
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_GRAY
    p.space_before = Pt(3)
    
    add_card(s8, Inches(6.8), Inches(5.45), Inches(5.9), Inches(1.5))
    tb_b2 = s8.shapes.add_textbox(Inches(7.0), Inches(5.55), Inches(5.5), Inches(1.3))
    tf_b2 = tb_b2.text_frame
    tf_b2.word_wrap = True
    tf_b2.margin_left = tf_b2.margin_top = tf_b2.margin_right = tf_b2.margin_bottom = 0
    p = tf_b2.paragraphs[0]
    p.text = "FITUR KETAHANAN ENCLOSURE LUAR RUANGAN"
    p.font.name = "Segoe UI"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = AMBER
    p = tf_b2.add_paragraph()
    p.text = "• Material cetak 3D PETG tahan sinar UV dan kelembapan lingkungan akuaponik.\n• Dilengkapi sun-shield (pelindung silau), cable gland M16 kedap air, dan silika gel.\n• Manajemen panas komputasi pasif + proteksi perangkat lunak (thermal guard 75°C)."
    p.font.name = "Segoe UI"
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_GRAY
    p.space_before = Pt(3)

    # =========================================================================
    # SLIDE 9: DASBOR IOT & INTEGRASI KONTROLER FUZZY
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "09 / Integrasi IoT & Kontrol Aktuator", "DASBOR PEMANTAUAN IOT & INTEGRASI KONTROLER FUZZY")
    
    col9_w = Inches(5.9)
    col9_h = Inches(5.46)
    
    # Left container: Web Dashboard Features
    add_card(s9, Inches(0.6), Inches(1.4), col9_w, col9_h)
    tb_dash = s9.shapes.add_textbox(Inches(0.85), Inches(1.6), col9_w - Inches(0.5), col9_h - Inches(0.4))
    tf_dash = tb_dash.text_frame
    tf_dash.word_wrap = True
    tf_dash.margin_left = tf_dash.margin_top = tf_dash.margin_right = tf_dash.margin_bottom = 0
    
    p = tf_dash.paragraphs[0]
    p.text = "FITUR DASBOR PEMANTAUAN WEB REAL-TIME"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = CYAN
    p.space_after = Pt(8)
    
    dash_items = [
        ("Heatmap Interaktif 24 Zona", "Visualisasi grid 4×6 interaktif yang diperbarui tiap 10 menit. Warna petak mewakili status panen, disertai titik status kesehatan daun (hijau, waspada, sakit)."),
        ("Kartu Telemetri Komputasi Tepi", "Menampilkan rata-rata tutupan kanopi bed, jumlah zona siap panen (X/24), nilai agregat PSI, serta suhu SoC Raspberry Pi dengan batas peringatan 75°C."),
        ("Grafik Runtun Waktu (Canvas 2D)", "Menyimpan hingga 144 pembacaan (24 jam) untuk menganalisis tren pertumbuhan vegetasi dan fluktuasi harian tanpa memerlukan pustaka eksternal yang berat."),
        ("Fault-Tolerant Outbox Architecture", "Pola antrean lokal di microSD jika internet terputus; data otomatis tersinkronisasi saat Wi-Fi pulih tanpa risiko kehilangan runtun waktu.")
    ]
    for d_title, d_desc in dash_items:
        p = tf_dash.add_paragraph()
        p.text = d_title
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = EMERALD
        p = tf_dash.add_paragraph()
        p.text = d_desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(8.8)
        p.font.color.rgb = TEXT_GRAY
        p.space_after = Pt(6)

    # Right container: Fuzzy Integration & Safety
    add_card(s9, Inches(6.8), Inches(1.4), col9_w, col9_h)
    tb_fuz = s9.shapes.add_textbox(Inches(7.05), Inches(1.6), col9_w - Inches(0.5), col9_h - Inches(0.4))
    tf_fuz = tb_fuz.text_frame
    tf_fuz.word_wrap = True
    tf_fuz.margin_left = tf_fuz.margin_top = tf_fuz.margin_right = tf_fuz.margin_bottom = 0
    
    p = tf_fuz.paragraphs[0]
    p.text = "INTEGRASI KONTROLER FUZZY & KESELAMATAN"
    p.font.name = "Segoe UI"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = CYAN
    p.space_after = Pt(8)
    
    fuzzy_items = [
        ("Kontrak Data fuzzy_input", "Visi komputer mengekspor payload terstruktur: psi (0–100), psi_maks (zona terburuk), zona_sakit (0–24), dan status validitas frame ke Firebase Firestore."),
        ("Inferensi Fuzzy Sugeno 3 Masukan", "Mikrokontroler aktuator (ESP32 rekan tim) menggabungkan data sensor air (pH, kekeruhan) dengan nilai PSI tanaman untuk menghasilkan rekomendasi % pergantian air."),
        ("Peran PSI dalam Rule-Base", "Parameter air menjadi pemicu utama; nilai PSI tinggi berfungsi menaikkan kelas tindakan air kolam ketika tanaman mulai menunjukkan stres biologis."),
        ("Prinsip Keselamatan (Fail-Safe & Human-in-the-Loop)", "• Data usang > 30 menit otomatis ditolak oleh pengendali.\n• PSI = None tidak pernah diperlakukan sebagai nol.\n• Eksekusi katup/pompa wajib konfirmasi persetujuan pengelola.")
    ]
    for f_title, f_desc in fuzzy_items:
        p = tf_fuz.add_paragraph()
        p.text = f_title
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = AMBER
        p = tf_fuz.add_paragraph()
        p.text = f_desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(8.8)
        p.font.color.rgb = TEXT_GRAY
        p.space_after = Pt(6)

    # =========================================================================
    # SLIDE 10: METRIK EVALUASI, SKENARIO PENGUJIAN, & JADWAL
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "10 / Evaluasi & Validasi Eksperimen", "METRIK EVALUASI, SKENARIO PENGUJIAN, & JADWAL RISET")
    
    # Left container: Metrics & Test Scenarios
    add_card(s10, Inches(0.6), Inches(1.4), Inches(7.5), Inches(5.46))
    tb_ev = s10.shapes.add_textbox(Inches(0.85), Inches(1.55), Inches(7.0), Inches(5.1))
    tf_ev = tb_ev.text_frame
    tf_ev.word_wrap = True
    tf_ev.margin_left = tf_ev.margin_top = tf_ev.margin_right = tf_ev.margin_bottom = 0
    
    p = tf_ev.paragraphs[0]
    p.text = "METRIK EVALUASI SEGMENTASI TERHADAP GROUND TRUTH"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = CYAN
    p.space_after = Pt(4)
    
    p = tf_ev.add_paragraph()
    p.text = "• Presisi (Precision)    : P = TP / (TP + FP)  — proporsi vegetasi terdeteksi yang benar tanaman.\n• Sensitivitas (Recall)   : R = TP / (TP + FN)  — proporsi vegetasi aktual yang berhasil terdeteksi.\n• F1-Score               : F1 = 2 · (P · R) / (P + R)  — penyeimbang antara presisi dan recall.\n• Intersection over Union : IoU = TP / (TP + FP + FN)  — rasio tumpang tindih dengan mask acuan."
    p.font.name = "Consolas"
    p.font.size = Pt(8.8)
    p.font.color.rgb = TEXT_WHITE
    p.space_after = Pt(10)
    
    p = tf_ev.add_paragraph()
    p.text = "4 SKENARIO PENGUJIAN KELAYAKAN PROTOTIPE"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = CYAN
    p.space_after = Pt(4)
    
    scenarios = [
        ("Skenario 1: Uji Stabilitas Iluminasi Terbuka", "Pengujian adaptasi faktor f pada 18 video & 5 foto lintas 3 kondisi pencahayaan harian: pagi (08–09), siang (11–13), dan sore (15–17). Target: variasi deviasi < 5%."),
        ("Skenario 2: Uji Akurasi Segmentasi Multi-Kelas", "Evaluasi piksel hijau, kuning, dan cokelat terhadap 10 mask ground truth anotasi manual. Target performa: F1-Score ≥ 85% dan IoU ≥ 75%."),
        ("Skenario 3: Uji Ketahanan Operasional Burn-In 24 Jam", "Menjalankan siklus inferensi kontinu tiap 10 menit di Raspberry Pi 4B selama 24 jam. Parameter: suhu SoC < 75°C, zero memory-leak, keberhasilan transmisi uplink 100%."),
        ("Skenario 4: Uji Integrasi Data PSI ke Kontroler Fuzzy", "Validasi kesesuaian format pertukaran data JSON, batas kadaluarsa 30 menit, dan konsistensi respon aktuasi pompa air pada mikrokontroler rekan tim.")
    ]
    for sc_title, sc_desc in scenarios:
        p = tf_ev.add_paragraph()
        p.text = sc_title
        p.font.name = "Segoe UI"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = EMERALD
        p = tf_ev.add_paragraph()
        p.text = sc_desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_GRAY
        p.space_after = Pt(4)

    # Right container: Research Timeline
    add_card(s10, Inches(8.3), Inches(1.4), Inches(4.43), Inches(5.46))
    tb_tm = s10.shapes.add_textbox(Inches(8.55), Inches(1.55), Inches(3.93), Inches(5.1))
    tf_tm = tb_tm.text_frame
    tf_tm.word_wrap = True
    tf_tm.margin_left = tf_tm.margin_top = tf_tm.margin_right = tf_tm.margin_bottom = 0
    
    p = tf_tm.paragraphs[0]
    p.text = "JADWAL PELAKSANAAN RISET (2026)"
    p.font.name = "Segoe UI"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = CYAN
    p.space_after = Pt(8)
    
    timeline = [
        ("Juli 2026", "Studi literatur, observasi awal ke Eco Farm UNNES, dan akuisisi video/foto awal."),
        ("Agustus 2026", "Perancangan algoritma Canny-quad, adaptasi HSV, dan formulasi matematis PSI v2.0."),
        ("September 2026", "Desain 3D CAD enclosure IP65, integrasi Raspberry Pi 4B, dan pembuatan dasbor web."),
        ("Oktober 2026", "Pemasangan perangkat di Eco Farm UNNES, uji iluminasi 3 waktu, dan burn-in test 24 jam."),
        ("November 2026", "Uji integrasi kontroler fuzzy, analisis hasil eksperimen, dan penyusunan laporan akhir.")
    ]
    for t_month, t_desc in timeline:
        p = tf_tm.add_paragraph()
        p.text = t_month.upper()
        p.font.name = "Segoe UI"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = AMBER
        p = tf_tm.add_paragraph()
        p.text = t_desc
        p.font.name = "Segoe UI"
        p.font.size = Pt(8.8)
        p.font.color.rgb = TEXT_GRAY
        p.space_after = Pt(8)
        
    p_badge = tf_tm.add_paragraph()
    p_badge.text = "Status Riset: Tahap implementasi pipeline & validasi data lapangan telah mencapai 100% fungsional."
    p_badge.font.name = "Segoe UI"
    p_badge.font.size = Pt(9)
    p_badge.font.italic = True
    p_badge.font.color.rgb = TEXT_WHITE

    prs.save(output_path)
    print(f"10-slide presentation successfully built and saved to: {output_path}")

if __name__ == '__main__':
    out_file = r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\PRESENTASI_PROTOTIPE_FELIX.pptx"
    build_full_deck(out_file)

