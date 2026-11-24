# apply_cleanup.py
"""Clean up the proposal document according to the latest user request.

Tasks performed:
1. Ensure Roman‑numeral page numbers appear **only** in a centered bottom footer for the
   front‑matter section (excluding the two cover pages). The numerals use lower‑case
   i, ii, iii… (`PAGE \\* roman`). Any existing page‑number fields in headers or other
   footers are removed.
2. Italicize only the specified English/foreign terms (word‑level), **not** entire
   sentences or paragraphs.
3. Delete the previously generated "final italic abbreviation" file.
4. Save the cleaned document as a new file:
   `PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_CLEAN.docx`.
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
SRC_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL.docx"
CLEAN_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_CLEAN.docx"

# File to delete (the earlier italic‑abbr version)
ABBR_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL_ITALIC_ABBR.docx"

# Whitelist of terms that should be italicized (word‑level).
WHITELIST = [
    "IoT", "Python", "Arduino", "sensor", "algorithm", "CNN", "Raspberry Pi",
    "machine learning", "deep learning", "computer vision", "Fuzzy", "Sugeno",
    "Wi‑Fi", "MQTT", "GPIO", "PID", "RGB", "UV", "LED",
]

def clear_section_header_footer(section):
    """Remove all content from header and footer of a section."""
    for hdr in (section.header, section.footer):
        for p in hdr.paragraphs:
            p.clear()

def add_roman_footer(section):
    """Add a centered bottom footer with lower‑case Roman numerals (i, ii, …)."""
    footer = section.footer
    for p in footer.paragraphs:
        p.clear()
    para = footer.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    # field start
    fld_begin = OxmlElement('w:fldChar')
    fld_begin.set(qn('w:fldCharType'), 'begin')
    # instruction text – lower‑case roman
    instr = OxmlElement('w:instrText')
    instr.text = 'PAGE \\* roman'
    fld_sep = OxmlElement('w:fldChar')
    fld_sep.set(qn('w:fldCharType'), 'separate')
    # placeholder (Word replaces it)
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

def italicize_terms_in_paragraph(paragraph, whitelist):
    """Re‑build the paragraph runs, italicising only whole‑word matches from *whitelist*.
    The rest of the text stays non‑italic.
    """
    text = paragraph.text
    # Build a single regex that matches any term (case‑insensitive) with word boundaries.
    escaped = [re.escape(term) for term in whitelist]
    pattern = re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)
    # Clear existing runs
    for run in list(paragraph.runs):
        paragraph._element.remove(run._element)
    pos = 0
    for m in pattern.finditer(text):
        # text before the match
        before = text[pos:m.start()]
        if before:
            paragraph.add_run(before)  # normal
        term = m.group(0)
        italic_run = paragraph.add_run(term)
        italic_run.italic = True
        pos = m.end()
    # trailing text
    after = text[pos:]
    if after:
        paragraph.add_run(after)

def main():
    # Delete the old italic‑abbr file if it exists.
    if ABBR_DOC.exists():
        ABBR_DOC.unlink()
        print(f"Deleted old file: {ABBR_DOC.name}")
    else:
        print("No previous italic‑abbr file found to delete.")

    if not SRC_DOC.is_file():
        raise FileNotFoundError(f"Source document not found: {SRC_DOC}")
    doc = docx.Document(str(SRC_DOC))

    # -------------------------------------------------
    # 1. Clean up headers/footers and add Roman footer
    # -------------------------------------------------
    # Ensure we have at least two sections: covers (0), front‑matter (1), body (2+)
    if len(doc.sections) >= 2:
        # Clear only the front‑matter header/footer (section 1) to avoid touching the body’s Arabic page numbers
        if len(doc.sections) > 1:
            clear_section_header_footer(doc.sections[1])
        # Front‑matter is section 1 (covers are section 0). Add roman footer.
        front_sec = doc.sections[1]
        front_sec.different_first_page_header_footer = False
        add_roman_footer(front_sec)
    else:
        print("Warning: Document has fewer than 2 sections; cannot set Roman footer properly.")

    # -------------------------------------------------
    # 2. Italicise whitelist terms (word‑level only)
    # -------------------------------------------------
    for para in doc.paragraphs:
        italicize_terms_in_paragraph(para, WHITELIST)

    # Save cleaned document
    doc.save(str(CLEAN_DOC))
    print(f"Clean document written to {CLEAN_DOC}")

if __name__ == "__main__":
    main()
