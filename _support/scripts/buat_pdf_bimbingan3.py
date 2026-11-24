from pathlib import Path
import sys
import pymupdf
ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "docs"
OUT = D / "BIMBINGAN3_WIRING_DAN_FLOWCHART.pdf"
WIRING_V, FLOW_V = D / "BIMBINGAN3_WIRING_PI_KAMERA.pdf", D / "BIMBINGAN3_FLOWCHART_SISTEM.pdf"
WIRING_P, FLOW_P = D / "BIMBINGAN3_WIRING_PI_KAMERA.png", D / "BIMBINGAN3_FLOWCHART_SISTEM.png"
W, H = 841.68, 595.28
JUDUL = "Bimbingan ke-3 -- Sistem Computer Vision Kangkung Aquaponik (Felix Enrique, bagian CV)"
KAKI = "Sumber terverifikasi: raspi/config.json, camera_pi.py, kangkung_pi.py, fuzzy_export.py, thermal_guard.py, firebase_uplink.py, docs/SKEMA_FIREBASE_BED_READINGS.md  |  Sisi ESP32/pompa = bagian teman"
HAL = [("Hal. 1/2 -- Desain Wiring / Circuit (Pi + Kamera, standalone)", WIRING_V, WIRING_P, pymupdf.Rect(20, 62, W - 20, H - 26)), ("Hal. 2/2 -- Flowchart Prinsip Kerja Sistem (siklus 10 menit)", FLOW_V, FLOW_P, pymupdf.Rect(70, 62, W - 70, H - 26))]
def hal(doc, sub, vec, png, r):
    pg = doc.new_page(width=W, height=H)
    pg.insert_textbox(pymupdf.Rect(20, 14, W - 20, 34), JUDUL, fontsize=11, fontname="helv", align=1)
    pg.insert_textbox(pymupdf.Rect(20, 34, W - 20, 52), sub, fontsize=10, fontname="helv", align=1)
    pg.insert_textbox(pymupdf.Rect(20, H - 22, W - 20, H - 6), KAKI, fontsize=6.5, fontname="helv", align=1)
    if vec.exists():
        pg.show_pdf_page(r, pymupdf.open(vec), 0)
        print("VEKTOR:", vec.name)
    else:
        assert png.exists(), "hilang: " + str(png)
        pg.insert_image(r, filename=str(png))
        print("PNG-FALLBACK:", png.name)
doc = pymupdf.open()
for h in HAL: hal(doc, *h)
t = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
doc.save(t, garbage=3, deflate=True); print("OK ->", OUT)
import sys, tempfile
