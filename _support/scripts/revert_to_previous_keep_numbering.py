# revert_to_previous_keep_numbering.py
"""Revert the proposal to the version before the clean‑up while preserving the revised page numbering.

Steps:
1. Copy the *final* version (`*_FINAL.docx`) back to the original file name
   (`PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx`). This file already contains:
   - Arabic page numbers (top‑right) in the body section.
   - Roman‑numeral page numbers (center‑bottom) in the front‑matter section.
2. Delete the intermediate *clean* document (`*_CLEAN.docx`).
3. (Optional safety) Verify that the body section still has a header with a PAGE field.
   If not, re‑insert it.

The script writes the reverted document as the original filename and removes the clean file.
"""

import os, shutil
from pathlib import Path

try:
    import docx
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt
except ImportError:
    print("Installing python-docx...")
    os.system("pip install python-docx")
    import docx
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

BASE_DIR = Path(r"C:/Users/felix/Documents/Project capstone/Computer Vision Aquaponic")
PROPOSAL_DIR = BASE_DIR / "docs" / "proposal"
FINAL_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL.docx"
ORIG_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx"
CLEAN_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_CLEAN.docx"

def ensure_arabic_page_numbers(doc):
    """Make sure the body section (section index 2 or later) has a right‑aligned PAGE field.
    If a header already contains a PAGE field, we leave it unchanged.
    """
    if len(doc.sections) < 3:
        print("Document has fewer than 3 sections; cannot guarantee Arabic page numbers.")
        return
    body_sec = doc.sections[2]
    # Check if header already has a PAGE field
    has_page = any('PAGE' in p.text for p in body_sec.header.paragraphs)
    if has_page:
        return
    # Add page number header
    header = body_sec.header
    for p in header.paragraphs:
        p.clear()
    para = header.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = para.add_run()
    # field start
    fld_begin = OxmlElement('w:fldChar')
    fld_begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.text = 'PAGE'
    fld_sep = OxmlElement('w:fldChar')
    fld_sep.set(qn('w:fldCharType'), 'separate')
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run.add_text('1')
    fld_end = OxmlElement('w:fldChar')
    fld_end.set(qn('w:fldCharType'), 'end')
    run._r.append(fld_end)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)

def main():
    if not FINAL_DOC.is_file():
        raise FileNotFoundError(f"Final doc not found: {FINAL_DOC}")
    # Copy final doc over the original name (overwrite if exists)
    shutil.copy2(str(FINAL_DOC), str(ORIG_DOC))
    print(f"Replaced original doc with final version: {ORIG_DOC.name}")
    # Load the copied document to verify Arabic page numbers
    doc = docx.Document(str(ORIG_DOC))
    ensure_arabic_page_numbers(doc)
    doc.save(str(ORIG_DOC))
    print("Ensured Arabic page numbers are present in the body section.")
    # Delete the clean doc if it exists
    if CLEAN_DOC.exists():
        CLEAN_DOC.unlink()
        print(f"Deleted clean document: {CLEAN_DOC.name}")
    else:
        print("Clean document not found; nothing to delete.")

if __name__ == '__main__':
    main()

