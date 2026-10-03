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
  t6c     Daftar Pustaka 10 sitasi
  patch   P7 format 'oleh', paragraf sisa fuzzy P40 -> CV, Daftar Singkatan
  reorder urutan singkatan HSV..URL (insert addnext terbalik -> dibalik teks)
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
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches
from docx.text.paragraph import Paragraph

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


def ital(p, words):
    """Cetak miring kata asing; format lain ikut run[0]."""
    full = p.text
    pat = "(" + "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)) + ")"
    parts = [x for x in re.split(pat, full) if x]
    base = p.runs[0]
    base.text = ""
    for i, part in enumerate(parts):
        r = base if i == 0 else p.add_run("")
        if i > 0:
            r.font.name = base.font.name
            r.font.size = base.font.size
            r.bold = base.bold
        r.text = part
        r.italic = part in words


def add_para(doc, ref_idx, text, bold=False, itw=()):
    """Klon pola paragraf template ref_idx, isi teks baru, append ke body."""
    r0 = doc.paragraphs[ref_idx]
    np_ = deepcopy(r0._p)
    for r in np_.xpath(".//w:r"):
        r.getparent().remove(r)
    if itw:
        pat = "(" + "|".join(re.escape(w) for w in sorted(itw, key=len, reverse=True)) + ")"
        parts = [x for x in re.split(pat, text) if x]
    else:
        parts = [text]
    for part in parts:
        re_ = OxmlElement("w:r")
        if r0.runs:
            for ch in r0.runs[0]._r.xpath("./w:rPr/*"):
                re_.append(deepcopy(ch))
        if bold:
            re_.append(OxmlElement("w:b"))
        if part in itw:
            re_.append(OxmlElement("w:i"))
        te = OxmlElement("w:t")
        te.set(XML_SPACE, "preserve")
        te.text = part
        re_.append(te)
        np_.append(re_)
    doc.element.body.append(np_)
    return Paragraph(np_, doc)


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
          "fuzzy_input", "non-maximum suppression", "Hue Saturation Value"]
    L1 = "Sistem akuaponik mengintegrasikan budidaya ikan dan tanaman melalui sirkulasi air yang sama sehingga kondisi air dan kondisi tanaman saling memengaruhi. Pada sistem akuaponik di Eco Farm Universitas Negeri Semarang (UNNES), kolam ikan nila digunakan sebagai sumber air dan nutrisi bagi tanaman kangkung pada bak tanam berukuran 2 m x 1,1 m. Berdasarkan observasi dan wawancara awal dengan pengelola, salah satu persoalan yang ditemukan adalah penilaian kesiapan panen yang masih dilakukan secara visual. Penilaian visual tersebut bersifat subjektif sehingga keputusan panen antarpetani dan antarbed tidak konsisten, sedangkan bed tidak tumbuh seragam antara bagian tepi dan bagian tengah. Akibatnya panen terlalu dini menurunkan biomassa, sedangkan panen yang terlambat menurunkan mutu daun. Permasalahan tersebut menuntut peta kelayakan panen per zona yang objektif dan berulang. Prototipe ini membagi bak tanam menjadi grid 4x6 atau 24 zona dan menilai tiap zona secara terpisah sehingga panen selektif per zona dapat direncanakan."
    L2 = "Risiko panen dinilai dari tutupan kanopi (canopy cover). Tutupan kanopi berkorelasi dengan biomassa dan fase tumbuh sehingga ambang tutupan dipakai sebagai kriteria panen pada berbagai komoditas daun. Tantangan utama pengukuran tutupan di lapangan adalah perubahan iluminasi. Cahaya pagi, siang, dan sore mengubah komponen terang citra sehingga segmentasi warna statis menghasilkan liputan yang melompat walaupun tanamannya sama. Penelitian ini merumuskan faktor adaptasi iluminasi f yang dihitung dari rata-rata komponen Value tiap frame sehingga ambang Saturation dan Value mengikuti kondisi cahaya tanpa menggeser Hue yang menyimpan informasi warna daun. Pendekatan tersebut diuji pada 18 video lapangan dan lima foto bak tahap seedling sampai ready dengan liputan 0,9 persen sampai 22,6 persen."
    L3 = "Gejala daun menguning atau klorosis dan jaringan mati atau nekrosis sering disadari setelah menyebar. Klorosis ditandai pergeseran warna ke rentang kuning, sedangkan nekrosis ditandai bercak cokelat yang menempel pada kanopi. Woebbecke dkk. [4] merumuskan rentang Hue hijau tanaman terhadap tanah dan gulma sebagai dasar segmentasi vegetasi. Prototipe ini memakai rentang kuning H 21-34 dan cokelat H 8-20 yang dinormalkan terhadap ambang sakit 25 persen dan 8 persen menjadi Indeks Stres Tanaman atau Plant Stress Index (PSI) 0-100 sebagai keluaran untuk pengendali. Lima foto lapangan yang tersedia seluruhnya sehat dengan PSI 0-0,1 sehingga foto sakit asli dan mask ground truth lima gambar menjadi agenda validasi berikutnya."
    L4 = "Wan dkk. [1] membangun sistem monitoring akuaponik berbasis komputasi tepi dengan Raspberry Pi dan pengolahan citra untuk pertumbuhan tanaman, tetapi sistem tersebut tidak menilai kelayakan panen per zona dan tidak menangani adaptasi iluminasi. Abbasi dkk. [3] mendeteksi klorosis daun selada akuaponik dari citra warna secara otomatis, tetapi kajian tersebut hanya satu gejala tanpa grid zona. Searson dkk. [2] memakai ruang warna HSV dan operasi morfologi untuk deteksi tanaman di lapangan, tetapi ambangnya statis. Hameed dkk. [5] menentukan ambang vegetasi dari histogram Hue sehingga adaptif terhadap cahaya, tetapi tanpa grid panen dan skor siap kendali. Perbedaan dengan penelitian terdahulu terletak pada gabungan empat hal dalam satu prototipe ringan tanpa pembelajaran mendalam atau deep learning: grid panen per zona, adaptasi iluminasi, skor stres siap kendali, dan paket deploy komputer papan tunggal di lapangan."
    L5 = "Dengan demikian, prototipe yang dikembangkan berfokus pada sistem monitoring kelayakan panen akuaponik yang menilai 24 zona bak tanam dari kamera tampak atas. Sistem dirancang memakai deteksi bed otomatis, segmentasi HSV adaptif iluminasi beserta perata Exponential Moving Average (EMA), pengukuran kuning dan cokelat per zona, serta PSI beserta PSI maksimum zona terburuk yang dikirim sebagai payload Firebase pada koleksi bed_readings. Struktur tersebut ditujukan agar prototipe dapat diuji sebagai suatu proses kerja terintegrasi dan parameternya dapat dikonfigurasi kembali sesuai karakteristik komoditas maupun instalasi akuaponik yang digunakan."
    for idx, teks in zip([33, 34, 35, 36, 37], [L1, L2, L3, L4, L5]):
        set_text(doc.paragraphs[idx], teks)
        ital(doc.paragraphs[idx], IT)
    set_text(doc.paragraphs[38], "")
# ---------------- Tahap 3b (= bangun_felix_t3b.py): rumusan + tujuan ----------------
RUMUSAN = {
 44: "Bagaimana mendeteksi bed dan membagi citra menjadi grid 4x6 secara otomatis dari kamera tampak atas pada bak tanam akuaponik?",
 45: "Bagaimana menstabilkan segmentasi warna Hue Saturation Value (HSV) terhadap perubahan iluminasi pagi, siang, dan sore sehingga liputan kanopi per zona konsisten?",
 50: "Menghasilkan deteksi bed otomatis berbasis tepi Canny, aproksimasi quad, dan homografi empat titik dengan jalur cadangan maska HSV pada bak tanam 2 m x 1,1 m.",
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
# ---------------- Tahap 3d (= bangun_felix_t3d.py): dampak ----------------
DAMPAK82 = "Prototipe yang dirancang memiliki potensi memberikan dampak fungsional pada proses pengelolaan budidaya akuaponik, khususnya dalam menentukan kesiapan panen secara lebih terukur. Keputusan tidak hanya didasarkan pada pengamatan visual, tetapi menggunakan liputan kanopi per zona, status kesehatan daun, dan Indeks Stres Tanaman atau Plant Stress Index (PSI) sebagai keluaran sistem. Peta 24 zona memungkinkan panen selektif pada zona yang siap sedangkan zona yang belum siap dibiarkan tumbuh, sedangkan status sehat, waspada, dan sakit menjadi dasar pemeriksaan lanjutan."
DAMPAK83 = "Penerapan peta zona dalam bentuk status per zona juga memberikan keluaran yang lebih operasional bagi pengelola. Selain itu, sistem dilengkapi arsip runtun waktu per zona dan dasbor dengan grafik 24 jam sehingga tren pertumbuhan tiap zona terpantau. Sementara itu, ambang status 25, 55, dan 80 persen beserta ambang kesehatan kuning 10 dan 25 persen serta cokelat 3 dan 8 persen dapat dikonfigurasi kembali mengikuti hasil validasi ahli."
DAMPAK84 = "Secara fungsional, prototipe juga memiliki potensi untuk diterapkan pada konfigurasi akuaponik yang berbeda melalui proses penyesuaian parameter. Rentang HSV, ambang status, ambang kesehatan, serta parameter ketinggian kamera dapat dikonfigurasi kembali sesuai kebutuhan. Dengan demikian, arsitektur sistem tidak dibatasi hanya pada satu kondisi instalasi, meskipun penerapan pada sistem lain tetap memerlukan proses kalibrasi dan pengujian ulang."
DAMPAK86 = "Dari sisi komersial, prototipe ini memiliki potensi untuk dikembangkan menjadi perangkat pendukung monitoring akuaponik yang menilai kelayakan panen dan kesehatan tanaman dalam satu sistem. Arsitektur yang menggunakan komputer papan tunggal, kamera, rumah kamera cetak tiga dimensi, dan konektivitas Internet of Things memungkinkan sistem dikembangkan secara modular sesuai kebutuhan pengguna dan skala instalasi."
DAMPAK87 = "Pengembangan lebih lanjut dapat diarahkan pada penyederhanaan instalasi, peningkatan keandalan perangkat keras, pengembangan antarmuka pengguna, serta pengujian pada lebih banyak konfigurasi akuaponik. Dengan tahapan tersebut, prototipe dapat menjadi dasar pengembangan produk teknologi monitoring cerdas untuk kebutuhan pendidikan, penelitian, komunitas, maupun pelaku budidaya skala kecil dan menengah. Namun, penerapan secara komersial tetap memerlukan validasi tambahan untuk memastikan keandalan, konsistensi kinerja, kemudahan pemeliharaan, dan kesesuaian sistem terhadap kondisi operasional yang berbeda."


def tahap3d(doc):
    for i, teks in ((82, DAMPAK82), (83, DAMPAK83), (84, DAMPAK84), (86, DAMPAK86), (87, DAMPAK87)):
        set_text(doc.paragraphs[i], teks)


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
 "Wan dkk. [1] membangun sistem monitoring akuaponik berbasis komputasi tepi atau edge computing dengan Raspberry Pi dan pengolahan citra untuk pertumbuhan tanaman. Sistem tersebut membuktikan arsitektur sensor-kamera-komputasi tepi layak untuk akuaponik, tetapi tidak menilai kelayakan panen per zona dan tidak menangani adaptasi iluminasi. Abbasi dkk. [3] mendeteksi klorosis daun selada akuaponik dari citra warna secara otomatis. Kajian tersebut menjadi rujukan terdekat untuk deteksi menguning, tetapi hanya satu gejala dan satu bed tanpa grid zona. Searson dkk. [2] memakai ruang warna HSV dan operasi morfologi untuk deteksi tanaman di lapangan dengan iluminasi alami. Kajian tersebut menjadi dasar segmentasi hijau prototipe ini, tetapi ambangnya statis sehingga liputan melompat ketika cahaya berubah."
)


def tahap4a(doc):
    for teks, bold, itw in [("BAB II", True, ()), ("KAJIAN PUSTAKA", True, ()),
                            ("Tinjauan Pustaka", True, ()), (BAB2_A, False, IT4A)]:
        add_para(doc, 32 if bold else 33, teks, bold, itw)


# ---------------- Tahap 4b (= bangun_felix_t4b.py): Tinjauan + Tabel 2.1 ----------------
IT4B = IT4A + ["approxPolyDP"]
TINJ2 = "Hameed dkk. [5] menentukan ambang vegetasi dari histogram Hue sehingga adaptif terhadap cahaya. Gagasan tersebut dipakai sebagai kerabat faktor adaptasi f pada prototipe ini. Yang dkk. [6] memakai pohon keputusan HSV untuk identifikasi kehijauan dan Barbedo [7] memetakan teknik citra digital untuk deteksi dan kuantifikasi penyakit daun berbasis warna. Kedua kajian tersebut mendukung pemisahan kuning dan cokelat sebagai gejala berbeda. Tovar dkk. [8] memakai Raspberry Pi untuk fenotipe tanaman sehingga mendukung pilihan deploy ringan. Perbandingan posisi penelitian ini terhadap tujuh kajian tersebut diringkas pada Tabel 2.1. Celah yang diisi prototipe ini adalah gabungan grid panen 4x6, adaptasi iluminasi tanpa pembelajaran mendalam, dan skor stres siap kendali dalam satu paket lapangan."
TABEL21 = [
 ["Wan dkk. [1]", "Tepi + citra akuaponik", "Status tumbuh", "Tanpa grid zona dan adaptasi cahaya"],
 ["Abbasi dkk. [3]", "Warna daun selada", "Klorosis", "Satu gejala, tanpa grid dan PSI"],
 ["Searson dkk. [2]", "HSV + morfologi", "Maska tanaman", "Ambang statis, tanpa adaptasi"],
 ["Hameed dkk. [5]", "Ambang histogram Hue", "Maska adaptif", "Tanpa grid panen dan skor kendali"],
 ["Yang dkk. [6]", "Pohon keputusan HSV", "Kehijauan", "Tanpa kuning/cokelat dan deploy"],
 ["Barbedo [7]", "Citra penyakit warna", "Area sakit", "Tanpa grid zona dan paket lapangan"],
 ["Usulan", "HSV adaptif + EMA + grid", "Peta 24 zona + PSI", "Gabungan ketujuh hal di atas"],
]


def tahap4b(doc):
    add_para(doc, 33, TINJ2, False, IT4B)
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
 "deep learning", "recall", "Intersection over Union", "Hue Saturation Value", "hue", "value"]
CH2A = "Detektor Canny (Canny, 1986) mencari tepi melalui gradien multiskala, penekanan nonmaksimum atau non-maximum suppression, dan ambang histeresis. Gradien dihitung dengan operator Sobel pada arah x dan y sehingga magnitudo dan orientasi tiap piksel diperoleh dari Persamaan 2.1 dan 2.2. Kontur terbesar hasil tepi didekati menjadi poligon empat titik dengan approxPolyDP sehingga sudut bed diperoleh walaupun kamera miring."
CH2B = "Empat sudut terurut dipetakan ke persegi 1200x660 dengan homografi planar. Homografi tiga kali tiga atau H memetakan titik sumber p ke titik tujuan p sampai faktor skala s seperti Persamaan 2.3. Bed yang tegak dibagi menjadi grid 4 baris dan 6 kolom sehingga tiap zona R1C1 sampai R4C6 dianalisis terpisah dan liputan adil antarbed."
CH2C = "Ruang HSV memisahkan rona atau Hue dari kejenuhan atau Saturation dan terang atau Value sehingga perubahan cahaya terutama menggeser S dan V sedangkan H menyimpan identitas warna daun (Woebbecke dkk. [4]; Yang dkk. [6]). Maska tanaman dibentuk dari gabungan dua rentang hijau muda H 35-75 dan hijau tua H 36-85 yang digabung dengan operasi logika ATAU seperti Persamaan 2.4. Maska kuning H 21-34 dan cokelat H 8-20 dibentuk terpisah, sedangkan cokelat wajib menempel kanopi lewat jendela ketetanggaan 21x21 agar media gelap tidak ikut terdeteksi."
CH2D = "Faktor adaptasi f dihitung dari rata-rata komponen V tiap frame terhadap acuan 128 lalu dijepit pada 0,6 sampai 1,6. Faktor tersebut menggeser ambang bawah S dan V tanpa menggeser Hue sehingga identitas hijau, kuning, dan cokelat tetap. Sudut hasil deteksi diratakan antarframe dengan Exponential Moving Average (EMA) berbobot 0,2 seperti Persamaan 2.5 sehingga jitter sudut turun dari 19,93 piksel menjadi 9,32 piksel atau 53 persen."
CH2E = "Liputan tiap zona adalah rasio piksel tanaman terhadap luas zona dalam persen. Persentase kuning dan cokelat dihitung terhadap piksel tanaman, bukan luas zona, sehingga zona jarang tetap adil. Status panen ditetapkan dari liputan: belum siap di bawah 25 persen, hampir siap 25-55 persen, siap panen 55-80 persen, dan harus panen di atas 80 persen. Persentase kuning dan cokelat dinormalkan terhadap ambang sakit 25 persen dan 8 persen menjadi PSI 0-100 seperti Persamaan 2.6 dan 2.7. PSI 40 menandai dominasi klorosis, PSI 60 menandai dominasi nekrosis, sedangkan PSI maksimum zona terburuk dikirim terpisah agar bahaya lokal tidak hilang dalam rata-rata."
CH2F = "Evaluasi memakai mask ground truth tiga kelas yaitu tanaman total, kuning, dan cokelat untuk lima gambar. Presisi mengukur ketepatan piksel terdeteksi, recall mengukur kelengkapan temuan, skor F1 adalah rata-rata harmonik keduanya, sedangkan Intersection over Union (IoU) mengukur tumpang tindih seperti Persamaan 2.8 dan 2.9. Target wajar untuk HSV beserta kontur pada foto lapangan adalah F1 0,85-0,95."


def tahap4cd(doc):
    add = lambda *a, **k: add_para(doc, *a, **k)
    add(32, "Landasan Teoretik", bold=True)
    add(32, "Deteksi Tepi Canny dan Aproksimasi Quad", bold=True)
    add(33, CH2A, itw=IT4)
    add(33, "G = akar(Gx^2 + Gy^2)   (2.1)")
    add(33, "theta = arctan(Gy / Gx)   (2.2)")
    add(33, CH2B, itw=IT4)
    add(33, "s . p = H . p   (2.3)")
    add(32, "Ruang Warna HSV dan Segmentasi Vegetasi", bold=True)
    add(33, CH2C, itw=IT4)
    add(33, "M_tanaman = M_muda ATAU M_mature   (2.4)")
    add(32, "Adaptasi Iluminasi dan Perata Temporal EMA", bold=True)
    add(33, CH2D, itw=["Hue", "Saturation", "Value", "Exponential Moving Average",
                       "Plant Stress Index", "ground truth", "recall", "Intersection over Union"])
    add(33, "x_t = 0,2 . z_t + 0,8 . x_{t-1}   (2.5)")
    add(32, "Liputan Kanopi dan Indeks Stres Tanaman", bold=True)
    add(33, CH2E, itw=["Hue", "Saturation", "Value", "Exponential Moving Average",
                       "Plant Stress Index", "ground truth", "recall", "Intersection over Union"])
    add(33, "PSI = 100 . min(1; 0,4 . min(K/25; 1) + 0,6 . min(C/8; 1))   (2.6)")
    add(33, "PSI_maks = maks(PSI_zona), z = 1..24   (2.7)")
    add(32, "Metrik Evaluasi Segmentasi", bold=True)
    add(33, CH2F, itw=["Hue", "Saturation", "Value", "Exponential Moving Average",
                       "Plant Stress Index", "ground truth", "recall", "Intersection over Union"])
    add(33, "F1 = 2 . P . R / (P + R)   (2.8)")
    add(33, "IoU = |A temu B| / |A gabung B|   (2.9)")
# ---------------- Tahap 5a (= bangun_felix_t5a.py): Bab 3 + Tabel 3.1/3.2 ----------------
IT5 = ["top-down", "ground truth", "bed_readings", "fuzzy_input", "Hue Saturation Value"]
LOKASI = "Riset dilaksanakan di bed akuaponik kangkung berukuran 2 m x 1,1 m pada Eco Farm UNNES, sedangkan pengembangan perangkat lunak dilakukan di laboratorium komputer. Pengambilan citra memakai kamera atas atau top-down pada tiga rentang iluminasi yaitu pagi pukul 08.00-09.00, siang pukul 11.00-13.00, dan sore pukul 15.00-17.00. Uji lapangan memakai 18 video dan lima foto bed tahap seedling sampai ready, sedangkan uji burn-in 24 jam dilakukan setelah rumah kamera terpasang permanen di lokasi."
BAHAN = "Bahan berupa bed akuaponik kangkung satu unit, tanaman tahap seedling sampai ready, dan lima foto lapangan beserta 18 video uji. Alat terdiri atas perangkat keras pada Tabel 3.1 dan perangkat lunak pada Tabel 3.2. Modul raspi/modules adalah salinan berkas adaptive_bed.py dan kangkung_cv.py sehingga hasil laptop dan komputer papan tunggal identik."
HW = [
 ["Raspberry Pi 4B", "RAM 2 GB, Debian 13, Python 3.13", "Komputasi pipeline tiap 10 menit"],
 ["Kamera CSI IR 5MP", "Sensor ov5647, 1296x972 via libcamera", "Akuisisi top-down"],
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
 ["Dasbor web statis", "web/ tanpa build", "Heatmap 4x6 dan grafik 24 jam"],
]


def tahap5a(doc):
    add_para(doc, 32, "BAB III", bold=True)
    add_para(doc, 32, "METODE PELAKSANAAN", bold=True)
    add_para(doc, 32, "Lokasi Riset", bold=True)
    add_para(doc, 33, LOKASI, itw=IT5)
    add_para(doc, 32, "Bahan dan Alat", bold=True)
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
ARSITEK = "Sistem dirancang sebagai sensor tanaman otomatis berlima tahap. Tahap akuisisi memakai kamera CSI atau HP secara top-down dengan pemanasan pajanan otomatis. Tahap visi di komputer papan tunggal menjalankan deteksi bed, warp, grid 4x6, liputan, kuning, cokelat, dan PSI seperti Persamaan 2.3 sampai 2.7. Tahap Firebase memakai koleksi bed_readings skema v1.1 dengan payload 2-3 KB tiap 10 menit. Tahap dasbor menampilkan heatmap 4x6, grafik 24 jam, distribusi status, dan kartu PSI secara baca saja. Tahap kendali membaca PSI, PSI maksimum, dan jumlah zona sakit menjadi keputusan pompa dengan persetujuan manusia. Blok diagram pada Gambar 3.1 meringkas aliran tersebut."
KONTRAK = "Kontrak antar tahap memakai fuzzy_input berisi kuning_pct, coklat_pct, zona_sakit, psi, psi_maks, dan psi_versi. Aturan keselamatan menetapkan data basi di atas 30 menit ditolak, nilai hilang menahan tindakan, dan status usulan wajib menunggu persetujuan manusia sehingga tidak ada aktuasi otomatis."


def tahap5b(doc):
    itw = ["top-down", "bed_readings", "fuzzy_input", "psi", "psi_maks", "psi_versi"]
    add_para(doc, 32, "Arsitektur Sistem", bold=True)
    add_para(doc, 33, ARSITEK, itw=itw)
    cap = add_para(doc, 89, "Gambar 3.1  Blok diagram sistem sensor tanaman otomatis dari kamera sampai dasbor dan pengendali.", bold=True)
    add_image_before(doc, cap, ROOT / "docs" / "blok_diagram.png", 5.5)
    add_para(doc, 33, KONTRAK, itw=itw)
# ---------------- Tahap 5c (= t5c.py): diagram alir + Gambar 3.2, skema + Gambar 3.3 ----------------
ALIR = "Diagram alir pada Gambar 3.2 memakai simbol baku algoritma yaitu elips untuk START dan END, jajar genjang untuk input dan output, belah ketupat untuk keputusan, dan persegi panjang untuk proses. Aliran dimulai dari frame kamera, lalu deteksi bed Canny-quad dengan keputusan lolos atau jalur cadangan, lalu warp dan grid, lalu segmentasi adaptif memakai Persamaan 2.4 dan faktor f Bagian 2.2.3, lalu skor zona memakai Persamaan 2.6 dan 2.7, lalu pengiriman payload, dan diakhiri keluaran MP4 beranotasi, CSV runtun waktu, JSON, dan dasbor. Diagram alir berbeda dengan blok diagram Gambar 3.1 karena diagram alir menunjukkan langkah yang dapat diprogram sedangkan blok diagram menunjukkan hubungan antar subsistem."
SKEMA = "Kamera dipasang di atas tengah bed secara top-down pada ketinggian sekitar 2,5 m sehingga seluruh tepi bed masuk frame dengan porsi bed minimal 12 persen luas frame seperti Gambar 3.3. Aturan pasang menghindari pantulan langsung ke modul kamera, pipa yang menutupi bed, dan rumah hitam yang terkena matahari langsung. Rumah PETG IP65 memakai pelindung matahari, kelenjar kabel, dan gel silika, sedangkan komputer papan tunggal memakai pelepas panas besar."


def tahap5c(doc):
    itw = ["f", "Hue", "Saturation", "Value", "top-down"]
    add_para(doc, 32, "Diagram Alir", bold=True)
    add_para(doc, 33, ALIR, itw=itw)
    c2 = add_para(doc, 89, "Gambar 3.2  Diagram alir pipeline computer vision dari START sampai END.", bold=True)
    add_image_before(doc, c2, ROOT / "docs" / "flowchart_cv.png", 3.2)
    add_para(doc, 32, "Skema Pemasangan", bold=True)
    add_para(doc, 33, SKEMA, itw=itw)
    c3 = add_para(doc, 89, "Gambar 3.3  Skema pemasangan kamera di atas bed akuaponik.", bold=True)
    add_image_before(doc, c3, ROOT / "docs" / "skema_kamera.png", 5.5)
# ---------------- Tahap 5d (= t5d.py): prinsip kerja + Gambar 3.4/3.5, metrik + Tabel 3.3 ----------------
KERJA = "Prinsip kerja mengikuti formulasi Bab 2 dan dirujuk eksplisit tiap langkah. Deteksi bed memakai Persamaan 2.1 dan 2.2 untuk tepi, lalu aproksimasi quad, lalu Persamaan 2.3 untuk warp. Segmentasi memakai Persamaan 2.4 untuk maska hijau serta rentang kuning dan cokelat yang dijaga statis agar diagnosis tegas. Faktor adaptasi Bagian 2.2.3 menggeser ambang S dan V lalu sudut diratakan dengan Persamaan 2.5. Tiap zona dihitung liputan, kuning, dan cokelat terhadap piksel tanaman, lalu status panen dan status kesehatan ditetapkan, lalu PSI dan PSI maksimum dihitung dengan Persamaan 2.6 dan 2.7. Zona dengan kanopi di bawah 30 persen luas zona berstatus tidak dinilai agar artefak tepi warp tidak memicu alarm."
BUKTI = "Bukti reproduksibilitas memakai data asli. Gambar 3.4 membandingkan frame mentah HP IMG_5159 dengan keluaran pipeline pada frame yang sama, sedangkan Gambar 3.5 membandingkan foto lapangan bed_04_ready.jpg dengan keluaran batch_segmentasi.py. Kedua gambar tersebut membuktikan masukan dan keluaran berasal dari data lapangan, bukan simulasi."
METRIK = "Metrik terdiri atas jitter sudut dalam piksel untuk stabilitas temporal, liputan rata-rata dan simpangan baku dalam persen untuk tren tumbuh, serta presisi, recall, F1, dan Intersection over Union (IoU) memakai Persamaan 2.8 dan 2.9 untuk akurasi segmentasi terhadap mask ground truth. Metrik sistem terdiri atas keberhasilan siklus burn-in, suhu SoC dalam derajat Celsius, dan keterbacaan snapshot. Skenario pada Tabel 3.3 menguji tiap rumusan masalah secara kuantitatif dan divisualkan dengan plot pada Bab 4 agar pembaca tidak menelusuri angka mentah satu per satu."
SKEN = [
 ["Stabilitas iluminasi", "18 video pagi/siang/sore", "Jitter turun >=40 persen, liputan stabil", "Persamaan 2.5"],
 ["Akurasi segmentasi", "5 mask ground truth", "F1 0,85-0,95, IoU per kelas", "Persamaan 2.8-2.9"],
 ["Kesehatan dan PSI", "5 foto lapangan + foto sakit", "0 zona sakit palsu, PSI 0-0,1 saat sehat", "Persamaan 2.6-2.7"],
 ["Banding metode", "5 gambar GT", "HSV vs ExG vs Otsu-Hue", "Tabel 2.1"],
 ["Burn-in lapangan", "24 jam, 144 siklus", ">=140 OK, suhu <70 derajat", "Tabel 3.1"],
]


def tahap5d(doc):
    itw = ["Hue", "Saturation", "Value", "ground truth", "top-down"]
    add_para(doc, 32, "Prinsip Kerja Algoritma", bold=True)
    add_para(doc, 33, KERJA, itw=itw)
    add_para(doc, 33, BUKTI, itw=itw)
    c4 = add_para(doc, 89, "Gambar 3.4  Bukti asli frame HP terhadap keluaran pipeline grid dan HUD.", bold=True)
    add_image_before(doc, c4, ROOT / "output" / "ppt_asli" / "01_asli_vs_anotasi.jpg", 5.8)
    c5 = add_para(doc, 89, "Gambar 3.5  Bukti asli foto lapangan terhadap keluaran segmentasi liputan 22,6 persen.", bold=True)
    add_image_before(doc, c5, ROOT / "output" / "ppt_asli" / "02_foto_vs_segmentasi.jpg", 5.2)
    add_para(doc, 32, "Metrik dan Skenario Pengujian", bold=True)
    add_para(doc, 33, METRIK, itw=["recall", "Intersection over Union", "ground truth"])
    add_para(doc, 89, "Tabel 3.3  Skenario pengujian kelayakan prototipe.", bold=True)
    t = doc.add_table(rows=6, cols=4)
    t.style = "Table Grid"
    for j, htxt in enumerate(["Skenario", "Data", "Metrik dan target", "Acuan"]):
        t.cell(0, j).text = htxt
    for i, row in enumerate(SKEN, 1):
        for j, v in enumerate(row):
            t.cell(i, j).text = v
# ---------------- Tahap 6b (= t6b.py): Daftar Isi statis P19-P28 ----------------
TOC = ["HALAMAN JUDUL ............................................................................................. ii",
 "PERSETUJUAN PEMBIMBING ...................................................................... iii",
 "DAFTAR ISI ......................................................................................................... iv",
 "DAFTAR TABEL .................................................................................................. v",
 "DAFTAR GAMBAR ............................................................................................ vi",
 "DAFTAR ISTILAH DAN SINGKATAN ......................................................... vii",
 "BAB I  PENDAHULUAN ..................................................................................... 1",
 "BAB II  KAJIAN PUSTAKA ........................................................................... 6",
 "BAB III  METODE PELAKSANAAN ............................................................... 10",
 "DAFTAR PUSTAKA .......................................................................................... 15"]


def tahap6b(doc):
    for k, teks in enumerate(TOC):
        p = doc.paragraphs[19 + k]
        if not p.runs:
            p.add_run(teks)
        else:
            p.runs[0].text = teks
            for r in p.runs[1:]:
                r.text = ""


# ---------------- Tahap 6c (= t6c.py): Daftar Pustaka ----------------
SITASI = [
 "[1] J. Canny, A computational approach to edge detection, IEEE Trans. Pattern Anal. Mach. Intell., vol. 8, no. 6, pp. 679-698, 1986. doi: 10.1109/TPAMI.1986.4767851.",
 "[2] D. Searson dkk., Automatic crop detection under field conditions using the HSV colour space and morphological operations, Comput. Electron. Agric., vol. 134, pp. 80-89, 2017. doi: 10.1016/j.compag.2016.12.013.",
 "[3] R. Abbasi, P. Martinez, dan R. Ahmad, Automated visual identification of foliage chlorosis in lettuce grown in aquaponic systems, Agriculture, vol. 13, no. 3, p. 615, 2023. doi: 10.3390/agriculture13030615.",
 "[4] D. M. Woebbecke, G. E. Meyer, K. Von Bargen, dan D. A. Mortensen, Color indices for weed identification under various soil, residue, and lighting conditions, Trans. ASAE, vol. 38, no. 1, pp. 259-269, 1995. doi: 10.13031/2013.27838.",
 "[5] I. A. Hameed, M. Usama dkk., A new vegetation segmentation approach for cropped fields based on threshold detection from hue histograms, Sensors, vol. 18, no. 4, p. 1258, 2018. doi: 10.3390/s18041258.",
 "[6] W. Yang, S. Wang, X. Zhao, J. Zhang, dan J. Feng, Greenness identification based on HSV decision tree, Inf. Process. Agric., vol. 2, no. 3-4, pp. 277-284, 2015. doi: 10.1016/j.inpa.2015.07.003.",
 "[7] J. G. A. Barbedo, Digital image processing techniques for detecting, quantifying and classifying plant diseases, SpringerPlus, vol. 2, p. 660, 2013. doi: 10.1186/2193-1801-2-660.",
 "[8] S. Wan, K. Zhao, Z. Lu dkk., A modularized IoT monitoring system with edge-computing for aquaponics, Sensors, vol. 22, no. 23, p. 9260, 2022. doi: 10.3390/s22239260.",
 "[9] J. C. Tovar dkk., Raspberry Pi-powered imaging for plant phenotyping, Appl. Plant Sci., vol. 6, no. 4, 2018. doi: 10.1002/aps3.1031.",
 "[10] A. F. A. Netto dkk., Segmentation of RGB images using different vegetation indices and thresholding methods, Nativa, vol. 6, no. 4, 2018. doi: 10.31413/nativa.v6i4.5405.",
]


def tahap6c(doc):
    add_para(doc, 32, "DAFTAR PUSTAKA", bold=True)
    for sit in SITASI:
        add_para(doc, 33, sit)
# ---------------- Patch final (= tmp_patchfinal.py + tmp_final.py) ----------------
# P7 format 'oleh' + newline seperti template; P40 sisa fuzzy -> CV;
# Daftar Singkatan HSV..URL (urutan akhir yang benar).
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
    r0 = doc.paragraphs[33]
    items = []
    for s in SINGKATAN:
        np_ = deepcopy(r0._p)
        for r in np_.xpath(".//w:r"):
            r.getparent().remove(r)
        re_ = OxmlElement("w:r")
        if r0.runs:
            for ch in r0.runs[0]._r.xpath("./w:rPr/*"):
                re_.append(deepcopy(ch))
        te = OxmlElement("w:t")
        te.set(XML_SPACE, "preserve")
        te.text = s
        re_.append(te)
        np_.append(re_)
        items.append(np_)
    # addnext satu-per-satu persis seperti skrip asal menimbulkan urutan
    # terbalik di XML; sengaja dipertahankan (dicek identik dgn verify).
    for it in items:
        p28._p.addnext(it)


def tahap_reorder_singkatan(doc):
    vals = [doc.paragraphs[i].text for i in range(29, 37)]
    for k, i in enumerate(range(29, 37)):
        doc.paragraphs[i].runs[0].text = vals[::-1][k]
        for r in doc.paragraphs[i].runs[1:]:
            r.text = ""
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
        nxt_txt = Paragraph(nxt, doc).text if nxt is not None else ""
        if nxt_txt.startswith("HSV:"):
            p_ist_keep = h
        else:
            p_ist_del = h
    assert p_ist_keep is not None
    target = p_ist_keep._p
    block = [clone_with_text(doc, p_gambar_tpl, "DAFTAR TABEL")]
    for teks in [
        "Tabel 1.1  Perbandingan Dengan Produk Lain ................................................... 5",
        "Tabel 2.1  Perbandingan Penelitian Terdahulu ..................................................... 7",
        "Tabel 3.1  Daftar Perangkat Keras .................................................................. 11",
        "Tabel 3.2  Daftar Perangkat Lunak .................................................................. 11",
        "Tabel 3.3  Skenario Pengujian Kelayakan Prototipe .............................................. 13",
    ]:
        block.append(clone_with_text(doc, entry_src, teks))
    block.append(clone_with_text(doc, p_gambar_tpl, "DAFTAR GAMBAR"))
    for teks in [
        "Gambar 3.1  Blok Diagram Sistem .................................................................. 11",
        "Gambar 3.2  Diagram Alir Pipeline .................................................................. 12",
        "Gambar 3.3  Skema Pemasangan Kamera ........................................................... 12",
        "Gambar 3.4  Bukti Asli Frame HP vs Pipeline ...................................................... 13",
        "Gambar 3.5  Bukti Asli Foto Lapangan vs Segmentasi .......................................... 13",
    ]:
        block.append(clone_with_text(doc, entry_src, teks))
    for nb in block:
        target.addprevious(nb._p)
    delete_p(p_gambar_tpl)
    delete_p(p_ist_del)


def tahap7bspasi(doc):
    ps = doc.paragraphs
    i_penutup = next(i for i, p in enumerate(ps) if p.text.startswith("Dengan demikian"))
    i_rumusan = next(i for i, p in enumerate(ps) if p.text.strip() == "Rumusan Masalah")
    assert i_rumusan == i_penutup + 1, (i_penutup, i_rumusan)
    i_blank = next(i for i, p in enumerate(ps) if p.text.strip() == "" and i > i_rumusan)
    np_ = deepcopy(ps[i_blank]._p)
    ps[i_rumusan]._p.addprevious(np_)
# ---------------- main + verifikasi ----------------
TAHAP = [
 ("t1 judul", tahap1), ("t2 profil", tahap2),
 ("t3a latar", tahap3a), ("t3b rumusan/tujuan", tahap3b),
 ("t3c manfaat", tahap3c), ("t3d dampak", tahap3d), ("t3e tabel1.1", tahap3e),
 ("t4a bab2-awal", tahap4a), ("t4b tabel2.1", tahap4b), ("t4cd landasan", tahap4cd),
 ("t5a bab3+tabel3.1/3.2", tahap5a), ("t5b arsitektur+g3.1", tahap5b),
 ("t5c alir+g3.2/skema+g3.3", tahap5c), ("t5d kerja+g3.4/3.5+metrik", tahap5d),
 ("t6b TOC", tahap6b), ("t6c pustaka", tahap6c),
 ("patch P7/P40/singkatan", tahap_patch), ("reorder singkatan", tahap_reorder_singkatan),
 ("t7 struktur", tahap7struct), ("t7b spasi", tahap7bspasi),
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
    checks = {
        "kata>=3900": len(teks.split()) >= 3900,
        "Felix==2": teks.count("Felix Enrique") == 2,
        "NIM==2": teks.count("2305110019") == 2,
        "tanpa Rafly/Sugeno": ("Rafly" not in teks and "Sugeno" not in teks),
        "tanpa pH": not re.findall(r"\bpH\b", teks),
        "1x Dengan demikian": sum(1 for p in d.paragraphs
                                  if p.text.startswith("Dengan demikian")) == 1,
        "tabel==6": len(d.tables) == 6,
        "gambar==9": len(d.inline_shapes) == 9,
        "BAB I/II/III": all(f"BAB {x}" in teks for x in ("I", "II", "III")),
        "DAFTAR PUSTAKA": "DAFTAR PUSTAKA" in teks,
        "sectPr terakhir": d.element.body[-1].tag == qn("w:sectPr"),
        "daftar tabel/gambar/istilah": all(
            s in teks for s in ("DAFTAR TABEL", "DAFTAR GAMBAR",
                                "DAFTAR ISTILAH DAN SINGKATAN")),
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

