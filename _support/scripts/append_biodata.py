from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document(r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx")

# Tambahkan section header di akhir
doc.add_paragraph()
p = doc.add_paragraph()
r = p.add_run("LAMPIRAN A: BIODATA PENULIS")
r.font.size = Pt(14)
r.bold = True
r.italic = True

doc.add_paragraph()

# Tabel Data Pribadi
data_pribadi = [
    ("Nama Lengkap", ""),
    ("Jenis Kelamin", ""),
    ("NIM", "2305110019"),
    ("Tempat Tanggal Lahir", "Cirebon, 15 Juni 2005"),
    ("Alamat E-mail", "raflyanggara02@students.unnes.ac.id"),
    ("Nomor Telepon/HP", "+62 83806934635"),
]

table_pribadi = doc.add_table(rows=7, cols=2)
table_pribadi.style = "Table Grid"
table_pribadi.alignment = WD_TABLE_ALIGNMENT.CENTER
table_pribadi.columns[0].width = Inches(2.5)
table_pribadi.columns[1].width = Inches(3.5)

hdr = table_pribadi.rows[0].cells
hdr[0].text = "Item"
hdr[1].text = "Nilai"
for cell in hdr:
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(11)

for i, (label, value) in enumerate(data_pribadi, start=1):
    cells = table_pribadi.rows[i].cells
    cells[0].text = label
    cells[1].text = value
    for cell in cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(11)

doc.add_paragraph()

# Tabel Riwayat Pendidikan
pendidikan_header = ["SD", "SMP", "SMA"]

p = doc.add_paragraph()
r = p.add_run("Riwayat Pendidikan")
r.font.size = Pt(12)
r.bold = True

ncols_pend = 4
nrows_pend = 4

table_pend = doc.add_table(rows=nrows_pend, cols=ncols_pend)
table_pend.style = "Table Grid"
table_pend.alignment = WD_TABLE_ALIGNMENT.CENTER

header_cells = table_pend.rows[0].cells
header_cells[0].text = "Item"
for j in range(1, ncols_pend):
    header_cells[j].text = pendidikan_header[j-1]
for cell in header_cells:
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(11)

pend_data = [
    ("Nama Instansi",),
    ("Jurusan",),
    ("Tahun Masuk",),
]
for i, (label,) in enumerate(pend_data, start=1):
    cells = table_pend.rows[i].cells
    cells[0].text = label
    for j in range(1, ncols_pend):
        cells[j].text = ""
    for cell in cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(11)

for idx, width in enumerate([Inches(1.5), Inches(1.8), Inches(1.8), Inches(1.8)]):
    if idx < len(table_pend.columns):
        table_pend.columns[idx].width = width

# Simpan
out_path = r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx"
doc.save(out_path)
print("Disimpan. Total paragraphs:", len(doc.paragraphs), "Total tables:", len(doc.tables))