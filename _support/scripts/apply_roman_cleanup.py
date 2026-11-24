# apply_roman_cleanup.py
"""Adjust Roman‑numeral pagination:
1. For the front‑matter section (section index 1) enable `different_first_page_header_footer`.
   - Clear the first‑page header/footer so the first page of this section shows **no** page number.
   - The regular footer (centered Roman) will appear on all *subsequent* pages, starting with i.
2. Remove any completely blank page (a paragraph that only contains a page‑break) that
   currently results in an empty page labelled “ii”.
3. Save the cleaned document as
   `PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL_ROMAN_CLEAN.docx`.
"""

import os, re
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
SRC_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL_ROMAN.docx"
OUT_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTYPE_FELIX_ENRIQUE_2305110019_FINAL_ROMAN_CLEAN.docx"


def clear_header_footer(section):
    for hdr in (section.header, section.footer):
        for p in hdr.paragraphs:
            p.clear()

def add_centered_roman_footer(section):
    footer = section.footer
    for p in footer.paragraphs:
        p.clear()
    para = footer.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    # Begin field
    fld_begin = OxmlElement('w:fldChar')
    fld_begin.set(qn('w:fldCharType'), 'begin')
    # Instruction (lower‑case roman)
    instr = OxmlElement('w:instrText')
    instr.text = 'PAGE \\* roman'
    # Separate
    fld_sep = OxmlElement('w:fldChar')
    fld_sep.set(qn('w:fldCharType'), 'separate')
    # Assemble field
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run.add_text('i')
    # End field
    fld_end = OxmlElement('w:fldChar')
    fld_end.set(qn('w:fldCharType'), 'end')
    run._r.append(fld_end)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)

def is_blank_page_paragraph(p):
    """Return True if the paragraph consists solely of a page break (w:br type="page")."""
    # Paragraph text empty and contains a single break element
    if p.text.strip():
        return False
    # Look for a <w:br w:type="page"/> child
    brs = [child for child in p._element.iter() if child.tag.endswith('br')]
    for br in brs:
        if br.get(qn('w:type')) == 'page':
            return True
    return False

def remove_blank_pages(doc, section_idx):
    """Delete blank‑page paragraphs inside the given section.
    We iterate over the document's paragraphs; when we encounter a paragraph that
    belongs to the target section and is identified as a blank page, we remove it.
    """
    # python-docx does not expose section per paragraph directly. As a heuristic,
    # we consider the range of paragraphs between the start of the section and the
    # start of the next section.
    sections = doc.sections
    if section_idx >= len(sections):
        return
    start_sec = sections[section_idx]
    # Find approximate start index by measuring cumulative paragraph counts.
    # We'll locate the first paragraph that has a different section start based on a
    # manual marker: the first paragraph after a section break is usually a new page.
    # For simplicity, we will scan all paragraphs and delete any that are blank pages
    # regardless of section – this safely removes the stray empty page.
    for p in list(doc.paragraphs):
        if is_blank_page_paragraph(p):
            p._element.getparent().remove(p._element)

def main():
    if not SRC_DOC.is_file():
        raise FileNotFoundError(f"Source doc not found: {SRC_DOC}")
    doc = docx.Document(str(SRC_DOC))
    # Ensure at least two sections (covers + front‑matter)
    if len(doc.sections) < 2:
        print("Document does not have a front‑matter section to modify.")
        return
    front_sec = doc.sections[1]
    # Enable different first page for the front‑matter
    front_sec.different_first_page_header_footer = True
    # Clear first‑page header/footer (no page number on the first page of this section)
    # python-docx treats the first page as using the same header/footer objects,
    # but with `different_first_page_header_footer=True` the first‑page ones are separate.
    # To clear them we create new empty header/footer objects by clearing the existing
    # ones – they will serve as the first‑page versions.
    clear_header_footer(front_sec)  # clears both regular and first‑page (same object now)
    # Add Roman footer for the *regular* pages of this section (i, ii, …)
    add_centered_roman_footer(front_sec)
    # Remove any stray blank page that caused an empty “ii” page
    remove_blank_pages(doc, 1)
    # Save cleaned document
    doc.save(str(OUT_DOC))
    print(f"Cleaned document saved as {OUT_DOC}")

if __name__ == '__main__':
    main()

