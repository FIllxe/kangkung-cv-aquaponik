# apply_roman_footer.py
"""Adjust page numbering as requested:
1. Roman numerals (i, ii, iii, …) placed **centered in the footer** of the front‑matter
   section (section index 1). The field code is `PAGE \\* roman` which yields lower‑case
   numerals.
2. Remove any page‑number fields that appear in the **top‑right header** of any section.
3. Ensure the two cover pages (section 0) have **different first page header/footer**
   enabled and cleared, so no numbers are visible on the covers.
4. Save the result as a new file:
   `PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL_ROMAN.docx`.
"""

import os
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
SRC_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx"
OUT_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL_ROMAN.docx"

def clear_header_footer(section):
    """Remove all runs from header and footer of a given section."""
    for hdr in (section.header, section.footer):
        for p in hdr.paragraphs:
            p.clear()

def add_centered_roman_footer(section):
    """Add a centered bottom footer with lower‑case Roman numerals (i, ii, …)."""
    footer = section.footer
    # clear any existing content first
    for p in footer.paragraphs:
        p.clear()
    para = footer.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    # FIELD BEGIN
    fld_begin = OxmlElement('w:fldChar')
    fld_begin.set(qn('w:fldCharType'), 'begin')
    # INSTRTEXT for lower‑case roman
    instr = OxmlElement('w:instrText')
    instr.text = 'PAGE \\* roman'
    # FIELD SEPARATE
    fld_sep = OxmlElement('w:fldChar')
    fld_sep.set(qn('w:fldCharType'), 'separate')
    # placeholder (Word will replace)
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run.add_text('i')
    # FIELD END
    fld_end = OxmlElement('w:fldChar')
    fld_end.set(qn('w:fldCharType'), 'end')
    run._r.append(fld_end)
    # styling
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)

def remove_top_right_page_numbers(doc):
    """Iterate through all sections and clear any header that contains a PAGE field.
    This removes the top‑right Arabic numbers.
    """
    for sec in doc.sections:
        header = sec.header
        for p in header.paragraphs:
            if 'PAGE' in p.text:
                p.clear()

def main():
    if not SRC_DOC.is_file():
        raise FileNotFoundError(f"Source document not found: {SRC_DOC}")
    doc = docx.Document(str(SRC_DOC))

    # -------------------------------------------------
    # 1. Ensure covers have no visible page numbers
    # -------------------------------------------------
    if len(doc.sections) >= 1:
        cover_sec = doc.sections[0]
        cover_sec.different_first_page_header_footer = True
        clear_header_footer(cover_sec)

    # -------------------------------------------------
    # 2. Front‑matter (section 1) – Roman footer, remove any header numbers
    # -------------------------------------------------
    if len(doc.sections) >= 2:
        front_sec = doc.sections[1]
        # Clear header (remove possible top‑right page numbers)
        clear_header_footer(front_sec)
        # Add centered Roman footer
        add_centered_roman_footer(front_sec)
        # Ensure the same footer appears on all pages of this section
        front_sec.different_first_page_header_footer = False
    else:
        print("Warning: Document has less than 2 sections; cannot set Roman footer.")

    # -------------------------------------------------
    # 3. Body section – keep Arabic page numbers in header (right‑aligned)
    # -------------------------------------------------
    # We only need to ensure we didn't delete them inadvertently. If missing, add.
    if len(doc.sections) >= 3:
        body_sec = doc.sections[2]
        # Check if header already has a PAGE field; if not, add it.
        has_page = any('PAGE' in p.text for p in body_sec.header.paragraphs)
        if not has_page:
            # Clear existing header just in case
            clear_header_footer(body_sec)
            header = body_sec.header
            para = header.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            run = para.add_run()
            # PAGE field for Arabic numbers
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
    else:
        print("Warning: Document has fewer than 3 sections; body may be missing.")

    # Save the adjusted document
    doc.save(str(OUT_DOC))
    print(f"Adjusted document saved as {OUT_DOC}")

if __name__ == '__main__':
    main()

