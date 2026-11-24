# apply_style_fix_and_verify.py
"""Apply explicit style fixes to a proposal DOCX (main version) and verify against the team proposal.

The script performs:
1. Load the target document (`PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx`).
2. Ensure the `Normal` style (used for body paragraphs) has:
   - Font: Times New Roman
   - Size: 12 pt
   - Line spacing: 1.5
   - First line indent: 0.5 cm (≈226 twips) – the team doc uses this.
   - Left indent: 0 cm (default).
3. Ensure heading styles (`Heading 1`, `Heading 2`, `Heading 3`) have:
   - Font: Times New Roman
   - Size: 14 pt (as seen in the team proposal for section titles)
   - Line spacing: 1.5
4. For any paragraph that still lacks an explicit font/size (run.font.name is None), set it to the defaults above.
5. Save the modified document (overwrites the original).
6. Re‑run the style‑comparison routine (`compare_styles`) from the previous
   `apply_page_numbers_and_style_check.py` script and write a fresh report to
   `style_check_report_after_fix.txt`.

The script uses `python-docx`. If it is not yet installed, the script will install it.
"""

import os
from pathlib import Path

try:
    import docx
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except ImportError:
    print("Installing python-docx...")
    os.system("pip install python-docx")
    import docx
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE_DIR = Path(r"C:/Users/felix/Documents/Project capstone/Computer Vision Aquaponic")
PROPOSAL_DIR = BASE_DIR / "docs" / "proposal"
TARGET_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx"
TEAM_DOC = Path(r"C:/Users/felix/.gemini/antigravity/brain/981bc2f8-3e09-4d63-9b77-2c8afe6b8aff/.user_uploaded/media_1793469441453_5deb8b5a.docx")


def set_style_defaults(doc):
    # Normal style
    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(12)
    # Paragraph format for Normal
    normal_par = normal.paragraph_format
    normal_par.line_spacing = 1.5
    # First line indent ~0.5 cm (226 twips)
    normal_par.first_line_indent = Pt(12)  # Approx 0.5 cm (12 pt) – close enough
    # Ensure any runs without explicit font inherit the style
    for para in doc.paragraphs:
        for run in para.runs:
            if run.font.name is None:
                run.font.name = 'Times New Roman'
            if run.font.size is None:
                run.font.size = Pt(12)
    # Heading styles
    for level in range(1, 4):
        style_name = f'Heading {level}'
        if style_name in doc.styles:
            heading = doc.styles[style_name]
            heading.font.name = 'Times New Roman'
            heading.font.size = Pt(14)  # team uses 14 pt for headings
            heading.paragraph_format.line_spacing = 1.5


def verify_styles(doc_path: Path, team_path: Path, report_path: Path):
    # Re‑use the same comparison logic from the earlier script
    from docx import Document
    doc = Document(str(doc_path))
    team = Document(str(team_path))
    mismatches = []
    def style_info(p):
        fmt = p.paragraph_format
        size = p.runs[0].font.size.pt if p.runs and p.runs[0].font.size else None
        return {
            "font": p.runs[0].font.name if p.runs else None,
            "size": size,
            "spacing": fmt.line_spacing,
            "first_indent": fmt.first_line_indent.pt if fmt.first_line_indent else None,
            "left_indent": fmt.left_indent.pt if fmt.left_indent else None,
        }
    team_map = {p.text[:30]: style_info(p) for p in team.paragraphs if p.text.strip()}
    for p in doc.paragraphs:
        txt = p.text[:30]
        if txt in team_map:
            dstyle = style_info(p)
            tstyle = team_map[txt]
            for key in dstyle:
                if dstyle[key] != tstyle[key]:
                    mismatches.append({"text": txt, "attribute": key, "doc": dstyle[key], "team": tstyle[key]})
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Style mismatches after fix for {doc_path.name}:\n")
        if not mismatches:
            f.write("  None detected. All compared paragraphs now match the team proposal.\n")
        else:
            for m in mismatches:
                f.write(f"  Paragraph snippet: '{m['text']}'\n")
                f.write(f"    {m['attribute']}: doc={m['doc']}  team={m['team']}\n")
    print(f"Verification report written to {report_path}")

if __name__ == "__main__":
    if not TARGET_DOC.is_file():
        raise FileNotFoundError(f"Target file not found: {TARGET_DOC}")
    doc = docx.Document(str(TARGET_DOC))
    set_style_defaults(doc)
    doc.save(str(TARGET_DOC))
    print(f"Applied style fixes to {TARGET_DOC.name}")
    # Verify
    report_file = BASE_DIR / "style_check_report_after_fix.txt"
    verify_styles(TARGET_DOC, TEAM_DOC, report_file)

