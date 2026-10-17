"""Build proposal Felix Enrique (2305110019) dari template menjadi DOCX final.

Menggantikan 19 skrip `bangun_felix_t*.py` + 4 skrip `tmp_*` perbaikan yang
sebelumnya dijalankan bertahap. Menjalankan ulang seluruh urutan yang sama
persis dari template `docs/kirim felix.docx` sehingga hasilnya identik.

Urutan tahap (nama skrip asal dicantumkan di tiap fungsi):
  t1      judul halaman depan (pola run-per-run template dipertahankan)
  t2      profil + persetujuan (nama/NIM/judul, Tabel 0)
  t3a-t3e Bab 1 penuh (latar P33-37, rumusan/tujuan, manfaat, dampak, Tabel 1.1)
  t4a-t4d Bab 2 (Tinjauan Pustaka + Tabel 2.1, Landasan Teoretik 2.2.1-2.2.5,
          Persamaan 2.1-2.9)
  t5a-t5d Bab 3 (3.1 lokasi, 3.2 bahan/alat + Tabel 3.1/3.2, 3.3 arsitektur +
          Gambar 3.1, 3.4 diagram alir + Gambar 3.2, 3.5 skema + Gambar 3.3,
          3.6 prinsip kerja + Gambar 3.4/3.5, 3.7 metrik + Tabel 3.3)
  t6b     Daftar Isi statis (t6.py gagal sebelum save -> digantikan t6b+t6c)
  t6c     Daftar Pustaka 26 sitasi
  patch   P7 format 'oleh', paragraf sisa fuzzy P40 -> CV, Daftar Istilah
          berupa tabel 9x3 (singkatan/kepanjangan/keterangan)
  t7      dedup penutup Bab I, sectPr ke akhir, tabel ke bawah caption,
          front matter (entri DAFTAR PUSTAKA, DAFTAR TABEL/GAMBAR, hapus ganda)
  t7b     spasi penutup Bab I - Rumusan Masalah

Strategi format (diwarisi dari skrip asal): tidak pernah membuat paragraf dari
nol - selalu deepcopy pola paragraf template (P32 heading / P33 body / P89
caption / entri TOC) sehingga style, font, numbering, alignment identik.
Kata asing dicetak miring per-run.

Pakai:
  python docs/build_proposal.py [--out PATH] [--compare A B]
"""
import argparse
import re
import shutil
import zipfile
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from docx import Document
from docx.enum.text import (WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT,
                            WD_TAB_LEADER)
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.text.paragraph import Paragraph
from docx.text.run import Run

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "docs" / "kirim felix.docx"
OUT = ROOT / "docs" / "PROPOSAL_PROTOTIPE_FELIX_ENRIQUE_2305110019.docx"
JUDUL = ("PENGEMBANGAN SISTEM MONITORING KELAYAKAN PANEN PADA BUDIDAYA "
         "AKUAPONIK DENGAN TEKNIK SEGMENTASI WARNA HSV")
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


# ---------------- helper format (semantik identik dgn skrip asal) ----------------
def set_text(p, text):
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ""


def ital_pat(words):
    """Pola regex: kata 1-huruf dibatasi word-boundary agar huruf di dalam
    kata lain (mis. 'f' pada 'faktor') tidak ikut tercetak miring."""
    alts = []
    for w in sorted(words, key=len, reverse=True):
        e = re.escape(w)
        alts.append(r"\b" + e + r"\b" if len(w) == 1 and w.isalnum() else e)
    return "(" + "|".join(alts) + ")"


def ital(p, words):
    """Cetak miring kata asing; format lain ikut run[0]."""
    full = p.text
    pat = ital_pat(words)
    parts = [x for x in re.split(pat, full) if x]
    base = p.runs[0]
    base_pr = []
    for ch in base._r.xpath("./w:rPr/*"):
        if ch.tag != qn("w:i"):
            base_pr.append(ch)
    base.text = ""
    for i, part in enumerate(parts):
        r = base if i == 0 else p.add_run("")
        if i > 0:
            r.font.name = base.font.name
            r.font.size = base.font.size
            r.bold = base.bold
        rpr = r._r.find(qn("w:rPr"))
        if rpr is None:
            rpr = OxmlElement("w:rPr")
            r._r.insert(0, rpr)
        for c in list(rpr):
            rpr.remove(c)
        for ch in base_pr:
            rpr.append(deepcopy(ch))
        r.text = part
        r.italic = part in words


def add_para(doc, ref_idx, text, bold=False, itw=()):
    """Klon pola paragraf template ref_idx, isi teks baru, append ke body."""
    r0 = doc.paragraphs[ref_idx]
    np_ = deepcopy(r0._p)
    for r in np_.xpath(".//w:r"):
        r.getparent().remove(r)
    base_pr = []
    if r0.runs:
        for ch in r0.runs[0]._r.xpath("./w:rPr/*"):
            if ch.tag != qn("w:i"):
                base_pr.append(ch)
    if itw:
        pat = ital_pat(itw)
        parts = [x for x in re.split(pat, text) if x]
    else:
        parts = [text]
    for part in parts:
        re_ = OxmlElement("w:r")
        rpr = OxmlElement("w:rPr")
        for ch in base_pr:
            rpr.append(deepcopy(ch))
        if bold:
            rpr.append(OxmlElement("w:b"))
        if part in itw:
            rpr.append(OxmlElement("w:i"))
        if len(rpr):
            re_.append(rpr)
        te = OxmlElement("w:t")
        te.set(XML_SPACE, "preserve")
        te.text = part
        re_.append(te)
        np_.append(re_)
    doc.element.body.append(np_)
    return Paragraph(np_, doc)


def add_formula(doc, ref_idx, segs):
    """Klon pola paragraf template ref_idx, isi dengan run-run berformat.

    segs: list tuple (teks, miring, subskrip, superskrip). Dipakai menulis
    persamaan 2.1-2.9 dengan notasi baku (simbol, subskrip, superskrip).
    """
    r0 = doc.paragraphs[ref_idx]
    np_ = deepcopy(r0._p)
    for r in np_.xpath(".//w:r"):
        r.getparent().remove(r)
    for teks, miring, sub, sup in segs:
        re_ = OxmlElement("w:r")
        rpr = OxmlElement("w:rPr")
        if r0.runs:
            for ch in r0.runs[0]._r.xpath("./w:rPr/*"):
                if ch.tag not in (qn("w:i"), qn("w:vertAlign")):
                    rpr.append(deepcopy(ch))
        if miring:
            i_ = OxmlElement("w:i")
            rpr.append(i_)
        if sub:
            vt = OxmlElement("w:vertAlign")
            vt.set(qn("w:val"), "subscript")
            rpr.append(vt)
        if sup:
            vt = OxmlElement("w:vertAlign")
            vt.set(qn("w:val"), "superscript")
            rpr.append(vt)
        if len(rpr):
            re_.append(rpr)
        te = OxmlElement("w:t")
        te.set(XML_SPACE, "preserve")
        te.text = teks
        re_.append(te)
        np_.append(re_)
    doc.element.body.append(np_)
    p = Paragraph(np_, doc)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER  # rumus matematis rata tengah
    return p


# ---------------- Font Times New Roman untuk seluruh dokumen (termasuk TOC) ----------------
def set_font_times_new_roman(doc):
    """Paksa setiap run di semua paragraf dan sel tabel jadi Times New Roman,
    sehingga TOC, daftar pustaka, body, caption, dan tabel seragam satu font."""
    for p in doc.paragraphs:
        for r in p.runs:
            r.font.name = "Times New Roman"
            rPr = r._r.find(qn("w:rPr"))
            if rPr is not None:
                rf = rPr.find(qn("w:rFonts"))
                if rf is None:
                    rf = OxmlElement("w:rFonts")
                    rPr.append(rf)
                rf.set(qn("w:ascii"), "Times New Roman")
                rf.set(qn("w:hAnsi"), "Times New Roman")
                rf.set(qn("w:cs"), "Times New Roman")
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for pp in cell.paragraphs:
                    for r in pp.runs:
                        r.font.name = "Times New Roman"
                        rPr = r._r.find(qn("w:rPr"))
                        if rPr is not None:
                            rf = rPr.find(qn("w:rFonts"))
                            if rf is None:
                                rf = OxmlElement("w:rFonts")
                                rPr.append(rf)
                            rf.set(qn("w:ascii"), "Times New Roman")
                            rf.set(qn("w:hAnsi"), "Times New Roman")
                            rf.set(qn("w:cs"), "Times New Roman")


# ---------------- Rapihkan sitasi: entri Daftar Pustaka selalu diawali [n] ----------------
def rapihkan_sitasi(doc):
    """Pastikan setiap entri Daftar Pustaka dimulai dengan [n] di posisi awal
    (tidak ada spasi/teks di depan nomor sitasi), sehingga tak ada sitasi
    yang tak terstruktur."""
    i_pus = next((i for i, p in enumerate(doc.paragraphs)
                  if p.text.strip() == "DAFTAR PUSTAKA"), None)
    if i_pus is None:
        return
    for p in doc.paragraphs[i_pus + 1:]:
        t = p.text.strip()
        if not t:
            continue
        if re.match(r"^(BAB |LAMPIRAN|\d+\.\d+)", t):
            break
        m = re.match(r"^\s*(\[\d+\]\s+.*)", t)
        if m and not t.startswith("["):
            set_text(p, m.group(1))


# ---------------- helper penomoran heading eksplisit (lihat DOK di tahap baru) ----------------
def strip_numbering(p):
    """Hapus numPr (penomoran otomatis) dari paragraf; format lain tetap."""
    for num in p._p.findall(".//" + qn("w:numPr")):
        num.getparent().remove(num)


def add_image_before(doc, cap_para, imgpath, width_in):
    pg = doc.add_paragraph()
    pg.style = doc.styles["Normal"]
    pg.alignment = 1
    pg.add_run().add_picture(str(imgpath), width=Inches(width_in))
    el = pg._p
    el.getparent().remove(el)
    cap_para._p.addprevious(el)


def clone_with_text(doc, src_p, text):
    np_ = Paragraph(deepcopy(src_p._p), doc)
    runs = np_.runs
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    return np_


def delete_p(p):
    p._p.getparent().remove(p._p)


def find_p(doc, prefix, start=0):
    for i, p in enumerate(doc.paragraphs):
        if i >= start and p.text.startswith(prefix):
            return p
    raise SystemExit(f"tidak ketemu: {prefix}")


# ---------------- Tahap 1 (= bangun_felix_t1.py): judul ----------------
def tahap1(doc):
    p2 = doc.paragraphs[2]
    words = JUDUL.split()
    runs = p2.runs
    new_runs_text = []
    for w in words:
        new_runs_text += [w[0], w[1:] + " "]
    new_runs_text[-1] = new_runs_text[-1].rstrip()
    while len(p2.runs) < len(new_runs_text):
        nr = p2.add_run("")
        nr.font.name = runs[0].font.name
        nr.font.size = runs[0].font.size
        nr.bold = True
    for i, t in enumerate(new_runs_text):
        p2.runs[i].text = t
    for r in p2.runs[len(new_runs_text):]:
        r.text = ""


# ---------------- Tahap 2 (= bangun_felix_t2.py): profil ----------------
def tahap2(doc):
    p7 = doc.paragraphs[7]
    for r in p7.runs:
        r.text = ""
    p7.runs[0].text = "Felix Enrique"
    p7.runs[1].text = ""
    p7.runs[2].text = "NIM. 2305110019"
    p13 = doc.paragraphs[13]
    for r in p13.runs:
        if "ANALISIS PERFORMA" in r.text:
            r.text = JUDUL
    t0 = doc.tables[0]
    t0.cell(0, 2).text = "Felix Enrique"
    t0.cell(1, 2).text = "2305110019"
# ---------------- Tahap 3a (= bangun_felix_t3a.py): latar Bab 1 P33-37 ----------------
def tahap3a(doc):
    IT = ["canopy cover", "Hue", "Saturation", "Value", "Plant Stress Index", "ground truth",
          "deep learning", "top-down", "cloud", "Exponential Moving Average", "bed_readings",
          "fuzzy_input", "non-maximum suppression", "Hue Saturation Value", "f", "H"]
    L1 = "Sistem akuaponik mengintegrasikan budidaya ikan dan tanaman melalui sirkulasi air yang sama sehingga kondisi air dan kondisi tanaman saling memengaruhi [1]. Monitoring kualitas air dan kondisi lingkungan menjadi bagian penting sistem akuaponik karena perubahan parameter air memengaruhi penyerapan nutrisi tanaman, seperti dipantau pada sistem aquaponik skala kecil [2]. Pada sistem akuaponik di Aquaponik Eco Farm Universitas Negeri Semarang (UNNES), kolam ikan nila digunakan sebagai sumber air dan nutrisi bagi tanaman kangkung pada bak tanam berukuran 2 m × 1,1 m. Berdasarkan observasi dan wawancara awal dengan pengelola, salah satu persoalan yang ditemukan adalah penilaian kesiapan panen yang masih dilakukan secara visual. Penilaian visual tersebut bersifat subjektif sehingga keputusan panen antarpetani dan antarbed tidak konsisten, sedangkan bed tidak tumbuh seragam antara bagian tepi dan bagian tengah. Akibatnya panen terlalu dini menurunkan biomassa, sedangkan panen yang terlambat menurunkan mutu daun. Permasalahan tersebut menuntut peta kelayakan panen per zona yang objektif dan berulang. Prototipe ini membagi bak tanam menjadi grid 4×6 atau 24 zona dan menilai tiap zona secara terpisah sehingga panen selektif per zona dapat direncanakan."
    L2 = "Risiko panen dinilai dari tutupan kanopi (canopy cover). Tutupan kanopi berkorelasi dengan biomassa dan fase tumbuh sehingga ambang tutupan dipakai sebagai kriteria panen pada berbagai komoditas daun. Tantangan utama pengukuran tutupan di lapangan adalah perubahan iluminasi. Cahaya pagi, siang, dan sore mengubah komponen terang citra sehingga segmentasi warna statis menghasilkan liputan yang melompat walaupun tanamannya sama [3]. Penelitian ini merumuskan faktor adaptasi iluminasi f yang dihitung dari rata-rata komponen Value tiap frame sehingga ambang Saturation dan Value mengikuti kondisi cahaya tanpa menggeser Hue yang menyimpan informasi warna daun. Pendekatan tersebut diuji pada 18 video lapangan dan lima foto bak tahap seedling sampai ready dengan liputan 0,9 persen sampai 22,6 persen."
    L3 = "Gejala daun menguning atau klorosis dan jaringan mati atau nekrosis sering disadari setelah menyebar [4]. Klorosis ditandai pergeseran warna ke rentang kuning, sedangkan nekrosis ditandai bercak cokelat yang menempel pada kanopi [5], [6]. Woebbecke dkk. [7] merumuskan rentang Hue hijau tanaman terhadap tanah dan gulma sebagai dasar segmentasi vegetasi. Prototipe ini memakai rentang kuning H 21-34 dan cokelat H 8-20 yang dijumlah per piksel menjadi Indeks Stres Tanaman atau Plant Stress Index (PSI) 0-100 sebagai keluaran untuk pengendali. Bobot kategori hijau, kuning, dan cokelat adalah 0, 0,5, dan 1, sehingga PSI 100 hanya tercapai bila seluruh piksel tanaman termasuk kategori cokelat. Lima foto lapangan yang tersedia seluruhnya sehat dengan PSI 0-0,1 sehingga foto sakit asli dan mask ground truth lima gambar menjadi agenda validasi berikutnya."
    L4 = "Wan dkk. [8] membangun sistem monitoring akuaponik berbasis komputasi tepi dengan Raspberry Pi dan pengolahan citra untuk pertumbuhan tanaman, tetapi sistem tersebut tidak menilai kelayakan panen per zona dan tidak menangani adaptasi iluminasi. Abbasi dkk. [9] mendeteksi klorosis daun selada akuaponik dari citra warna secara otomatis, tetapi kajian tersebut hanya satu gejala tanpa grid zona. Searson dkk. [10] memakai ruang warna HSV (Hue Saturation Value) dan operasi morfologi untuk deteksi tanaman di lapangan, tetapi ambangnya statis. Hameed dkk. [11] menentukan ambang vegetasi dari histogram Hue sehingga adaptif terhadap cahaya, tetapi tanpa grid panen dan skor siap kendali. Variyar dkk. [12] memantau kualitas air dan pertumbuhan tanaman akuaponik dengan komputasi tepi dan dasbor waktu nyata, sedangkan Prajapati dkk. [13] merancang sistem monitoring akuaponik berbasis mikrokontroler dengan tampilan web. Bayas dkk. [14] merangkum tren penerapan visi komputer pada sistem akuaponik, tetapi seluruh kajian tersebut belum menilai kelayakan panen per zona. Perbedaan dengan penelitian terdahulu terletak pada gabungan empat hal dalam satu prototipe ringan tanpa pembelajaran mendalam atau deep learning: grid panen per zona, adaptasi iluminasi, skor stres siap kendali, dan paket deploy komputer papan tunggal di lapangan."
    L5 = "Dengan demikian, prototipe yang dikembangkan berfokus pada sistem monitoring kelayakan panen akuaponik yang menilai 24 zona bak tanam dari kamera tampak atas. Sistem dirancang memakai deteksi bed otomatis, segmentasi HSV adaptif iluminasi beserta perata Exponential Moving Average (EMA), pengukuran kuning dan cokelat per zona, serta PSI beserta PSI maksimum zona terburuk yang dikirim sebagai payload Firebase pada koleksi bed_readings. Struktur tersebut ditujukan agar prototipe dapat diuji sebagai suatu proses kerja terintegrasi dan parameternya dapat dikonfigurasi kembali sesuai karakteristik komoditas maupun instalasi akuaponik yang digunakan."
    for idx, teks in zip([33, 34, 35, 36, 37], [L1, L2, L3, L4, L5]):
        set_text(doc.paragraphs[idx], teks)
        ital(doc.paragraphs[idx], IT)
    set_text(doc.paragraphs[38], "")
# ---------------- Tahap 3b (= bangun_felix_t3b.py): rumusan + tujuan ----------------
RUMUSAN = {
 44: "Bagaimana mendeteksi bed dan membagi citra menjadi grid 4×6 secara otomatis dari kamera tampak atas pada bak tanam akuaponik?",
 45: "Bagaimana menstabilkan segmentasi warna Hue Saturation Value (HSV) terhadap perubahan iluminasi pagi, siang, dan sore sehingga liputan kanopi per zona konsisten?",
 50: "Menghasilkan deteksi bed otomatis berbasis tepi Canny, aproksimasi quad, dan homografi empat titik dengan jalur cadangan maska HSV pada bak tanam 2 m × 1,1 m.",
 51: "Menghasilkan segmentasi HSV adaptif iluminasi dengan faktor f = mean(V)/128 beserta perata Exponential Moving Average (EMA) yang menurunkan jitter sudut sampai 53 persen.",
}
PSI46 = "Bagaimana mengukur persentase kuning dan cokelat per zona serta merumuskannya menjadi Indeks Stres Tanaman atau Plant Stress Index (PSI) 0-100 yang siap dibaca pengendali?"
TUJ52 = "Menghasilkan pengukuran kuning dan cokelat per zona beserta PSI, PSI maksimum zona terburuk, dan versi rumus yang dikirim sebagai payload Firebase, serta paket deploy komputer papan tunggal dan dasbor web yang memenuhi kriteria burn-in 24 jam."


def tahap3b(doc):
    for i, teks in RUMUSAN.items():
        set_text(doc.paragraphs[i], teks)
    set_text(doc.paragraphs[46], PSI46)
    set_text(doc.paragraphs[46], doc.paragraphs[46].text)
    ital(doc.paragraphs[46], ["Plant Stress Index", "top-down"])
    set_text(doc.paragraphs[52], TUJ52)
    for i in (44, 45, 50, 51):
        ital(doc.paragraphs[i], ["Hue Saturation Value", "Exponential Moving Average"])
# ---------------- Tahap 3c (= bangun_felix_t3c.py): manfaat ----------------
MANFAAT = {
 56: "Menambah pengetahuan dan keterampilan dalam merancang sistem visi komputer, segmentasi warna HSV adaptif iluminasi, serta deploy komputer papan tunggal untuk monitoring akuaponik.",
 57: "Meningkatkan kemampuan dalam mengukur liputan kanopi, persentase kuning dan cokelat per zona, serta merumuskan Indeks Stres Tanaman atau Plant Stress Index (PSI) 0-100 sebagai keluaran siap kendali.",
 58: "Meningkatkan kemampuan dalam melakukan pengujian stabilitas iluminasi, evaluasi segmentasi terhadap mask ground truth, serta uji burn-in lapangan 24 jam.",
 60: "Memberikan kontribusi sebagai rujukan pengembangan penelitian terapan di bidang visi komputer, sistem tertanam, dan akuaponik cerdas bagi sivitas akademika Universitas Negeri Semarang, khususnya Program Studi Teknik Komputer dan Fakultas Teknik.",
 61: "Mendukung pengembangan Eco Farm Universitas Negeri Semarang sebagai lokasi penerapan dan pengujian teknologi monitoring kelayakan panen berbasis visi komputer.",
 62: "Menyediakan prototipe sensor tanaman otomatis yang dapat dikembangkan lebih lanjut sebagai sarana penelitian, pembelajaran, dan pengujian integrasi antara kondisi tanaman dan sistem pengambilan keputusan.",
 64: "Membantu pengelola dalam menentukan kesiapan panen per zona berdasarkan peta 24 zona beserta status belum siap, hampir siap, siap panen, dan harus panen.",
 65: "Memberikan rekomendasi panen selektif yang lebih terukur dibandingkan keputusan yang hanya didasarkan pada pengamatan visual.",
 66: "Memberikan informasi kondisi sistem melalui dasbor sehingga pengelola dapat memantau liputan kanopi, kesehatan daun, dan rekomendasi tindakan dalam satu sistem.",
 67: "Mendukung pengoperasian budidaya yang lebih terjadwal melalui pemantauan berkala tiap 10 menit beserta arsip runtun waktu per zona.",
 69: "Memberikan alternatif penerapan sistem monitoring kelayakan panen yang menilai kondisi tanaman secara langsung, bukan hanya parameter air.",
 70: "Mendukung pengelolaan panen secara lebih terukur dengan mempertimbangkan kondisi aktual tiap zona, bukan hanya satu nilai rata-rata bed.",
 71: "Menjadi dasar pengembangan sistem monitoring yang dapat dikonfigurasi ulang sesuai karakteristik jenis tanaman, ukuran bed, serta kondisi lingkungan budidaya yang berbeda.",
 73: "Memberikan kontribusi terhadap penerapan segmentasi HSV adaptif iluminasi beserta perata Exponential Moving Average (EMA) untuk stabilisasi liputan kanopi lintas kondisi cahaya.",
 74: "Memberikan contoh integrasi fungsional antara sistem visi komputer dan sistem pengendalian, yaitu dengan memanfaatkan PSI hasil evaluasi visual tanaman sebagai salah satu masukan proses inferensi.",
 75: "Menjadi dasar bagi penelitian selanjutnya dalam pengembangan ambang kesehatan, metode penentuan PSI, serta strategi panen selektif yang lebih adaptif berdasarkan karakteristik sistem akuaponik.",
 77: "Memberikan gambaran penerapan teknologi berbasis kamera, Internet of Things, dan kecerdasan komputasional untuk membantu pengelolaan sistem akuaponik.",
 78: "Menjadi referensi awal bagi pengembangan sistem monitoring cerdas yang dapat diterapkan pada skala budidaya lain dengan penyesuaian parameter dan kalibrasi sesuai kondisi instalasi.",
}


def tahap3c(doc):
    for i, teks in MANFAAT.items():
        set_text(doc.paragraphs[i], teks)
    # Hapus paragraf sisa template akuaponik: paragraf "Dengan demikian"
    # versi SPK beserta paragraf intro rumusan versi SPK. Penutup "Dengan
    # demikian" versi CV dipertahankan (dicek via tahap7struct).
    for p in list(doc.paragraphs):
        tx = p.text
        if tx.startswith("\tDengan demikian, prototipe yang dikembangkan berfokus pada SPK"):
            delete_p(p)
        elif tx.startswith("\tBerdasarkan latar belakang yang telah diuraikan, rumusan masalah dalam perancangan prototipe ini adalah sebagai berikut"):
            delete_p(p)
# ---------------- Tahap 3d (= bangun_felix_t3d.py): dampak ----------------
LABEL_151 = "1.5.1  Potensi Dampak Fungsional"
LABEL_152 = "1.5.2  Potensi Dampak Komersial"
DAMPAK82 = "Bagian ini menggambarkan dampak fungsional dan komersial prototipe: dampak fungsional berkaitan dengan manfaat operasional sistem dalam mendukung keputusan panen secara lebih objektif dan terukur, sedangkan dampak komersial berkaitan dengan potensi sistem dikembangkan menjadi produk siap pakai bagi pelaku budidaya akuaponik. Prototipe yang dirancang memiliki potensi memberikan dampak fungsional pada proses pengelolaan budidaya akuaponik, khususnya dalam menentukan kesiapan panen secara lebih terukur. Keputusan tidak hanya didasarkan pada pengamatan visual, tetapi menggunakan liputan kanopi per zona, status kesehatan daun, dan Indeks Stres Tanaman atau Plant Stress Index (PSI) sebagai keluaran sistem. Peta 24 zona memungkinkan panen selektif pada zona yang siap sedangkan zona yang belum siap dibiarkan tumbuh, sedangkan status sehat, waspada, dan sakit menjadi dasar pemeriksaan lanjutan."
DAMPAK84 = "Secara fungsional, prototipe juga memiliki potensi untuk diterapkan pada konfigurasi akuaponik yang berbeda melalui proses penyesuaian parameter. Rentang HSV, ambang status, ambang kesehatan, serta parameter ketinggian kamera dapat dikonfigurasi kembali sesuai kebutuhan. Dengan demikian, arsitektur sistem tidak dibatasi hanya pada satu kondisi instalasi, meskipun penerapan pada sistem lain tetap memerlukan proses kalibrasi dan pengujian ulang."
DAMPAK86 = "Dari sisi komersial, prototipe ini memiliki potensi untuk dikembangkan menjadi perangkat pendukung monitoring akuaponik yang menilai kelayakan panen dan kesehatan tanaman dalam satu sistem. Arsitektur yang menggunakan komputer papan tunggal, kamera, rumah kamera cetak tiga dimensi, dan konektivitas Internet of Things memungkinkan sistem dikembangkan secara modular sesuai kebutuhan pengguna dan skala instalasi. Perbandingan prototipe terhadap produk pembanding lain diringkas pada Tabel 1.1."
DAMPAK87_HEADING = "1.5.3  Pengembangan lebih lanjut"
DAMPAK87_BODY = ("Dapat diarahkan pada penyederhanaan instalasi, peningkatan keandalan perangkat keras, "
                 "pengembangan antarmuka pengguna, serta pengujian pada lebih banyak konfigurasi akuaponik. "
                 "Dengan tahapan tersebut, prototipe dapat menjadi dasar pengembangan produk teknologi "
                 "monitoring cerdas untuk kebutuhan pendidikan, penelitian, komunitas, maupun pelaku "
                 "budidaya skala kecil dan menengah. Namun, penerapan secara komersial tetap memerlukan "
                 "validasi tambahan untuk memastikan keandalan, konsistensi kinerja, kemudahan pemeliharaan, "
                 "dan kesesuaian sistem terhadap kondisi operasional yang berbeda.")


def tahap3d(doc):
    for i, teks in ((79, LABEL_151), (82, DAMPAK82), (83, DAMPAK84),
                    (84, LABEL_152), (85, DAMPAK86), (86, DAMPAK87_HEADING),
                    (87, DAMPAK87_BODY)):
        set_text(doc.paragraphs[i], teks)
    # Rapikan format body yang menimpa paragraf template berformat khusus:
    # DAMPAK84 (idx 83) menimpa LABEL template (bold + indent gantung),
    # DAMPAK87_BODY (idx 87) menimpa caption template (center + bold).
    # Biar konsisten dgn body lain: JUSTIFY non-bold; first-line indent 18pt
    # diberikan otomatis oleh tahap_spasi_rafly utk paragraf JUSTIFY.
    for i in (83, 87):
        pb = doc.paragraphs[i]
        pb.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in pb.runs:
            r.bold = False
    # Sisa numbering list warisan paragraf label template di body 1.5.1
    # (idx 83) bikin tahap_spasi_rafly melewatkannya (syarat numPr None)
    # sehingga indent gantung 567 twips tertinggal -> hapus numPr-nya.
    strip_numbering(doc.paragraphs[83])
    # Heading 1.5.1 (idx 79) juga warisi hanging 567 dari label template
    # -> bersihkan supaya tampil seperti heading 1.5.2/1.5.3 lainnya.
    doc.paragraphs[79].paragraph_format.first_line_indent = None
    # Paragraf 86 (1.5.3 Pengembangan lebih lanjut): jadi heading (Heading 3 ditetapkan
    # oleh tahap_struktur_mirza melalui pola teks "^\d+\.\d+\.\d+\s"), jadi jangan
    # diformat sebagai teks biasa non-bold/justify di sini.
    # Hapus sisa dampak akuaponik template (indeks 82-84 versi lama masih
    # terbaca sebagai teks baru? tidak -- yang bertahan adalah paragraf
    # TAMBAHAN di luar indeks tsb). Singkirkan paragraf template yang masih
    # memuat frasa fokus lama.
    SISA_DAMPAK = ("kebutuhan pergantian air", "rekomendasi pergantian air",
                   "ketinggian air", "pengurasan", "luapan saat hujan",
                   "pengamatan manual")
    for p in list(doc.paragraphs):
        if p.text.startswith("\t") and any(s in p.text for s in SISA_DAMPAK):
            delete_p(p)


def _strip_numpr_keep(p):
    """Hapus numPr (daftar bernomor otomatis) dari paragraf, format lain utuh."""
    pPr = p._p.find(qn("w:pPr"))
    if pPr is not None:
        n = pPr.find(qn("w:numPr"))
        if n is not None:
            pPr.remove(n)


# ---------------- Tahap 3e (= bangun_felix_t3e.py): Tabel 1.1 ----------------
TABEL11 = [
 ["PlantEye (Phenospex)", "Rp 150.000.000", "Pemindai 3D multispektral dengan metrik kanopi terstandar untuk riset.", "Harga sangat mahal dan butuh operator terlatih, bukan untuk bed akuaponik kecil."],
 ["CropSnap / sensor kanopi genggam", "Rp 3.000.000", "Ringkas untuk cek cepat satu titik tanam di lapangan.", "Hanya satu titik ukur tanpa peta zona dan tanpa arsip runtun waktu."],
 ["Aplikasi cek daun via ponsel", "Gratis-Rp 500.000", "Mudah dipakai untuk foto satu daun dan klasifikasi cepat.", "Hasil per foto tidak konsisten antarbed dan tanpa grid zona serta dasbor."],
]


def tahap3e(doc):
    t1 = doc.tables[1]
    for i, row in enumerate(TABEL11, 1):
        t1.cell(i, 0).text = row[0]
        t1.cell(i, 2).text = row[1]
        t1.cell(i, 3).text = row[2]
        t1.cell(i, 4).text = row[3]
# ---------------- Tahap 4a (= bangun_felix_t4a.py): Bab 2 awal ----------------
IT4A = ["canopy cover", "Hue", "Saturation", "Value", "Plant Stress Index", "ground truth",
      "deep learning", "edge computing", "non-maximum suppression", "Exponential Moving Average",
      "Intersection over Union", "recall", "Hue Saturation Value", "hue", "value", "top-down"]
BAB2_A = (
 "Wan dkk. [8] membangun sistem monitoring akuaponik berbasis komputasi tepi atau edge computing dengan Raspberry Pi dan pengolahan citra untuk pertumbuhan tanaman. Sistem tersebut membuktikan arsitektur sensor-kamera-komputasi tepi layak untuk akuaponik, tetapi tidak menilai kelayakan panen per zona dan tidak menangani adaptasi iluminasi. Abbasi dkk. [9] mendeteksi klorosis daun selada akuaponik dari citra warna secara otomatis. Kajian tersebut menjadi rujukan terdekat untuk deteksi menguning, tetapi hanya satu gejala dan satu bed tanpa grid zona. Searson dkk. [10] memakai ruang warna HSV dan operasi morfologi untuk deteksi tanaman di lapangan dengan iluminasi alami. Kajian tersebut menjadi dasar segmentasi hijau prototipe ini, tetapi ambangnya statis sehingga liputan melompat ketika cahaya berubah."
)


def tahap4a(doc):
    for teks, bold, itw in [("BAB II", True, ()), ("KAJIAN PUSTAKA", True, ()),
                            ("Tinjauan Pustaka", True, ()), (BAB2_A, False, IT4A)]:
        add_para(doc, 32 if bold else 33, teks, bold, itw)


# ---------------- Tahap 4b (= bangun_felix_t4b.py): Tinjauan + Tabel 2.1 ----------------
IT4B = IT4A + ["approxPolyDP"]
TINJ2 = "Hameed dkk. [11] menentukan ambang vegetasi dari histogram Hue sehingga adaptif terhadap cahaya. Gagasan tersebut dipakai sebagai kerabat faktor adaptasi f pada prototipe ini. Yang dkk. [15] memakai pohon keputusan HSV untuk identifikasi kehijauan dan Barbedo [16] memetakan teknik citra digital untuk deteksi dan kuantifikasi penyakit daun berbasis warna. Kedua kajian tersebut mendukung pemisahan kuning dan cokelat sebagai gejala berbeda. Tovar dkk. [17] memakai Raspberry Pi untuk fenotipe tanaman sehingga mendukung pilihan deploy ringan. Perbandingan posisi penelitian ini terhadap tujuh kajian tersebut diringkas pada Tabel 2.1. Celah yang diisi prototipe ini adalah gabungan grid panen 4×6, adaptasi iluminasi tanpa pembelajaran mendalam, dan skor stres siap kendali dalam satu paket lapangan."
TINJ3 = "Kajian pendukung lain diperiksa untuk memperkuat posisi prototipe ini. Zhang dkk. [18] mendeteksi baris tanaman dari citra tampak atas dengan pengelompokan posisi dan lintasan terpendek, yang sejalan dengan deteksi bed pada Bagian 2.2.1. Liakos dkk. [19] merangkum penerapan pembelajaran mesin pada pertanian dan Kamilaris dan Prenafeta-Boldú [20] merangkum penerapan pembelajaran mendalam; kedua tinjauan tersebut menegaskan bahwa pendekatan berbasis data membutuhkan pelatihan berlabel dalam jumlah besar. Perez-Marin dkk. [21] memprediksi pertumbuhan dan hasil panen tanaman hortikultura dengan jaringan saraf temporal, Mane dkk. [22] memperkirakan tinggi tanaman dan luas tajuk dari titik Light Detection and Ranging (LiDAR), serta Athanasiadis dkk. [23] meramalkan pertumbuhan tanaman dengan autoencoder dan wavelet. Seluruh pendekatan pembelajaran mendalam tersebut bergantung pada data pelatihan berlabel yang belum tersedia pada prototipe ini sehingga deteksi tepi dan ambang warna tetap dipilih."
TABEL21 = [
 ["Wan dkk. [8]", "Tepi + citra akuaponik", "Status tumbuh", "Tanpa grid zona dan adaptasi cahaya"],
 ["Abbasi dkk. [9]", "Warna daun selada", "Klorosis", "Satu gejala, tanpa grid dan PSI"],
 ["Searson dkk. [10]", "HSV + morfologi", "Maska tanaman", "Ambang statis, tanpa adaptasi"],
 ["Hameed dkk. [11]", "Ambang histogram Hue", "Maska adaptif", "Tanpa grid panen dan skor kendali"],
 ["Yang dkk. [15]", "Pohon keputusan HSV", "Kehijauan", "Tanpa kuning/cokelat dan deploy"],
 ["Barbedo [16]", "Citra penyakit warna", "Area sakit", "Tanpa grid zona dan paket lapangan"],
 ["Usulan", "HSV adaptif + EMA + grid", "Peta 24 zona + PSI", "Gabungan ketujuh hal di atas"],
]


def tahap4b(doc):
    add_para(doc, 33, TINJ2, False, IT4B)
    add_para(doc, 33, TINJ3, False, IT4B + ["autoencoder", "wavelet", "Light Detection and Ranging"])
    add_para(doc, 89, "Tabel 2.1  Perbandingan penelitian terdahulu dengan penelitian yang diusulkan.", True, ())
    t = doc.add_table(rows=8, cols=4)
    t.style = "Table Grid"
    for j, htxt in enumerate(["Kajian", "Metode", "Keluaran", "Beda dengan usulan"]):
        t.cell(0, j).text = htxt
    for i, row in enumerate(TABEL21, 1):
        for j, v in enumerate(row):
            t.cell(i, j).text = v
# ---------------- Tahap 4c/4d (= t4c.py, t4d.py): 2.2.1-2.2.5 + Pers. 2.1-2.9 ----------------
IT4 = ["non-maximum suppression", "Hue", "Saturation", "Value", "approxPolyDP", "top-down",
 "canopy cover", "Exponential Moving Average", "Plant Stress Index", "ground truth",
 "deep learning", "recall", "Intersection over Union", "Hue Saturation Value", "hue", "value",
 "x", "y", "Gx", "Gy", "G", "H", "p", "s", "S", "V", "f", "P", "R", "A", "B", "K", "C", "z"]
CH2A = "Detektor Canny [24] mencari tepi melalui gradien multiskala, penekanan nonmaksimum atau non-maximum suppression, dan ambang histeresis. Gradien dihitung dengan operator Sobel pada arah x dan y sehingga magnitudo dan orientasi tiap piksel diperoleh dari Persamaan 2.1 dan 2.2. Kontur terbesar hasil tepi didekati menjadi poligon empat titik dengan approxPolyDP sehingga sudut bed diperoleh walaupun kamera miring."
CH2B = "Empat sudut terurut dipetakan ke persegi 1200×660 dengan homografi planar. Homografi tiga kali tiga atau H memetakan titik sumber p ke titik tujuan p dengan faktor skala s seperti Persamaan 2.3. Bed yang tegak dibagi menjadi grid 4 baris dan 6 kolom sehingga tiap zona R1C1 sampai R4C6 dianalisis terpisah dan liputan adil antarbed."
CH2C = "Ruang HSV memisahkan rona atau Hue dari kejenuhan atau Saturation dan terang atau Value sehingga perubahan cahaya terutama menggeser S dan V sedangkan H menyimpan identitas warna daun [7], [15]. Maska tanaman dibentuk dari gabungan dua rentang hijau muda H 35-75 dan hijau tua H 36-85 yang digabung dengan operasi logika ATAU seperti Persamaan 2.4. Maska kuning H 21-34 dan cokelat H 8-20 dibentuk terpisah, sedangkan cokelat wajib menempel kanopi lewat jendela ketetanggaan 21×21 agar media gelap tidak ikut terdeteksi."
CH2D = "Faktor adaptasi f dihitung dari rata-rata komponen V tiap frame terhadap acuan 128 lalu dijepit pada 0,6 sampai 1,6. Faktor tersebut menggeser ambang bawah S dan V tanpa menggeser Hue sehingga identitas hijau, kuning, dan cokelat tetap. Sudut hasil deteksi diratakan antarframe dengan Exponential Moving Average (EMA) berbobot 0,2 seperti Persamaan 2.5 sehingga jitter sudut turun dari 19,93 piksel menjadi 9,32 piksel atau 53 persen."
CH2E = "Liputan tiap zona adalah rasio piksel tanaman terhadap luas zona dalam persen. Persentase kuning dan cokelat dihitung terhadap piksel tanaman, bukan luas zona, sehingga zona jarang tetap adil. Status panen ditetapkan dari liputan: belum siap di bawah 25 persen, hampir siap 25-55 persen, siap panen 55-80 persen, dan harus panen di atas 80 persen. Jumlah piksel hijau, kuning, dan cokelat tiap zona dijumlah lintas zona lebih dahulu, kemudian dihitung menjadi PSI 0-100 seperti Persamaan 2.6a dan 2.6b. Penjumlahan dilakukan sebelum perhitungan, bukan rata-rata PSI per zona, karena luas tanaman tiap zona berbeda sehingga rata-rata memberi bobot sama pada zona jarang dan zona rapat. Bobot kategori adalah hijau 0, kuning 0,5, dan cokelat 1, sehingga PSI 0 hanya terjadi bila seluruh piksel hijau dan PSI 100 hanya bila seluruh piksel cokelat. Karena rumusnya linear, gradien indeks tetap ada sampai nekrosis penuh sehingga pengendali masih dapat membedakan tingkat keparahan di area paling penting. PSI maksimum zona terburuk dikirim terpisah agar bahaya lokal tidak hilang dalam agregat bed, sedangkan penanda validitas dan alasan kegagalan dikirim bersama agar PSI 0 yang sah tidak tertukar dengan kegagalan pengambilan gambar."
CH2F = "Evaluasi memakai mask ground truth tiga kelas yaitu tanaman total, kuning, dan cokelat untuk lima gambar. Presisi mengukur ketepatan piksel terdeteksi, recall mengukur kelengkapan temuan, skor F1 sebagai harmonic mean atau rata-rata harmonik presisi dan recall, sedangkan Intersection over Union (IoU) mengukur tumpang tindih seperti Persamaan 2.8 dan 2.9. Target wajar untuk HSV beserta kontur pada foto lapangan adalah F1 0,85-0,95."


# ---------------- Persamaan 2.1-2.9 (notasi baku: simbol, sub/superskrip, italic) ----------------
F = add_formula
EQ21 = [("G", 1, 0, 0), (" = √(", 0, 0, 0), ("G", 1, 0, 0), ("x", 1, 1, 0),
        ("2", 0, 0, 1), (" + ", 0, 0, 0), ("G", 1, 0, 0), ("y", 1, 1, 0),
        ("2", 0, 0, 1), (")   (2.1)", 0, 0, 0)]
EQ22 = [("θ", 1, 0, 0), (" = arctan(", 0, 0, 0), ("G", 1, 0, 0), ("y", 1, 1, 0),
        (" / ", 0, 0, 0), ("G", 1, 0, 0), ("x", 1, 1, 0), (")   (2.2)", 0, 0, 0)]
EQ23 = [("s", 1, 0, 0), ("·", 0, 0, 0), ("p", 1, 0, 0), ("′", 0, 0, 0),
        (" = ", 0, 0, 0), ("H", 1, 0, 0), ("·", 0, 0, 0), ("p", 1, 0, 0),
        ("   (2.3)", 0, 0, 0)]
EQ24 = [("M", 1, 0, 0), ("tanaman", 1, 1, 0), (" = ", 0, 0, 0), ("M", 1, 0, 0),
        ("muda", 1, 1, 0), (" ∪ ", 0, 0, 0), ("M", 1, 0, 0), ("tua", 1, 1, 0),
        ("   (2.4)", 0, 0, 0)]
EQ25 = [("x", 1, 0, 0), ("t", 1, 1, 0), (" = 0,2·", 0, 0, 0), ("z", 1, 0, 0),
        ("t", 1, 1, 0), (" + 0,8·", 0, 0, 0), ("x", 1, 0, 0), ("t−1", 1, 1, 0),
        ("   (2.5)", 0, 0, 0)]
EQ26 = [("N", 1, 0, 0), (" = ", 0, 0, 0), ("G", 1, 0, 0), (" + ", 0, 0, 0),
        ("Y", 1, 0, 0), (" + ", 0, 0, 0), ("B", 1, 0, 0),
        ("   (2.6a)", 0, 0, 0)]
EQ26B = [("PSI", 1, 0, 0), (" = 100·(", 0, 0, 0), ("0,5Y", 1, 0, 0),
         (" + ", 0, 0, 0), ("B", 1, 0, 0), (")/", 0, 0, 0), ("N", 1, 0, 0),
         ("   (2.6b)", 0, 0, 0)]
EQ27 = [("PSI", 1, 0, 0), ("maks", 1, 1, 0), (" = maks(", 0, 0, 0),
        ("PSI", 1, 0, 0), ("zona", 1, 1, 0), ("), ", 0, 0, 0), ("z", 1, 0, 0),
        (" = 1..24   (2.7)", 0, 0, 0)]
EQ28 = [("F", 1, 0, 0), ("1", 1, 1, 0), (" = 2·", 0, 0, 0), ("P", 1, 0, 0),
        ("·", 0, 0, 0), ("R", 1, 0, 0), ("/(", 0, 0, 0), ("P", 1, 0, 0),
        (" + ", 0, 0, 0), ("R", 1, 0, 0), (")   (2.8)", 0, 0, 0)]
EQ29 = [("IoU", 1, 0, 0), (" = |", 0, 0, 0), ("A", 1, 0, 0), (" ∩ ", 0, 0, 0),
        ("B", 1, 0, 0), ("| / |", 0, 0, 0), ("A", 1, 0, 0), (" ∪ ", 0, 0, 0),
        ("B", 1, 0, 0), ("|   (2.9)", 0, 0, 0)]


def tahap4cd(doc):
    add = lambda *a, **k: add_para(doc, *a, **k)
    add(32, "Landasan Teoretik", bold=True)
    add(32, "Deteksi Tepi Canny dan Aproksimasi Quad", bold=True)
    add(33, CH2A, itw=IT4)
    F(doc, 33, EQ21)
    F(doc, 33, EQ22)
    add(33, CH2B, itw=IT4)
    F(doc, 33, EQ23)
    add(32, "Ruang Warna HSV dan Segmentasi Vegetasi", bold=True)
    add(33, CH2C, itw=IT4)
    F(doc, 33, EQ24)
    add(32, "Adaptasi Iluminasi dan Perata Temporal EMA", bold=True)
    add(33, CH2D, itw=["Hue", "Saturation", "Value", "Exponential Moving Average",
                       "Plant Stress Index", "ground truth", "recall", "Intersection over Union",
                       "f"])
    F(doc, 33, EQ25)
    add(32, "Liputan Kanopi dan Indeks Stres Tanaman", bold=True)
    add(33, CH2E, itw=["Hue", "Saturation", "Value", "Exponential Moving Average",
                       "Plant Stress Index", "ground truth", "recall", "Intersection over Union"])
    F(doc, 33, EQ26)
    F(doc, 33, EQ26B)
    F(doc, 33, EQ27)
    add(32, "Metrik Evaluasi Segmentasi", bold=True)
    add(33, CH2F, itw=["Hue", "Saturation", "Value", "Exponential Moving Average",
                       "Plant Stress Index", "ground truth", "recall", "Intersection over Union",
                       "harmonic mean"])
    F(doc, 33, EQ28)
    F(doc, 33, EQ29)
# ---------------- Tahap 5a (= t5a.py): Bab 3: 3.1 pendekatan, 3.2 lokasi+waktu, 3.3 prosedur ----------------
PENDEKATAN = "Perancangan prototipe ini memakai pendekatan rekayasa sistem berbasis aturan visi komputer konvensional, yaitu deteksi tepi Canny, aproksimasi quad, homografi planar, dan segmentasi warna HSV adaptif iluminasi, tanpa pembelajaran mendalam atau deep learning [20], [19]. Pendekatan tersebut dipilih karena data lapangan yang tersedia terbatas pada 18 video dan lima foto, ambang warna tetap transparan dan mudah dikalibrasi ulang mengikuti karakteristik bed, serta beban komputasi ringan sehingga pipeline dapat berjalan tiap 10 menit pada Raspberry Pi 4B. Alur perancangan mengikuti observasi dan wawancara kebutuhan, perumusan arsitektur berlima tahap, implementasi pipeline beserta kontrak data, lalu pengujian iluminasi, akurasi segmentasi, dan burn-in lapangan."
LOKWAKTU = "Riset dilaksanakan pada bed akuaponik kangkung berukuran 2 m × 1,1 m di Aquaponik Eco Farm Universitas Negeri Semarang (UNNES), sedangkan pengembangan perangkat lunak dilakukan di laboratorium komputer. Periode riset berlangsung pada Juli sampai November 2026. Pengambilan citra memakai kamera atas atau top-down pada tiga rentang iluminasi yaitu pagi pukul 08.00-09.00, siang pukul 11.00-13.00, dan sore pukul 15.00-17.00. Uji lapangan memakai 18 video dan lima foto bed tahap seedling sampai ready, sedangkan uji burn-in 24 jam dilakukan setelah rumah kamera terpasang permanen di lokasi."
PROSEDUR = "Prosedur perancangan dilaksanakan dalam enam langkah. (1) Observasi dan wawancara awal dengan pengelola Aquaponik Eco Farm UNNES untuk memetakan persoalan penilaian visual panen dan kondisi bed. (2) Analisis kebutuhan fungsional, yaitu deteksi bed otomatis, grid 4×6, segmentasi adaptif iluminasi, skor kuning dan cokelat, PSI siap kendali, serta arsip dan dasbor. (3) Perancangan arsitektur berlima tahap beserta kontrak data fuzzy_input dan aturan keselamatan seperti pada Bagian 3.3.1. (4) Implementasi pipeline visi komputer mengikuti diagram alir pada Bagian 3.3.2 beserta skema pemasangan pada Bagian 3.3.3. (5) Integrasi Firebase dan dasbor web sehingga tiap siklus 10 menit menghasilkan payload bed_readings serta visualisasi heatmap 4×6. (6) Pengujian stabilitas iluminasi, akurasi segmentasi terhadap mask ground truth, dan burn-in lapangan memakai metrik serta skenario pada Bagian 3.5."


def tahap5a(doc):
    add_para(doc, 32, "BAB III", bold=True)
    add_para(doc, 32, "METODE PELAKSANAAN", bold=True)
    add_para(doc, 32, "3.1  Pendekatan Perancangan", bold=True)
    add_para(doc, 33, PENDEKATAN, itw=IT5)
    add_para(doc, 32, "3.2  Lokasi dan Waktu", bold=True)
    add_para(doc, 33, LOKWAKTU, itw=IT5)
    add_para(doc, 32, "3.3  Prosedur Perancangan", bold=True)
    add_para(doc, 33, PROSEDUR, itw=IT5 + ["fuzzy_input", "bed_readings"])
# ---------------- Tahap 5e: 3.4 Bahan dan Alat + Tabel 3.1/3.2 (dipindah ke sini agar urut 3.1-3.5) ----------------
BAHAN = "Bahan berupa bed akuaponik kangkung di Aquaponik Eco Farm UNNES satu unit beserta tanaman tahap seedling sampai ready, lima foto lapangan, dan 18 video uji. Alat terdiri atas perangkat keras pada Tabel 3.1 dan perangkat lunak pada Tabel 3.2. Modul raspi/modules adalah salinan berkas adaptive_bed.py dan kangkung_cv.py sehingga hasil laptop dan komputer papan tunggal identik."
IT5 = ["top-down", "ground truth", "bed_readings", "fuzzy_input", "Hue Saturation Value"]
HW = [
 ["Raspberry Pi 4B", "RAM 2 GB, Debian 13, Python 3.13", "Komputasi pipeline tiap 10 menit"],
 ["Kamera CSI IR 5MP", "Sensor ov5647, 1296×972 via libcamera", "Akuisisi top-down"],
 ["Adaptor 5V/3A", "USB-C 5 V polos", "Catu daya stabil"],
 ["microSD high-endurance", "Minimal 16 GB", "Media sistem 24/7"],
 ["Rumah kamera 3DP", "PETG, IP65, sun shield, silica", "Pelindung outdoor"],
 ["Laptop", "Windows, Python 3.12", "Analisis video dan GT"],
]
SW = [
 ["OpenCV headless", "4.10.0", "Canny, kontur, warp, HSV"],
 ["NumPy", "1.26.4", "Operasi matriks dan maska"],
 ["firebase-admin", "6.5.0", "Uplink Firestore/Storage"],
 ["Picamera2/libcamera", "Sistem Pi", "Akuisisi CSI"],
 ["Tailscale + SSH", "Layanan jarak jauh", "Administrasi tanpa buka port"],
 ["Dasbor web statis", "web/ tanpa build", "Heatmap 4×6 dan grafik 24 jam"],
]


def tahap5e(doc):
    add_para(doc, 32, "3.4  Bahan dan Alat", bold=True)
    add_para(doc, 33, BAHAN, itw=["raspi/modules", "adaptive_bed.py", "kangkung_cv.py"])
    add_para(doc, 89, "Tabel 3.1  Daftar perangkat keras dan spesifikasinya.", bold=True)
    t = doc.add_table(rows=7, cols=3)
    t.style = "Table Grid"
    for j, htxt in enumerate(["Perangkat", "Spesifikasi", "Fungsi"]):
        t.cell(0, j).text = htxt
    for i, row in enumerate(HW, 1):
        for j, v in enumerate(row):
            t.cell(i, j).text = v
    add_para(doc, 89, "Tabel 3.2  Daftar perangkat lunak dan pustaka.", bold=True)
    t2 = doc.add_table(rows=7, cols=3)
    t2.style = "Table Grid"
    for j, htxt in enumerate(["Perangkat lunak", "Versi/Sumber", "Fungsi"]):
        t2.cell(0, j).text = htxt
    for i, row in enumerate(SW, 1):
        for j, v in enumerate(row):
            t2.cell(i, j).text = v
# ---------------- Tahap 5b (= t5b.py): arsitektur + Gambar 3.1 ----------------
ARSITEK = "Sistem dirancang sebagai sensor tanaman otomatis berlima tahap. Tahap akuisisi memakai kamera CSI atau HP secara top-down dengan pemanasan pajanan otomatis. Tahap visi di komputer papan tunggal menjalankan deteksi bed, warp, grid 4×6, liputan, kuning, cokelat, dan PSI seperti Persamaan 2.3 sampai 2.7. Tahap Firebase memakai koleksi bed_readings skema v1.1 dengan payload 2-3 KB tiap 10 menit. Tahap dasbor menampilkan heatmap 4×6, grafik 24 jam, distribusi status, dan kartu PSI secara baca saja. Tahap kendali membaca PSI, PSI maksimum, dan jumlah zona sakit menjadi keputusan pompa dengan persetujuan manusia. Perancangan sensor, komputer papan tunggal, dan aktuator dalam satu skema terkendali sejalan dengan tren otomasi greenhouse yang dirangkum Shamshiri dkk. [25]. Blok diagram pada Gambar 3.1 meringkas aliran tersebut. Kode sumber pipeline, skema Firebase, dan dasbor tersedia pada Lampiran 1, biodata penulis pada Lampiran 2, serta sketsa rumah kamera pada Lampiran 3."
KONTRAK = "Kontrak antar tahap memakai fuzzy_input berisi kuning_pct, coklat_pct, zona_sakit, psi, psi_maks, dan psi_versi. Aturan keselamatan menetapkan data basi di atas 30 menit ditolak, nilai hilang menahan tindakan, dan status usulan wajib menunggu persetujuan manusia sehingga tidak ada aktuasi otomatis."


def tahap5b(doc):
    itw = ["top-down", "bed_readings", "fuzzy_input", "psi", "psi_maks", "psi_versi"]
    add_para(doc, 32, "3.3.1  Arsitektur Sistem", bold=True)
    add_para(doc, 33, ARSITEK, itw=itw)
    cap = add_para(doc, 89, "Gambar 3.1  Blok diagram sistem sensor tanaman otomatis dari kamera sampai dasbor dan pengendali.", bold=True)
    add_image_before(doc, cap, ROOT / "docs" / "blok_diagram.png", 5.5)
    add_para(doc, 33, KONTRAK, itw=itw)
# ---------------- Tahap 5c (= t5c.py): diagram alir + Gambar 3.2, skema + Gambar 3.3 ----------------
ALIR = "Diagram alir pada Gambar 3.2 memakai simbol baku algoritma yaitu elips untuk START dan END, jajar genjang untuk input dan output, belah ketupat untuk keputusan, dan persegi panjang untuk proses. Aliran dimulai dari frame kamera, lalu deteksi bed Canny-quad dengan keputusan lolos atau jalur cadangan, lalu warp dan grid, lalu segmentasi adaptif memakai Persamaan 2.4 dan faktor f Bagian 2.2.3, lalu skor zona memakai Persamaan 2.6 dan 2.7, lalu pengiriman payload, dan diakhiri keluaran MP4 beranotasi, CSV runtun waktu, JSON, dan dasbor. Diagram alir berbeda dengan blok diagram Gambar 3.1 karena diagram alir menunjukkan langkah yang dapat diprogram sedangkan blok diagram menunjukkan hubungan antar subsistem."
SKEMA = "Kamera dipasang di atas tengah bed secara top-down pada ketinggian sekitar 2,5 m sehingga seluruh tepi bed masuk frame dengan porsi bed minimal 12 persen luas frame seperti Gambar 3.3. Aturan pasang menghindari pantulan langsung ke modul kamera, pipa yang menutupi bed, dan rumah hitam yang terkena matahari langsung. Rumah PETG IP65 memakai pelindung matahari, kelenjar kabel, dan gel silika, sedangkan komputer papan tunggal memakai pelepas panas besar. Sketsa rumah kamera lengkap terdapat pada Lampiran 3."


def tahap5c(doc):
    itw = ["f", "Hue", "Saturation", "Value", "top-down"]
    add_para(doc, 32, "3.3.2  Diagram Alir", bold=True)
    add_para(doc, 33, ALIR, itw=itw)
    c2 = add_para(doc, 89, "Gambar 3.2  Diagram alir pipeline computer vision dari START sampai END.", bold=True)
    add_image_before(doc, c2, ROOT / "docs" / "flowchart_cv.png", 3.2)
    add_para(doc, 32, "3.3.3  Skema Pemasangan", bold=True)
    add_para(doc, 33, SKEMA, itw=itw)
    c3 = add_para(doc, 89, "Gambar 3.3  Skema pemasangan kamera di atas bed akuaponik.", bold=True)
    add_image_before(doc, c3, ROOT / "docs" / "skema_kamera.png", 5.5)
# ---------------- Tahap 5d (= t5d.py): prinsip kerja + Gambar 3.4/3.5, metrik + Tabel 3.3 ----------------
KERJA = "Prinsip kerja mengikuti formulasi Bab 2 dan dirujuk eksplisit tiap langkah. Deteksi bed memakai Persamaan 2.1 dan 2.2 untuk tepi, lalu aproksimasi quad, lalu Persamaan 2.3 untuk warp. Segmentasi memakai Persamaan 2.4 untuk maska hijau serta rentang kuning dan cokelat yang dijaga statis agar diagnosis tegas. Faktor adaptasi Bagian 2.2.3 menggeser ambang S dan V lalu sudut diratakan dengan Persamaan 2.5. Tiap zona dihitung liputan, kuning, dan cokelat terhadap piksel tanaman, lalu status panen dan status kesehatan ditetapkan, lalu PSI dan PSI maksimum dihitung dengan Persamaan 2.6 dan 2.7. Zona dengan kanopi di bawah 30 persen luas zona berstatus tidak dinilai agar artefak tepi warp tidak memicu alarm."
BUKTI = "Bukti reproduksibilitas memakai data asli. Gambar 3.4 membandingkan frame mentah HP IMG_5159 dengan keluaran pipeline pada frame yang sama, sedangkan Gambar 3.5 membandingkan frame video lapangan IMG_5388 dengan keluaran segmentasi HSV adaptif pada frame yang sama. Kedua gambar tersebut membuktikan masukan dan keluaran berasal dari data lapangan, bukan simulasi."
METRIK = "Metrik terdiri atas jitter sudut dalam piksel untuk stabilitas temporal, liputan rata-rata dan simpangan baku dalam persen untuk tren tumbuh, serta presisi, recall, F1 (harmonic mean presisi dan recall), dan Intersection over Union (IoU) memakai Persamaan 2.8 dan 2.9 untuk akurasi segmentasi terhadap mask ground truth. Sebagai pembanding, segmentasi HSV diuji terhadap indeks vegetasi Excess Green (ExG) dan ambang Otsu-Hue mengikuti prosedur Netto dkk. [26] sehingga keunggulan metode dapat diuji pada data lapangan yang sama. Metrik sistem terdiri atas keberhasilan siklus burn-in, suhu System on Chip (SoC) dalam °C, dan keterbacaan snapshot. Skenario pada Tabel 3.3 menguji tiap rumusan masalah secara kuantitatif dan divisualkan dengan plot pengujian agar pembaca tidak menelusuri angka mentah satu per satu."
SKEN = [
 ["Stabilitas iluminasi", "18 video pagi/siang/sore", "Jitter turun >=40 persen, liputan stabil", "Persamaan 2.5"],
 ["Akurasi segmentasi", "5 mask ground truth", "F1 0,85-0,95, IoU per kelas", "Persamaan 2.8-2.9"],
 ["Kesehatan dan PSI", "5 foto lapangan + foto sakit", "0 zona sakit palsu, PSI 0-0,1 saat sehat", "Persamaan 2.6-2.7"],
 ["Banding metode", "5 gambar GT", "HSV vs ExG vs Otsu-Hue", "Tabel 2.1"],
 ["Burn-in lapangan", "24 jam, 144 siklus", ">=140 OK, suhu <70 °C", "Tabel 3.1"],
]


def tahap5d1(doc):
    itw = ["Hue", "Saturation", "Value", "ground truth", "top-down"]
    add_para(doc, 32, "3.3.4  Prinsip Kerja Algoritma", bold=True)
    add_para(doc, 33, KERJA, itw=itw)
    add_para(doc, 33, BUKTI, itw=itw)
    c4 = add_para(doc, 89, "Gambar 3.4  Bukti asli frame HP terhadap keluaran pipeline grid dan HUD.", bold=True)
    add_image_before(doc, c4, ROOT / "output" / "ppt_asli" / "01_asli_vs_anotasi.jpg", 5.8)
    c5 = add_para(doc, 89, "Gambar 3.5  Bukti asli frame video lapangan IMG_5388 terhadap keluaran segmentasi liputan 47,4 persen.", bold=True)
    add_image_before(doc, c5, ROOT / "output" / "ppt_asli" / "02_foto_vs_segmentasi.jpg", 5.2)


def tahap5d2(doc):
    add_para(doc, 32, "3.5  Metrik dan Skenario Pengujian", bold=True)
    add_para(doc, 33, METRIK, itw=["recall", "Intersection over Union", "ground truth", "Excess Green"])
    add_para(doc, 89, "Tabel 3.3  Skenario pengujian kelayakan prototipe.", bold=True)
    t = doc.add_table(rows=6, cols=4)
    t.style = "Table Grid"
    for j, htxt in enumerate(["Skenario", "Data", "Metrik dan target", "Acuan"]):
        t.cell(0, j).text = htxt
    for i, row in enumerate(SKEN, 1):
        for j, v in enumerate(row):
            t.cell(i, j).text = v
# ---------------- Tahap 6L (baru): Lampiran QR + biodata + sketsa ----------------
LAMP_INTRO = "Lampiran 1 memuat kode QR repositori pada Gambar L.1 yang mengarah langsung ke kode sumber pipeline, skema Firebase, dan dasbor. Lampiran 2 memuat biodata penulis. Lampiran 3 memuat sketsa rumah kamera. Kode QR berukuran kecil dan diletakkan di sudut kanan atas halaman lampiran dengan tata letak yang konsisten."
LAMP_BIODATA = "Lampiran 2: Biodata penulis — Nama: Felix Enrique, NIM: 2305110019, Program Studi: Teknik Komputer (S1), Fakultas: Fakultas Teknik, Perguruan Tinggi: Universitas Negeri Semarang (UNNES), Bidang minat: Computer Vision, Embedded Systems, Aquaponik."
LAMP_SKETSA = "Lampiran 3: Sketsa rumah kamera — lihat hardware/stl dan hardware/renders pada repositori via QR Gambar L.1."


def tambah_pagebreak(p):
    r = p.add_run()
    r.add_break(WD_BREAK.PAGE)
    return p


def mulai_halaman_baru(p):
    """Paksa paragraf (heading bab) mulai di halaman baru via property
    w:pageBreakBefore, sehingga judul bab tidak menempel di halaman
    terakhir bab sebelumnya. Berbeda dgn tambah_pagebreak yang memasang
    break DI AKHIR paragraf (judul tetap di halaman lama)."""
    pPr = p._p.get_or_add_pPr()
    for old in pPr.findall(qn("w:pageBreakBefore")):
        pPr.remove(old)
    pbb = OxmlElement("w:pageBreakBefore")
    pPr.append(pbb)
    return p


def tahap_lampiran(doc):
    h = add_para(doc, 32, "LAMPIRAN", bold=True)
    mulai_halaman_baru(h)
    # Paragraf isi lampiran diklon dari template 33 (gaya List Paragraph,
    # numId 1, bold bawaan) spt entri pustaka -> buang penomoran otomatis
    # dan bold; judul-judul "Lampiran 1/2/3" ditulis manual di teks.
    p = add_para(doc, 33, LAMP_INTRO)
    strip_numbering(p)
    for r in p.runs:
        r.bold = False
    qrp = doc.add_paragraph()
    qrp.style = doc.styles["Normal"]
    qrp.alignment = 2
    qrp.add_run().add_picture(str(ROOT / "docs" / "qr_repo.png"), width=Inches(1.2))
    g = doc.add_paragraph()
    g.style = doc.styles["Normal"]
    g.alignment = 2
    r = g.add_run("Gambar L.1  Kode QR repositori sumber terbuka")
    if doc.paragraphs[89].runs:
        r.font.size = doc.paragraphs[89].runs[0].font.size
    for teks in ("Lampiran 1: Kode sumber dan data — akses penuh via QR Gambar L.1.",
                 LAMP_BIODATA, LAMP_SKETSA):
        p = add_para(doc, 33, teks)
        strip_numbering(p)
        for r in p.runs:
            r.bold = False


# ---------------- Tahap 6b (= t6b.py): Daftar Isi statis P19-P28 ----------------
TOC = ["HALAMAN JUDUL ............................................................................................. i",
 "PERSETUJUAN PEMBIMBING ...................................................................... ii",
 "DAFTAR ISI ......................................................................................................... iii",
 "DAFTAR TABEL .................................................................................................. iv",
 "DAFTAR GAMBAR ............................................................................................ v",
 "DAFTAR ISTILAH DAN SINGKATAN ......................................................... vi",
 "BAB I  PENDAHULUAN ..................................................................................... 1",
 "BAB II  KAJIAN PUSTAKA ........................................................................... 9",
 "BAB III  METODE PELAKSANAAN .............................................................. 13",
 "DAFTAR PUSTAKA .......................................................................................... 19",
 "LAMPIRAN .......................................................................................................... 21"]


def tahap6b(doc):
    # TOC kini 11 entri (bertambah LAMPIRAN); paragraf persis-forma template
    # hanya tersedia 10 (indeks 19-28): entri ke-11 disisipkan persis setelah
    # entri DAFTAR PUSTAKA dengan meniru pola entri di sebelahnya.
    for k, teks in enumerate(TOC):
        if k <= 9:
            p = doc.paragraphs[19 + k]
            if not p.runs:
                p.add_run(teks)
            else:
                p.runs[0].text = teks
                for r in p.runs[1:]:
                    r.text = ""
    p10 = find_p(doc, TOC[9])
    np_ = Paragraph(deepcopy(p10._p), doc)
    np_.runs[0].text = TOC[10]
    for r in np_.runs[1:]:
        r._r.getparent().remove(r._r)
    p10._p.addnext(np_._p)


# ---------------- Tahap N (baru): nomor heading eksplisit 1.x/2.x/3.x ----------------
# Template memakai satu list (numId 1, ilvl 1, "%1.%2") untuk SEMUA heading,
# sehingga Word merender "1.1 Latar Belakang" ... "1.6 BAB II" ... "1.17 Lokasi
# Riset" ... "1.24 DAFTAR PUSTAKA". Tahap ini menulis nomor panduan secara
# eksplisit di awal teks heading (1.x untuk Bab I, 2.1/2.2/2.2.1-2.2.5 untuk
# Bab II, 3.1-3.5 + 3.3.1-3.3.4 untuk Bab III) lalu menghapus numPr agar tidak
# ganda. Heading chapter (BAB I/II/III, KAJIAN PUSTAKA, METODE PELAKSANAAN,
# DAFTAR PUSTAKA) tidak diberi nomor seperti pada template (BAB I polos).
# Setiap numId memakai abstract berbeda, jadi yang tayang terpisah adalah
# nomor BAB (numId 1, dikontrol eksplisit di bawah). numId lain dipakai
# ulang template (1.4.1, rumusan 1-3, singkatan) dan pustaka/lampiran.
NOMOR_HEADING = {
 "Latar Belakang": "1.1  ",
 "Rumusan Masalah": "1.2  ",
 "Tujuan Prototipe": "1.3  ",
 "Manfaat Prototipe": "1.4  ",
 "Potensi Dampak Fungsional/Komersial": "1.5  ",
 "Tinjauan Pustaka": "2.1  ",
 "Landasan Teoretik": "2.2  ",
 "Deteksi Tepi Canny dan Aproksimasi Quad": "2.2.1  ",
 "Ruang Warna HSV dan Segmentasi Vegetasi": "2.2.2  ",
 "Adaptasi Iluminasi dan Perata Temporal EMA": "2.2.3  ",
 "Liputan Kanopi dan Indeks Stres Tanaman": "2.2.4  ",
 "Metrik Evaluasi Segmentasi": "2.2.5  ",
}
TANPA_NOMOR = ("BAB II", "KAJIAN PUSTAKA", "BAB III", "METODE PELAKSANAAN",
               "DAFTAR PUSTAKA", "LAMPIRAN")


def tahap_heading_numbering(doc):
    for p in doc.paragraphs:
        if p._p.find(".//" + qn("w:numId")) is None:
            continue
        nid = p._p.find(".//" + qn("w:numId")).get(qn("w:val"))
        if nid != "1":
            continue  # daftar isi lain (1.4.1, rumusan 1-3, dst) sudah benar
        teks = p.text.strip()
        if teks in TANPA_NOMOR or teks in NOMOR_HEADING:
            if teks in NOMOR_HEADING:
                if p.runs:
                    p.runs[0].text = NOMOR_HEADING[teks] + p.text
                    for r in p.runs[1:]:
                        r.text = ""
                else:
                    p.add_run(NOMOR_HEADING[teks] + p.text)
            strip_numbering(p)


# ---------------- Tahap akhir: normalisasi format (tahan drift indeks) ----------------
# Dua cacat keluaran yang muncul karena referensi indeks template (32 = heading,
# 89 = caption) bergeser setelah tahap sebelumnya menghapus paragraf template Bab 1:
#   1) heading Bab 3 (3.1-3.5, 3.3.1-3.3.4) masih membawa numPr numId=1 sehingga
#      Word menomori ganda ("1.x  3.1 ..."). Bab 1/2 sudah dibersihkan
#      tahap_heading_numbering; di sini semua heading bernomor eksplisit dibersihkan.
#   2) caption Tabel/Gambar di body mewarisi gaya ListParagraph + numPr + rata kiri,
#      bukan gaya caption template (P89: tanpa style, rata tengah, tebal).
# Heading chapter BAB II/III juga dirata tengah + tebal 14pt agar seragam dgn BAB I.
# Normalisasi berbasis TEKS (bukan indeks) sehingga kebal drift.
CHAPTER_HEADS = ("BAB II", "KAJIAN PUSTAKA", "BAB III", "METODE PELAKSANAAN")


def _rata_tengah_tebal(p, pt=None, bold=True):
    """Rata tengah; buang numPr & style daftar (meniru caption/heading
    chapter template P89/P31). pt: ukuran font opsional (14 untuk chapter).
    bold=True utk heading chapter; False utk caption gaya Rafly (non-bold)."""
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    strip_numbering(p)
    pPr = p._p.get_or_add_pPr()
    st = pPr.find(qn("w:pStyle"))
    if st is not None:
        pPr.remove(st)
    for r in p.runs:
        r.bold = bold
        if pt is not None:
            r.font.size = Pt(pt)


def tahap_normalize_format(doc):
    nomor_re = re.compile(r"^\d+(?:\.\d+)+\s")
    for p in doc.paragraphs:
        t = p.text.strip()
        # 1) heading bab bernomor eksplisit (1.x/2.x/3.x) -> buang nomor otomatis sisa
        if nomor_re.match(t):
            strip_numbering(p)
            continue
        # 2) heading chapter BAB II/III + label -> rata tengah tebal 14pt (spt BAB I)
        if t in CHAPTER_HEADS:
            _rata_tengah_tebal(p, pt=14)
            continue
        # 3) caption body Tabel/Gambar (tanpa tab/titik) -> rata tengah NON-bold
        #    (gaya Rafly: caption 12pt regular, bukan tebal)
        if (t.startswith("Tabel ") or t.startswith("Gambar ")) \
                and "\t" not in p.text and "...." not in p.text:
            _rata_tengah_tebal(p, bold=False)


# ---------------- Tahap akhir-2: struktur penulisan ala dokumen Rafly ----------------
# Menyelaraskan struktur penulisan ke dokumen acuan Rafly (Proposal Prototipe
# Fuzzy Logic Sugeno):
#   * nomor bab memakai ANGKA ROMAWI (BAB I/II/III);
#   * judul bab digabung satu paragraf "BAB N\nJUDUL" (spt template P31),
#     menggantikan dua paragraf terpisah buatan tahap4a/tahap5a;
#   * memakai style Heading1/2/3 asli agar bab & sub-bab muncul di navigasi/
#     outline Word;
#   * DAFTAR PUSTAKA bukan heading - baris teks biasa 12pt non-bold rata kiri
#     menempel di akhir Bab III (ditangani tahap6c).
# Warna judul bab & sub-heading HITAM dan ukuran rapi (bab 14pt, sub 12pt)
# agar seragam dgn template kampus. Normalisasi berbasis TEKS, kebal drift.
GABUNG_BAB = [("BAB II", "KAJIAN PUSTAKA"), ("BAB III", "METODE PELAKSANAAN")]


def _set_run_hitam(p, pt=None, bold=None):
    for r in p.runs:
        r.font.color.rgb = RGBColor(0, 0, 0)
        if pt is not None:
            r.font.size = Pt(pt)
        if bold is not None:
            r.bold = bold


def _gabung_judul_bab(p_bab, p_judul):
    """Gabung paragraf judul bab ke p_bab dengan line break, lalu hapus p_judul."""
    src = p_judul.runs[0] if p_judul.runs else None
    rb = p_bab.add_run()
    rb.add_break(WD_BREAK.LINE)
    r2 = p_bab.add_run(p_judul.text)
    if src is not None:
        r2.bold = src.bold
        r2.font.size = src.font.size
    delete_p(p_judul)


def tahap_struktur_mirza(doc):
    # 0) tentukan batas body LEBIH DULU memakai tanda "\n":
    #    heading bab asli template berbentuk "BAB I\nPENDAHULUAN" (ada line break),
    #    sedangkan entri TOC front matter berbentuk "BAB I  PENDAHULUAN\t1"
    #    (pakai tab). Ini menghindari entri TOC ikut ter-style Heading1.
    i_body = next(i for i, p in enumerate(doc.paragraphs)
                  if p.text.startswith("BAB I\n"))
    # 1) nomor bab DIPERTAHANKAN romawi (BAB I/II/III) sesuai gaya dokumen Rafly
    #    (keputusan: ikut Rafly penuh - tanpa rename ke angka Arab).
    # 2) gabung judul bab terpisah -> satu paragraf "BAB N\nJUDUL"
    for bab, judul in GABUNG_BAB:
        p_bab = next((p for p in doc.paragraphs[i_body:]
                      if p.text.strip() == bab), None)
        if p_bab is None:
            continue
        nxt = p_bab._p.getnext()
        if nxt is not None and nxt.tag == qn("w:p"):
            p_judul = Paragraph(nxt, doc)
            if p_judul.text.strip() == judul:
                _gabung_judul_bab(p_bab, p_judul)
    # 3) assign Heading style + warna hitam + ukuran rapi (hanya body).
    #    Setiap judul bab DAHALAMI pageBreakBefore supaya BAB II/III dan LAMPIRAN
    #    tidak menempel di halaman terakhir bab sebelumnya.
    #    DAFTAR PUSTAKA TIDAK dijadikan heading (gaya Rafly: baris teks biasa
    #    12pt non-bold rata kiri menempel di akhir bab - ditangani tahap6c).
    for p in doc.paragraphs[i_body:]:
        t = p.text.strip()
        if t.startswith(("BAB I", "BAB II", "BAB III")):
            p.style = doc.styles["Heading 1"]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _set_run_hitam(p, pt=14, bold=True)
            mulai_halaman_baru(p)
        elif re.match(r"^\d+\.\d+\.\d+\s", t):
            p.style = doc.styles["Heading 3"]
            _set_run_hitam(p, pt=12, bold=True)
        elif re.match(r"^\d+\.\d+\s", t):
            p.style = doc.styles["Heading 2"]
            _set_run_hitam(p, pt=12, bold=True)


def tahap_judul_persetujuan(doc):
    """Format halaman judul gaya dokumen Rafly: judul 16pt bold (3 baris,
    spasi 1,5) dan baris pendukung 12pt eksplisit. Teks & identitas (nama, NIM,
    dosen pembimbing, kampus) TIDAK diubah - hanya format. Berbasis teks =>
    kebal drift indeks."""
    # Porting editan manual halaman judul: gabung baris fakultas+universitas
    # dan hapus dua paragraf kosong di atas blok PROGRAM STUDI.
    i_prog = next((i for i, p in enumerate(doc.paragraphs)
                   if p.text.startswith('PROGRAM STUDI')), None)
    if i_prog is not None:
        p_prog = doc.paragraphs[i_prog]
        set_text(p_prog, 'PROGRAM STUDI TEKNIK KOMPUTER\nFAKULTAS TEKNIK UNIVERSITAS NEGERI SEMARANG\n2026')
        for _ in range(2):
            prev = p_prog._p.getprevious()
            if prev is not None and prev.tag == qn('w:p') and not Paragraph(prev, doc).text.strip():
                prev.getparent().remove(prev)
    i_persetujuan = next(i for i, p in enumerate(doc.paragraphs)
                         if p.text.strip() == "PERSETUJUAN PEMBIMBING")
    for p in doc.paragraphs[:i_persetujuan]:
        t = p.text
        if t.startswith("PENGEMBANGAN SISTEM MONITORING"):        # baris judul
            for r in p.runs:
                r.font.size = Pt(16)
        elif t.startswith(("diajukan", "oleh", "Felix", "PROGRAM STUDI")):
            for r in p.runs:
                r.font.size = Pt(12)


# ---------------- Tahap gaya Rafly: spasi 1,5 + indent baris pertama ----------------
# Ukuran dari PDF dokumen Rafly: spasi baris body top-to-top 20,76pt untuk 12pt
# = kelipatan 1,5 (Word 1.5 lines). Baris pertama paragraf body menjorok 18pt
# (0,25 in) dari tepi kiri paragraf (149,4 - 131,4). Halaman judul & persetujuan
# juga memakai kelipatan 1,5. Entri DAFTAR PUSTAKA Rafly justru 1,15 (15,96pt)
# -> dipertahankan spasi template. List bernomor (rumusan/manfaat) memakai
# hanging indent numbering sendiri -> first-line indent TIDAK diterapkan.
JML_SPASI = 1.5
INDEN_PERTAMA = Pt(18)          # 0,25 in = 18pt, sama dgn dokumen Rafly


def tahap_spasi_rafly(doc):
    ps = doc.paragraphs
    i_setuju = next(i for i, p in enumerate(ps)
                    if p.text.strip() == "PERSETUJUAN PEMBIMBING")
    i_daftar = next(i for i, p in enumerate(ps)
                    if p.text.strip() == "DAFTAR ISI")
    i_body = next(i for i, p in enumerate(ps)
                  if p.text.startswith("BAB I\n"))
    i_pus = next(i for i, p in enumerate(ps)
                 if p.text.strip() == "DAFTAR PUSTAKA" and i > i_body)
    i_lamp = next(i for i, p in enumerate(ps)
                  if p.text.strip() == "LAMPIRAN" and i > i_pus)

    def spasi_15(p):
        if p.text.strip():
            p.paragraph_format.line_spacing = JML_SPASI

    # (a) halaman judul + halaman persetujuan: spasi 1,5, tanpa indent
    for p in ps[:i_setuju]:
        spasi_15(p)
    for p in ps[i_setuju + 1:i_daftar]:
        spasi_15(p)
    # (b) body BAB I..sebelum DAFTAR PUSTAKA: spasi 1,5 + indent baris pertama
    for p in ps[i_body:i_pus]:
        spasi_15(p)
        if (p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY
                and not p.style.style_id.startswith("Heading")
                and p._p.find(".//" + qn("w:numPr")) is None
                and p._p.find(".//" + qn("w:drawing")) is None):
            p.paragraph_format.first_line_indent = INDEN_PERTAMA
    # (c) isi LAMPIRAN (paragraf biasa) ikut spasi 1,5 + indent
    for p in ps[i_lamp:]:
        spasi_15(p)
        if (p.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY
                and p._p.find(".//" + qn("w:numPr")) is None
                and p._p.find(".//" + qn("w:drawing")) is None):
            p.paragraph_format.first_line_indent = INDEN_PERTAMA
    # (d) entri DAFTAR PUSTAKA: biarkan spasi template (1,15) spt dokumen Rafly


# ---------------- Tahap 6c (= t6c.py): Daftar Pustaka ----------------
SITASI = [
 "[1] P. Lindholm-Lehto, Water quality monitoring in recirculating aquaculture systems, Aquaculture and Fisheries, 2023. doi: 10.1002/aff2.102.",
 "[2] Y. Rahmanto, A. Rifaini, S. Samsugi, dan S. D. Riskiono, Sistem monitoring pH air pada aquaponik menggunakan mikrokontroler Arduino Uno, Jurnal Teknologi dan Sistem Tertanam, vol. 1, no. 1, 2020. doi: 10.33365/jtst.v1i1.711.",
 "[3] S. Mardanisamani, M. Eramian dkk., Segmentation of vegetation and microplots in aerial agriculture images: A survey, Plant Phenome J., vol. 5, no. 1, 2022. doi: 10.1002/ppj2.20042.",
 "[4] N. Zhang dkk., A review of advanced technologies and development for hyperspectral-based plant disease detection in the past three decades, Remote Sens., vol. 12, no. 19, p. 3188, 2020. doi: 10.3390/rs12193188.",
 "[5] W. Huang, Z. Yu dkk., K-mean and HSV model based segmentation of unhealthy plant leaves and classification using machine learning approach, IEEE Access, 2021.",
 "[6] A. Raza, M. A. Khan dkk., Robust leaf disease detection using complex fuzzy sets and HSV-based color segmentation techniques, Adv. Trends Artif. Intell. Mach. Learn., vol. 3, no. 3, 2024.",
 "[7] D. M. Woebbecke, G. E. Meyer, K. Von Bargen, dan D. A. Mortensen, Color indices for weed identification under various soil, residue, and lighting conditions, Trans. ASAE, vol. 38, no. 1, pp. 259-269, 1995. doi: 10.13031/2013.27838.",
 "[8] S. Wan, K. Zhao, Z. Lu dkk., A modularized IoT monitoring system with edge-computing for aquaponics, Sensors, vol. 22, no. 23, p. 9260, 2022. doi: 10.3390/s22239260.",
 "[9] R. Abbasi, P. Martinez, dan R. Ahmad, Automated visual identification of foliage chlorosis in lettuce grown in aquaponic systems, Agriculture, vol. 13, no. 3, p. 615, 2023. doi: 10.3390/agriculture13030615.",
 "[10] D. Searson dkk., Automatic crop detection under field conditions using the HSV colour space and morphological operations, Comput. Electron. Agric., vol. 134, pp. 80-89, 2017. doi: 10.1016/j.compag.2016.12.013.",
 "[11] I. A. Hameed, M. Usama dkk., A new vegetation segmentation approach for cropped fields based on threshold detection from hue histograms, Sensors, vol. 18, no. 4, p. 1258, 2018. doi: 10.3390/s18041258.",
 "[12] V. Variyar, N. Haridas dkk., Water IoT monitoring system for aquaponics health and fishery applications, Sensors, vol. 22, no. 19, p. 7679, 2022. doi: 10.3390/s22197679.",
 "[13] R. Prajapati, P. Tamang, dan E. Kumar, IoT based aquaponics monitoring system, KEC Conference, Lalitpur, Nepal, 2018.",
 "[14] M. C. Bayas, M. T. R. Ponce dkk., Trend forecasting of computer vision application in aquaponic cropping systems industry, IEEE Access, 2021.",
 "[15] W. Yang, S. Wang, X. Zhao, J. Zhang, dan J. Feng, Greenness identification based on HSV decision tree, Inf. Process. Agric., vol. 2, no. 3-4, pp. 277-284, 2015. doi: 10.1016/j.inpa.2015.07.003.",
 "[16] J. G. A. Barbedo, Digital image processing techniques for detecting, quantifying and classifying plant diseases, SpringerPlus, vol. 2, p. 660, 2013. doi: 10.1186/2193-1801-2-660.",
 "[17] J. C. Tovar dkk., Raspberry Pi-powered imaging for plant phenotyping, Appl. Plant Sci., vol. 6, no. 4, 2018. doi: 10.1002/aps3.1031.",
 "[18] X. Zhang, X. Li, B. Zhang, J. Zhou, G. Tian, Y. Xiong, dan B. Gu, Automated robust crop-row detection in maize fields based on position clustering algorithm and shortest path method, Comput. Electron. Agric., 2018. doi: 10.1016/j.compag.2018.09.014.",
 "[19] K. G. Liakos dkk., Machine learning in agriculture: A review, Sensors, vol. 18, no. 8, p. 2674, 2018. doi: 10.3390/s18082674.",
 "[20] A. Kamilaris dan F. X. Prenafeta-Boldú, Deep learning in agriculture: A survey, Comput. Electron. Agric., 2018. doi: 10.1016/j.compag.2018.02.016.",
 "[21] A. Perez-Marin, A. J. Slater dkk., Using deep learning to predict plant growth and yield in greenhouse environments, arXiv:1907.00624, 2019.",
 "[22] P. Mane, V. Agrawal dkk., Deep learning-based prediction of plant height and crown area of vegetable crops using LiDAR point cloud, Sci. Rep., vol. 14, 2024. doi: 10.1038/s41598-024-59643-8.",
 "[23] I. Athanasiadis dkk., An autoencoder wavelet based deep neural network with attention mechanism for multistep prediction of plant growth, arXiv:2012.04041, 2020.",
 "[24] J. Canny, A computational approach to edge detection, IEEE Trans. Pattern Anal. Mach. Intell., vol. 8, no. 6, pp. 679-698, 1986. doi: 10.1109/TPAMI.1986.4767851.",
 "[25] R. R. Shamshiri dkk., Advances in greenhouse automation and controlled environment agriculture: A transition to plant factories and urban agriculture, Int. J. Agric. Biol. Eng., vol. 11, no. 1, 2018. doi: 10.25165/j.ijabe.20181101.3210.",
 "[26] A. F. A. Netto dkk., Segmentation of RGB images using different vegetation indices and thresholding methods, Nativa, vol. 6, no. 4, 2018. doi: 10.31413/nativa.v6i4.5405.",
]


def tahap6c(doc):
    # Gaya Rafly: "DAFTAR PUSTAKA" BUKAN heading (14pt bold halaman baru),
    # melainkan baris teks biasa 12pt non-bold rata kiri yang menempel di
    # akhir Bab III (tanpa page break).
    h = add_para(doc, 32, "DAFTAR PUSTAKA")
    h.style = doc.styles["Normal"]
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    strip_numbering(h)
    for r in h.runs:
        r.bold = False
        r.font.size = Pt(12)
    for sit in SITASI:
        p = add_para(doc, 33, sit)
        # Entri pustaka TANPA bold dan TANPA penomoran daftar otomatis (1.x dari
        # numId 1 template); nomor sitasi [n] sudah tertulis di awal teks.
        # Hanging indent 24pt (0,85 cm) spt dokumen Rafly: baris lanjutan
        # menjorok, nomor [n] tetap di tepi kiri.
        strip_numbering(p)
        for r in p.runs:
            r.bold = False
        pf = p.paragraph_format
        pf.left_indent = Pt(24)
        pf.first_line_indent = Pt(-24)
# ---------------- Patch final (= tmp_patchfinal.py + tmp_final.py) ----------------
# P7 format 'oleh' + newline seperti template; P40 sisa fuzzy -> CV;
# Daftar Istilah sebagai tabel 9x3 (singkatan/kepanjangan/keterangan).
CV40 = "Dengan demikian, prototipe yang dikembangkan berfokus pada sistem monitoring kelayakan panen akuaponik yang menilai 24 zona bak tanam dari kamera tampak atas. Sistem dirancang memakai deteksi bed otomatis, segmentasi HSV adaptif iluminasi beserta perata Exponential Moving Average (EMA), pengukuran kuning dan cokelat per zona, serta PSI beserta PSI maksimum zona terburuk yang dikirim sebagai payload Firebase pada koleksi bed_readings. Struktur tersebut ditujukan agar prototipe dapat diuji sebagai suatu proses kerja terintegrasi dan parameternya dapat dikonfigurasi kembali sesuai karakteristik komoditas maupun instalasi akuaponik yang digunakan."
SINGKATAN = [
 "HSV: Hue Saturation Value, ruang warna yang dipakai segmentasi.",
 "EMA: Exponential Moving Average, perata temporal pada Persamaan 2.5.",
 "PSI: Plant Stress Index, indeks stres 0-100 pada Persamaan 2.6.",
 "F1: harmonic mean presisi-recall, metrik evaluasi pada Persamaan 2.8.",
 "IoU: Intersection over Union, metrik evaluasi pada Persamaan 2.9.",
 "RPi: Raspberry Pi, komputer papan tunggal 4B yang dipakai deploy.",
 "CSI: Camera Serial Interface, antar muka kamera ov5647.",
 "URL: Uniform Resource Locator, alamat dokumen Firestore dan Storage.",
]
# Tabel 9x3 (header + 8 baris) untuk Daftar Istilah dan Singkatan.
ISTILAH_TABEL = [("Singkatan", "Kepanjangan", "Keterangan")]
for s in SINGKATAN:
    ab, sisa = s.split(": ", 1)
    kep, ket = sisa.split(", ", 1)
    ISTILAH_TABEL.append((ab, kep, ket.rstrip(".")))


def tahap_patch(doc):
    p7 = doc.paragraphs[7]
    for r in p7.runs:
        r.text = ""
    p7.runs[0].text = "oleh"
    p7.runs[1].text = "\n"
    p7.runs[2].text = "\nFelix Enrique "
    p7.runs[3].text = "\nNIM. 2305110019"
    p40 = doc.paragraphs[40]
    set_text(p40, CV40)
    ital(p40, ["Exponential Moving Average", "bed_readings"])
    p28 = doc.paragraphs[28]
    p28.runs[0].text = "DAFTAR ISTILAH DAN SINGKATAN"
    for r in p28.runs[1:]:
        r.text = ""
    # Daftar Istilah berupa TABEL 9x3 (header + 8 baris) menggantikan 8 paragraf
    # pada build lama. Paragraf kosong setelah tabel menampung section break
    # roman (t8) dan memberi jarak sebelum heading BAB 1 pada body.
    tbl = doc.add_table(rows=len(ISTILAH_TABEL), cols=3)
    tbl.style = "Table Grid"
    for i, row in enumerate(ISTILAH_TABEL):
        for j, v in enumerate(row):
            tbl.cell(i, j).text = v
    p28._p.addnext(tbl._tbl)
    # paragraf kosong TANPA gambar & tanpa sectPr (hindari klon logo/materai)
    emp = deepcopy(next(p for p in doc.paragraphs if p.text == ""
                        and p._p.find(".//" + qn("w:drawing")) is None
                        and p._p.find(".//" + qn("w:sectPr")) is None)._p)
    tbl._tbl.addnext(emp)
# ---------------- Tahap 7 (= tmp_t7.py + tmp_t7b.py): struktur akhir ----------------
def tahap7struct(doc):
    body = doc.element.body
    ps = doc.paragraphs
    dups = [p for p in ps if p.text.startswith("Dengan demikian")]
    assert len(dups) == 2, f"duplikat: {len(dups)}"
    i2 = [i for i, p in enumerate(ps) if p.text == dups[1].text][1]
    ps = doc.paragraphs
    to_del = []
    if ps[i2 - 1].text.strip() == "":
        to_del.append(ps[i2 - 1])
    if ps[i2 - 2].text.strip() == "":
        to_del.append(ps[i2 - 2])
    to_del.append(ps[i2])
    if ps[i2 + 1].text.strip() == "" and not ps[i2 + 1].text.startswith("Rumusan"):
        to_del.append(ps[i2 + 1])
    for p in to_del:
        delete_p(p)
    sect = body.find(qn("w:sectPr"))
    assert sect is not None
    body.remove(sect)
    body.append(sect)

    def tbl_first_cell(el):
        t = el.findall(".//" + qn("w:tr"))[0]
        r0 = t.findall(qn("w:tc"))[0]
        return "".join(n.text or "" for n in r0.findall(".//" + qn("w:t"))).strip()

    tbl_by_key = {}
    for el in list(body):
        if el.tag == qn("w:tbl"):
            tbl_by_key[tbl_first_cell(el)] = el
    for cap_prefix, key in [("Tabel 2.1", "Kajian"), ("Tabel 3.1", "Perangkat"),
                            ("Tabel 3.2", "Perangkat lunak"), ("Tabel 3.3", "Skenario")]:
        cap = find_p(doc, cap_prefix)
        el = tbl_by_key[key]
        parent = el.getparent()
        if parent is not None:
            parent.remove(el)
        cap._p.addnext(el)

    toc_bab3 = find_p(doc, "BAB III  METODE PELAKSANAAN")
    entry_src = find_p(doc, "HALAMAN JUDUL")
    np2 = clone_with_text(doc, entry_src, "DAFTAR PUSTAKA ................................................................................. 14")
    toc_bab3._p.addnext(np2._p)
    heads_gambar = [p for p in doc.paragraphs if p.text.strip() == "DAFTAR GAMBAR"]
    assert len(heads_gambar) == 1, len(heads_gambar)
    p_gambar_tpl = heads_gambar[0]
    heads_istilah = [p for p in doc.paragraphs if p.text.strip() == "DAFTAR ISTILAH DAN SINGKATAN"]
    assert len(heads_istilah) == 2, len(heads_istilah)
    p_ist_keep, p_ist_del = None, None
    for h in heads_istilah:
        nxt = h._p.getnext()
        # heading aktif diikuti tabel istilah (bentuk baru) atau paragraf "HSV:"
        if nxt is not None and nxt.tag == qn("w:tbl"):
            p_ist_keep = h
        elif nxt is not None and Paragraph(nxt, doc).text.startswith("HSV:"):
            p_ist_keep = h
        else:
            p_ist_del = h
    assert p_ist_keep is not None
    target = p_ist_keep._p
    block = [clone_with_text(doc, p_gambar_tpl, "DAFTAR TABEL")]
    for teks in [
        "Tabel 1.1  Perbandingan Dengan Produk Lain ................................................... 5",
        "Tabel 2.1  Perbandingan Penelitian Terdahulu ..................................................... 7",
        "Tabel 3.1  Daftar Perangkat Keras .................................................................. 13",
        "Tabel 3.2  Daftar Perangkat Lunak .................................................................. 13",
        "Tabel 3.3  Skenario Pengujian Kelayakan Prototipe .............................................. 14",
    ]:
        block.append(clone_with_text(doc, entry_src, teks))
    block.append(clone_with_text(doc, p_gambar_tpl, "DAFTAR GAMBAR"))
    for teks in [
        "Gambar 3.1  Blok Diagram Sistem .................................................................. 10",
        "Gambar 3.2  Diagram Alir Pipeline .................................................................. 11",
        "Gambar 3.3  Skema Pemasangan Kamera ........................................................... 12",
        "Gambar 3.4  Bukti Asli Frame HP vs Pipeline ...................................................... 12",
        "Gambar 3.5  Bukti Asli Frame Video vs Segmentasi .......................................... 13",
    ]:
        block.append(clone_with_text(doc, entry_src, teks))
    for nb in block:
        target.addprevious(nb._p)
    delete_p(p_gambar_tpl)
    delete_p(p_ist_del)


def tahap7bspasi(doc):
    ps = doc.paragraphs
    i_penutup = next(i for i, p in enumerate(ps) if p.text.startswith("Dengan demikian"))
    i_rumusan = next(i for i, p in enumerate(ps) if p.text.strip().endswith("Rumusan Masalah"))
    if i_rumusan == i_penutup + 1:
        i_blank = next(i for i, p in enumerate(ps) if p.text.strip() == "" and i > i_rumusan)
        np_ = deepcopy(ps[i_blank]._p)
        ps[i_rumusan]._p.addprevious(np_)
    # Pastikan semua paragraf "Pengembangan lebih lanjut" di akhir bagian 1.5
    # yang BELUM jadi heading berformat teks biasa: tidak bold, tidak center,
    # rata kiri/justify, sehingga menyatu dengan paragraf sebelumnya.
    # Paragraf yang sudah berupa heading (1.5.3 Pengembangan lebih lanjut)
    # ditangani oleh tahap_struktur_mirza (Heading 3) dan tidak diubah di sini.
    for p in ps:
        if "Pengembangan lebih lanjut" in p.text:
            if p.style.style_id.startswith("Heading"):
                continue
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in p.runs:
                r.bold = False
    # Hapus duplikasi teks lama "Pengembangan lebih lanjut dapat diarahkan pada..."
    # yang tersisa sebagai paragraf biasa (bukan heading), karena kini diformat
    # sebagai sub-bab 1.5.3 di paragraf lain.
    for p in list(ps):
        if ("Pengembangan lebih lanjut dapat diarahkan pada" in p.text
                and not p.style.style_id.startswith("Heading")):
            delete_p(p)


# ---------------- Tahap 8: rapikan Daftar Isi/Tabel/Gambar ----------------
# Masalah build bertahap: (1) tiap entri daftar memakai titik literal "....." TANPA
# tab stop sehingga nomor halaman wrap ke baris kedua; (2) section break (sectPr
# lowerRoman) menempel di paragraf heading bukan entri terakhir sehingga entri
# berserak antar halaman; (3) Daftar Isi tanpa sub-entri; (4) entri LAMPIRAN
# malformasi (bold/center/14pt bertitik). Tahap ini membangun ulang SELURUH wilayah
# front matter dengan tab stop kanan ber-dot-leader, sub-entri, dan section break
# yang benar. Nomor halaman body (arabic, restart di 1) & roman front matter diambil
# dari keluaran Word build saat ini; isi body tidak berubah jadi angka stabil.

# (judul, halaman, level-indent)
# Nomor hal = posisi AKTUAL hasil render Word (diverifikasi via ekspor PDF),
# menyesuaikan penambahan page break awal tiap bab.
DAFTAR_ISI = [
    ("HALAMAN JUDUL", "i", 0),
    ("PERSETUJUAN PEMBIMBING", "ii", 0),
    ("DAFTAR ISI", "iii", 0),
    ("DAFTAR TABEL", "v", 0),
    ("DAFTAR GAMBAR", "vi", 0),
    ("DAFTAR ISTILAH DAN SINGKATAN", "vii", 0),
    ("BAB I  PENDAHULUAN", "1", 0),
    ("1.1  Latar Belakang", "1", 1),
    ("1.2  Rumusan Masalah", "3", 1),
    ("1.3  Tujuan Prototipe", "3", 1),
    ("1.4  Manfaat Prototipe", "4", 1),
    ("1.5  Potensi Dampak Fungsional/Komersial", "6", 1),
    ("1.5.1  Potensi Dampak Fungsional", "6", 1),
    ("1.5.2  Potensi Dampak Komersial", "7", 1),
    ("1.5.3  Pengembangan lebih lanjut", "7", 1),
    ("BAB II  KAJIAN PUSTAKA", "9", 0),
    ("2.1  Tinjauan Pustaka", "9", 1),
    ("2.2  Landasan Teoretik", "10", 1),
    ("2.2.1  Deteksi Tepi Canny dan Aproksimasi Quad", "10", 2),
    ("2.2.2  Ruang Warna HSV dan Segmentasi Vegetasi", "11", 2),
    ("2.2.3  Adaptasi Iluminasi dan Perata Temporal EMA", "11", 2),
    ("2.2.4  Liputan Kanopi dan Indeks Stres Tanaman", "11", 2),
    ("2.2.5  Metrik Evaluasi Segmentasi", "12", 2),
    ("BAB III  METODE PELAKSANAAN", "13", 0),
    ("3.1  Pendekatan Perancangan", "13", 1),
    ("3.2  Lokasi dan Waktu", "13", 1),
    ("3.3  Prosedur Perancangan", "13", 1),
    ("3.3.1  Arsitektur Sistem", "14", 2),
    ("3.3.2  Diagram Alir", "15", 2),
    ("3.3.3  Skema Pemasangan", "16", 2),
    ("3.3.4  Prinsip Kerja Algoritma", "16", 2),
    ("3.4  Bahan dan Alat", "17", 1),
    ("3.5  Metrik dan Skenario Pengujian", "18", 1),
    ("DAFTAR PUSTAKA", "19", 0),
    ("LAMPIRAN", "21", 0),
]

DAFTAR_TABEL = [
    ("Tabel 1.1  Perbandingan Dengan Produk Lain", "7"),
    ("Tabel 2.1  Perbandingan Penelitian Terdahulu", "9"),
    ("Tabel 3.1  Daftar Perangkat Keras", "17"),
    ("Tabel 3.2  Daftar Perangkat Lunak", "17"),
    ("Tabel 3.3  Skenario Pengujian Kelayakan Prototipe", "18"),
]

DAFTAR_GAMBAR = [
    ("Gambar 3.1  Blok Diagram Sistem", "14"),
    ("Gambar 3.2  Diagram Alir Pipeline", "15"),
    ("Gambar 3.3  Skema Pemasangan Kamera", "16"),
    ("Gambar 3.4  Bukti Asli Frame HP vs Pipeline", "16"),
    ("Gambar 3.5  Bukti Asli Frame Video vs Segmentasi", "17"),
]
def _set_entry(p, judul, halaman, level=0):
    """Ubah paragraf entri daftar menjadi: judul <TAB-kanan-dot-leader> halaman.

    Hapus run lama + sectPr lama, pasang satu tab stop kanan ber-dot-leader di
    margin kanan (lebar teks 5.512 in), lalu tulis judul, tab, nomor halaman.
    Sub-entri (level 1/2) diberi indent kiri agar sesuai kaidah penulisan.
    """
    pPr = p._p.get_or_add_pPr()
    for sect in pPr.findall(qn("w:sectPr")):
        pPr.remove(sect)
    for tabs in pPr.findall(qn("w:tabs")):
        pPr.remove(tabs)
    if level:
        ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), str(int(level * 0.25 * 1440)))
        pPr.append(ind)
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "right")
    tab.set(qn("w:leader"), "dot")
    # Sedikit di dalam margin kanan (5.49 in) agar nomor 2-digit tak overflow
    # dan wrap ke baris kedua saat bersebelahan dengan section break.
    tab.set(qn("w:pos"), "7900")
    tabs.append(tab)
    pPr.append(tabs)
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    r1 = p.add_run(judul)
    r1.add_tab()
    p.add_run(halaman)
    return p


def _strip_sect(p):
    pPr = p._p.find(qn("w:pPr"))
    if pPr is not None:
        for sect in pPr.findall(qn("w:sectPr")):
            pPr.remove(sect)


def _put_sect(p, sect_tpl):
    """Pasang sectPr (section break) pada paragraf p (hapus yang lama dulu)."""
    pPr = p._p.get_or_add_pPr()
    for sect in pPr.findall(qn("w:sectPr")):
        pPr.remove(sect)
    pPr.append(deepcopy(sect_tpl))


def tahap_daftar_rapi(doc):
    ps = list(doc.paragraphs)

    # templat entri & heading (dipakai untuk klon baru)
    entry_tpl = next(p for p in ps if p.text.startswith("HALAMAN JUDUL"))
    head_tpl = next(p for p in ps if p.text.strip() == "DAFTAR GAMBAR")

    # templat sectPr lowerRoman untuk dipakai ulang sebagai section break
    sect_tpl = None
    for p in ps:
        pPr = p._p.find(qn("w:pPr"))
        if pPr is not None:
            s = pPr.find(qn("w:sectPr"))
            if s is not None and s.find(qn("w:pgNumType")) is not None:
                sect_tpl = deepcopy(s)
                break
    assert sect_tpl is not None, "template sectPr lowerRoman tidak ditemukan"

    # penanda wilayah front matter (heading, bukan entri TOC bertitik)
    def idx(pred, start=0):
        for i, p in enumerate(ps):
            if i >= start and pred(p):
                return i
        return None

    i_head_isi = idx(lambda p: p.text.strip() == "DAFTAR ISI")
    assert i_head_isi is not None
    i_dt = idx(lambda p: p.text.strip() == "DAFTAR TABEL", i_head_isi)
    i_dg = idx(lambda p: p.text.strip() == "DAFTAR GAMBAR", i_head_isi)
    i_di = idx(lambda p: p.text.strip() == "DAFTAR ISTILAH DAN SINGKATAN", i_head_isi)
    i_lamp = idx(lambda p: p.text.strip().startswith("LAMPIRAN ") and ".." in p.text, i_head_isi)
    assert None not in (i_dt, i_dg, i_di), (i_dt, i_dg, i_di)

    # hapus: entri TOC lama (setelah heading DAFTAR ISI s/d sebelum DAFTAR TABEL),
    # blok DAFTAR TABEL (heading+entri) s/d sebelum DAFTAR GAMBAR, blok DAFTAR GAMBAR
    # (heading+entri) s/d sebelum DAFTAR ISTILAH, dan entri LAMPIRAN malformasi.
    # Blok DAFTAR ISTILAH (heading + singkatan) DIPERTAHANKAN.
    to_delete = list(range(i_head_isi + 1, i_dt))
    to_delete += list(range(i_dt, i_dg))
    to_delete += list(range(i_dg, i_di))
    if i_lamp is not None:
        to_delete.append(i_lamp)
    for i in sorted(set(to_delete), reverse=True):
        ps[i]._p.getparent().remove(ps[i]._p)

    # bangun ulang, sisipkan berurutan SEBELUM heading DAFTAR ISTILAH
    anchor = next(p for p in doc.paragraphs
                  if p.text.strip() == "DAFTAR ISTILAH DAN SINGKATAN")

    def clone_entry():
        np_ = Paragraph(deepcopy(entry_tpl._p), doc)
        _strip_sect(np_)
        return np_

    def clone_head(text):
        np_ = Paragraph(deepcopy(head_tpl._p), doc)
        _strip_sect(np_)
        for r in list(np_.runs):
            r._r.getparent().remove(r._r)
        np_.add_run(text)
        return np_

    blocks = []
    for judul, hal, lvl in DAFTAR_ISI:
        blocks.append(_set_entry(clone_entry(), judul, hal, lvl))
    blocks.append(clone_head("DAFTAR TABEL"))
    for judul, hal in DAFTAR_TABEL:
        blocks.append(_set_entry(clone_entry(), judul, hal, 0))
    blocks.append(clone_head("DAFTAR GAMBAR"))
    for judul, hal in DAFTAR_GAMBAR:
        blocks.append(_set_entry(clone_entry(), judul, hal, 0))
    for b in blocks:
        anchor._p.addprevious(b._p)

    # section break (roman) pada ENTRI TERAKHIR tiap bagian front matter
    ps = list(doc.paragraphs)
    i_dt2 = next(i for i, p in enumerate(ps) if p.text.strip() == "DAFTAR TABEL")
    _put_sect(ps[i_dt2 - 1], sect_tpl)  # akhir Daftar Isi (entri LAMPIRAN)

    ps = list(doc.paragraphs)
    i_dg2 = next(i for i, p in enumerate(ps) if p.text.strip() == "DAFTAR GAMBAR")
    _put_sect(ps[i_dg2 - 1], sect_tpl)  # akhir Daftar Tabel

    # akhir Daftar Gambar = entri sebelum heading DAFTAR ISTILAH. Heading DAFTAR
    # ISTILAH membawa sectPr sisa template; pindahkan ke entri singkatan TERAKHIR
    # (URL) agar seluruh blok Daftar Istilah tetap dalam section roman, bukan
    # tercecer ke section body (arabic).
    ps = list(doc.paragraphs)
    i_di2 = next(i for i, p in enumerate(ps)
                 if p.text.strip() == "DAFTAR ISTILAH DAN SINGKATAN")
    _put_sect(ps[i_di2 - 1], sect_tpl)      # akhir Daftar Gambar (Gambar 3.5)
    _strip_sect(ps[i_di2])                  # buang sectPr sisa di heading istilah
    # akhir Daftar Istilah = paragraf kosong setelah tabel singkatan
    # (satu-satunya w:p antara tabel dan heading body BAB I)
    i_body2 = next(i for i, p in enumerate(ps) if p.text == "BAB I\nPENDAHULUAN")
    _put_sect(ps[i_body2 - 1], sect_tpl)    # akhir Daftar Istilah (paragraf kosong)

    # perbaiki caption Tabel 1.1 yang hilang di body. Templat caption diambil
    # dari caption body Tabel 2.1 (paragraf justify bold, BUKAN entri Daftar
    # Tabel bertab). Bedakan: entri daftar memuat karakter tab / berakhiran
    # nomor halaman; caption body tidak.
    def is_body_caption(p, prefix):
        t = p.text
        return t.strip().startswith(prefix) and "\t" not in t and "...." not in t

    cap2 = next((p for p in doc.paragraphs if is_body_caption(p, "Tabel 2.1")), None)
    if cap2 is not None and not any(
            is_body_caption(p, "Tabel 1.1") for p in doc.paragraphs):
        for tbl in doc.tables:
            if tbl.rows[0].cells[0].text.strip() == "Nama Produk":
                cap = Paragraph(deepcopy(cap2._p), doc)
                for r in list(cap.runs):
                    r._r.getparent().remove(r._r)
                cap.add_run("Tabel 1.1  Perbandingan Dengan Produk Lain")
                tbl._tbl.addprevious(cap._p)
                break


# ---------------- main + verifikasi ----------------
TAHAP = [
 ("t1 judul", tahap1), ("t2 profil", tahap2),
 ("t3a latar", tahap3a), ("t3b rumusan/tujuan", tahap3b),
 ("t3c manfaat", tahap3c), ("t3d dampak", tahap3d), ("t3e tabel1.1", tahap3e),
 ("t4a bab2-awal", tahap4a), ("t4b tabel2.1", tahap4b), ("t4cd landasan", tahap4cd),
 ("t5a bab3-pendekatan/lokasi/prosedur", tahap5a),
 ("t5b 3.3.1 arsitektur+g3.1", tahap5b),
 ("t5c 3.3.2/3.3.3 alir+g3.2/skema+g3.3", tahap5c),
 ("t5d1 3.3.4 kerja+g3.4/3.5", tahap5d1),
 ("t5e 3.4 bahan/alat+tabel3.1/3.2", tahap5e),
 ("t5d2 3.5 metrik+tabel3.3", tahap5d2),
 ("t6b TOC", tahap6b), ("t6c pustaka", tahap6c),
 ("t6L lampiran", tahap_lampiran),
 ("patch P7/P40/istilah-tabel", tahap_patch),
 ("tN nomor-heading", tahap_heading_numbering),
 ("t7 struktur", tahap7struct), ("t7b spasi", tahap7bspasi),
 ("t8 daftar-rapi", tahap_daftar_rapi),
 ("tN normalize-format", tahap_normalize_format),
 ("tN struktur-mirza", tahap_struktur_mirza),
 ("tN judul-persetujuan", tahap_judul_persetujuan),
 ("tN spasi-rafly", tahap_spasi_rafly),
 ("tN font-times-new-roman", set_font_times_new_roman),
 ("tN rapihkan-sitasi", rapihkan_sitasi),
]


def doc_signature(path):
    """Sidik deterministik: teks body berurutan + tabel + gambar + style ids.

    Bukan hash biner zip (docx menyimpan timestamp/rid acak), melainkan isi
    semantik: urutan paragraf (teks, style, alignment, flag gambar), sel tabel,
    dan ukuran gambar - cukup untuk membuktikan hasil identik.
    """
    from lxml import etree
    d = Document(str(path))
    parts = []
    for el in d.element.body.iterchildren():
        if el.tag == qn("w:p"):
            runs = []
            for r in el.findall(".//" + qn("w:r")):
                t = "".join(n.text or "" for n in r.findall(qn("w:t")))
                b = r.find(qn("w:rPr") + "/" + qn("w:b")) is not None
                i = r.find(qn("w:rPr") + "/" + qn("w:i")) is not None
                runs.append(f"{t}|b={b},i={i}")
            pstyle = el.find(qn("w:pPr") + "/" + qn("w:pStyle"))
            jc = el.find(qn("w:pPr") + "/" + qn("w:jc"))
            img = f"IMGx{len(el.findall('.//' + qn('w:drawing')))}"
            if runs or img != "IMGx0":
                sty = pstyle.get(qn("w:val")) if pstyle is not None else "-"
                al = jc.get(qn("w:val")) if jc is not None else "-"
                parts.append("P[" + sty + "/" + al + "/" + img + "]" + "\n".join(runs))
        elif el.tag == qn("w:tbl"):
            cells = ["|".join("".join(n.text or "" for n in c.findall(".//" + qn("w:t")))
                               for c in tr.findall(qn("w:tc")))
                     for tr in el.findall(".//" + qn("w:tr"))]
            parts.append("TBL:" + "\n".join(cells))
        elif el.tag == qn("w:sectPr"):
            parts.append("SECTPR")
    for shp in d.inline_shapes:
        parts.append(f"PIC:{shp.width.emu}x{shp.height.emu}")
    return sha256("\n".join(parts).encode("utf-8")).hexdigest()


def verify(path):
    d = Document(str(path))
    teks = " ".join(p.text for p in d.paragraphs)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                teks += " " + c.text
    # paragraf front matter (sebelum heading body "BAB I\nPENDAHULUAN")
    i_body = next(i for i, p in enumerate(d.paragraphs)
                  if p.text == "BAB I\nPENDAHULUAN")
    front = d.paragraphs[:i_body]
    # Heading front matter yang BUKAN entri daftar (tak bertitik/tab):
    HEAD_DAFTAR = ("DAFTAR ISI", "DAFTAR TABEL", "DAFTAR GAMBAR",
                   "DAFTAR ISTILAH DAN SINGKATAN", "PERSETUJUAN PEMBIMBING")
    # Entri daftar = paragraf front matter bergaya entri (judul + nomor hal).
    # Semua entri daftar WAJIB memakai tab (bukan titik literal).
    calon_entri = [p for p in front
                   if p.text.strip() and p.text.strip() not in HEAD_DAFTAR
                   and p.text.startswith(("HALAMAN JUDUL", "BAB ",
                                          "1.", "2.", "3.", "DAFTAR PUSTAKA",
                                          "LAMPIRAN", "Tabel ", "Gambar "))]
    checks = {
        "kata>=4200": len(teks.split()) >= 4200,
        "Felix==3": teks.count("Felix Enrique") == 3,
        "NIM==3": teks.count("2305110019") == 3,
        "tanpa Rafly/Sugeno": ("Rafly" not in teks and "Sugeno" not in teks),
        "tanpa pH-sisa": not re.findall(r"sensor pH|pH, kekeruhan|kendali pH|pergantian air", teks),
        "1x Dengan demikian": sum(1 for p in d.paragraphs
                                  if p.text.startswith("Dengan demikian")) == 1,
        "tabel==7": len(d.tables) == 7,
        "tabel istilah 9x3": any(len(t.rows) == 9 and len(t.columns) == 3
            and t.rows[0].cells[0].text.strip() == "Singkatan"
            and t.rows[8].cells[0].text.strip() == "URL" for t in d.tables),
        "gambar==10": len(d.inline_shapes) == 10,
        "BAB I/II/III": all(("BAB %s\n" % x) in teks for x in ("I", "II", "III")),
        "DAFTAR PUSTAKA": "DAFTAR PUSTAKA" in teks,
        "LAMPIRAN": "LAMPIRAN" in teks,
        "Gambar L.1": "Gambar L.1" in teks,
        "Bab3 3.1-3.5": all(t in teks for t in
            ("3.1  Pendekatan Perancangan", "3.2  Lokasi dan Waktu",
             "3.3  Prosedur Perancangan", "3.4  Bahan dan Alat",
             "3.5  Metrik dan Skenario Pengujian")),
        "Bab3 3.3.1-3.3.4": all(t in teks for t in
            ("3.3.1  Arsitektur Sistem", "3.3.2  Diagram Alir",
             "3.3.3  Skema Pemasangan", "3.3.4  Prinsip Kerja Algoritma")),
        "Bab2 2.1/2.2/2.2.x": all(t in teks for t in
            ("2.1  Tinjauan Pustaka", "2.2  Landasan Teoretik",
             "2.2.1  Deteksi Tepi", "2.2.2  Ruang Warna",
             "2.2.3  Adaptasi Iluminasi", "2.2.4  Liputan Kanopi",
             "2.2.5  Metrik Evaluasi")),
        "Bab1 1.1-1.5": all(t in teks for t in
            ("1.1  Latar Belakang", "1.2  Rumusan Masalah",
             "1.3  Tujuan Prototipe", "1.4  Manfaat Prototipe",
             "1.5  Potensi Dampak")),
        "heading bab tak bernomor-otomatis": not any(
            el.find(".//" + qn("w:numId")) is not None and
            el.find(".//" + qn("w:numId")).get(qn("w:val")) == "1" and
            el.find(".//" + qn("w:t")) is not None and
            el.find(".//" + qn("w:t")).text in ("BAB I", "BAB II", "BAB III",
                "DAFTAR PUSTAKA")
            for el in d.element.body.findall(qn("w:p"))),
        # --- Tahap struktur gaya Rafly ---
        "judul bab digabung": all(
            any(p.text == "BAB %s\n%s" % (n, j) for p in d.paragraphs)
            for n, j in (("I", "PENDAHULUAN"), ("II", "KAJIAN PUSTAKA"),
                         ("III", "METODE PELAKSANAAN"))),
        "bab pakai Heading1 hitam": all(
            p.style.style_id == "Heading1" and
            all(r.font.color.rgb == RGBColor(0, 0, 0) for r in p.runs if r.text)
            for p in d.paragraphs
            if p.text.startswith(("BAB I\n", "BAB II\n", "BAB III\n"))),
        "pustaka bukan heading (gaya Rafly)": all(
            p.style.style_id != "Heading1"
            for p in d.paragraphs if p.text.strip() == "DAFTAR PUSTAKA"),
        "sub-bab pakai Heading2/3": all(
            p.style.style_id in ("Heading2", "Heading3")
            for p in d.paragraphs[i_body:]
            if re.match(r"^\d+\.\d+(\.\d+)?\s", p.text.strip())),
        "bab pakai Romawi": re.search(r"BAB (I|II|III)\b", teks) is not None,
        "tanpa BAB angka-arab": not re.search(r"BAB [123]\b", teks),
        "tanpa Bab 4": not re.findall(r"\bBab 4\b", teks),
        "sitasi [8]/[17]": ("Wan dkk. [8]" in teks and "Tovar dkk. [17]" in teks
            and "Wan dkk. [24]" not in teks and "Tovar dkk. [8]" not in teks),
        "26 sitasi dikutip di body": all(("[%d]" % n) in teks.rsplit("DAFTAR PUSTAKA", 1)[0]
            for n in range(1, 27)),
        "Canny [24]": "Detektor Canny [24]" in teks,
        "nama lokasi": "Aquaponik Eco Farm Universitas Negeri Semarang" in teks,
        "°C dan ×": ("°C" in teks and "4×6" in teks
            and "derajat Celsius" not in teks and "grid 4x6" not in teks),
        "sectPr terakhir": d.element.body[-1].tag == qn("w:sectPr"),
        "daftar tabel/gambar/istilah": all(
            s in teks for s in ("DAFTAR TABEL", "DAFTAR GAMBAR",
                                "DAFTAR ISTILAH DAN SINGKATAN")),
        # --- Tahap 8: daftar rapi ---
        # Entri DAFTAR (front matter) memakai tab kanan ber-dot-leader + nomor
        # halaman (bukan titik literal); judul sama di body (heading) tak bertab.
        "entri daftar pakai TAB (bukan titik)": calon_entri and all(
            "\t" in p.text and "...." not in p.text for p in calon_entri),
        "tanpa titik literal di entri daftar": not any(
            "...." in p.text for p in calon_entri),
        "Daftar Isi punya sub-entri": all(
            any(p.text.startswith(pref) for p in d.paragraphs)
            for pref in ("1.1  Latar Belakang", "2.1  Tinjauan Pustaka",
                         "3.3.1  Arsitektur Sistem")),
        "caption Tabel 1.1 di body": any(
            p.text.strip().startswith("Tabel 1.1") and "\t" not in p.text
            and "...." not in p.text for p in d.paragraphs),
        "4 sectPr front matter": sum(
            1 for el in d.element.body.findall(qn("w:p"))
            if el.find(qn("w:pPr")) is not None
            and el.find(qn("w:pPr")).find(qn("w:sectPr")) is not None) == 4,
        # Setiap judul bab wajib memakai w:pageBreakBefore sehingga bab baru
        # selalu dimulai di halaman sendiri. DAFTAR PUSTAKA (gaya Rafly) menempel
        # di akhir Bab III tanpa page break - karenanya tidak dicakup cek ini.
        "bab mulai halaman baru": all(
            p._p.find(qn("w:pPr")) is not None
            and p._p.find(qn("w:pPr")).find(qn("w:pageBreakBefore")) is not None
            for p in d.paragraphs
            if p.text.startswith(("BAB I\n", "BAB II\n", "BAB III\n"))
            and p.style.style_id in ("Heading1",)
        ) and all(
            p._p.find(qn("w:pPr")) is not None
            and p._p.find(qn("w:pPr")).find(qn("w:pageBreakBefore")) is not None
            for p in d.paragraphs if p.text.strip() == "LAMPIRAN"),
        "pustaka tanpa page-break": all(
            p._p.find(qn("w:pPr")) is None
            or p._p.find(qn("w:pPr")).find(qn("w:pageBreakBefore")) is None
            for p in d.paragraphs if p.text.strip() == "DAFTAR PUSTAKA"),
    }
    for cap, ok in checks.items():
        print(("OK  " if ok else "GAGAL ") + cap)
    return all(checks.values())


def build(out_path):
    shutil.copyfile(str(TPL), str(out_path))
    doc = Document(str(out_path))
    for nama, fn in TAHAP:
        fn(doc)
        print(" -", nama)
    # Set document core properties author
    cp = doc.core_properties
    cp.author = "Felix Enrique"
    cp.last_modified_by = "Felix Enrique"

    # Pastikan semua paragraf "Pengembangan lebih lanjut" di akhir bagian 1.5
    # yang BELUM jadi heading berformat teks biasa: tidak bold, tidak center,
    # rata kiri/justify, sehingga menyatu dengan paragraf sebelumnya.
    # Paragraf yang sudah berupa heading (1.5.3 Pengembangan lebih lanjut)
    # ditangani oleh tahap_struktur_mirza (Heading 3) dan tidak diubah di sini.
    for p in doc.paragraphs:
        if "Pengembangan lebih lanjut" in p.text:
            if p.style.style_id.startswith("Heading"):
                continue
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            for r in p.runs:
                r.bold = False

    doc.save(str(out_path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--compare", nargs=2, metavar=("LAMA", "BARU"), default=None)
    ap.add_argument("--regenerate", action="store_true",
                    help="Tulis ulang OUT dari template (default hanya verify).")
    args = ap.parse_args()
    if args.compare:
        a = doc_signature(args.compare[0])
        b = doc_signature(args.compare[1])
        print("lama:", a)
        print("baru:", b)
        print("IDENTIK" if a == b else "BERBEDA")
        return
    out = Path(args.out) if args.out else OUT
    if args.regenerate:
        build(out)
    assert zipfile.ZipFile(str(out)).testzip() is None
    if not verify(out):
        raise SystemExit("verifikasi GAGAL")
    print("BUILD OK:", out)


if __name__ == "__main__":
    main()
