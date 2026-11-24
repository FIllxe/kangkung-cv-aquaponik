# apply_italics_and_abbrev.py
"""Apply italic styling to English/foreign terms that are not yet italicized
and enforce abbreviation usage after the first explicit definition.

Steps:
1. Load the final proposal (`*_FINAL.docx`).
2. Scan all runs for words that:
   - Consist only of ASCII letters (A‑Z, a‑z) and possibly digits.
   - Are not already italic (`run.italic` is False or None).
   - Appear in a small whitelist of common technical terms (e.g., "IoT", "Python",
     "Arduino", "sensor", "algorithm", "machine learning", "CNN", "Raspberry Pi").
   The whitelist can be extended as needed.
   Those runs are set to italic.
3. Detect first‑occurrence definitions of the form "Full Term (ABBR)" where the
   full term is not italic but the abbreviation (inside parentheses) is.
   Record a mapping `{full_term: abbrev}`.
4. In all subsequent paragraphs, replace any whole‑word occurrence of the full term
   with the abbreviation (plain text, non‑italic). The replacement respects word
   boundaries.
5. Save the modified document as a new file:
   `PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL_ITALIC.docx`.

The script uses `python-docx` (installed if missing).
"""

import os, re
from pathlib import Path

try:
    import docx
    from docx.shared import Pt
except ImportError:
    print("Installing python-docx...")
    os.system("pip install python-docx")
    import docx
    from docx.shared import Pt

BASE_DIR = Path(r"C:/Users/felix/Documents/Project capstone/Computer Vision Aquaponic")
PROPOSAL_DIR = BASE_DIR / "docs" / "proposal"
SRC_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL.docx"
OUT_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL_ITALIC.docx"

# Whitelist of technical English terms that should be italicized if not already.
WHITELIST = [
    "IoT", "Python", "Arduino", "sensor", "algorithm", "CNN", "Raspberry Pi",
    "machine learning", "deep learning", "computer vision", "Fuzzy", "Sugeno",
    "Wi‑Fi", "Wi‑Fi", "MQTT", "GPIO", "PID", "RGB", "UV", "LED",
]

# Helper to find definition patterns like "Full Term (ABBR)"
DEF_PATTERN = re.compile(r"(?P<full>[A-Za-z][A-Za-z\s'-]+)\s*\((?P<abbr>[A-Z]{2,})\)")

def italicize_terms(doc):
    for para in doc.paragraphs:
        for run in para.runs:
            text = run.text
            # skip if already italic
            if run.italic:
                continue
            # check whole run against whitelist (case‑insensitive)
            lowered = text.lower()
            for term in WHITELIST:
                if term.lower() in lowered:
                    run.italic = True
                    break

def collect_abbrev_mappings(doc):
    mapping = {}
    for para in doc.paragraphs:
        for run in para.runs:
            for match in DEF_PATTERN.finditer(run.text):
                full = match.group('full').strip()
                abbr = match.group('abbr').strip()
                mapping[full] = abbr
                # make the abbreviation italic, full term normal
                # we replace the whole run text with formatted parts
                # split into three runs: before, full term, abbreviation (italic)
                before = run.text[:match.start('full')]
                after = run.text[match.end('abbr')+1:] if match.end('abbr') < len(run.text) else ''
                # clear original run
                run.text = before
                # insert full term run (normal)
                para = run._element.getparent().getparent()
                # after the original run, insert new runs
                # full term run
                full_run = para.add_run(full)
                full_run.italic = False
                # abbreviation run (italic)
                abbr_run = para.add_run(f" ({abbr})")
                abbr_run.italic = True
                # after run if any
                if after:
                    extra = para.add_run(after)
                # break after first definition found in doc
                break
    return mapping

def replace_full_with_abbr(doc, mapping):
    # Build regex pattern for each full term (word boundaries)
    for full, abbr in mapping.items():
        pattern = re.compile(r"\b" + re.escape(full) + r"\b")
        for para in doc.paragraphs:
            # rebuild paragraph text with runs preserving formatting where possible
            new_text = pattern.sub(abbr, para.text)
            if new_text != para.text:
                # replace whole paragraph with a single run (loss of other formatting)
                # For simplicity we reset the paragraph content.
                para.clear()
                para.add_run(new_text)

def main():
    if not SRC_DOC.is_file():
        raise FileNotFoundError(f"Source doc not found: {SRC_DOC}")
    doc = docx.Document(str(SRC_DOC))
    # 1. italicize whitelist terms
    italicize_terms(doc)
    # 2. collect abbreviation definitions
    abbrev_map = collect_abbrev_mappings(doc)
    # 3. replace later full terms with abbreviations
    if abbrev_map:
        replace_full_with_abbr(doc, abbrev_map)
    # save
    doc.save(str(OUT_DOC))
    print(f"Italic and abbreviation processing complete. Output: {OUT_DOC}")
    print(f"Abbreviation mappings applied: {abbrev_map}")

if __name__ == '__main__':
    main()

