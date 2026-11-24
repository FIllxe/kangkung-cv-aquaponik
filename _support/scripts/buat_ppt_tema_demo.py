# -*- coding: utf-8 -*-
"""Generator PPT presentasi capstone — Tema Demo Segmentasi Warna.
Background putih, aksen hijau/orange/merah (status zona), tata letak bersih.
Slide: judul, latar, tujuan, metode, flowchart, cara kerja, bukti real, 3D design.
Jalankan: python docs/buat_ppt_tema_demo.py
Output: docs/PRESENTASI_TEMA_DEMO_SEGMENTASI.pptx
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "PRESENTASI_TEMA_DEMO_SEGMENTASI.pptx"

# Palet tema Demo Segmentasi Warna
PUTIH   = RGBColor(0xFF, 0xFF, 0xFF)
HIJAU   = RGBColor(0x2E, 0x7D, 0x32)      # sehat
HIJAU_M = RGBColor(0xE8, 0xF5, 0xE9)      # bg hijau muda
ORANGE  = RGBColor(0xE6, 0x8A, 0x00)      # waspada
ORANGE_M= RGBColor(0xFF, 0xF3, 0xE0)      # bg orange muda
MERAH   = RGBColor(0xC6, 0x28, 0x28)      # sakit
MERAH_M = RGBColor(0xFF, 0xEB, 0xEE)      # bg merah muda
ABU     = RGBColor(0x42, 0x42, 0x42)
ABU_M   = RGBColor(0x75, 0x75, 0x75)
ABU_BG  = RGBColor(0xF5, 0xF5, 0xF5)
AKSEN   = RGBColor(0x1B, 0x5E, 0x20)

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW = prs.slide_width
SH = prs.slide_height
TOTAL = 14

def add_rect(slide, l, t, w, h, fill, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(1)
    s.shadow.inherit = False
    return s

def add_round(slide, l, t, w, h, fill, line=None, radius=0.06):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    try:
        s.adjustments[0] = radius
    except Exception:
        pass
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(1)
    s.shadow.inherit = False
    return s

def add_text(slide, l, t, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             space_after=4, line_spacing=1.0, wrap=True):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf = box.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    if isinstance(runs, dict):
        runs = [runs]
    for i, rd in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = rd.get("align", align)
        p.space_after = Pt(rd.get("space_after", space_after))
        p.space_before = Pt(rd.get("space_before", 0))
        p.line_spacing = rd.get("line_spacing", line_spacing)
        segs = rd.get("segs")
        if segs is None:
            segs = [{"text": rd.get("text", ""), "bold": rd.get("bold", False),
                     "color": rd.get("color", ABU), "size": rd.get("size", 14),
                     "italic": rd.get("italic", False)}]
        for sg in segs:
            r = p.add_run(); r.text = sg.get("text", "")
            f = r.font
            f.size = Pt(sg.get("size", rd.get("size", 14)))
            f.bold = sg.get("bold", rd.get("bold", False))
            f.italic = sg.get("italic", rd.get("italic", False))
            f.color.rgb = sg.get("color", rd.get("color", ABU))
            f.name = "Calibri"
    return box

def add_header(slide, kicker, judul, sub="", num=None):
    add_rect(slide, 0, 0, SW, Inches(1.0), PUTIH)
    add_rect(slide, 0, Inches(1.0), SW, Inches(0.06), HIJAU)
    add_text(slide, Inches(0.5), Inches(0.15), Inches(12.0), Inches(0.4),
             [{"text": kicker.upper(), "size": 13, "bold": True, "color": HIJAU}])
    add_text(slide, Inches(0.5), Inches(0.45), Inches(12.0), Inches(0.5),
             [{"text": judul, "size": 26, "bold": True, "color": AKSEN}])
    if sub:
        add_text(slide, Inches(0.5), Inches(0.95), Inches(12.0), Inches(0.25),
                 [{"text": sub, "size": 12, "color": ABU_M, "italic": True}])
    if num is not None:
        add_text(slide, SW - Inches(1.0), SH - Inches(0.4), Inches(0.6), Inches(0.35),
                 [{"text": f"{num}/{TOTAL}", "size": 11, "color": ABU_M, "align": PP_ALIGN.RIGHT}])

def add_img_fit(slide, path, l, t, max_w, max_h):
    path = str(path)
    im = Image.open(path)
    iw, ih = im.size
    ar = iw / ih
    tar_ar = max_w / max_h
    if ar > tar_ar:
        w = max_w
        h = Emu(int(max_w / ar))
    else:
        h = max_h
        w = Emu(int(max_h * ar))
    left = int(l + (max_w - w) / 2)
    top = int(t + (max_h - h) / 2)
    return slide.shapes.add_picture(path, left, top, w, h)

def add_kartu(slide, l, t, w, h, judul, isi, fill=HIJAU_M, jcolor=HIJAU, line=HIJAU,
              isize=14, isize2=11.5, align=PP_ALIGN.LEFT):
    s = add_round(slide, l, t, w, h, fill, line=line)
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = judul
    r.font.size = Pt(isize); r.font.bold = True; r.font.color.rgb = jcolor; r.font.name = "Calibri"
    p2 = tf.add_paragraph(); p2.alignment = align
    r2 = p2.add_run(); r2.text = isi
    r2.font.size = Pt(isize2); r2.font.bold = False; r2.font.color.rgb = ABU; r2.font.name = "Calibri"
    return s

# ============================================================
# SLIDE 1 — JUDUL (Tema Demo Segmentasi Warna)
# ============================================================
s = prs.slides.add_slide(BLANK)
add_rect(s, 0, 0, SW, SH, PUTIH)
add_rect(s, 0, 0, SW, Inches(0.12), HIJAU)
add_rect(s, Inches(0.8), Inches(1.15), Inches(0.08), Inches(1.9), HIJAU)
add_text(s, Inches(1.1), Inches(1.0), Inches(11.5), Inches(0.5),
         [{"text": "PROYEK CAPSTONE — KOMPONEN COMPUTER VISION", "size": 15, "bold": True, "color": HIJAU}])
add_text(s, Inches(1.1), Inches(1.55), Inches(11.5), Inches(1.2),
         [{"text": "Sistem Deteksi Kesiapan Panen & Kesehatan Daun Kangkung Aquaponik", "size": 30, "bold": True, "color": AKSEN}])
add_text(s, Inches(1.1), Inches(2.9), Inches(11.5), Inches(0.5),
         [{"text": "Bed Aquaponik 2 m × 1,1 m  •  Grid 4×6 (24 Zona)  •  Segmentasi HSV Adaptif  •  PSI 0–100",
           "size": 15, "color": ABU_M}])
add_rect(s, Inches(0.8), Inches(3.75), Inches(11.7), Inches(0.02), ABU_BG)
add_text(s, Inches(0.8), Inches(4.0), Inches(11.7), Inches(2.2), [
    {"text": "Rangkap presentasi:", "size": 14, "bold": True, "color": HIJAU, "space_after": 6},
    {"text": "• Metode computer vision (HSV adaptif + EMA)", "size": 13, "color": ABU, "space_after": 4},
    {"text": "• Flowchart & cara kerja sistem", "size": 13, "color": ABU, "space_after": 4},
    {"text": "• Bukti real: video beranotasi, foto lapangan, timeseries", "size": 13, "color": ABU, "space_after": 4},
    {"text": "• Desain 3D enclosure & mounting kamera", "size": 13, "color": ABU},
], space_after=4)
add_text(s, Inches(0.8), SH - Inches(0.6), Inches(11.7), Inches(0.4),
         [{"text": "Sumber: output pipeline asli, laporan progres, dan render desain 3D dari repositori project",
           "size": 10.5, "italic": True, "color": ABU_M}])
# ============================================================
# SLIDE 2 — LATAR BELAKANG & MASALAH
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Latar Belakang", "Masa Panen & Kesehatan per Zona Sulit Dilihat Secara Konsisten",
           "Petani butuh peta 24 zona, bukan satu angka keseluruhan bed", num=2)
add_kartu(s, Inches(0.5), Inches(1.45), Inches(6.0), Inches(2.3), "Masalah di Lapangan",
          "Bed tidak seragam (tepi vs tengah berbeda). Penilaian mata subjektif dan melelahkan. Panen terlalu dini merugikan biomassa; terlambat menurunkan mutu.", fill=HIJAU_M, jcolor=HIJAU, line=HIJAU)
add_kartu(s, Inches(6.8), Inches(1.45), Inches(6.0), Inches(2.3), "Hambatan Teknis",
          "Cahaya berubah (pagi/siang/sore + bayangan) membuat HSV statis gagal. Tanpa deep learning; harus jalan di Raspberry Pi 4B.", fill=ORANGE_M, jcolor=ORANGE, line=ORANGE)
add_text(s, Inches(0.5), Inches(4.05), Inches(12.3), Inches(2.9), [
    {"text": "Rumusan masalah", "size": 15, "bold": True, "color": HIJAU, "space_after": 3},
    {"text": "1) Deteksi panen per zona otomatis?  2) Stabilisasi coverage lintas cahaya?  3) Skor kuning/coklat + stres sebagai input fuzzy?", "size": 13, "color": ABU, "space_after": 10},
    {"text": "Batasan scope", "size": 15, "bold": True, "color": HIJAU, "space_after": 3},
    {"text": "Satu bed kangkung aquaponik, kamera top-down, tanpa deep learning, dijalankan pada Raspberry Pi 4B.", "size": 13, "color": ABU},
])
# ============================================================
# SLIDE 3 — TUJUAN & LUARAN
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Tujuan & Luaran", "Target Prototipe & Apa yang Akan Dihasilkan", "Setiap tujuan dilengkapi berkas bukti, tidak ada klaim kosong", num=3)
items = [
    ("T1", "Grid deteksi otomatis", "Bed dicari otomatis via Canny + homografi, dibagi 4×6 = 24 zona.", HIJAU_M, HIJAU),
    ("T2", "HSV adaptif stabil cahaya", "f = mean(V)/128 menyesuaikan S/V per frame; coverage stabil ±38% (puncak 65%).", ORANGE_M, ORANGE),
    ("T3", "Kesehatan daun + PSI", "Kuning (klorosis) & coklat (nekritis) per zona; PSI 0–100 sebagai input fuzzy.", MERAH_M, MERAH),
    ("T4", "Deploy Pi + Dashboard", "Raspberry Pi 4B + kamera CSI → Firebase → web dashboard live monitoring.", HIJAU_M, HIJAU),
]
pos = [(0.5, 1.45), (6.8, 1.45), (0.5, 4.0), (6.8, 4.0)]
for (l, t), (kode, judul, isi, bgc, jc) in zip(pos, items):
    add_kartu(s, Inches(l), Inches(t), Inches(6.0), Inches(2.3),
              f"{kode} — {judul}", isi, fill=bgc, jcolor=jc, line=jc, isize=13.5, isize2=11, align=PP_ALIGN.LEFT)
add_text(s, Inches(0.5), Inches(6.5), Inches(12.3), Inches(0.6),
         [{"text": "Luaran: MP4 beranotasi • CSV timeseries • JSON laporan • payload bed_readings (Firebase) • dashboard web • box kamera 3D-print",
           "size": 13, "bold": True, "color": HIJAU}])
# ============================================================
# SLIDE 4 — METODE (1/2)
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Metode (1/2)", "Pipeline Computer Vision — 4 Tahap Utama",
           "Dari frame kamera hingga keputusan kesiapan panen per zona", num=4)
steps = [
    ("1. Deteksi Bed", "Canny edge → deteksi quad 4 sudut → homografi (warp perspektif). Fallback HSV-mask jika quad gagal.", HIJAU_M, HIJAU),
    ("2. Grid 4×6", "Bed yang sudah diwarp dibagi 24 zona (4 kolom × 6 baris). Tiap zona diproses terpisah.", ORANGE_M, ORANGE),
    ("3. HSV Adaptif", "f = mean(V)/128 geser ambang S/V per frame. Stabilisasi coverage lintas cahaya rata-rata 38%.", MERAH_M, MERAH),
    ("4. Segmentasi Warna", "Hijau = tanaman; Kuning H 21–34 (klorosis); Coklat H 8–20 + adjacency kanopi (nekrosis).", HIJAU_M, HIJAU),
]
pos = [(0.5, 1.45), (6.8, 1.45), (0.5, 3.95), (6.8, 3.95)]
for (l, t), (jdl, isi, bgc, jc) in zip(pos, steps):
    add_kartu(s, Inches(l), Inches(t), Inches(6.0), Inches(2.3), jdl, isi, fill=bgc, jcolor=jc, line=jc, isize=13.5, isize2=11, align=PP_ALIGN.LEFT)
add_text(s, Inches(0.5), Inches(6.45), Inches(12.3), Inches(0.6),
         [{"text": "EMA α = 0,2 untuk stabilisasi temporal (jitter sudut turun −53%). Output: coverage + %kuning + %coklat per zona + PSI.",
           "size": 12.5, "color": ABU_M, "italic": True}])
# ============================================================
# SLIDE 5 — METODE (2/2)
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Metode (2/2)", "Skor Zona, PSI, dan Kontrak Fuzzy", "Perhitungan indeks stres tanaman yang dikirim ke kontroler fuzzy", num=5)
add_kartu(s, Inches(0.5), Inches(1.45), Inches(6.0), Inches(2.3),
          "Skor Zona per Frame",
          "Zona = (piksel hijau zona / piksel bed zona) × 100%. Kategori: belum / hampir / siap / harus panen berdasarkan coverage ambang.",
          fill=HIJAU_M, jcolor=HIJAU, line=HIJAU, isize=13, isize2=11, align=PP_ALIGN.LEFT)
add_kartu(s, Inches(6.8), Inches(1.45), Inches(6.0), Inches(2.3),
          "PSI (Plant Stress Index)",
          "PSI = 100 × (0,5·Y + B) / N  (N = total piksel tanaman, Y = kuning, B = coklat). Agregasi jumlahkan piksel semua zona DULU, baru hitung PSI.",
          fill=ORANGE_M, jcolor=ORANGE, line=ORANGE, isize=13, isize2=11, align=PP_ALIGN.LEFT)
add_kartu(s, Inches(0.5), Inches(4.0), Inches(6.0), Inches(2.3),
          "Kontrak Firebase v1.1",
          "Kirim: psi, psi_maks (zona terburuk), valid, reason, psi_versi 2.0, frame_id, captured_at_ms, zona_sakit. Tanpa aktuasi otomatis — ACC manusia wajib.",
          fill=MERAH_M, jcolor=MERAH, line=MERAH, isize=13, isize2=11, align=PP_ALIGN.LEFT)
add_kartu(s, Inches(6.8), Inches(4.0), Inches(6.0), Inches(2.3),
          "Keamanan Data",
          "Stale > 30 menit ditolak. Null = tahan tindakan. Anti-spam 60 menit. Skema bed_readings versi 1.1 telah diverifikasi di Pi.",
          fill=HIJAU_M, jcolor=HIJAU, line=HIJAU, isize=13, isize2=11, align=PP_ALIGN.LEFT)
# ============================================================
# SLIDE 6 — FLOWCHART
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Flowchart", "Diagram Alir Sistem — Siklus 10 Menit",
           "Simbol baku: elips START/END, belah ketupat keputusan, kotak proses, panah aliran", num=6)
flow_img = ROOT / "docs" / "BIMBINGAN3_FLOWCHART_SISTEM.png"
if flow_img.exists():
    add_img_fit(s, flow_img, Inches(0.5), Inches(1.45), Inches(12.3), Inches(5.2))
else:
    add_text(s, Inches(0.5), Inches(1.45), Inches(12.3), Inches(5.2),
             [{"text": "[Gambar flowchart tidak ditemukan — jalankan docs/buat_flowchart_bimbingan3.py terlebih dahulu]",
               "size": 14, "color": ABU_M, "align": PP_ALIGN.CENTER}])
add_text(s, Inches(0.5), Inches(6.85), Inches(12.3), Inches(0.4),
         [{"text": "Sumber: raspi/kangkung_pi.py::siklus() — thermal guard → capture → CV → PSI → Firebase → dashboard + fuzzy (tidak ada aktuasi otomatis).",
           "size": 11, "italic": True, "color": ABU_M}])
# ============================================================
# SLIDE 7 — CARA KERJA
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Cara Kerja", "Alur Operasi Sistem Secara Rinci", "Dari pemasangan kamera hingga data muncul di dashboard", num=7)
cara = [
    ("1. Pasang Kamera", "Kamera CSI IR 5MP dipasang di atas bed (top-down, ~2,5 m) dalam enclosure PETG IP65 dengan sun shield.", HIJAU),
    ("2. Capture Setiap 10 Menit", "Pi ambil 1 frame, warmup AE/AWB, resize ke 960 px untuk hemat CPU. Thermal guard menunda jika SoC > 75°C.", ORANGE),
    ("3. Deteksi & Segmentasi", "Cari bed via Canny + warp → grid 4×6 → HSV adaptif → hitung coverage, %kuning, %coklat per zona.", HIJAU),
    ("4. Hitung PSI & Payload", "Gabungkan piksel semua zona → PSI 0–100 → buat JSON payload + snapshot JPEG → simpan outbox.", ORANGE),
    ("5. Kirim Firebase", "Upload ke Firestore (bed_readings) + Storage (snapshot). Jika offline, antre di outbox dan kirim ulang saat online.", HIJAU),
    ("6. Dashboard & Fuzzy", "Web dashboard menampilkan heatmap 4×6 + grafik 24 jam + kartu PSI. Teman mengambil fuzzy_input untuk pengendalian pompa.", ORANGE),
]
pos = [(0.5, 1.45), (6.8, 1.45), (0.5, 3.1), (6.8, 3.1), (0.5, 4.75), (6.8, 4.75)]
for (l, t), (jdl, isi, acolor) in zip(pos, cara):
    add_kartu(s, Inches(l), Inches(t), Inches(6.0), Inches(1.5), jdl, isi, fill=PUTIH, jcolor=ABU, line=acolor, isize=12.5, isize2=10.5, align=PP_ALIGN.LEFT)
# ============================================================
# SLIDE 8 — ARSITEKTUR
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Arsitektur Sistem", "Edge (Pi) → Cloud (Firebase) → Dashboard (Web)",
           "Arsitektur edge-to-cloud tanpa layanan masuk; Pi hanya mengirim data", num=8)
arch = [
    ("Edge — Raspberry Pi 4B", "Debian 13, Python 3.13, venv. OpenCV 4.10 + NumPy + Firebase Admin. Kamera CSI IR 5MP via libcamera/Picamera2.", HIJAU_M, HIJAU),
    ("Pipeline CV", "adaptive_bed.py + kangkung_cv.py. Deteksi bed → warp → grid → HSV adaptif → PSI → JSON 2–3 KB per siklus.", ORANGE_M, ORANGE),
    ("Cloud — Firebase", "Firestore koleksi bed_readings (skema v1.1) + Storage snapshot JPEG. Multi-user read-only, tanpa login.", HIJAU_M, HIJAU),
    ("Dashboard Web", "Statis (tanpa build): heatmap 4×6, grafik 24 jam (144 dokumen), distribusi zona, kartu PSI (tinggi = stres).", ORANGE_M, ORANGE),
    ("Teman — Fuzzy + IoT", "Mengambil fuzzy_input dari payload. ESP32 + pompa air dipadu kontroler fuzzy + ACC manusia.", HIJAU_M, HIJAU),
    ("Offline Guard", "Outbox antrean saat tidak ada internet; auto-sync saat online. Systemd user service auto-start + auto-restart.", ORANGE_M, ORANGE),
]
pos = [(0.5, 1.45), (6.8, 1.45), (0.5, 3.0), (6.8, 3.0), (0.5, 4.55), (6.8, 4.55)]
for (l, t), (jdl, isi, bgc, jc) in zip(pos, arch):
    add_kartu(s, Inches(l), Inches(t), Inches(6.0), Inches(1.35), jdl, isi, fill=bgc, jcolor=jc, line=jc, isize=11.5, isize2=9.5, align=PP_ALIGN.LEFT)
# ============================================================
# SLIDE 9 — BUKTI REAL (1/2) — Demo Segmentasi Warna
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Bukti Real (1/2)", "Demo Segmentasi Warna — Output Pipeline dari Foto Lapangan Asli",
           "Semua bukti diambil langsung dari output proses video asli — tidak ada hasil AI-generatif", num=9)
add_img_fit(s, ROOT / "output" / "ppt_asli" / "01_asli_vs_anotasi.jpg", Inches(0.5), Inches(1.45), Inches(6.0), Inches(2.6))
add_img_fit(s, ROOT / "output" / "ppt_asli" / "02_foto_vs_segmentasi.jpg", Inches(6.8), Inches(1.45), Inches(6.0), Inches(2.6))
add_img_fit(s, ROOT / "output" / "ppt_asli" / "03_timeseries_IMG5159.png", Inches(0.5), Inches(4.25), Inches(6.0), Inches(2.5))
add_img_fit(s, ROOT / "output" / "ppt_asli" / "05_tabel_PSI_5foto.png", Inches(6.8), Inches(4.25), Inches(6.0), Inches(2.5))
add_text(s, Inches(0.5), Inches(6.9), Inches(12.3), Inches(0.4),
         [{"text": "Kiri atas: asli vs anotasi  •  Kanan atas: foto vs segmentasi  •  Kiri bawah: timeseries 763 frame  •  Kanan bawah: tabel PSI 5 foto lapangan",
           "size": 11, "italic": True, "color": ABU_M, "align": PP_ALIGN.CENTER}])
# ============================================================
# SLIDE 10 — BUKTI REAL (2/2)
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Bukti Real (2/2)", "Tren 5 Foto Lapangan & Video Beranotasi",
           "Tren coverage naik logis sesuai pertumbuhan kangkung; tanpa manipulasi data", num=10)
add_img_fit(s, ROOT / "output" / "ppt_asli" / "04_tren_5foto_asli.png", Inches(0.5), Inches(1.45), Inches(6.0), Inches(2.8))
add_img_fit(s, ROOT / "output" / "ppt_asli" / "frame_IMG5388_250.jpg", Inches(6.8), Inches(1.45), Inches(6.0), Inches(2.8))
add_text(s, Inches(0.5), Inches(4.45), Inches(12.3), Inches(2.3), [
    {"text": "Bukti yang tersedia:", "size": 14, "bold": True, "color": HIJAU, "space_after": 5},
    {"text": "• 18 video MP4 beranotasi (termasuk IMG_5159, IMG_5388, IMG_4462, dst.)", "size": 12.5, "color": ABU, "space_after": 3},
    {"text": "• 5 foto bed lapangan (bed_01..05): semua sehat, PSI 0–0,1, 0 zona sakit", "size": 12.5, "color": ABU, "space_after": 3},
    {"text": "• CSV timeseries per zona + JSON laporan per sesi", "size": 12.5, "color": ABU, "space_after": 3},
    {"text": "• Demo 2 video side-by-side + uji dummy kuning/coklat (hanya verifikasi fungsi, diletakkan appendix)", "size": 12.5, "color": ABU},
], space_after=3)
# ============================================================
# SLIDE 11 — DESAIN 3D (1/2)
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Desain 3D (1/2)", "Enclosure Kamera & Mounting — Model OpenSCAD",
           "Semua part dirancang dari nol dengan params.scad; dicetak PETG, IP65, sun shield", num=11)
add_img_fit(s, ROOT / "hardware" / "renders" / "HD_rakit_iso.png", Inches(0.5), Inches(1.45), Inches(6.1), Inches(3.0))
add_img_fit(s, ROOT / "hardware" / "renders" / "HD_rakit_miring.png", Inches(6.7), Inches(1.45), Inches(6.1), Inches(3.0))
add_img_fit(s, ROOT / "hardware" / "renders" / "HD_part_box.png", Inches(0.5), Inches(4.65), Inches(6.1), Inches(2.1))
add_img_fit(s, ROOT / "hardware" / "renders" / "HD_part_lengan.png", Inches(6.7), Inches(4.65), Inches(6.1), Inches(2.1))
add_text(s, Inches(0.5), Inches(6.9), Inches(12.3), Inches(0.4),
         [{"text": "Kiri: rakitan isometrik + part box (enclosure)  •  Kanan: rakitan miring + lengan mounting. Render 300 dpi, latar putih.",
           "size": 11, "italic": True, "color": ABU_M, "align": PP_ALIGN.CENTER}])
# ============================================================
# SLIDE 12 — DESAIN 3D (2/2)
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Desain 3D (2/2)", "Ledakan, X-Ray, dan Detail Partisi",
           "Exploded view menunjukkan susunan part; X-Ray verifikasi clearance antar komponen", num=12)
add_img_fit(s, ROOT / "hardware" / "renders" / "HD_ledakan_iso.png", Inches(0.5), Inches(1.45), Inches(6.1), Inches(3.0))
add_img_fit(s, ROOT / "hardware" / "renders" / "HD_xray_iso.png", Inches(6.7), Inches(1.45), Inches(6.1), Inches(3.0))
add_img_fit(s, ROOT / "hardware" / "renders" / "HD_part_jepit.png", Inches(0.5), Inches(4.65), Inches(6.1), Inches(2.1))
add_img_fit(s, ROOT / "hardware" / "renders" / "HD_part_tutup.png", Inches(6.7), Inches(4.65), Inches(6.1), Inches(2.1))
add_text(s, Inches(0.5), Inches(6.9), Inches(12.3), Inches(0.4),
         [{"text": "Kiri: exploded view + part jepit kamera  •  Kanan: X-Ray transparan + tutup box. Semua STL siap dicetak (100% skala, tanpa support).",
           "size": 11, "italic": True, "color": ABU_M, "align": PP_ALIGN.CENTER}])
# ============================================================
# SLIDE 13 — HASIL & RENCANA
# ============================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Hasil & Rencana", "Sudah Tercapai vs Belum (Roadmap ke Sidang Akhir)",
           "Jujur tentang status prototipe menambah nilai lebih pada evaluasi", num=13)
add_kartu(s, Inches(0.5), Inches(1.45), Inches(6.0), Inches(2.3),
          "SUDAH (dengan bukti)", "18 video, jitter −53%, kesehatan 100%, Pi test OK, Firebase v1.1, dashboard, 53 paper, STL siap dicetak.",
          fill=HIJAU_M, jcolor=HIJAU, line=HIJAU, isize=12.5, isize2=10.5, align=PP_ALIGN.LEFT)
add_kartu(s, Inches(6.8), Inches(1.45), Inches(6.0), Inches(2.3),
          "BELUM (roadmap)", "GT 5 gambar + F1/IoU (Sep), validasi ambang (Okt), burn-in 24 jam outdoor (Okt), Bab 4–5 (Nov).",
          fill=ORANGE_M, jcolor=ORANGE, line=ORANGE, isize=12.5, isize2=10.5, align=PP_ALIGN.LEFT)
add_text(s, Inches(0.5), Inches(4.05), Inches(12.3), Inches(2.6), [
    {"text": "Tool siap dieksekusi", "size": 14, "bold": True, "color": HIJAU, "space_after": 3},
    {"text": "buat_gt.py → evaluasi_segmentasi.py → bandingkan_metode.py. Target F1 0,85–0,95.", "size": 12.5, "color": ABU, "space_after": 10},
    {"text": "Risiko + mitigasi", "size": 14, "bold": True, "color": HIJAU, "space_after": 3},
    {"text": "Hujan > fallback + shield. Panas > guard + heatsink. Offline > outbox antrean.", "size": 12.5, "color": ABU},
])
# ============================================================
# SLIDE 14 — KESIMPULAN
# ============================================================
s = prs.slides.add_slide(BLANK)
add_rect(s, 0, 0, SW, SH, PUTIH)
add_rect(s, 0, 0, SW, Inches(0.12), HIJAU)
add_text(s, Inches(0.8), Inches(0.9), Inches(11.7), Inches(0.5),
         [{"text": "KESIMPULAN", "size": 16, "bold": True, "color": HIJAU}])
add_text(s, Inches(0.8), Inches(1.35), Inches(11.7), Inches(1.0),
         [{"text": "Sistem computer vision per zona berjalan end-to-end: stabil terhadap cahaya, sehat/sakit tepat zona, PSI siap untuk kontroler fuzzy.",
           "size": 24, "bold": True, "color": AKSEN}])
add_rect(s, Inches(0.8), Inches(2.6), Inches(11.7), Inches(0.02), ABU_BG)
add_text(s, Inches(0.8), Inches(2.85), Inches(11.7), Inches(1.8), [
    {"text": "Output siap disampaikan:", "size": 14, "bold": True, "color": HIJAU, "space_after": 6},
    {"text": "• Peta kesiapan panen 24 zona + kesehatan daun per zona", "size": 13, "color": ABU, "space_after": 4},
    {"text": "• PSI 0–100 sebagai input fuzzy (pompa air, bagian teman)", "size": 13, "color": ABU, "space_after": 4},
    {"text": "• Paket deploy Raspberry Pi + dashboard web + enclosure 3D-print", "size": 13, "color": ABU},
], space_after=4)
add_text(s, Inches(0.8), SH - Inches(0.7), Inches(11.7), Inches(0.5),
         [{"text": "Terima kasih — mohon arahan dan masukan dari penguji.", "size": 16, "bold": True, "color": HIJAU}],
         align=PP_ALIGN.CENTER)

prs.save(str(OUT))
print(f"OK -> {OUT} ({len(prs.slides)} slide)")