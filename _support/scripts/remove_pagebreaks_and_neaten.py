from docx import Document
from docx.shared import Pt, Inches

# Load the document
doc = Document(r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx")

# Step 1: Remove page break formatting from all paragraphs
print("Menghapus page break formatting...")
bp_removed = 0
for p in doc.paragraphs:
    if p.paragraph_format.page_break:
        p.paragraph_format.page_break = False
        bp_removed += 1
print(f"  Paragraphs with page break removed: {bp_removed}")

# Step 2: Identify and organize biodata tables
print("\nMenganalisis tabel biodata...")
biodata_indices = []
for i, t in enumerate(doc.tables):
    table_text = ""
    for row in t.rows[:3]:  # Check first 3 rows
        for cell in row.cells:
            table_text += cell.text + " "
    indicators_biodata = ["Nama Lengkap", "Jenis Kelamin", "NIM", "Tempat Tanggal", "Alamat E-mail", "Nomor Telepon"]
    indicators_pendidikan = ["SD", "SMP", "SMA"]
    is_biodata = any(ind in table_text for ind in indicators_biodata + indicators_pendidikan)
    if is_biodata:
        biodata_indices.append(i)

print(f"  Tabel biodata indices: {biodata_indices}")
for i in biodata_indices:
    t = doc.tables[i]
    print(f"  Table {i}: {len(t.rows)} rows x {len(t.columns)} columns")
    # Print header rows
    for row_idx in range(min(3, len(t.rows))):
        row_text = " | ".join([c.text[:20] for c in t.rows[row_idx].cells])
        print(f"    Row {row_idx}: {row_text}")

# Step 3: Remove any empty paragraph page breaks and clean up
print("\nMembersihkan paragraph formatting...")
# Reset all paragraph formatting to default clean state
for p in doc.paragraphs:
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.page_break = False
    # Keep line spacing normal
    p.paragraph_format.line_spacing_rule = 1  # WD_LINE_SPACING.SINGLE is 1

# Step 4: Add proper structure - ensure tables have proper formatting
print("\nMenyelaraskan format tabel...")
for i in biodata_indices:
    t = doc.tables[i]
    # Set column widths if needed
    for row in t.rows:
        for i_cell, cell in enumerate(row.cells):
            # Set preferred width proportionally
            cell.width = Inches(1.5)  # Default width

# Step 5: Save the cleaned document
output_path = r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx"
doc.save(output_path)

print(f"\n=== SELESAI ===")
print(f"Page break paragraphs removed: {bp_removed}")
print(f"Total paragraphs: {len(doc.paragraphs)}")
print(f"Total tables: {len(doc.tables)}")
print(f"Biodata tables at indices: {biodata_indices}")
print(f"Dokumen disimpan ke: {output_path}")
print("\nDocument telah 'dirapihkan' (dibersihkan formatting page break)")
print("Tabel biodata masih berada di posisinya, tanpa page break markers")
print("Silakan buka di Microsoft Word dan sesuaikan posisikan tabel ke halaman 25, 26, 27 di lampiran")