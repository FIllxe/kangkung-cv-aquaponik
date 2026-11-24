"""Buat dokumen Biodata Penulis sebagai DOCX mandiri."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# Set margins
for section in doc.sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

# Normal style font
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(12)

# ---------------- Header UNNES ----------------
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("KEMENTERIAN PENDIDIKAN, KEBUDAYAAN, RISET, DAN TEKNOLOGI")
r.font.size = Pt(10)
r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("UNIVERSITAS NEGERI SEMARANG")
r.font.size = Pt(13)
r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("FAKULTAS TEKNIK")
r.font.size = Pt(13)
r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("PROGRAM STUDI TEKNIK KOMPUTER")
r.font.size = Pt(12)
r.italic = True

# ---------------- Judul ----------------
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("BIODATA PENULIS")
r.font.size = Pt(16)
r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Proyek Capstone: Computer Vision Aquaponik")
r.font.size = Pt(12)
r.italic = True

# ---------------- Tabel Data Pribadi ----------------
data_pribadi = [
    ("Nama Lengkap", "Felix Enrique"),
    ("Jenis Kelamin", "Laki-laki"),
    ("Nomor Induk Mahasiswa", "2305110019"),
    ("Tempat dan Tanggal Lahir", "Cirebon, 15 Juni 2005"),
    ("Alamat E-mail", "raflyanggara02@students.unnes.ac.id"),
    ("Nomor Telepon/HP", "+62 83806934635"),
]

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
r = p.add_run("Data Pribadi")
r.font.size = Pt(12)
r.bold = True

table = doc.add_table(rows=len(data_pribadi) + 1, cols=2)
table.style = "Table Grid"
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.columns[0].width = Inches(2.5)
table.columns[1].width = Inches(3.5)

# Header
hdr = table.rows[0].cells
hdr[0].text = "Item"
hdr[1].text = "Nilai"
for cell in hdr:
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(11)

# Rows
for i, (label, value) in enumerate(data_pribadi, start=1):
    cells = table.rows[i].cells
    cells[0].text = label
    cells[1].text = value
    for cell in cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(11)

# ---------------- Tabel Riwayat Pendidikan ----------------
pendidikan_header = ["SD", "SMP", "MA"]
pendidikan_rows = [
    ("Nama Instansi", "SD Negeri 2 Palimanan Timur", "SMP Negeri 1 Palimanan", "SMKN 1 Jamblang"),
    ("Jurusan", "-", "-", "Teknik Komputer Jaringan"),
    ("Tahun Masuk", "2011", "2017", "2020"),
]

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
r = p.add_run("Riwayat Pendidikan")
r.font.size = Pt(12)
r.bold = True

ncols = len(pendidikan_header) + 1
nrows = len(pendidikan_rows) + 1
table2 = doc.add_table(rows=nrows, cols=ncols)
table2.style = "Table Grid"
table2.alignment = WD_TABLE_ALIGNMENT.CENTER

# Header row: Item + pendidikan levels
header_cells = table2.rows[0].cells
header_cells[0].text = "Item"
for j, col in enumerate(pendidikan_header, start=1):
    header_cells[j].text = col
for cell in header_cells:
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(11)

# Data rows
for i, row in enumerate(pendidikan_rows, start=1):
    cells = table2.rows[i].cells
    cells[0].text = row[0]
    for j in range(1, ncols):
        cells[j].text = row[j]
    for cell in cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(11)

# ---------------- Tanda Tangan ----------------
doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = p.add_run("Semarang, 23 Oktober 2026")
r.font.size = Pt(11)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = p.add_run("Felix Enrique")
r.font.size = Pt(12)
r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = p.add_run("NIM. 2305110019")
r.font.size = Pt(11)

# ---------------- Simpan ----------------
out_path = "docs/Biodata_Felix_Enrique_2305110019.docx"
doc.save(out_path)
print("Disimpan:", out_path)
