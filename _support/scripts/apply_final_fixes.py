# apply_final_fixes.py
"""Apply the final formatting adjustments requested:
1. Roman‑numeral page numbers (centered bottom) on all front‑matter pages *except* the two cover pages.
2. Delete the "Lampiran 3" appendix (heading and its content) while keeping any textual mentions; replace those mentions with "gambar 3.3".
3. Make every centered paragraph (used for equations) bold.

The script works on the main proposal document:
    docs/proposal/PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx
It preserves the Arabic page numbers already added to the body section.
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
DOC_PATH = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx"


def add_roman_footer(section):
    """Add a centered bottom footer with Roman‑numeral PAGE field to *section*.
    The field code is: PAGE  \* ROMAN
    """
    footer = section.footer
    # Clear existing paragraphs
    for p in footer.paragraphs:
        p.clear()
    para = footer.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    # Insert field start
    fldChar_begin = OxmlElement('w:fldChar')
    fldChar_begin.set(qn('w:fldCharType'), 'begin')
    # Instruction text
    instr = OxmlElement('w:instrText')
    instr.text = 'PAGE \\* ROMAN'
    # Separate
    fldChar_sep = OxmlElement('w:fldChar')
    fldChar_sep.set(qn('w:fldCharType'), 'separate')
    # End
    fldChar_end = OxmlElement('w:fldChar')
    fldChar_end.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar_begin)
    run._r.append(instr)
    run._r.append(fldChar_sep)
    # placeholder text (Word will replace)
    run.add_text('i')
    run._r.append(fldChar_end)
    # Font styling
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)


def delete_lampiran_3(doc):
    """Remove the 'Lampiran 3' section (heading and following content) until the next 'Lampiran' heading or end of document.
    Returns True if something was removed.
    """
    paragraphs = list(doc.paragraphs)
    start_idx = None
    end_idx = None
    for i, p in enumerate(paragraphs):
        txt = p.text.strip().lower()
        if txt.startswith('lampiran 3'):
            start_idx = i
            continue
        if start_idx is not None:
            # stop when another 'lampiran' heading appears (e.g., Lampiran 4)
            if txt.startswith('lampiran'):
                end_idx = i
                break
    if start_idx is not None:
        if end_idx is None:
            end_idx = len(paragraphs)
        # Delete range
        for _ in range(end_idx - start_idx):
            p = doc.paragraphs[start_idx]
            p._element.getparent().remove(p._element)
        return True
    return False


def replace_lampiran_mentions(doc):
    """Replace any textual occurrence of 'Lampiran 3' with 'gambar 3.3'."""
    for p in doc.paragraphs:
        if 'Lampiran 3' in p.text:
            new_text = p.text.replace('Lampiran 3', 'gambar 3.3')
            p.text = new_text
        # also handle lower‑case variants
        if 'lampiran 3' in p.text:
            p.text = p.text.replace('lampiran 3', 'gambar 3.3')


def bold_centered_paragraphs(doc):
    """Make all runs in centered paragraphs bold (commonly used for equations)."""
    for p in doc.paragraphs:
        if p.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            for run in p.runs:
                run.bold = True


def main():
    if not DOC_PATH.is_file():
        raise FileNotFoundError(f"Document not found: {DOC_PATH}")
    doc = docx.Document(str(DOC_PATH))
    # -------------------------------------------------
    # 1. Roman numeral footer on front‑matter (section 1)
    # -------------------------------------------------
    if len(doc.sections) >= 2:
        front_section = doc.sections[1]
        # Ensure different first page header/footer false (we want same footer for all front‑matter pages)
        front_section.different_first_page_header_footer = False
        add_roman_footer(front_section)
    else:
        print("Warning: Less than 2 sections – cannot add Roman footer.")
    # -------------------------------------------------
    # 2. Delete Lampiran 3 and replace mentions
    # -------------------------------------------------
    removed = delete_lampiran_3(doc)
    replace_lampiran_mentions(doc)
    # -------------------------------------------------
    # 3. Bold centered paragraphs (equations)
    # -------------------------------------------------
    bold_centered_paragraphs(doc)
    # Save
    doc.save(str(DOC_PATH))
    print(f"Final fixes applied. Lampiran 3 removed: {removed}")

if __name__ == "__main__":
    main()

