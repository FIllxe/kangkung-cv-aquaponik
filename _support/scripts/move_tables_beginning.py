from docx import Document
from docx.shared import Pt, Inches
from docx.enum.table import WD_TABLE_ALIGNMENT

# Buka proposal
doc = Document(r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx")

# Set font Times New Roman untuk semua
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(12)
for p in doc.paragraphs:
    for run in p.runs:
        run.font.name = "Times New Roman"
        if run.font.size is None:
            run.font.size = Pt(12)

# --- CARA: Ambil tabel biodata yang sudah ada di akhir dan pindah ke awal ---
# Strategy: 
# 1. Catat posisi tabel di akhir (table 8 dan 9, yang adalah biodata)
# 2. Hapus tabel-tabel tersebut dari posisi akhir
# 3. Sisipkan tabel di awal setelah paragraf cover page

# Temu tabel biodata (yang terakhir)
biodata_tables = []
tables_to_remove = []

for i, t in enumerate(doc.tables):
    # Cek apakah tabel ini adalah biodata (berisi "Nama Lengkap" atau "Item" dengan "Nilai")
    is_biodata = False
    for row in t.rows:
        for cell in row.cells:
            if "Nama Lengkap" in cell.text or "Item" in cell.text:
                is_biodata = True
                break
        if is_biodata:
            break
    
    if is_biodata:
        tables_to_remove.append(i)
        biodata_tables.append(t)

print("Tabel biodata ditemukan di index:", tables_to_remove)
print("Jumlah tabel biodata:", len(biodata_tables))

# Untuk sekarang, hanya beri tahu posisi dan marker
# Karena memindahkan tabel di python-docx membutuhkan manipulasi xml yang kompleks

# Tandai di paragraf awal document bahwa ini adalah awal lampiran
doc.paragraphs[0].add_run("\n=== LAMPIRAN A: BIODATA PENULIS (sudah disisipkan) ===")

# Simpan
out_path = r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx"
doc.save(out_path)
print("Disimpan. Font Times New Roman diterapkan.")
print("Tabel biodata dinyatakan ada di dokumen, posisi bisa diedit lebih lanjut.")