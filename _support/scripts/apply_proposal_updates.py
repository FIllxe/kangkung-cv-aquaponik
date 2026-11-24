import docx
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml

def apply_updates():
    doc_path = r'docs\proposal\PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx'
    doc = docx.Document(doc_path)

    # 1. VERIFY HEADINGS
    p_rm = None
    p_tujuan = None
    p_manfaat = None
    p_151 = None
    p_152 = None
    p_153 = None
    
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if t == "1.2  Rumusan Masalah":
            p_rm = p
        elif t == "1.3  Tujuan Prototipe":
            p_tujuan = p
        elif t == "1.4  Manfaat Prototipe":
            p_manfaat = p
        elif "1.5.1  Potensi Dampak Fungsional" in t:
            p_151 = p
        elif "1.5.2  Potensi Dampak Komersial" in t:
            p_152 = p
        elif "1.5.3  Pengembangan lebih lanjut" in t:
            p_153 = p

    print("Headings found:", all([p_rm, p_tujuan, p_manfaat, p_151, p_152, p_153]))

    # Helper function to format paragraph
    def format_paragraph(p, text, is_first_line_indent=True):
        p.text = text
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)
        if is_first_line_indent:
            p.paragraph_format.first_line_indent = Pt(21.6) # 432 dxa
            p.paragraph_format.left_indent = Pt(0)
            p.paragraph_format.space_after = Pt(0)

    # Helper to insert list item after a paragraph
    def insert_list_item_after(prev_p, text, num_id):
        xml_str = f'''
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:pPr>
            <w:pStyle w:val="ListParagraph"/>
            <w:numPr>
              <w:ilvl w:val="0"/>
              <w:numId w:val="{num_id}"/>
            </w:numPr>
            <w:tabs>
              <w:tab w:val="left" w:pos="432"/>
            </w:tabs>
            <w:spacing w:after="40"/>
            <w:ind w:left="432" w:hanging="432"/>
            <w:jc w:val="both"/>
            <w:rPr>
              <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
              <w:sz w:val="24"/>
              <w:szCs w:val="24"/>
            </w:rPr>
          </w:pPr>
          <w:r>
            <w:rPr>
              <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
              <w:sz w:val="24"/>
              <w:szCs w:val="24"/>
            </w:rPr>
            <w:t>{text}</w:t>
          </w:r>
        </w:p>
        '''
        new_elm = parse_xml(xml_str)
        prev_p._p.addnext(new_elm)
        return new_elm

    # -------------------------------------------------------------
    # 2. UPDATE RUMUSAN MASALAH (4 Focused Points)
    # -------------------------------------------------------------
    # Items currently:
    # P93: rm1
    # P94: rm2
    # P95: rm3
    # P96: blank
    # P97: 1.3 Tujuan Prototipe
    rm_items = [
        "Bagaimana mendeteksi area bak tanam (bed) dan membagi citra menjadi partisi grid 4×6 (24 zona) secara otomatis dan stabil dari kamera tampak atas (top-down view) pada instalasi akuaponik.",
        "Bagaimana menentukan tingkat kelayakan panen tanaman kangkung pada tiap zona budidaya secara objektif berbasis persentase tutupan kanopi (canopy coverage) menggunakan segmentasi ruang warna adaptif Hue Saturation Value (HSV) terhadap fluktuasi intensitas iluminasi.",
        "Bagaimana tingkat keakurasian penentuan kelayakan panen berbasis visi komputer jika dibandingkan dengan hasil penilaian manual oleh pengelola akuaponik di lapangan.",
        "Bagaimana mengukur persentase daun klorosis (kuning) dan nekrosis (cokelat) per zona serta memformulasikannya menjadi Indeks Stres Tanaman atau Plant Stress Index (PSI) 0–100 sebagai indikator kesehatan kanopi yang siap dibaca oleh pengendali sistem."
    ]

    p93 = doc.paragraphs[93]
    p94 = doc.paragraphs[94]
    p95 = doc.paragraphs[95]

    format_paragraph(p93, rm_items[0], is_first_line_indent=False)
    format_paragraph(p94, rm_items[1], is_first_line_indent=False)
    format_paragraph(p95, rm_items[2], is_first_line_indent=False)

    # Insert 4th item after p95
    insert_list_item_after(p95, rm_items[3], num_id=2)
    print("Updated 1.2 Rumusan Masalah (4 points).")

    # -------------------------------------------------------------
    # 3. UPDATE TUJUAN PROTOTIPE (4 Aligned Points)
    # -------------------------------------------------------------
    tujuan_items = [
        "Menghasilkan algoritma deteksi batas bed otomatis berbasis tepi Canny, aproksimasi quad, dan homografi empat titik dengan jalur cadangan maska HSV pada bak tanam 2 m × 1,1 m.",
        "Menghasilkan metode segmentasi ruang warna HSV adaptif iluminasi dengan faktor f = mean(V)/128 beserta perata Exponential Moving Average (EMA) untuk menentukan kelayakan panen kangkung secara objektif ke dalam 4 kategori kesiapan (belum siap, hampir siap, siap panen, dan harus panen) berbasis persentase tutupan kanopi 24 zona.",
        "Menganalisis dan mengevaluasi tingkat keakurasian klasifikasi kelayakan panen sistem visi komputer terhadap data pembanding (ground truth) hasil penilaian manual pengelola Aquaponik Eco Farm UNNES.",
        "Menghasilkan pengukuran persentase kuning (klorosis) dan cokelat (nekrosis) per zona yang dilengkapi gerbang spasial Brown Adjacency Gate, formulasi skalar PSI v2.0 beserta nilai PSI maksimum zona terburuk, serta paket deploy komputer papan tunggal dan dasbor web yang memenuhi kriteria burn-in 24 jam."
    ]

    # Re-find Tujuan items
    # In original: P99, P100, P101. Note that we inserted 1 element earlier, so index is offset by 1
    p_tujuan_heading = None
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip() == "1.3  Tujuan Prototipe":
            p_tujuan_heading = i
            break
            
    # p_tujuan_heading + 1 is the intro: "Berdasarkan rumusan masalah..."
    # p_tujuan_heading + 2 is item 1
    # p_tujuan_heading + 3 is item 2
    # p_tujuan_heading + 4 is item 3
    t1 = doc.paragraphs[p_tujuan_heading + 2]
    t2 = doc.paragraphs[p_tujuan_heading + 3]
    t3 = doc.paragraphs[p_tujuan_heading + 4]

    format_paragraph(t1, tujuan_items[0], is_first_line_indent=False)
    format_paragraph(t2, tujuan_items[1], is_first_line_indent=False)
    format_paragraph(t3, tujuan_items[2], is_first_line_indent=False)

    insert_list_item_after(t3, tujuan_items[3], num_id=3)
    print("Updated 1.3 Tujuan Prototipe (4 points).")

    # -------------------------------------------------------------
    # 4. UPDATE POTENSI DAMPAK FUNGSIONAL (1.5.1)
    # -------------------------------------------------------------
    fungsional_p1 = (
        "Bagian ini menguraikan potensi dampak fungsional dan komersial dari prototipe sistem visi komputer pemantau "
        "kelayakan panen dan kesehatan kanopi kangkung. Secara fungsional, prototipe ini mentransformasi proses monitoring "
        "budidaya dari pengamatan visual manual yang bersifat subjektif, sporadis, dan tidak konsisten antar-tenaga kerja "
        "menjadi sistem pemantauan digital yang objektif, non-destruktif, dan terotomasi secara kontinyu (tiap 10 menit) "
        "dari kamera tampak atas (top-down view). Keputusan penentuan panen tidak lagi didasarkan pada perkiraan kasat "
        "mata, melainkan mengacu pada estimasi persentase tutupan kanopi (canopy coverage) per zona yang terukur secara presisi "
        "menggunakan segmentasi ruang warna adaptif HSV."
    )
    fungsional_p2 = (
        "Penerapan diskretisasi kisi 24 zona (4 baris × 6 kolom) memberikan dampak fungsional langsung berupa penerapan "
        "strategi panen selektif (selective harvesting). Pengelola kebun dapat memanen hanya pada petak tanam yang telah mencapai "
        "status siap panen (>55%) atau harus panen (>80%), sementara petak kangkung yang masih muda dibiarkan tumbuh untuk "
        "memaksimalkan akumulasi biomassa tanpa perlu membabat habis seluruh bed secara serentak. Pemanenan sebelum kanopi melebihi 80% "
        "juga memitigasi risiko agronomis fatal, yaitu fenomena self-shading (pembusukan daun lapisan bawah akibat kekurangan cahaya "
        "yang memicu lonjakan amonia beracun bagi ikan nila di kolam) serta akumulasi massa akar berlebih (root clogging) yang menyumbat "
        "saluran hidraulik talang air. Selain itu, integrasi filter spasial Brown Adjacency Gate dan formulasi Indeks Stres Tanaman "
        "(Plant Stress Index / PSI v2.0) memungkinkan deteksi dini klorosis dan nekrosis per zona sebelum patologi meluas, sekaligus "
        "menyediakan tolok ukur kesesuaian akurasi penentuan panen terotomasi terhadap penilaian manual pengelola budidaya di lapangan."
    )

    idx_151 = -1
    for i, p in enumerate(doc.paragraphs):
        if "1.5.1  Potensi Dampak Fungsional" in p.text:
            idx_151 = i
            break

    format_paragraph(doc.paragraphs[idx_151 + 1], fungsional_p1, is_first_line_indent=True)
    format_paragraph(doc.paragraphs[idx_151 + 2], fungsional_p2, is_first_line_indent=True)
    print("Updated 1.5.1 Potensi Dampak Fungsional.")

    # -------------------------------------------------------------
    # 5. UPDATE POTENSI DAMPAK KOMERSIAL (1.5.2)
    # -------------------------------------------------------------
    komersial_p1 = (
        "Secara komersial, prototipe berpotensi dikembangkan menjadi produk perangkat pemantau kanopi cerdas (smart crop "
        "monitoring kit) berbiaya terjangkau (low-cost edge AI) yang dapat diadopsi oleh pelaku budidaya akuaponik, hidroponik komersial, "
        "maupun pertanian perkotaan (urban farming). Dari sisi efisiensi operasional, sistem ini mampu mereduksi biaya tenaga kerja "
        "(labor cost reduction) dengan meminimalkan frekuensi inspeksi fisik harian secara manual, di mana satu pengelola dapat memantau "
        "puluhan bed tanaman secara terpusat melalui dasbor web IoT. Dari sisi nilai jual komoditas, pemanenan selektif berbasis tutupan kanopi "
        "memastikan sayuran kangkung dipanen pada fase vegetatif prima dengan tekstur batang renyah sebelum mengalami lignifikasi (batang mengeras "
        "dan berserat kayu), sehingga meningkatkan mutu hasil panen dan daya saing harga di pasar ritel modern."
    )

    komersial_p2 = (
        "Tabel 1.1 merangkum spesifikasi fungsi beberapa produk pemantauan akuaponik komersial yang beredar di pasaran. "
        "Berdasarkan dokumentasi yang ditinjau, produk komersial yang ada saat ini [15], [16], [17] seluruhnya hanya berfokus pada pemantauan "
        "parameter kualitas air kolam (pH, suhu, konduktivitas/EC, dan amonia), dan belum ada satu pun yang menyediakan modul pemantauan kondisi "
        "visual kanopi tanaman maupun penentuan kelayakan panen secara otomatis. Di sisi lain, sistem visi komputer industri pertanian presisi berskala "
        "besar (seperti sistem rumah kaca terpusat atau kamera multispektral) memiliki harga puluhan hingga ratusan juta rupiah yang tidak terjangkau "
        "bagi pembudidaya skala mikro, kecil, dan menengah (UMKM). Di sinilah prototipe yang dikembangkan memiliki keunggulan komersial yang kuat: "
        "hadir sebagai modul sensor visi komputer tepi mandiri (plug-and-play edge sensor) berbiaya terjangkau berbasis Raspberry Pi 4B dan kamera CSI "
        "yang mengisi kekosongan pemantau kanopi tanaman pada sistem budidaya akuaponik."
    )

    idx_152 = -1
    for i, p in enumerate(doc.paragraphs):
        if "1.5.2  Potensi Dampak Komersial" in p.text:
            idx_152 = i
            break

    format_paragraph(doc.paragraphs[idx_152 + 1], komersial_p1, is_first_line_indent=True)

    # Paragraph discussing Table 1.1 (currently contains "Berdasarkan dokumentasi yang ditinjau...")
    for p in doc.paragraphs[idx_152:]:
        if "Berdasarkan dokumentasi yang ditinjau" in p.text:
            format_paragraph(p, komersial_p2, is_first_line_indent=True)
            break
            
    print("Updated 1.5.2 Potensi Dampak Komersial.")

    # -------------------------------------------------------------
    # 6. UPDATE PENGEMBANGAN LEBIH LANJUT (1.5.3)
    # -------------------------------------------------------------
    pengembangan_text = (
        "Pengembangan lebih lanjut dapat diarahkan pada standardisasi fabrikasi selubung perangkat (enclosure) berstandar industri IP65, "
        "integrasi modul kamera dengan lensa fokus otomatis (autofocus), pengayaan model segmentasi untuk komoditas sayuran daun lain (seperti "
        "selada, pakcoy, dan bayam), serta pengembangan fitur prediksi estimasi tonase hasil panen pada dasbor berbasis komputasi awan. Melalui langkah "
        "tersebut, prototipe dapat diproduksi secara massal sebagai paket teknologi pertanian cerdas (smart agriculture kit) yang siap pakai bagi komunitas, "
        "institusi pendidikan, maupun pelaku industri budidaya komersial."
    )

    idx_153 = -1
    for i, p in enumerate(doc.paragraphs):
        if "1.5.3  Pengembangan lebih lanjut" in p.text:
            idx_153 = i
            break

    format_paragraph(doc.paragraphs[idx_153 + 1], pengembangan_text, is_first_line_indent=True)
    print("Updated 1.5.3 Pengembangan lebih lanjut.")

    # Save
    doc.save(doc_path)
    print("SUCCESS: Document updated and saved at", doc_path)

if __name__ == "__main__":
    apply_updates()

