import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document('docs/proposal/PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx')

for idx in [147, 148, 153, 170, 226, 232, 256]:
    print(f'P{idx}: {doc.paragraphs[idx].text[:120]}...')

