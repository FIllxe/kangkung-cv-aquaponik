# Panduan Ground Truth Mask & Evaluasi (Bab 4)

Target: **5–7 gambar** dianotasi → `evaluasi_segmentasi.py` + `bandingkan_metode.py`
menghasilkan tabel P/R/F1/IoU untuk Bab 4. Perkiraan waktu **±45–60 menit**
(±8 menit per gambar, makin cepat setelah gambar pertama).

## 1. Sumber gambar

`dataset1/` sudah berisi 7 kandidat (bed_01_seedling … bed_05_mixed + 2 PNG).
Pilih minimal 5 yang kondisi tanamannya beragam (seedling, young, growing,
ready, mixed) — variasi kondisi membuat angka evaluasi lebih kuat.

## 2. Anotasi dengan `buat_gt.py`

Jalankan dari folder `files/`:

```
cd files
python buat_gt.py ../dataset1/bed_04_ready.jpg --out ../gt
```

Kontrol (muncul juga di jendela tool):

| Tombol | Fungsi |
|---|---|
| Klik/drag kiri | Cat area tanaman (putih) |
| `E` | Toggle cat ↔ hapus (eraser) |
| `+` / `-` | Besar/kecil brush |
| `Z` | Undo |
| `C` | Kosongkan mask kelas aktif |
| `N` | Ganti kelas: Tanaman Total → Kuning → Coklat |
| `S` | Simpan mask kelas aktif |
| `Q` / `ESC` | Keluar |

Tips:
- **Wajib simpan 3 kelas per gambar** (tekan `S` setelah selesai tiap kelas);
  minimal harus ada mask **Tanaman Total** — itu yang dievaluasi utama.
- Kuning = daun menguning (klorosis); coklat = jaringan mati/nekrosis.
- Kepala HUD menampilkan coverage % — pembanding berguna saat cek silang.
- Jangan cat air, styrofoam, pipa, bayangan — hanya jaringan tanaman.

## 3. Penamaan (otomatis, sudah kompatibel)

`buat_gt.py` menulis ke `gt/`:

```
bed_04_ready_gt.png          # Tanaman Total  → vs mask_total
bed_04_ready_kuning_gt.png   # Kuning         → vs mask_kuning
bed_04_ready_coklat_gt.png   # Coklat         → vs mask_coklat
```

`evaluasi_segmentasi.py` mencari suffix `_gt` dan `_<kelas>_gt`
(`find_gt_class`, suffix `_kuning_gt`), jadi tidak perlu rename manual.
Resolusi mask boleh beda — otomatis di-resize nearest ke mask prediksi.

## 4. Jalankan evaluasi

```
cd files
python evaluasi_segmentasi.py --images ../dataset1 --gt ../gt
python bandingkan_metode.py   --images ../dataset1 --gt ../gt
```

Output untuk Bab 4 (di `files/output/`):
`evaluasi_segmentasi.csv` / `.json` / `.png` (grafik bar P/R/F1/IoU) dan
`perbandingan_metode.csv` / `.png` (HSV vs ExG vs Otsu-Hue).

> Rata-rata target wajar untuk HSV + kontur di foto lapangan: F1 ≈ 0.85–0.95.
> Kalau ada gambar dengan F1 jauh di bawah yang lain, cek mask GT-nya dulu
> (sering kali kurang teliti), baru evaluasi apakah itu kasus gagal metode.

---

# Checklist Deploy Raspberry Pi

Referensi lengkap: `raspi/README.md` (setup 15 menit + burn-in test 24 jam).

## Pra-deploy (di laptop — 2 field tersisa)

`raspi/config.json` sudah terisi; tinggal:

- [ ] `firebase.storage_bucket`: ganti `NAMA-PROYEK-FIREBASE.appspot.com`
      dengan bucket asli (Firebase Console → Storage → tab *Files*,
      format `nama-proyek.firebasestorage.app` atau `….appspot.com`).
- [ ] Letakkan kredensial di `raspi/service-account.json` (saat ini baru
      `service-account.json.EXAMPLE`). Firebase Console → Project settings →
      Service accounts → *Generate new private key* → simpan.
- [ ] Pastikan keduanya **tidak ter-push**: keduanya sudah di `.gitignore` —
      jangan pindahkan/commit file aslinya.

## Deploy di Pi

```
git clone https://github.com/FIllxe/kangkung-cv-aquaponik.git ~/kangkung_pi_src
cd ~/kangkung_pi_src/raspi && bash install.sh      # salin paket → ~/kangkung_pi
cd ~/kangkung_pi
nano config.json                                   # isi storage_bucket di Pi juga
cp /path/service-account.json .                    # taruh kredensial di Pi
./venv/bin/python kangkung_pi.py --test            # 1 siklus → outbox/sent/
sudo systemctl start kangkung && journalctl -u kangkung -f
```

## Burn-in 24 jam (kriteria lulus — ringkas dari `raspi/README.md`)

- [ ] Dokumen baru tiap ±10 menit di Firestore; ≥ 140 siklus `[OK]` / 24 jam
- [ ] `suhu_pi_c` < 70°C (75°C sering → heatsink/ventilasi)
- [ ] Snapshot di dashboard terbaca (grid 4×6 tidak hitam/penuh putih)
- [ ] `outbox/` (bukan `outbox/sent/`) hampir kosong; cabut WiFi 15 menit →
      antrean terkirim setelah online
- [ ] `sudo reboot` → monitor jalan lagi sendiri tanpa login

Semua lulus → pasang outdoor permanen (box IP65 terang, sun shield,
microSD high-endurance — detail di `raspi/README.md` § Catatan hardware).
