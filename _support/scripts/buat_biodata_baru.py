"""Buat dokumen Biodata Penulis sebagai DOCX mandiri.
Tabel disiapkan untuk pengisian oleh penulis nanti.
Structur tabel tidak diubah dari template asli."""
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
# Tabel dengan kolom: Label | Nilai
# Nilai diserahinkan diisi oleh penulis nanti
data_pribadi_labels = [
    "Nama Lengkap",
    "Jenis Kelamin",
    "NIM",
    "Tempat Tanggal Lahir",
    "Alamat E-mail",
    "Nomor Telepon/HP",
]

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
r = p.add_run("Data Pribadi")
r.font.size = Pt(12)
r.bold = True

# Create table with headers + data rows
num_rows = len(data_pribadi_labels) + 1  # +1 for header
table = doc.add_table(rows=num_rows, cols=2)
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

# Data rows - labels only, values to be filled by user
for i, label in enumerate(data_pribadi_labels, start=1):
    cells = table.rows[i].cells
    cells[0].text = label
    # cells[1].text remains empty for user to fill
    for cell in cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(11)

# ---------------- Tabel Riwayat Pendidikan ----------------
# Struktur: baris = SD, SMP, SMA; kolom = Nama Instansi, Jurusan, Tahun Masuk
pendidikan_header = ["SD", "SMP", "SMA"]
pendidikan_rows = [
    # Setiap row adalah: [Nama Instansi, Jurusan, Tahun Masuk]
    # Values kosong untuk diisi oleh penulis nanti
    ("", "", ""),  # SD
    ("", "", ""),  # SMP
    ("", "", ""),  # SMA
]

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
r = p.add_run("Riwayat Pendidikan")
r.font.size = Pt(12)
r.bold = True

# Header: Item + pendidikan levels
ncols = len(pendidikan_header) + 1  # +1 for "Item" column
nrows = len(pendidikan_rows) + 1    # +1 for header row

table2 = doc.add_table(rows=nrows, cols=ncols)
table2.style = "Table Grid"
table2.alignment = WD_TABLE_ALIGNMENT.CENTER

# Header row: Item + SD, SMP, MA
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
    cells[0].text = row[0]  # Item (SD/SMP/SMA label)
    for j in range(1, ncols):
        cells[j].text = row[j-1]  # Nilai instansi/jurusan/tahun
    for cell in cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(11)

# Set lebar kolom pendidikan
for idx, width in enumerate([Inches(1.5), Inches(2.0), Inches(1.5)]):
    table2.columns[idx].width = width

# ---------------- Tanda Tangan ----------------
doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = p.add_run("Semarang, 23 Oktober 2026")
r.font.size = Pt(11)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = p.add_run("Nama Penulis")
r.font.size = Pt(12)
r.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
r = p.add_run("NIM. 2305110019")
r.font.size = Pt(11)

# ---------------- Simpan ----------------
out_path = "docs/Biodata_Template_Felix_2305110019.docx"
doc.save(out_path)
print("Disimpan:", out_path)
print("Tabel biodata siap diisi oleh penulis.")