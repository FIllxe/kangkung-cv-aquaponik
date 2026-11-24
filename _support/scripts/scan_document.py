from docx import Document
import json

doc = Document(r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\docs\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx")

# Scan document
result = {
    "total_paragraphs": len(doc.paragraphs),
    "total_tables": len(doc.tables),
    "page_break_paragraphs": sum(1 for p in doc.paragraphs if p.paragraph_format.page_break),
    "tables": []
}

for i, t in enumerate(doc.tables):
    table_info = {
        "index": i,
        "rows": len(t.rows),
        "cols": len(t.columns),
        "first_row_text": [c.text[:40] for c in t.rows[0].cells] if t.rows else [],
        "last_row_text": [c.text[:40] for c in t.rows[-1].cells] if t.rows else [],
    }
    result["tables"].append(table_info)

# Save to file
with open(r"C:\Users\felix\Documents\Project capstone\Computer Vision Aquaponic\scan_result.txt", "w", encoding="utf-8") as f:
    f.write(json.dumps(result, indent=2, ensure_ascii=False))

# Also print to console
print("=== SCAN HASIL ===")
print(f"Total paragraphs: {len(doc.paragraphs)}")
print(f"Total tables: {len(doc.tables)}")
print(f"Page break paragraphs: {sum(1 for p in doc.paragraphs if p.paragraph_format.page_break)}")
print()
for i, t in enumerate(doc.tables):
    print(f"Table {i}: {len(t.rows)}x{len(t.columns)}")
    print(f"  Header: {[c.text[:30] for c in t.rows[0].cells]}")
    if len(t.rows) > 1:
        print(f"  Last row: {[c.text[:30] for c in t.rows[-1].cells]}")