import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

# --- PALETTE CONFIGURATION ---
BG_COLOR = RGBColor(10, 14, 23)        # #0A0E17 Dark Slate/Navy
CARD_BG = RGBColor(17, 24, 39)        # #111827 Dark Surface
CARD_BORDER = RGBColor(30, 41, 59)    # #1E293B Subtle Border
CYAN = RGBColor(6, 182, 212)          # #06B6D4 Primary Accent
EMERALD = RGBColor(16, 185, 129)      # #10B981 Green Accent
AMBER = RGBColor(245, 158, 11)        # #F59E0B Warning/Problem Accent
TEXT_WHITE = RGBColor(248, 250, 252)  # #F8FAFC Heading text
TEXT_GRAY = RGBColor(148, 163, 184)   # #94A3B8 Body text
TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B Secondary text

def set_slide_background(slide):
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_COLOR

def add_header(slide, tag_text, title_text):
    # Header tag
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
    
    # Title
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
    
    # Divider line
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

def build_presentation(output_pptx_path):
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
    
    # Left container: 3 Problem Cards
    card1_h = Inches(1.7)
    card_gap = Inches(0.18)
    
    # Problem Item 1
    add_card(s1, Inches(0.6), Inches(1.4), Inches(6.8), card1_h)
    tb = s1.shapes.add_textbox(Inches(0.85), Inches(1.5), Inches(6.3), card1_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p1 = tf.paragraphs[0]
    p1.text = "Heterogenitas Pertumbuhan Kanopi pada Bed Akuaponik"
    p1.font.name = "Segoe UI"
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = CYAN
    p2 = tf.add_paragraph()
    p2.text = "Pada bed tanam kangkung Eco Farm UNNES (2,0 m × 1,1 m), aliran nutrisi menghasilkan dinamika pertumbuhan yang tidak seragam antar titik tanam. Evaluasi gelondongan rata-rata bed mengaburkan zona tanaman yang kekurangan nutrisi atau telah mengalami over-dense."
    p2.font.name = "Segoe UI"
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = TEXT_GRAY
    p2.space_before = Pt(4)
    
    # Problem Item 2
    top2 = Inches(1.4) + card1_h + card_gap
    add_card(s1, Inches(0.6), top2, Inches(6.8), card1_h)
    tb = s1.shapes.add_textbox(Inches(0.85), top2 + Inches(0.1), Inches(6.3), card1_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p1 = tf.paragraphs[0]
    p1.text = "Keterbatasan Pengamatan Visual Petani (Manual & Subjektif)"
    p1.font.name = "Segoe UI"
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = AMBER
    p2 = tf.add_paragraph()
    p2.text = "Penilaian kesiapan panen konvensional bersifat kualitatif dan rentan bias mata pengelola. Gejala klorosis (daun kuning) dan nekrosis (daun busuk/cokelat) kerap baru disadari saat patologi tanaman telah meluas, sehingga mitigasi kualitas air terlambat dilakukan."
    p2.font.name = "Segoe UI"
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = TEXT_GRAY
    p2.space_before = Pt(4)
    
    # Problem Item 3
    top3 = top2 + card1_h + card_gap
    add_card(s1, Inches(0.6), top3, Inches(6.8), card1_h)
    tb = s1.shapes.add_textbox(Inches(0.85), top3 + Inches(0.1), Inches(6.3), card1_h - Inches(0.2))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p1 = tf.paragraphs[0]
    p1.text = "Kebutuhan Sensor Visi Komputer Edge Otomatis & Non-Destruktif"
    p1.font.name = "Segoe UI"
    p1.font.size = Pt(13)
    p1.font.bold = True
    p1.font.color.rgb = EMERALD
    p2 = tf.add_paragraph()
    p2.text = "Diperlukan sistem monitoring berbasis computer vision pada komputasi tepi (Raspberry Pi 4B) yang mengukur tutupan kanopi 24 zona dan memformulasikan Plant Stress Index (PSI) secara kontinyu (tiap 10 menit), objektif, dan siap diintegrasikan dengan kendali aktuator air."
    p2.font.name = "Segoe UI"
    p2.font.size = Pt(10.5)
    p2.font.color.rgb = TEXT_GRAY
    p2.space_before = Pt(4)
    
    # Right container: Image of actual site
    add_card(s1, Inches(7.7), Inches(1.4), Inches(5.03), Inches(5.46))
    img_situasi = os.path.join(base_dir, r"docs\images\Situasi 1.jpg")
    if os.path.exists(img_situasi):
        s1.shapes.add_picture(img_situasi, Inches(7.85), Inches(1.55), Inches(4.73), Inches(3.55))
    
    tb_cap = s1.shapes.add_textbox(Inches(7.85), Inches(5.25), Inches(4.73), Inches(1.4))
    tf_cap = tb_cap.text_frame
    tf_cap.word_wrap = True
    tf_cap.margin_left = tf_cap.margin_top = tf_cap.margin_right = tf_cap.margin_bottom = 0
    p_cap1 = tf_cap.paragraphs[0]
    p_cap1.text = "LOKASI RISET: AQUAPONIK ECO FARM UNNES"
    p_cap1.font.name = "Segoe UI"
    p_cap1.font.size = Pt(10)
    p_cap1.font.bold = True
    p_cap1.font.color.rgb = CYAN
    p_cap2 = tf_cap.add_paragraph()
    p_cap2.text = "Instalasi bed kangkung air (Ipomoea aquatica) 2,0 m × 1,1 m dengan pencahayaan alami matahari terbuka. Menjadi basis observasi, kalibrasi algoritma, serta pengujian prototipe lapangan."
    p_cap2.font.name = "Segoe UI"
    p_cap2.font.size = Pt(9.5)
    p_cap2.font.color.rgb = TEXT_GRAY
    p_cap2.space_before = Pt(3)

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
            "challenge_title": "Tantangan Rekayasa:",
            "challenge": "Distorsi perspektif kamera miring (tilt) serta jitter posisi akibat getaran mekanis pompa dan hembusan angin luar ruangan.",
            "sol_title": "Pendekatan Solusi:",
            "solution": "Deteksi tepi Canny + aproksimasi quad + penstabilan temporal EMA (alpha = 0,2) + rektifikasi homografi planar ke kanvas 1200 × 660 px.",
            "color": CYAN
        },
        {
            "num": "02",
            "title": "Stabilitas Iluminasi Terbuka",
            "question": "Bagaimana menstabilkan segmentasi warna HSV terhadap perubahan iluminasi pagi, siang, dan sore sehingga liputan kanopi per zona konsisten?",
            "challenge_title": "Tantangan Rekayasa:",
            "challenge": "Fluktuasi intensitas matahari ekstrem (pagi redup vs siang terik/glare) yang menyebabkan thresholding statis gagal mendeteksi kanopi.",
            "sol_title": "Pendekatan Solusi:",
            "solution": "Faktor adaptasi dinamis f = mean(V)/128 untuk menggeser batas Saturation dan Value secara linier, dengan menjaga rona Hue tetap invarian.",
            "color": AMBER
        },
        {
            "num": "03",
            "title": "Formulasi Sinyal Indeks Stres (PSI)",
            "question": "Bagaimana mengukur persentase kuning dan cokelat per zona serta merumuskannya menjadi Plant Stress Index (PSI) 0–100 yang siap dibaca pengendali?",
            "challenge_title": "Tantangan Rekayasa:",
            "challenge": "Formula kuantifikasi lama mengalami saturasi dini (mentok di 100) dan noise media tanam gelap yang tertukar sebagai daun mati.",
            "sol_title": "Pendekatan Solusi:",
            "solution": "Model linear tanpa saturasi: PSI = 100 × (0,5Y + B)/N, dilengkapi filter adjasensi nekrosis morfologi kanopi daun hijau.",
            "color": EMERALD
        }
    ]
    
    for idx, r_item in enumerate(rumusan_data):
        left_pos = Inches(0.6) + idx * (col_w + col_gap)
        add_card(s2, left_pos, Inches(1.4), col_w, col_h)
        
        tb = s2.shapes.add_textbox(left_pos + Inches(0.25), Inches(1.6), col_w - Inches(0.5), col_h - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        # Number badge
        p_num = tf.paragraphs[0]
        p_num.text = r_item["num"]
        p_num.font.name = "Segoe UI"
        p_num.font.size = Pt(28)
        p_num.font.bold = True
        p_num.font.color.rgb = r_item["color"]
        
        # Subtitle
        p_title = tf.add_paragraph()
        p_title.text = r_item["title"].upper()
        p_title.font.name = "Segoe UI"
        p_title.font.size = Pt(11)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE
        p_title.space_after = Pt(8)
        
        # Question
        p_q = tf.add_paragraph()
        p_q.text = f'"{r_item["question"]}"'
        p_q.font.name = "Segoe UI"
        p_q.font.size = Pt(10.5)
        p_q.font.italic = True
        p_q.font.color.rgb = TEXT_WHITE
        p_q.space_after = Pt(12)
        
        # Challenge
        p_c1 = tf.add_paragraph()
        p_c1.text = r_item["challenge_title"]
        p_c1.font.name = "Segoe UI"
        p_c1.font.size = Pt(9.5)
        p_c1.font.bold = True
        p_c1.font.color.rgb = r_item["color"]
        p_c2 = tf.add_paragraph()
        p_c2.text = r_item["challenge"]
        p_c2.font.name = "Segoe UI"
        p_c2.font.size = Pt(9.5)
        p_c2.font.color.rgb = TEXT_GRAY
        p_c2.space_after = Pt(10)
        
        # Solution
        p_s1 = tf.add_paragraph()
        p_s1.text = r_item["sol_title"]
        p_s1.font.name = "Segoe UI"
        p_s1.font.size = Pt(9.5)
        p_s1.font.bold = True
        p_s1.font.color.rgb = r_item["color"]
        p_s2 = tf.add_paragraph()
        p_s2.text = r_item["solution"]
        p_s2.font.name = "Segoe UI"
        p_s2.font.size = Pt(9.5)
        p_s2.font.color.rgb = TEXT_GRAY

    # =========================================================================
    # SLIDE 3: ARSITEKTUR & PIPELINE CARA KERJA SISTEM
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "03 / Arsitektur & Rekayasa Sistem", "PIPELINE CARA KERJA SISTEM PROTOTIPE")
    
    # Top Card: Blok Diagram Image
    add_card(s3, Inches(0.6), Inches(1.35), Inches(12.13), Inches(2.75))
    img_blok = os.path.join(base_dir, r"docs\images\blok_diagram.png")
    if os.path.exists(img_blok):
        s3.shapes.add_picture(img_blok, Inches(0.85), Inches(1.45), Inches(11.63), Inches(2.55))
        
    # Bottom Section: 5 Tahapan Pipeline
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
        
        p1 = tf.paragraphs[0]
        p1.text = st_title
        p1.font.name = "Segoe UI"
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = st_color
        p1.space_after = Pt(4)
        
        p2 = tf.add_paragraph()
        p2.text = st_desc
        p2.font.name = "Segoe UI"
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_GRAY

    # =========================================================================
    # SLIDE 4: DETAIL PIPELINE COMPUTER VISION & HASIL IMPLEMENTASI
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "04 / Algoritma Visi Komputer & Bukti Lapangan", "DETAIL PIPELINE COMPUTER VISION & VALIDASI VISUAL")
    
    # Left container: Flowchart
    add_card(s4, Inches(0.6), Inches(1.35), Inches(4.5), Inches(5.6))
    img_flow = os.path.join(base_dir, r"docs\images\flowchart_cv.png")
    if os.path.exists(img_flow):
        s4.shapes.add_picture(img_flow, Inches(0.8), Inches(1.5), Inches(4.1), Inches(5.3))
        
    # Right container: 2 Result Comparison Images
    add_card(s4, Inches(5.3), Inches(1.35), Inches(7.43), Inches(5.6))
    
    tb_res_title = s4.shapes.add_textbox(Inches(5.5), Inches(1.5), Inches(7.0), Inches(0.35))
    tf_rt = tb_res_title.text_frame
    tf_rt.word_wrap = True
    tf_rt.margin_left = tf_rt.margin_top = tf_rt.margin_right = tf_rt.margin_bottom = 0
    p_rt = tf_rt.paragraphs[0]
    p_rt.text = "BUKTI REPRODUKSIBILITAS PADA DATA CITRA LAPANGAN NYATA"
    p_rt.font.name = "Segoe UI"
    p_rt.font.size = Pt(11.5)
    p_rt.font.bold = True
    p_rt.font.color.rgb = CYAN
    
    # Image 1: Frame HP vs Anotasi Grid
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
    
    # Image 2: Video vs Segmentasi Warna
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
    # SLIDE 5: DESAIN 3D CAD PERANGKAT & SKEMA PENEMPATAN ALAT
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "05 / Desain Mekanikal & Penempatan Perangkat", "DESAIN 3D PERANGKAT & SKEMA PENEMPATAN ALAT")
    
    # Left Card: 3D CAD Assembly Bed & Kolam
    add_card(s5, Inches(0.6), Inches(1.35), Inches(5.9), Inches(3.6))
    img_3d_rakit = os.path.join(base_dir, r"docs\images\GAMBAR3D_1_RAKITAN.png")
    if os.path.exists(img_3d_rakit):
        s5.shapes.add_picture(img_3d_rakit, Inches(0.75), Inches(1.48), Inches(5.6), Inches(3.2))
        
    tb_3d_1 = s5.shapes.add_textbox(Inches(0.6), Inches(5.05), Inches(5.9), Inches(0.35))
    tf_3d_1 = tb_3d_1.text_frame
    tf_3d_1.margin_left = tf_3d_1.margin_top = tf_3d_1.margin_right = tf_3d_1.margin_bottom = 0
    p3d_1 = tf_3d_1.paragraphs[0]
    p3d_1.text = "Desain 3D CAD Rakitan Keseluruhan Instalasi Bed & Penempatan Sensor"
    p3d_1.font.name = "Segoe UI"
    p3d_1.font.size = Pt(9.5)
    p3d_1.font.bold = True
    p3d_1.font.color.rgb = CYAN
    
    # Right Card: 3D CAD Enclosure Box IP65
    add_card(s5, Inches(6.8), Inches(1.35), Inches(5.9), Inches(3.6))
    img_3d_box = os.path.join(base_dir, r"hardware\_diag\uji_rakit_iso.png")
    if os.path.exists(img_3d_box):
        s5.shapes.add_picture(img_3d_box, Inches(7.4), Inches(1.48), Inches(4.7), Inches(3.33))
        
    tb_3d_2 = s5.shapes.add_textbox(Inches(6.8), Inches(5.05), Inches(5.9), Inches(0.35))
    tf_3d_2 = tb_3d_2.text_frame
    tf_3d_2.margin_left = tf_3d_2.margin_top = tf_3d_2.margin_right = tf_3d_2.margin_bottom = 0
    p3d_2 = tf_3d_2.paragraphs[0]
    p3d_2.text = "Desain 3D CAD Enclosure Box IP65 (Bahan PETG) untuk RPi 4B & Kamera CSI"
    p3d_2.font.name = "Segoe UI"
    p3d_2.font.size = Pt(9.5)
    p3d_2.font.bold = True
    p3d_2.font.color.rgb = CYAN
    
    # Bottom Technical Specs Container (2 cards)
    add_card(s5, Inches(0.6), Inches(5.45), Inches(5.9), Inches(1.5))
    tb_b1 = s5.shapes.add_textbox(Inches(0.8), Inches(5.55), Inches(5.5), Inches(1.3))
    tf_b1 = tb_b1.text_frame
    tf_b1.word_wrap = True
    tf_b1.margin_left = tf_b1.margin_top = tf_b1.margin_right = tf_b1.margin_bottom = 0
    pb1 = tf_b1.paragraphs[0]
    pb1.text = "SPESIFIKASI RANGKA & INTEGRASI SENSOR"
    pb1.font.name = "Segoe UI"
    pb1.font.size = Pt(10)
    pb1.font.bold = True
    pb1.font.color.rgb = EMERALD
    pb2 = tf_b1.add_paragraph()
    pb2.text = "• Dimensi bed tanam: 2,0 m × 1,1 m kapasitas 24 lubang tanam kangkung air.\n• Rangka hollow besi square pipe mendukung tiang kantilever kamera top-down.\n• Penempatan probe sensor air (pH, kekeruhan, suhu) pada kolam bawah."
    pb2.font.name = "Segoe UI"
    pb2.font.size = Pt(9)
    pb2.font.color.rgb = TEXT_GRAY
    pb2.space_before = Pt(3)
    
    add_card(s5, Inches(6.8), Inches(5.45), Inches(5.9), Inches(1.5))
    tb_b2 = s5.shapes.add_textbox(Inches(7.0), Inches(5.55), Inches(5.5), Inches(1.3))
    tf_b2 = tb_b2.text_frame
    tf_b2.word_wrap = True
    tf_b2.margin_left = tf_b2.margin_top = tf_b2.margin_right = tf_b2.margin_bottom = 0
    pb3 = tf_b2.paragraphs[0]
    pb3.text = "FITUR KETAHANAN ENCLOSURE LUAR RUANGAN"
    pb3.font.name = "Segoe UI"
    pb3.font.size = Pt(10)
    pb3.font.bold = True
    pb3.font.color.rgb = AMBER
    pb4 = tf_b2.add_paragraph()
    pb4.text = "• Material cetak 3D PETG tahan sinar UV dan kelembapan lingkungan akuaponik.\n• Dilengkapi sun-shield (pelindung silau), cable gland M16 kedap air, dan silika gel.\n• Manajemen panas komputasi pasif + proteksi perangkat lunak (thermal guard 75°C)."
    pb4.font.name = "Segoe UI"
    pb4.font.size = Pt(9)
    pb4.font.color.rgb = TEXT_GRAY
    pb4.space_before = Pt(3)

    prs.save(output_pptx_path)
    print(f"Presentation saved successfully to: {output_pptx_path}")

if __name__ == '__main__':
    out_path = r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\PRESENTASI_PROTOTIPE_FELIX.pptx"
    build_presentation(out_path)

