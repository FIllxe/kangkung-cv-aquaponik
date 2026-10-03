"""Draf Proposal Prototipe Bab 1-3 — CV (p1: setup+helpers+sampul)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document()
st = doc.styles["Normal"]
st.font.name = "Times New Roman"; st.font.size = Pt(12)
def judul_tengah(teks, size=16, bold=True):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(teks); r.bold = bold; r.font.size = Pt(size); return p
def apar(items, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=12):
    p = doc.add_paragraph(); p.alignment = align
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(size)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def bld(t): return (t, False, True)
def par(teks):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(teks); r.font.size = Pt(12); return p
for _ in range(2): doc.add_paragraph()
judul_tengah("SISTEM COMPUTER VISION DETEKSI KESIAPAN PANEN KANGKUNG AQUAPONIK BERBASIS SEGMENTASI HSV ADAPTIF DAN INDEKS STRES TANAMAN PADA GRID 4x6", 15)
doc.add_paragraph()
judul_tengah("Proposal Prototipe", 13)
judul_tengah("diajukan sebagai salah satu syarat untuk memperoleh gelar Sarjana Teknik", 11, False)
judul_tengah("oleh", 11, False)
judul_tengah("[NAMA LENGKAP]", 13)
judul_tengah("NIM. [NOMOR INDUK MAHASISWA]", 12)
judul_tengah("PROGRAM STUDI TEKNIK KOMPUTER", 12)
judul_tengah("FAKULTAS TEKNIK", 12)
judul_tengah("UNIVERSITAS NEGERI SEMARANG", 12)
judul_tengah("2026", 12)
doc.add_page_break()
judul_tengah("PERSETUJUAN PEMBIMBING", 13)
apar([nor("Prototipe berjudul SISTEM COMPUTER VISION DETEKSI KESIAPAN PANEN KANGKUNG AQUAPONIK BERBASIS SEGMENTASI HSV ADAPTIF DAN INDEKS STRES TANAMAN PADA GRID 4x6 yang disusun oleh")])
apar([bld("Nama : "), nor("[NAMA LENGKAP]")])
apar([bld("NIM : "), nor("[NOMOR INDUK MAHASISWA]")])
apar([bld("Prodi/Fakultas : "), nor("Teknik Komputer/Teknik")])
apar([nor("telah disetujui untuk diajukan ke penilaian proposal prototipe.")])
apar([nor("Semarang, [TANGGAL]")])
apar([nor("Pembimbing,")])
for _ in range(4): doc.add_paragraph()
apar([nor("[NAMA PEMBIMBING, GELAR]")]); apar([nor("NIP. [NOMOR INDUK PEGAWAI]")])
doc.add_page_break()
doc.save(str(OUT))
print("P1 OK ->", OUT)
judul_tengah("DAFTAR ISI", 13)
for b in ["HALAMAN JUDUL ... ii","PERSETUJUAN PEMBIMBING ... iii","DAFTAR ISI ... iv","DAFTAR TABEL ... v","DAFTAR GAMBAR ... vi","DAFTAR ISTILAH DAN SINGKATAN ... vii","BAB 1  PENDAHULUAN ... 1","    1.1  Latar Belakang ... 1","    1.2  Rumusan Masalah ... 3","    1.3  Tujuan Prototipe ... 3","    1.4  Manfaat Prototipe ... 4","    1.5  Potensi Dampak Fungsional/Komersial ... 4","BAB 2  KAJIAN PUSTAKA ... 6","    2.1  Tinjauan Pustaka ... 6","    2.2  Landasan Teoretik ... 8","BAB 3  METODE PELAKSANAAN ... 13","    3.1  Lokasi Riset ... 13","    3.2  Bahan dan Alat ... 13","    3.3  Arsitektur Sistem ... 14","    3.4  Diagram Alir ... 15","    3.5  Skema Pemasangan ... 16","    3.6  Prinsip Kerja Algoritma ... 16","    3.7  Metrik dan Skenario Pengujian ... 18","DAFTAR PUSTAKA ... 20","LAMPIRAN ... 22"]:
    par(b)
doc.add_page_break()
"""Draf Proposal CV (p2: daftar tabel/gambar/singkatan)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def judul_tengah(teks, size=13, bold=True):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(teks); r.bold = bold; r.font.size = Pt(size); return p
def par(teks):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(teks); r.font.size = Pt(12); return p
def buat_tabel(header, rows):
    t = doc.add_table(rows=1+len(rows), cols=len(header))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(header):
        r = t.cell(0, j).paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(11)
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            r = t.cell(i, j).paragraphs[0].add_run(v); r.font.size = Pt(11)
    doc.add_paragraph(); return t
judul_tengah("DAFTAR TABEL")
for b in ["Tabel 2.1  Perbandingan penelitian terdahulu ... 7","Tabel 3.1  Perangkat keras dan spesifikasinya ... 13","Tabel 3.2  Perangkat lunak dan pustaka ... 14","Tabel 3.3  Skenario pengujian kelayakan ... 18"]:
    par(b)
doc.add_page_break()
judul_tengah("DAFTAR GAMBAR")
for b in ["Gambar 3.1  Blok diagram sistem ... 14","Gambar 3.2  Diagram alir pipeline ... 15","Gambar 3.3  Skema pemasangan kamera ... 16","Gambar 3.4  Bukti frame HP terhadap keluaran pipeline ... 17","Gambar 3.5  Bukti foto lapangan terhadap keluaran segmentasi ... 17"]:
    par(b)
doc.add_page_break()
judul_tengah("DAFTAR ISTILAH DAN SINGKATAN")
buat_tabel(["Singkatan", "Kepanjangan", "Keterangan"], [
 ["HSV", "Hue Saturation Value", "Ruang warna segmentasi"],
 ["EMA", "Exponential Moving Average", "Perata temporal, Persamaan 2.5"],
 ["PSI", "Plant Stress Index", "Indeks stres 0-100, Persamaan 2.6"],
 ["F1", "Harmonic mean presisi-recall", "Metrik evaluasi, Persamaan 2.8"],
 ["IoU", "Intersection over Union", "Metrik evaluasi, Persamaan 2.9"],
 ["RPi", "Raspberry Pi", "Komputer papan tunggal 4B untuk deploy"],
 ["CSI", "Camera Serial Interface", "Antar muka kamera ov5647"],
 ["URL", "Uniform Resource Locator", "Alamat dokumen Firestore/Storage"],
])
doc.add_page_break()
doc.save(str(OUT))
print("P2 OK")
"""Draf Proposal CV (p3: Bab 1)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h1(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t.upper())
    r.bold = True; r.font.size = Pt(13); return p
def h2(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.font.size = Pt(12); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def par(t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(t); r.font.size = Pt(12); return p
h1("BAB 1", "Pendahuluan")
h2("1.1", "Latar Belakang")
apar([nor("Penilaian kesiapan panen kangkung pada bed aquaponik berukuran 2 m x 1,1 m dilakukan secara visual oleh petani. Penilaian visual tersebut bersifat subjektif sehingga keputusan panen antarpetani dan antarbed tidak konsisten. Bed yang sama dinilai berbeda oleh penilai yang berbeda, sedangkan bed tidak tumbuh seragam antara bagian tepi dan bagian tengah. Akibatnya panen terlalu dini menurunkan biomassa, sedangkan panen yang terlambat menurunkan mutu daun. Permasalahan tersebut menuntut peta kesiapan panen per zona yang objektif dan berulang. Prototipe ini membagi bed menjadi grid 4x6 atau 24 zona dan menilai tiap zona secara terpisah sehingga panen selektif per zona dapat direncanakan.")])
apar([nor("Risiko panen dinilai dari tutupan kanopi ("), it("canopy cover"), nor("). Tutupan kanopi berkorelasi dengan biomassa dan fase tumbuh sehingga ambang tutupan dipakai sebagai kriteria panen pada berbagai komoditas daun (Jain "), it("et al."), nor(", 2024; Sharma "), it("et al."), nor(", 2025). Tantangan utama pengukuran tutupan di lapangan adalah perubahan iluminasi. Cahaya pagi, siang, dan sore mengubah komponen terang citra sehingga segmentasi warna statis menghasilkan liputan yang melompat walaupun tanamannya sama. Penelitian ini merumuskan faktor adaptasi iluminasi "), it("f"), nor(" yang dihitung dari rata-rata komponen "), it("Value"), nor(" tiap frame sehingga ambang "), it("Saturation"), nor(" dan "), it("Value"), nor(" mengikuti kondisi cahaya tanpa menggeser "), it("Hue"), nor(" yang menyimpan informasi warna daun. Pendekatan tersebut diuji pada 18 video lapangan dan lima foto bed tahap seedling sampai ready dengan liputan 0,9 persen sampai 22,6 persen.")])
apar([nor("Gejala daun menguning atau klorosis dan jaringan mati atau nekrosis sering disadari setelah menyebar. Klorosis ditandai pergeseran warna ke rentang kuning, sedangkan nekrosis ditandai bercak coklat yang menempel pada kanopi. Woebbecke "), it("et al."), nor(" (1995) merumuskan rentang "), it("Hue"), nor(" hijau tanaman terhadap tanah dan gulma sebagai dasar segmentasi vegetasi. Prototipe ini memakai rentang kuning H 21-34 dan coklat H 8-20 yang dinormalkan terhadap ambang sakit 25 persen dan 8 persen menjadi Indeks Stres Tanaman atau "), it("Plant Stress Index"), nor(" (PSI) 0-100 sebagai keluaran untuk pengendali. Lima foto lapangan yang tersedia seluruhnya sehat dengan PSI 0-0,1 sehingga foto sakit asli dan mask "), it("ground truth"), nor(" lima gambar menjadi agenda validasi berikutnya. Perbedaan dengan penelitian terdahulu terletak pada gabungan empat hal dalam satu prototipe ringan tanpa pembelajaran mendalam atau "), it("deep learning"), nor(": grid panen per zona, adaptasi iluminasi, skor stres siap kendali, dan paket deploy komputer papan tunggal di lapangan.")])
h2("1.2", "Rumusan Masalah")
par("Berdasarkan latar belakang tersebut, rumusan masalah penelitian ini adalah:")
par("1. Bagaimana mendeteksi bed dan membagi citra menjadi grid 4x6 secara otomatis dari kamera atas?")
par("2. Bagaimana menstabilkan segmentasi warna terhadap perubahan iluminasi pagi, siang, dan sore?")
doc.save(str(OUT))
print("P3a OK")
"""Draf Proposal CV (p4: sisa Bab 1)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h2(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.font.size = Pt(12); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def par(t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(t); r.font.size = Pt(12); return p
par("3. Bagaimana mengukur persentase kuning dan coklat per zona serta merumuskannya menjadi indeks stres 0-100 untuk pengendali?")
par("4. Bagaimana mengemas pipeline tersebut menjadi prototipe lapangan berbasis komputer papan tunggal dan dasbor yang memenuhi kriteria burn-in 24 jam?")
h2("1.3", "Tujuan Prototipe")
par("Tujuan prototipe ini adalah:")
par("1. Menghasilkan deteksi bed otomatis berbasis tepi Canny, aproksimasi quad, dan homografi empat titik dengan jalur cadangan maska HSV.")
par("2. Menghasilkan segmentasi Hue Saturation Value (HSV) adaptif iluminasi dengan faktor f = mean(V)/128 dan perata Exponential Moving Average (EMA) yang menurunkan jitter sudut sampai 53 persen.")
par("3. Menghasilkan pengukuran kuning dan coklat per zona beserta PSI, PSI maksimum zona terburuk, dan versi rumus yang dikirim sebagai payload Firebase.")
par("4. Menghasilkan paket deploy Raspberry Pi (RPi) 4B dengan kamera Camera Serial Interface (CSI) dan dasbor web yang lolos burn-in 24 jam dengan minimal 140 dari 144 siklus berhasil.")
h2("1.4", "Manfaat Prototipe")
par("Manfaat prototipe ini adalah:")
par("1. Bagi petani, peta 24 zona dengan status belum siap, hampir siap, siap panen, dan harus panen beserta status kesehatan sehat, waspada, dan sakit menjadi dasar panen selektif dan pemeriksaan gejala.")
par("2. Bagi pengembang kendali, PSI beserta PSI maksimum dan jumlah zona sakit menjadi masukan tegas yang siap dibaca pengendali logika fuzzy pompa.")
par("3. Bagi akademik, prototipe menjadi rujukan awal yang ringan tanpa pembelajaran mendalam untuk monitoring aquaponik berbasis komputer papan tunggal.")
h2("1.5", "Potensi Dampak Fungsional/Komersial")
apar([nor("Fungsi utama prototipe adalah sensor tanaman otomatis yang menilai satu bed 2 m x 1,1 m setiap 10 menit dengan payload 2-3 KB per sesi ke "), it("cloud"), nor(". Fungsi tersebut mengurangi kunjungan manual ke bed dan mempercepat keputusan panen selektif. Potensi komersial terletak pada paket instalasi per bed yang terdiri atas komputer papan tunggal, kamera, dan rumah kamera cetak tiga dimensi atau "), it("three-dimensional printing"), nor(" (3DP), ditambah langganan dasbor untuk banyak bed. Skema bisnis tersebut layak diuji setelah kriteria burn-in 24 jam terpenuhi dan validasi "), it("ground truth"), nor(" lima gambar selesai.")])
doc.save(str(OUT))
print("P4 OK")
"""Draf Proposal CV (p5: Bab 2 tinjauan pustaka + Tabel 2.1)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h1(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t.upper())
    r.bold = True; r.font.size = Pt(13); return p
def h2(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.font.size = Pt(12); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def captab(n, t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Tabel " + n + "  " + t); r.bold = True; r.font.size = Pt(11); return p
h1("BAB 2", "Kajian Pustaka")
h2("2.1", "Tinjauan Pustaka")
apar([nor("Wan "), it("et al."), nor(" (2022) membangun sistem monitoring aquaponik berbasis komputasi tepi atau "), it("edge computing"), nor(" dengan Raspberry Pi dan pengolahan citra untuk pertumbuhan tanaman. Sistem tersebut membuktikan arsitektur sensor-kamera-komputasi tepi layak untuk aquaponik, tetapi tidak menilai kesiapan panen per zona dan tidak menangani adaptasi iluminasi. Abbasi "), it("et al."), nor(" (2023) mendeteksi klorosis daun selada aquaponik dari citra warna secara otomatis. Kajian tersebut menjadi rujukan terdekat untuk deteksi menguning, tetapi hanya satu gejala dan satu bed tanpa grid zona. Searson "), it("et al."), nor(" (2017) memakai ruang warna HSV dan operasi morfologi untuk deteksi tanaman di lapangan dengan iluminasi alami. Kajian tersebut menjadi dasar segmentasi hijau proyek ini, tetapi ambangnya statis sehingga liputan melompat ketika cahaya berubah.")])
apar([nor("Hameed "), it("et al."), nor(" (2018) menentukan ambang vegetasi dari histogram "), it("Hue"), nor(" sehingga adaptif terhadap cahaya. Gagasan tersebut dipakai sebagai kerabat faktor adaptasi "), it("f"), nor(" pada prototipe ini. Yang dkk. (2015) memakai pohon keputusan HSV untuk identifikasi kehijauan dan Barbedo (2013) memetakan teknik citra digital untuk deteksi dan kuantifikasi penyakit daun berbasis warna. Kedua kajian tersebut mendukung pemisahan kuning dan coklat sebagai gejala berbeda. Tovar "), it("et al."), nor(" (2018) memakai Raspberry Pi untuk fenotipe tanaman sehingga mendukung pilihan deploy ringan. Perbandingan posisi penelitian ini terhadap enam kajian tersebut diringkas pada Tabel 2.1. Celah yang diisi prototipe ini adalah gabungan grid panen 4x6, adaptasi iluminasi tanpa pembelajaran mendalam, dan skor stres siap kendali dalam satu paket lapangan.")])
captab("2.1", "Perbandingan penelitian terdahulu dengan penelitian yang diusulkan")
t = doc.add_table(rows=8, cols=4)
t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, htxt in enumerate(["Kajian", "Metode", "Keluaran", "Beda dengan usulan"]):
    r = t.cell(0, j).paragraphs[0].add_run(htxt); r.bold = True; r.font.size = Pt(10)
rows = [
 ["Wan dkk. (2022)", "Edge + citra aquaponik", "Status tumbuh", "Tanpa grid zona dan adaptasi cahaya"],
 ["Abbasi dkk. (2023)", "Warna daun selada", "Klorosis", "Satu gejala, tanpa grid dan PSI"],
 ["Searson dkk. (2017)", "HSV + morfologi", "Maska tanaman", "Ambang statis, tanpa adaptasi"],
 ["Hameed dkk. (2018)", "Ambang histogram Hue", "Maska adaptif", "Tanpa grid panen dan skor kendali"],
 ["Yang dkk. (2015)", "Pohon keputusan HSV", "Kehijauan", "Tanpa kuning/coklat dan deploy"],
 ["Barbedo (2013)", "Citra penyakit warna", "Area sakit", "Tanpa grid zona dan paket lapangan"],
 ["Usulan", "HSV adaptif + EMA + grid", "Peta 24 zona + PSI", "Gabungan keempat hal di atas"],
]
for i, row in enumerate(rows, 1):
    for j, v in enumerate(row):
        r = t.cell(i, j).paragraphs[0].add_run(v); r.font.size = Pt(10)
doc.add_paragraph()
doc.save(str(OUT))
print("P5 OK")
"""Draf Proposal CV (p6: landasan 2.2.1-2.2.3 + Persamaan 2.1-2.4)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h2(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.font.size = Pt(12); return p
def h3(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.italic = True; r.font.size = Pt(12); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def pers(n, t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(t + "   (" + n + ")"); r.italic = True; r.font.size = Pt(12); return p
h2("2.2", "Landasan Teoretik")
h3("2.2.1", "Deteksi Tepi Canny dan Aproksimasi Quad")
apar([nor("Detektor Canny (Canny, 1986) mencari tepi melalui gradien multiskala, penekanan nonmaksimum atau "), it("non-maximum suppression"), nor(", dan ambang histeresis. Gradien dihitung dengan operator Sobel pada arah "), it("x"), nor(" dan "), it("y"), nor(" sehingga magnitudo dan orientasi tiap piksel diperoleh dari Persamaan 2.1 dan 2.2. Kontur terbesar hasil tepi didekati menjadi poligon empat titik dengan "), it("approxPolyDP"), nor(" sehingga sudut bed diperoleh walaupun kamera miring.")])
pers("2.1", "G = akar(Gx^2 + Gy^2)")
pers("2.2", "theta = arctan(Gy / Gx)")
apar([nor("Empat sudut terurut dipetakan ke persegi 1200x660 dengan homografi planar. Homografi tiga kali tiga atau "), it("H"), nor(" memetakan titik sumber "), it("p"), nor(" ke titik tujuan "), it("p'"), nor(" sampai faktor skala "), it("s"), nor(" seperti Persamaan 2.3. Bed yang tegak dibagi menjadi grid 4 baris dan 6 kolom sehingga tiap zona R1C1 sampai R4C6 dianalisis terpisah dan liputan adil antarbed.")])
pers("2.3", "s . p' = H . p")
h3("2.2.2", "Ruang Warna HSV dan Segmentasi Vegetasi")
apar([nor("Ruang HSV memisahkan rona atau "), it("Hue"), nor(" dari kejenuhan atau "), it("Saturation"), nor(" dan terang atau "), it("Value"), nor(" sehingga perubahan cahaya terutama menggeser "), it("S"), nor(" dan "), it("V"), nor(" sedangkan "), it("H"), nor(" menyimpan identitas warna daun (Woebbecke "), it("et al."), nor(", 1995; Yang "), it("et al."), nor(", 2015). Maska tanaman dibentuk dari gabungan dua rentang hijau muda H 35-75 dan hijau tua H 36-85 yang digabung dengan operasi logika ATAU seperti Persamaan 2.4. Maska kuning H 21-34 dan coklat H 8-20 dibentuk terpisah, sedangkan coklat wajib menempel kanopi lewat jendela ketetanggaan 21x21 agar media gelap tidak ikut terdeteksi.")])
pers("2.4", "M_tanaman = M_muda OR M_mature")
h3("2.2.3", "Adaptasi Iluminasi dan Perata Temporal EMA")
doc.save(str(OUT))
print("P6 OK")
"""Draf Proposal CV (p7: 2.2.3-2.2.5 + Persamaan 2.5-2.9)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h3(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.italic = True; r.font.size = Pt(12); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def pers(n, t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(t + "   (" + n + ")"); r.italic = True; r.font.size = Pt(12); return p
apar([nor("Faktor adaptasi "), it("f"), nor(" dihitung dari rata-rata komponen "), it("V"), nor(" tiap frame terhadap acuan 128 lalu dijepit pada 0,6 sampai 1,6. Faktor tersebut menggeser ambang bawah "), it("S"), nor(" dan "), it("V"), nor(" tanpa menggeser "), it("Hue"), nor(" sehingga identitas hijau, kuning, dan coklat tetap. Sudut hasil deteksi diratakan antarframe dengan "), it("Exponential Moving Average"), nor(" (EMA) berbobot 0,2 seperti Persamaan 2.5 sehingga jitter sudut turun dari 19,93 piksel menjadi 9,32 piksel atau 53 persen.")])
pers("2.5", "x_t = 0,2 . z_t + 0,8 . x_{t-1}")
h3("2.2.4", "Liputan Kanopi dan Indeks Stres Tanaman")
apar([nor("Liputan tiap zona adalah rasio piksel tanaman terhadap luas zona dalam persen. Persentase kuning dan coklat dihitung terhadap piksel tanaman, bukan luas zona, sehingga zona jarang tetap adil. Status panen ditetapkan dari liputan: belum siap di bawah 25 persen, hampir siap 25-55 persen, siap panen 55-80 persen, dan harus panen di atas 80 persen. Persentase kuning dan coklat dinormalkan terhadap ambang sakit 25 persen dan 8 persen menjadi PSI 0-100 seperti Persamaan 2.6 dan 2.7. PSI 40 menandai dominasi klorosis, PSI 60 menandai dominasi nekrosis, sedangkan PSI maksimum zona terburuk dikirim terpisah agar bahaya lokal tidak hilang dalam rata-rata.")])
pers("2.6", "PSI = 100 . min(1; 0,4 . min(K/25; 1) + 0,6 . min(C/8; 1))")
pers("2.7", "PSI_maks = maks(PSI_zona), z = 1..24")
h3("2.2.5", "Metrik Evaluasi Segmentasi")
apar([nor("Evaluasi memakai mask "), it("ground truth"), nor(" tiga kelas yaitu tanaman total, kuning, dan coklat untuk lima gambar. Presisi mengukur ketepatan piksel terdeteksi, "), it("recall"), nor(" mengukur kelengkapan temuan, skor F1 adalah rata-rata harmonik keduanya, sedangkan "), it("Intersection over Union"), nor(" (IoU) mengukur tumpang tindih seperti Persamaan 2.8 dan 2.9. Target wajar untuk HSV beserta kontur pada foto lapangan adalah F1 0,85-0,95.")])
pers("2.8", "F1 = 2 . P . R / (P + R)")
pers("2.9", "IoU = |A temu B| / |A gabung B|")
doc.save(str(OUT))
print("P7 OK")
"""Draf Proposal CV (p8: Bab 3 lokasi+alat+tabel 3.1-3.2)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h1(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t.upper())
    r.bold = True; r.font.size = Pt(13); return p
def h2(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.font.size = Pt(12); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def par(t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(t); r.font.size = Pt(12); return p
def captab(n, t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Tabel " + n + "  " + t); r.bold = True; r.font.size = Pt(11); return p
def tab(header, rows):
    tb = doc.add_table(rows=1+len(rows), cols=len(header))
    tb.style = "Table Grid"; tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, htxt in enumerate(header):
        r = tb.cell(0, j).paragraphs[0].add_run(htxt); r.bold = True; r.font.size = Pt(10)
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            r = tb.cell(i, j).paragraphs[0].add_run(v); r.font.size = Pt(10)
    doc.add_paragraph(); return tb
h1("BAB 3", "Metode Pelaksanaan")
h2("3.1", "Lokasi Riset")
apar([nor("Riset dilaksanakan di bed aquaponik kangkung berukuran 2 m x 1,1 m pada lokasi mitra petani, sedangkan pengembangan perangkat lunak dilakukan di laboratorium komputer. Pengambilan citra memakai kamera atas atau "), it("top-down"), nor(" pada tiga rentang iluminasi yaitu pagi pukul 08.00-09.00, siang pukul 11.00-13.00, dan sore pukul 15.00-17.00. Uji lapangan memakai 18 video dan lima foto bed tahap seedling sampai ready, sedangkan uji burn-in 24 jam dilakukan setelah rumah kamera terpasang permanen di lokasi.")])
h2("3.2", "Bahan dan Alat")
apar([nor("Bahan berupa bed aquaponik kangkung satu unit, tanaman tahap seedling sampai ready, dan lima foto lapangan beserta 18 video uji. Alat terdiri atas perangkat keras pada Tabel 3.1 dan perangkat lunak pada Tabel 3.2. Modul "), it("raspi/modules"), nor(" adalah salinan berkas "), it("adaptive_bed.py"), nor(" dan "), it("kangkung_cv.py"), nor(" sehingga hasil laptop dan komputer papan tunggal identik.")])
captab("3.1", "Daftar perangkat keras dan spesifikasinya")
tab(["Perangkat", "Spesifikasi", "Fungsi"], [
 ["Raspberry Pi 4B", "RAM 2 GB, Debian 13, Python 3.13", "Komputasi pipeline tiap 10 menit"],
 ["Kamera CSI IR 5MP", "Sensor ov5647, 1296x972 via libcamera", "Akuisisi top-down"],
 ["Adaptor 5V/3A", "USB-C 5 V polos", "Catu daya stabil"],
 ["microSD high-endurance", "Minimal 16 GB", "Media sistem 24/7"],
 ["Rumah kamera 3DP", "PETG, IP65, sun shield, silica", "Pelindung outdoor"],
 ["Laptop", "Windows, Python 3.12", "Analisis video dan GT"],
])
captab("3.2", "Daftar perangkat lunak dan pustaka")
tab(["Perangkat lunak", "Versi/Sumber", "Fungsi"], [
 ["OpenCV headless", "4.10.0", "Canny, kontur, warp, HSV"],
 ["NumPy", "1.26.4", "Operasi matriks dan maska"],
 ["firebase-admin", "6.5.0", "Uplink Firestore/Storage"],
 ["Picamera2/libcamera", "Sistem Pi", "Akuisisi CSI"],
 ["Tailscale + SSH", "Layanan jarak jauh", "Administrasi tanpa buka port"],
 ["Dasbor web statis", "web/ tanpa build", "Heatmap 4x6 dan grafik 24 jam"],
])
doc.save(str(OUT))
print("P8 OK")
"""Draf Proposal CV (p9: 3.3 arsitektur + Gambar 3.1)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h2(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.font.size = Pt(12); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def capg(n, t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Gambar " + n + "  " + t); r.font.size = Pt(11); return p
h2("3.3", "Arsitektur Sistem")
apar([nor("Sistem dirancang sebagai sensor tanaman otomatis berlima tahap. Tahap akuisisi memakai kamera CSI atau HP secara "), it("top-down"), nor(" dengan pemanasan pajanan otomatis. Tahap visi di komputer papan tunggal menjalankan deteksi bed, warp, grid 4x6, liputan, kuning, coklat, dan PSI seperti Persamaan 2.3 sampai 2.7. Tahap Firebase memakai koleksi "), it("bed_readings"), nor(" skema v1.1 dengan payload 2-3 KB tiap 10 menit. Tahap dasbor menampilkan heatmap 4x6, grafik 24 jam, distribusi status, dan kartu PSI secara baca saja. Tahap kendali milik tim fuzzy membaca PSI, PSI maksimum, dan jumlah zona sakit menjadi keputusan pompa dengan persetujuan manusia. Blok diagram pada Gambar 3.1 meringkas aliran tersebut.")])
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(str(ROOT / "docs" / "blok_diagram.png"), width=Inches(6.0))
capg("3.1", "Blok diagram sistem sensor tanaman otomatis dari kamera sampai dasbor dan pengendali")
apar([nor("Kontrak antar tahap memakai "), it("fuzzy_input"), nor(" berisi kuning_pct, coklat_pct, zona_sakit, "), it("psi"), nor(", "), it("psi_maks"), nor(", dan "), it("psi_versi"), nor(". Aturan keselamatan menetapkan data basi di atas 30 menit ditolak, nilai hilang menahan tindakan, dan status usulan wajib menunggu persetujuan manusia sehingga tidak ada aktuasi otomatis.")])
doc.save(str(OUT))
print("P9 OK")
"""Draf Proposal CV (p10: 3.4 flowchart + 3.5 skema)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h2(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.font.size = Pt(12); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def capg(n, t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Gambar " + n + "  " + t); r.font.size = Pt(11); return p
h2("3.4", "Diagram Alir")
apar([nor("Diagram alir pada Gambar 3.2 memakai simbol baku algoritma yaitu elips untuk START dan END, jajar genjang untuk input dan output, belah ketupat untuk keputusan, dan persegi panjang untuk proses. Aliran dimulai dari frame kamera, lalu deteksi bed Canny-quad dengan keputusan lolos atau jalur cadangan, lalu warp dan grid, lalu segmentasi adaptif memakai Persamaan 2.4 dan faktor "), it("f"), nor(" Bagian 2.2.3, lalu skor zona memakai Persamaan 2.6 dan 2.7, lalu pengiriman payload, dan diakhiri keluaran MP4 beranotasi, CSV runtun waktu, JSON, dan dasbor. Diagram alir berbeda dengan blok diagram Gambar 3.1 karena diagram alir menunjukkan langkah yang dapat diprogram sedangkan blok diagram menunjukkan hubungan antar subsistem.")])
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(str(ROOT / "docs" / "flowchart_cv.png"), width=Inches(3.4))
capg("3.2", "Diagram alir pipeline computer vision dari START sampai END")
h2("3.5", "Skema Pemasangan")
apar([nor("Kamera dipasang di atas tengah bed secara "), it("top-down"), nor(" pada ketinggian sekitar 2,5 m sehingga seluruh tepi bed masuk frame dengan porsi bed minimal 12 persen luas frame seperti Gambar 3.3. Aturan pasang menghindari pantulan langsung ke modul kamera, pipa yang menutupi bed, dan rumah hitam yang terkena matahari langsung. Rumah PETG IP65 memakai pelindung matahari, kelenjar kabel, dan gel silika, sedangkan komputer papan tunggal memakai pelepas panas besar.")])
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(str(ROOT / "docs" / "skema_kamera.png"), width=Inches(5.5))
capg("3.3", "Skema pemasangan kamera di atas bed aquaponik")
doc.save(str(OUT))
print("P10 OK")
"""Draf Proposal CV (p11: 3.6 prinsip kerja + Gambar 3.4-3.5)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h2(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.font.size = Pt(12); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def capg(n, t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Gambar " + n + "  " + t); r.font.size = Pt(11); return p
h2("3.6", "Prinsip Kerja Algoritma")
apar([nor("Prinsip kerja mengikuti formulasi Bab 2 dan dirujuk eksplisit tiap langkah. Deteksi bed memakai Persamaan 2.1 dan 2.2 untuk tepi, lalu aproksimasi quad, lalu Persamaan 2.3 untuk warp. Segmentasi memakai Persamaan 2.4 untuk maska hijau serta rentang kuning dan coklat yang dijaga statis agar diagnosis tegas. Faktor adaptasi Bagian 2.2.3 menggeser ambang "), it("S"), nor(" dan "), it("V"), nor(" lalu sudut diratakan dengan Persamaan 2.5. Tiap zona dihitung liputan, kuning, dan coklat terhadap piksel tanaman, lalu status panen dan status kesehatan ditetapkan, lalu PSI dan PSI maksimum dihitung dengan Persamaan 2.6 dan 2.7. Zona dengan kanopi di bawah 30 persen luas zona berstatus tidak dinilai agar artefak tepi warp tidak memicu alarm.")])
apar([nor("Bukti reproduksibilitas memakai data asli. Gambar 3.4 membandingkan frame mentah HP IMG_5159 dengan keluaran pipeline pada frame yang sama, sedangkan Gambar 3.5 membandingkan foto lapangan bed_04_ready.jpg dengan keluaran batch_segmentasi.py. Kedua gambar tersebut membuktikan masukan dan keluaran berasal dari data lapangan, bukan simulasi.")])
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(str(ROOT / "output" / "ppt_asli" / "01_asli_vs_anotasi.jpg"), width=Inches(6.0))
capg("3.4", "Bukti asli frame HP terhadap keluaran pipeline grid dan HUD")
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(str(ROOT / "output" / "ppt_asli" / "02_foto_vs_segmentasi.jpg"), width=Inches(5.5))
capg("3.5", "Bukti asli foto lapangan terhadap keluaran segmentasi liputan 22,6 persen")
doc.save(str(OUT))
print("P11 OK")
"""Draf Proposal CV (p12: 3.7 metrik+skenario + Tabel 3.3)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h2(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t)
    r.bold = True; r.font.size = Pt(12); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def captab(n, t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Tabel " + n + "  " + t); r.bold = True; r.font.size = Pt(11); return p
h2("3.7", "Metrik dan Skenario Pengujian")
apar([nor("Metrik terdiri atas jitter sudut dalam piksel untuk stabilitas temporal, liputan rata-rata dan simpangan baku dalam persen untuk tren tumbuh, serta presisi, "), it("recall"), nor(", F1, dan "), it("Intersection over Union"), nor(" (IoU) memakai Persamaan 2.8 dan 2.9 untuk akurasi segmentasi terhadap mask "), it("ground truth"), nor(". Metrik sistem terdiri atas keberhasilan siklus burn-in, suhu SoC dalam derajat Celsius, dan keterbacaan snapshot. Skenario pada Tabel 3.3 menguji tiap rumusan masalah secara kuantitatif dan divisualkan dengan plot pada Bab 4 agar pembaca tidak menelusuri angka mentah satu per satu.")])
captab("3.3", "Skenario pengujian kelayakan prototipe")
tb = doc.add_table(rows=6, cols=4)
tb.style = "Table Grid"; tb.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, htxt in enumerate(["Skenario", "Data", "Metrik dan target", "Acuan"]):
    r = tb.cell(0, j).paragraphs[0].add_run(htxt); r.bold = True; r.font.size = Pt(10)
rows = [
 ["Stabilitas iluminasi", "18 video pagi/siang/sore", "Jitter turun >=40 persen, liputan stabil", "Persamaan 2.5"],
 ["Akurasi segmentasi", "5 mask ground truth", "F1 0,85-0,95, IoU per kelas", "Persamaan 2.8-2.9"],
 ["Kesehatan dan PSI", "5 foto lapangan + foto sakit", "0 zona sakit palsu, PSI 0-0,1 saat sehat", "Persamaan 2.6-2.7"],
 ["Banding metode", "5 gambar GT", "HSV vs ExG vs Otsu-Hue", "Tabel 2.1"],
 ["Burn-in lapangan", "24 jam, 144 siklus", ">=140 OK, suhu <70 C", "Tabel 3.1"],
]
for i, row in enumerate(rows, 1):
    for j, v in enumerate(row):
        r = tb.cell(i, j).paragraphs[0].add_run(v); r.font.size = Pt(10)
doc.add_paragraph()
doc.save(str(OUT))
print("P12 OK")
"""Draf Proposal CV (p13: pustaka + lampiran QR + save info)."""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "DRAFT_PROPOSAL_PROTOTIPE_BAB1-3_CV.docx"
doc = Document(str(OUT))
def h1(n, t):
    p = doc.add_paragraph(); r = p.add_run(n + "  " + t.upper())
    r.bold = True; r.font.size = Pt(13); return p
def apar(items):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for t, italic, bold in items:
        r = p.add_run(t); r.italic = italic; r.bold = bold; r.font.size = Pt(12)
    return p
def nor(t): return (t, False, False)
def it(t): return (t, True, False)
def par(t):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(t); r.font.size = Pt(12); return p
h1("", "Daftar Pustaka")
for b in [
 "J. Canny, A computational approach to edge detection, IEEE Trans. Pattern Anal. Mach. Intell., vol. 8, no. 6, pp. 679-698, 1986. doi: 10.1109/TPAMI.1986.4767851.",
 "D. M. Woebbecke, G. E. Meyer, K. Von Bargen, dan D. A. Mortensen, Color indices for weed identification under various soil, residue, and lighting conditions, Trans. ASAE, vol. 38, no. 1, pp. 259-269, 1995. doi: 10.13031/2013.27838.",
 "D. Searson dkk., Automatic crop detection under field conditions using the HSV colour space and morphological operations, Comput. Electron. Agric., vol. 134, pp. 80-89, 2017. doi: 10.1016/j.compag.2016.12.013.",
 "I. A. Hameed, M. Usama dkk., A new vegetation segmentation approach for cropped fields based on threshold detection from hue histograms, Sensors, vol. 18, no. 4, p. 1258, 2018. doi: 10.3390/s18041258.",
 "W. Yang, S. Wang, X. Zhao, J. Zhang, dan J. Feng, Greenness identification based on HSV decision tree, Inf. Process. Agric., vol. 2, no. 3-4, pp. 277-284, 2015. doi: 10.1016/j.inpa.2015.07.003.",
 "J. G. A. Barbedo, Digital image processing techniques for detecting, quantifying and classifying plant diseases, SpringerPlus, vol. 2, p. 660, 2013. doi: 10.1186/2193-1801-2-660.",
 "S. Wan, K. Zhao, Z. Lu dkk., A modularized IoT monitoring system with edge-computing for aquaponics, Sensors, vol. 22, no. 23, p. 9260, 2022. doi: 10.3390/s22239260.",
 "R. Abbasi, P. Martinez, dan R. Ahmad, Automated visual identification of foliage chlorosis in lettuce grown in aquaponic systems, Agriculture, vol. 13, no. 3, p. 615, 2023. doi: 10.3390/agriculture13030615.",
 "J. C. Tovar dkk., Raspberry Pi-powered imaging for plant phenotyping, Appl. Plant Sci., vol. 6, no. 4, 2018. doi: 10.1002/aps3.1031.",
 "A. F. A. Netto dkk., Segmentation of RGB images using different vegetation indices and thresholding methods, Nativa, vol. 6, no. 4, 2018. doi: 10.31413/nativa.v6i4.5405.",
]:
    par(b)
h1("", "Lampiran")
apar([nor("Lampiran 1 memuat kode QR repositori pada Gambar L.1 yang mengarah langsung ke kode sumber pipeline, skema Firebase, dan dasbor. Lampiran 2 memuat biodata penulis. Lampiran 3 memuat sketsa rumah kamera. Kode QR berukuran kecil dan diletakkan di sudut kanan atas halaman lampiran dengan tata letak yang konsisten.")])
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
p.add_run().add_picture(str(ROOT / "docs" / "qr_repo.png"), width=Inches(1.2))
g = doc.add_paragraph(); g.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = g.add_run("Gambar L.1  Kode QR repositori sumber terbuka"); r.font.size = Pt(10)
par("Lampiran 1: Kode sumber dan data — [URL REPOSITORI, AKSES VIA QR Gambar L.1]")
par("Lampiran 2: Biodata penulis — Nama: [NAMA LENGKAP], NIM: [NOMOR INDUK MAHASISWA], Tempat tanggal lahir: [KOTA, TANGGAL], Program Studi: Teknik Komputer (S1), Fakultas: Fakultas Teknik, Perguruan Tinggi: Universitas Negeri Semarang (UNNES), Alamat surel: [EMAIL], Bidang minat: Computer Vision, Embedded Systems, Aquaponik.")
par("Lampiran 3: Sketsa rumah kamera — lihat hardware/stl dan hardware/renders pada repositori via QR Gambar L.1.")
doc.save(str(OUT))
from docx import Document as D2
d = D2(str(OUT))
print("SELESAI paragraf:", len(d.paragraphs), "tabel:", len(d.tables))
