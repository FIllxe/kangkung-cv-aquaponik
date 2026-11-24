# apply_final_fixes_v2.py
"""Apply the final formatting adjustments to a copy of the proposal.

Features:
1. Add Roman‑numeral page numbers (centered bottom footers) to all front‑matter pages *except* the two cover pages.
2. Delete the "Lampiran 3" appendix (heading and its content) while keeping any textual mentions; replace those mentions with "gambar 3.3".
3. Make every centered paragraph (used for equations) bold.
4. Save the result to a new file so we avoid file‑lock issues.

The script works on:
    docs/proposal/PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx
and writes:
    docs/proposal/PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL.docx
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
OUT_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL.docx"


def add_roman_footer(section):
    """Add a centered bottom footer with a Roman‑numeral PAGE field to *section*.
    The field instruction is: PAGE \\* ROMAN
    """
    footer = section.footer
    # clear existing content
    for p in footer.paragraphs:
        p.clear()
    para = footer.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    # field start
    fld_begin = OxmlElement('w:fldChar')
    fld_begin.set(qn('w:fldCharType'), 'begin')
    # instruction text
    instr = OxmlElement('w:instrText')
    instr.text = 'PAGE \\* ROMAN'
    # field separate
    fld_sep = OxmlElement('w:fldChar')
    fld_sep.set(qn('w:fldCharType'), 'separate')
    # placeholder (Word will replace)
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run.add_text('i')
    # field end
    fld_end = OxmlElement('w:fldChar')
    fld_end.set(qn('w:fldCharType'), 'end')
    run._r.append(fld_end)
    # styling
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)


def delete_lampiran_3(doc):
    """Remove the 'Lampiran 3' heading and all following paragraphs until the next heading that starts with 'Lampiran' (e.g., Lampiran 4) or end of document.
    Returns True if something was removed.
    """
    paras = list(doc.paragraphs)
    start = None
    end = None
    for i, p in enumerate(paras):
        txt = p.text.strip().lower()
        if txt.startswith('lampiran 3'):
            start = i
            continue
        if start is not None and txt.startswith('lampiran'):
            end = i
            break
    if start is not None:
        if end is None:
            end = len(paras)
        # delete range [start, end)
        for _ in range(end - start):
            p = doc.paragraphs[start]
            p._element.getparent().remove(p._element)
        return True
    return False


def replace_lampiran_mentions(doc):
    """Replace any occurrence of the phrase 'Lampiran 3' (any case) with 'gambar 3.3'."""
    for p in doc.paragraphs:
        if 'Lampiran 3' in p.text:
            p.text = p.text.replace('Lampiran 3', 'gambar 3.3')
        if 'lampiran 3' in p.text:
            p.text = p.text.replace('lampiran 3', 'gambar 3.3')


def bold_centered_paragraphs(doc):
    """Set bold=True for all runs in paragraphs that are centered (used for equations)."""
    for p in doc.paragraphs:
        if p.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            for run in p.runs:
                run.bold = True


def main():
    if not SRC_DOC.is_file():
        raise FileNotFoundError(f"Source document not found: {SRC_DOC}")
    # Load source
    doc = docx.Document(str(SRC_DOC))
    # -------------------------------------------------
    # 1. Roman numeral footer on front‑matter (section 1)
    # -------------------------------------------------
    if len(doc.sections) >= 2:
        front_section = doc.sections[1]
        # Ensure same footer for all pages of this section
        front_section.different_first_page_header_footer = False
        add_roman_footer(front_section)
    else:
        print('Warning: Not enough sections to add Roman footer.')
    # -------------------------------------------------
    # 2. Delete Lampiran 3 and replace mentions
    # -------------------------------------------------
    removed = delete_lampiran_3(doc)
    replace_lampiran_mentions(doc)
    # -------------------------------------------------
    # 3. Bold centered paragraphs (equations)
    # -------------------------------------------------
    bold_centered_paragraphs(doc)
    # -------------------------------------------------
    # Save to new file
    # If the output already exists, overwrite it.
    doc.save(str(OUT_DOC))
    print(f"Final document written to {OUT_DOC}")
    print(f"Lampiran 3 removed: {removed}")

if __name__ == '__main__':
    main()

