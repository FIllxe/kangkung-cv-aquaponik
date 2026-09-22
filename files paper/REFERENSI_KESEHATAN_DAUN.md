# Referensi Tambahan — Kesehatan Daun (Kuning & Coklat)

> Pendamping `DAFTAR_PAPER_REFERENSI.md`, `REFERENSI_TAMBAHAN_20.md`, `REFERENSI_METHOD_BARU.md`.
> Total daftar pustaka proyek: **53 paper** (47 + 6 baru di file ini).
> Semua entri terverifikasi via OpenAlex (judul, penulis, tahun, venue, DOI, sitasi per Sept 2026).

## Daftar Paper Baru (6)

| # | Paper | Venue | Sitasi | Akses |
|---|---|---|---|---|
| A1 ⭐ | Barbedo, J.G.A. (2013). *Digital image processing techniques for detecting, quantifying and classifying plant diseases*. | SpringerPlus | 619 | Open access (CC-BY) — DOI: `10.1186/2193-1801-2-660` |
| A2 | Zhang, N. et al. (2020). *A Review of Advanced Technologies and Development for Hyperspectral-Based Plant Disease Detection in the Past Three Decades*. | Remote Sensing 12(19):3188 | 246 | Open access — DOI: `10.3390/rs12193188` |
| A3 | Kamilaris, A. & Prenafeta-Boldú, F.X. (2018). *Deep learning in agriculture: A survey*. | Computers and Electronics in Agriculture | 5.018 | DOI: `10.1016/j.compag.2018.02.016` |
| B1 | Liakos, K.G. et al. (2018). *Machine Learning in Agriculture: A Review*. | Sensors 18(8):2674 | 3.312 | Open access — DOI: `10.3390/s18082674` |
| C1 | Shamshiri, R.R. et al. (2018). *Advances in greenhouse automation and controlled environment agriculture: A transition to plant factories and urban agriculture*. | Int. J. Agric. & Biol. Eng. 11(1) | 529 | DOI: `10.25165/j.ijabe.20181101.3210` |
| C2 | Lindholm-Lehto, P. (2023). *Water quality monitoring in recirculating aquaculture systems*. | Aquaculture and Fisheries | 155 | DOI: `10.1002/aff2.102` |

⭐ = wajib dikutip (fondasi langsung method segmentasi warna kuning/coklat).

## Paper Existing yang Dipakai Ulang (sudah di daftar lain)

- **Woebbecke et al. (1995)** — indeks warna lintas kondisi cahaya (1.543 sitasi) → fondasi HSV.
- **Searson et al. (2017)** — morfologi HSV segmentasi tanaman → detail open/close bercak.

## Pemetaan ke Bab Laporan

| Bab | Gunakan paper | Untuk membenarkan |
|---|---|---|
| Bab 1 (Latar) | C2, B1 | Kualitas air/nutrisi mempengaruhi warna daun; kebutuhan monitoring |
| Bab 2 (Tinjauan Pustaka) | A1, A3, C1, C3 (Farooq 2019, IEEE Access) | Segmentasi area penyakit; kamera-vs-DL; arsitektur sensing-aktuasi |
| Bab 3 (Metode) | A1, A2, Searson 2017 | HSV kuning (H 21–34) & coklat (H 8–20); kuning=clorosis vs coklat=nekrosis dipisah |
| Bab 4 (Hasil) | A1 | Metrik per zona (pct_kuning/pct_coklat vs GT 3 kelas) |
| Bab 5 (Fuzzy rekan tim) | Liakos 2018 + Agriculture 4.0 (Araújo 2021, Agronomy 11:667, DOI `10.3390/agronomy11040667`, 331 sitasi) | Crisp input `pct_kuning`/`pct_coklat` untuk kontrol pompa |

## Temuan Pencarian (untuk argumen novelty)

Query spesifik "fuzzy logic pump aquaponik" dan "HSV threshold daun kuning kangkung" **tidak**
menghasilkan paper yang mengkombinasikan keduanya — kombinasi grid 4×6 + kesehatan daun per zona
+ fuzzy pompa adalah celah riset (argumen novelty skripsi). Konsekuensi: threshold kesehatan
(`KESEHATAN` di `kangkung_cv.py`) dinyatakan jujur sebagai heuristik awal yang divalidasi belakangan.
