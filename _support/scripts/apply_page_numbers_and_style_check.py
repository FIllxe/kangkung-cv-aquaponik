# apply_page_numbers_and_style_check.py
"""Script to insert page numbers (top‑right, Arabic) into proposal DOCX files
and to verify style consistency against the team proposal.

Assumptions:
- The proposal documents are located in `docs/proposal/`.
- The team proposal file is provided as an artifact and is accessible at the
  path given in the artifact list.
- We use `python-docx` for manipulation. It supports adding headers/footers
  per‑section, but does not expose the "different first page" flag directly.
  We emulate the required layout by:
  1. Ensuring the first two sections (covers) have empty headers.
  2. Adding a right‑aligned PAGE field to the header of the body section.

The script performs:
- Load each target DOCX (main and "tanpa_i" variant).
- Ensure there are at least three sections (cover, front‑matter, body).
- For the body section, create a header if missing, add a right‑aligned PAGE
  field, and set the font to Times New Roman, 12 pt.
- Save the modified files.
- Compare paragraph and heading styles with the team proposal and report any
  mismatches (font name, size, line spacing, indentation). The report is saved
  to `style_check_report.txt`.
"""

import sys
import os
from pathlib import Path

# Ensure python-docx is installed
try:
    import docx
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, Inches
except ImportError:
    print("python-docx not found, installing via pip...")
    os.system("pip install python-docx")
    import docx
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, Inches

# Paths
BASE_DIR = Path(r"C:/Users/felix/Documents/Project capstone/Computer Vision Aquaponic")
PROPOSAL_DIR = BASE_DIR / "docs" / "proposal"
MAIN_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx"
NO_I_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_TANPA_I.docx"
TEAM_DOC = Path(r"C:/Users/felix/.gemini/antigravity/brain/981bc2f8-3e09-4d63-9b77-2c8afe6b8aff/.user_uploaded/media_1793469441453_5deb8b5a.docx")

TARGETS = [MAIN_DOC, NO_I_DOC]

def add_page_number_header(section):
    """Add a right‑aligned PAGE field to the header of *section*.
    The header is created if absent. Existing content is cleared.
    """
    header = section.header
    # Clear existing paragraphs
    for p in header.paragraphs:
        p.clear()
    paragraph = header.add_paragraph()
    paragraph.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.RIGHT
    # Insert PAGE field
    run = paragraph.add_run()
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.text = 'PAGE'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    # placeholder text – Word will replace it
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run.add_text('1')  # placeholder
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar3)
    # Set font
    font = run.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

def process_document(doc_path: Path):
    doc = docx.Document(str(doc_path))
    # Ensure we have at least three sections; python-docx treats each section as a separate object
    if len(doc.sections) < 3:
        print(f"Warning: {doc_path.name} has only {len(doc.sections)} sections; expected >=3.")
    # Section 0: cover – ensure empty header/footer
    for sec in doc.sections[:2]:
        sec.header.paragraphs[0].clear() if sec.header.paragraphs else None
        sec.footer.paragraphs[0].clear() if sec.footer.paragraphs else None
    # Body section (assumed index 2)
    body_sec = doc.sections[2]
    add_page_number_header(body_sec)
    doc.save(str(doc_path))
    print(f"Processed {doc_path.name}")

def compare_styles(doc_path: Path, team_path: Path):
    """Compare paragraph/heading style attributes between *doc_path* and *team_path*.
    Returns a list of mismatches.
    """
    doc = docx.Document(str(doc_path))
    team = docx.Document(str(team_path))
    mismatches = []
    # Helper to extract style info from a paragraph
    def style_info(p):
        fmt = p.paragraph_format
        return {
            "font": p.runs[0].font.name if p.runs else None,
            "size": p.runs[0].font.size.pt if p.runs and p.runs[0].font.size else None,
            "spacing": fmt.line_spacing,
            "first_indent": fmt.first_line_indent.pt if fmt.first_line_indent else None,
            "left_indent": fmt.left_indent.pt if fmt.left_indent else None,
        }
    # Build maps by text content (first 30 chars) for quick comparison
    team_map = {p.text[:30]: style_info(p) for p in team.paragraphs if p.text.strip()}
    for p in doc.paragraphs:
        txt = p.text[:30]
        if txt in team_map:
            doc_style = style_info(p)
            team_style = team_map[txt]
            for key in doc_style:
                if doc_style[key] != team_style[key]:
                    mismatches.append({
                        "text": txt,
                        "attribute": key,
                        "doc_value": doc_style[key],
                        "team_value": team_style[key]
                    })
    return mismatches

if __name__ == "__main__":
    for target in TARGETS:
        if target.is_file():
            process_document(target)
        else:
            print(f"Target file not found: {target}")
    # Style check report
    report_path = BASE_DIR / "style_check_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        for target in TARGETS:
            mism = compare_styles(target, TEAM_DOC)
            f.write(f"Style mismatches for {target.name}:\n")
            if not mism:
                f.write("  None detected.\n")
            else:
                for m in mism:
                    f.write(f"  Paragraph snippet: '{m['text']}'\n")
                    f.write(f"    {m['attribute']}: doc={m['doc_value']}  team={m['team_value']}\n")
            f.write("\n")
    print(f"Style check report written to {report_path}")

