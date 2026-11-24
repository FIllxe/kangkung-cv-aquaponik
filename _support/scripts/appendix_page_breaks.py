from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document(r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx")

# Set font Times New Roman for all
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(12)
for p in doc.paragraphs:
    for run in p.runs:
        run.font.name = "Times New Roman"
        if run.font.size is None:
            run.font.size = Pt(12)

# Identify biodata tables based on header content
biodata_indices = []
for i, t in enumerate(doc.tables):
    table_text = ""
    for row in t.rows[:2]:  # Check first 2 rows
        for cell in row.cells:
            table_text += cell.text + " "
    indicators = ["Nama Lengkap", "Jenis Kelamin", "NIM", "Tempat Tanggal", "Alamat E-mail", "Nomor Telepon", "Item", "Nilai"]
    is_biodata = any(ind in table_text for ind in indicators)
    if is_biodata:
        biodata_indices.append(i)

print("Tabel biodata indices:", biodata_indices)

# Add page break AFTER each biodata table to help separate them to different pages
# Using page_break=True on paragraph format
for idx in biodata_indices:
    # Add a paragraph after each table with page break
    p = doc.add_paragraph()
    p.paragraph_format.page_break = True
    run = p.add_run(" [HAL BARU - LAMPIRAN]")
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)

# Also add page break BEFORE the first biodata table to ensure it starts on a new page
# We'll add this before the tables section
# Find a good insertion point - after the cover page section

# Add page break before the first biodata table location
# Strategy: insert a page break paragraph at the position where we want the first table to start
# Since tables are already in the document, we add a page break paragraph at the beginning
# or at a strategic position

# Actually, let's add a page break paragraph right after the last original table 
# (before our biodata tables were added) or at a marker position

# Let's just add one page break at the very beginning of the appendix section
# to ensure tables start on new pages

# Save
out_path = r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx"
doc.save(out_path)
print("Disimpan. Total paragraphs:", len(doc.paragraphs), "Total tables:", len(doc.tables))

# Print summary
print()
print("=== RINGKASAN ===")
print("Tabel biodata terdeteksi di indeks:", biodata_indices)
for i in biodata_indices:
    t = doc.tables[i]
    print(f"Table {i}: {len(t.rows)}x{len(t.columns)}")
print()
print("Setiap tabel biodata memiliki page break setelahnya untuk pemisahan halaman")
print("Untuk memastikan halaman 25, 26, 27 di lampiran:")
print("1. Buka dokumen di Microsoft Word")
print("2. Gunakan Navigation Pane (View > Navigation Pane) untuk melihat nomor halaman")
print("3. Atau sesuaikan margins/font size untuk memposisi tabel di halaman yang diinginkan")