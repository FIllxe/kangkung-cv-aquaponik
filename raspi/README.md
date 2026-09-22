 Monitor Kangkung Live — Raspberry Pi (ready-to-use)

Paket ini menjadikan Raspberry Pi + kamera sebagai **senser tanaman otomatis**:
capture → deteksi bed → warp → grid 4×6 → coverage + **kesehatan daun
(kuning/coklat)** → kirim ke dashboard Firebase yang sudah ada.
Multi-user tanpa login: semua orang membuka dashboard; Raspi hanya *mengirim*
data (tidak melayani koneksi masuk).

## Setup (±15 menit)

1. **Flash Raspberry Pi OS Lite (64-bit)** ke microSD (Raspberry Pi Imager),
   isi WiFi + aktifkan SSH saat flashing.
2. **Clone repo langsung di Pi** (jika Pi sudah online):
   ```
   git clone https://github.com/<USER>/kangkung-cv-aquaponik.git ~/kangkung_pi_src
   ```
   *(alternatif SCP/USB: `scp -r raspi pi@<ip-pi>:~/kangkung_pi` — lalu
   langsung ke langkah 4)*
3. **Jalankan installer** (otomatis copy paket → `~/kangkung_pi`):
   ```
   cd ~/kangkung_pi_src/raspi && bash install.sh
   ```
4. **Isi kredensial Firebase**: download service-account JSON dari Firebase
   Console → Project settings → Service accounts → Generate private key,
   simpan sebagai `service-account.json` (di folder ini).
5. **Isi `config.json`**: `device_id` unik per bed, `storage_bucket` (nama
   bucket Firebase), `interval_menit` (10 = aman untuk suhu).
6. **Uji sekali** (tanpa service):
   ```
   ./venv/bin/python kangkung_pi.py --test
   ```
   → 1 siklus berjalan, snapshot + payload muncul di `outbox/sent/`.
7. **Mulai service**:
   ```
   sudo systemctl start kangkung
   journalctl -u kangkung -f     # lihat log live
   ```

## Remote dari jauh (admin): Tailscale (rekomendasi)

```
# di Pi dan di laptop Anda:
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
Lalu SSH dari mana saja: `ssh pi@nama-pi` (nama Tailscale). Tidak perlu
buka port router, aman, tembus NAT kampus.

## Multi-user tanpa login (dashboard)

- Raspi **push** data ke Firestore/Storage → penonton tidak mengakses Pi langsung.
- Aturan Firebase (read publik, tulis terkunci):

  **Firestore rules:**
  ```
  match /bed_readings/{doc} {
    allow read: if true;
    allow write: if false;   // tulis hanya via service-account (server)
  }
  ```
  **Storage rules** (folder snapshots):
  ```
  match /snapshots/{all=**} {
    allow read: if true;
    allow write: if false;
  }
  ```
- Siapa pun dengan link dashboard bisa melihat grid + snapshot **tanpa login**.
  Kontrol pompa (tulis) tetap milik akun rekan tim Anda.

## Burn-in test 24 jam (WAJIB sebelum dipasang permanen outdoor)

| Cek | Cara | Kriteria lulus |
|---|---|---|
| Data masuk rutin | Dashboard / Firestore Console | Dokumen baru tiap ±10 menit (±3 dokumen/30 menit) |
| Tidak ada gap | `journalctl -u kangkung --since "24 hours ago" \| grep -c "\[OK\]"` | ≥ 140 siklus OK (dari ~144 ideal) |
| Suhu aman | Field `suhu_pi_c` di payload | Maks < 70°C; jika 75°C sering → tambah heatsink/ventilasi |
| Snapshot tidak kosong | Buka beberapa `snapshot_url` di dashboard | Grid 4×6 terlihat, tidak hitam/putih penuh |
| Status masuk akal | Bandingkan visual bed vs distribusi status | Zona tanaman rapat = siap/hampir, kosong = belum |
| Antrean tidak menumpuk | `ls outbox/` di Pi (bukan outbox/sent) | Kosong / < 3 file (internet lancar) |
| Auto-restart hidup | `sudo reboot` → cek 2 menit kemudian | Monitor jalan lagi tanpa login manual |
| Offline queue | Cabut WiFi 15 menit, sambungkan lagi | File di outbox terkirim setelah online |

**Jika semua lulus → taruh di outdoor permanen.** Jika tidak, perbaiki dulu
(kipas/ventilasi untuk suhu, `interval_menit` dinaikkan untuk mengurangi beban).

## Perbarui kode

Edit modul di laptop (`modules/adaptive_bed.py` / `modules/kangkung_cv.py`
adalah salinan dari `files/`), kirim ulang:
`scp modules/kangkung_cv.py pi@nama-pi:~/kangkung_pi/modules/`
lalu `sudo systemctl restart kangkung`.

## Catatan hardware outdoor

- Box IP65 terang + sun shield + cable gland + silica gel (jangan box hitam
  kena matahari langsung).
- Heatsink besar; kipas opsional dengan termostat.
- microSD high-endurance; service auto-restart setelah hang.
- Monitor mungkin berhenti sementara bila SoC > `suhu_maks_c` (75°C) —
  ini perilaku normal (thermal guard), bukan error.

## Struktur

| File | Fungsi |
|---|---|
| `kangkung_pi.py` | Pipeline inti (capture → analisis → payload → kirim) |
| `modules/` | Salinan `adaptive_bed.py` + `kangkung_cv.py` dari proyek |
| `firebase_uplink.py` | Upload Firestore/Storage + antrean offline |
| `fuzzy_export.py` | Membangun `fuzzy_input` untuk kontrol pompa |
| `thermal_guard.py` | Baca suhu SoC; tunda capture saat panas |
| `config.json` | Konfigurasi per perangkat (satu-satunya file yang diedit) |
