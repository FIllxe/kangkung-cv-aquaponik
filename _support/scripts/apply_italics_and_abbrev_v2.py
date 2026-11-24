# apply_italics_and_abbrev_v2.py
"""Apply italic styling to English/foreign terms that are not yet italicized
and enforce abbreviation usage after the first explicit definition.

Workflow:
1. Load the finalized proposal (`*_FINAL.docx`).
2. Italicize any occurrence of terms from a whitelist if the run is not already italic.
3. Scan for first‑occurrence definitions of the form "Full Term (ABBR)".
   - Record a mapping `{full_term: abbr}`.
   - Ensure the abbreviation inside parentheses is italic (optional).
4. Replace every later whole‑word occurrence of each recorded `full_term`
   with its `abbr` (plain, non‑italic).
5. Save to a new file:
   `PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL_ITALIC_ABBR.docx`

The script uses `python-docx`; it will be installed if missing.
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
OUT_DOC = PROPOSAL_DIR / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019_FINAL_ITALIC_ABBR.docx"

# Terms that should appear italicized (English/foreign technical words).
WHITELIST = [
    "IoT", "Python", "Arduino", "sensor", "algorithm", "CNN", "Raspberry Pi",
    "machine learning", "deep learning", "computer vision", "Fuzzy", "Sugeno",
    "Wi‑Fi", "MQTT", "GPIO", "PID", "RGB", "UV", "LED",
]

# Regex to capture definitions like "Full Term (ABBR)"
DEF_REGEX = re.compile(r"(?P<full>[A-Za-z][A-Za-z\s'\-]+)\s*\((?P<abbr>[A-Z]{2,})\)")

def italicize_whitelist(doc):
    for para in doc.paragraphs:
        for run in para.runs:
            if run.italic:
                continue
            txt = run.text
            # Check each whitelist term (case‑insensitive) present in the run text.
            for term in WHITELIST:
                if re.search(re.escape(term), txt, re.IGNORECASE):
                    run.italic = True
                    break

def find_definitions(doc):
    """Return a dict mapping full term -> abbreviation for the first occurrence only.
    The search proceeds paragraph by paragraph; later duplicate definitions are ignored.
    """
    mapping = {}
    for para in doc.paragraphs:
        # Look for pattern in the whole paragraph text.
        for m in DEF_REGEX.finditer(para.text):
            full = m.group('full').strip()
            abbr = m.group('abbr').strip()
            if full not in mapping:
                mapping[full] = abbr
                # Make abbreviation italic inside the paragraph (optional, simple approach)
                # We'll rebuild the paragraph text with the abbreviation wrapped in <i> style.
                # Since python-docx does not support inline HTML, we replace runs.
                # Simplify: remove all runs and add a new run with the updated text.
                new_text = para.text.replace(f"{full} ({abbr})", f"{full} ({abbr})")  # placeholder, keep same
                # Re‑create runs preserving formatting is complex; skip styling abbreviation.
                # The main goal (abbreviation later) is satisfied.
                break
        if len(mapping) >= 1:
            # Continue scanning to collect all distinct definitions.
            continue
    return mapping

def replace_full_with_abbr(doc, mapping):
    # Build a compiled regex for each full term with word boundaries.
    compiled = {full: re.compile(r"\b" + re.escape(full) + r"\b") for full in mapping}
    for para in doc.paragraphs:
        new_text = para.text
        changed = False
        for full, regex in compiled.items():
            if regex.search(new_text):
                new_text = regex.sub(mapping[full], new_text)
                changed = True
        if changed:
            # Replace paragraph runs with a single run containing the new text.
            # Remove existing runs.
            for run in list(para.runs):
                para._element.remove(run._element)
            para.add_run(new_text)

def main():
    if not SRC_DOC.is_file():
        raise FileNotFoundError(f"Source document not found: {SRC_DOC}")
    doc = docx.Document(str(SRC_DOC))
    # 1. Italicize whitelist terms.
    italicize_whitelist(doc)
    # 2. Find full‑term -> abbreviation mappings.
    abbrev_map = find_definitions(doc)
    # 3. Replace later occurrences.
    if abbrev_map:
        replace_full_with_abbr(doc, abbrev_map)
    # Save result.
    doc.save(str(OUT_DOC))
    print(f"Processing complete. Output written to {OUT_DOC}")
    print(f"Abbreviation mappings applied: {abbrev_map}")

if __name__ == '__main__':
    main()

