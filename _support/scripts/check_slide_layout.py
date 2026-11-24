from pptx import Presentation

prs = Presentation('docs/PRESENTASI_FORMULATIF_KALKULATIF_MINIMALIS.pptx')
print('Total Slides:', len(prs.slides))

for idx in [14, 18, 21, 24, 27, 31]:  # slide 15,19,22,25,28,32
    s = prs.slides[idx]
    print(f'\nSlide {idx+1}: {len(s.shapes)} shapes')
    for shape in s.shapes:
        L = round(shape.left / 914400, 2)
        T = round(shape.top / 914400, 2)
        W = round(shape.width / 914400, 2)
        H = round(shape.height / 914400, 2)
        print(f'  [{shape.shape_type}] {shape.name}: pos={L}" {T}" size={W}"x{H}"')
