import docx, json, sys

def extract_structure(path):
    doc = docx.Document(path)
    data = {'headings': [], 'paragraphs': [], 'tables': []}
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if not text:
            continue
        style = p.style.name if p.style else ''
        if 'Heading' in style:
            data['headings'].append({'index': i, 'style': style, 'text': text})
        else:
            data['paragraphs'].append({'index': i, 'text': text})
    for ti, tbl in enumerate(doc.tables):
        rows = []
        for r in tbl.rows:
            cells = [c.text.strip() for c in r.cells]
            rows.append(cells)
        data['tables'].append({'table_index': ti, 'rows': rows})
    return data

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    path = 'C:/Users/felix/.gemini/antigravity/brain/981bc2f8-3e09-4d63-9b77-2c8afe6b8aff/.user_uploaded/media_1793469441453_5deb8b5a.docx'
    struct = extract_structure(path)
    print(json.dumps(struct, ensure_ascii=False, indent=2))

