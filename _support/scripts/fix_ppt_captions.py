"""Script untuk membersihkan caption textbox di bawah code card pada slide code (s15,s19,s22,s25,s28,s32)."""
import re

with open('build_white_presentation_math.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern caption blocks: textbox di baris Y=6.0 untuk slide code
# Format yang ada:
#     tb_s15_l = s15.shapes.add_textbox(Inches(0.8), Inches(6.0), w_box2, Inches(1.1))
#     tf_s15_l = tb_s15_l.text_frame
#     tf_s15_l.word_wrap = True
#     p = tf_s15_l.paragraphs[0]
#     p.text = "..."
#     p.font.name = FONT_MATH
#     p.font.size = Pt(9.2)
#     p.font.color.rgb = TEXT_BODY

# Gunakan multiline regex untuk menghapus blok-blok ini
pattern = re.compile(
    r'\n    tb_s(?:15|19|22|25|28|32)_[lr] = s(?:15|19|22|25|28|32)\.shapes\.add_textbox'
    r'\(Inches\([0-9.]+\), Inches\(6\.0\), (?:w_box2|Inches\([0-9.]+\)), Inches\([0-9.]+\)\)\n'
    r'    tf_s(?:15|19|22|25|28|32)_[lr] = tb_s(?:15|19|22|25|28|32)_[lr]\.text_frame\n'
    r'    tf_s(?:15|19|22|25|28|32)_[lr]\.word_wrap = True\n'
    r'    p = tf_s(?:15|19|22|25|28|32)_[lr]\.paragraphs\[0\]\n'
    r'    p\.text = "(?:[^"\\]|\\.)*"\n'
    r'    p\.font\.name = FONT_MATH\n'
    r'    p\.font\.size = Pt\([0-9.]+\)\n'
    r'    p\.font\.color\.rgb = TEXT_BODY\n',
    re.MULTILINE
)

matches = pattern.findall(content)
print(f'Caption blocks found: {len(matches)}')
for m in matches:
    print('  ->', m[:80].replace('\n', '\\n'))

content_new = pattern.sub('\n', content)

with open('build_white_presentation_math.py', 'w', encoding='utf-8') as f:
    f.write(content_new)

print(f'Done. Removed {len(matches)} caption blocks.')
