from docx import Document
import json

doc = Document(r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx")

print("=== PROPOSAL DOCUMENT STRUCTURE ===")
print("Total paragraphs:", len(doc.paragraphs))
print("Total tables:", len(doc.tables))
print()

# Print first 50 paragraphs
print("=== First 50 Paragraphs ===")
for i, p in enumerate(doc.paragraphs[:50]):
    if p.text.strip():
        print(f"P{i}: {p.text[:80]}")

print()
print("=== All Tables ===")
for i, t in enumerate(doc.tables):
    print(f"Table {i}: {len(t.rows)}x{len(t.columns)}")
    for row_idx, row in enumerate(t.rows[:3]):
        cells_text = [c.text[:30] for c in row.cells]
        print(f"  Row {row_idx}: {cells_text}")