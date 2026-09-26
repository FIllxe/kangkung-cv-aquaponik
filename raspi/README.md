# Monitor Kangkung Live — Raspberry Pi (ready-to-use)

Paket ini menjadikan Raspberry Pi + kamera sebagai **sensor tanaman otomatis**:
capture → deteksi bed → warp → grid 4×6 → coverage + **kesehatan daun
(kuning/coklat)** → kirim ke dashboard Firebase yang sudah ada.
Multi-user tanpa login: semua orang membuka dashboard; Raspi hanya *mengirim*
data (tidak melayani koneksi masuk).

Dokumen terkait:
[skema Firebase](../docs/SKEMA_FIREBASE_BED_READINGS.md) ·
[checklist deploy](../docs/PANDUAN_GT.md#checklist-deploy-raspberry-pi) ·
[indeks dokumentasi](../docs/README.md)

## Kebutuhan

| Komponen | Keterangan |
|---|---|
| Raspberry Pi 4B (RAM 2 GB cukup) | sudah diuji: Pi 4B + Debian 13 *trixie* (aarch64), Python 3.13 |
| microSD ≥ 16 GB | kelas *high-endurance* untuk operasi 24/7 |
| Kamera | **CSI IR 5MP (ov5647)** lewat libcamera; webcam USB juga bisa (`video_source: 0`) |
| Adaptor 5 V / 3 A (USB-C) | charger HP "PD pintar" kadang tidak mau menyuplai Pi 4B — pakai adaptor resmi/5 V polos |
| Internet | router/hotspot sendiri lebih stabil untuk deployment (lihat § Troubleshooting) |

## Setup (±15 menit)

1. **Flash OS** ke microSD (Raspberry Pi Imager): Raspberry Pi OS Lite/Desktop
   64-bit **atau** Debian 13 — keduanya jalan. Isi WiFi + aktifkan SSH saat flashing.
2. **Ambil paket `raspi/`** — pilih salah satu:
   - di Pi (bila sudah online):
     `git clone https://github.com/FIllxe/kangkung-cv-aquaponik.git ~/kangkung_pi_src`
   - dari laptop (SCP, tanpa git):
     `scp -r raspi aquaponic@<ip-pi>:~/kangkung_pi`
3. **Jalankan installer** (copy paket → `~/kangkung_pi`, venv, deps, systemd):
   ```
   cd ~/kangkung_pi_src/raspi && bash install.sh    # jalur repo
   cd ~/kangkung_pi && bash install.sh              # jalur SCP/paket sudah ada
   ```
4. **Isi kredensial Firebase**: Firebase Console → Project settings →
   Service accounts → *Generate new private key* → simpan sebagai
   `service-account.json` di `~/kangkung_pi/` (tidak di-commit).
5. **Isi `config.json`** — lihat tabel § Konfigurasi.
6. **Uji sekali** (tanpa service):
   ```
   cd ~/kangkung_pi
   ./venv/bin/python camera_pi.py            # cek kamera: 1 frame → /tmp/camera_pi_test.jpg
   ./venv/bin/python kangkung_pi.py --test   # 1 siklus → outbox/
   ```
   Kriteria lulus: baris `[OK] pi-bed-01_<stamp>  cov=..%`.
   Bila `[WARN] bed tidak terdeteksi` → bidikan/fokus lensa belum benar
   (§ Troubleshooting).
7. **Mulai service**:
   ```
   sudo systemctl start kangkung
   journalctl -u kangkung -f     # lihat log live
   ```

## Konfigurasi `config.json`

| Key | Default | Fungsi |
|---|---|---|
| `device_id` | `pi-bed-01` | ID perangkat — unik per bed, jadi awalan `doc_id` Firestore |
| `video_source` | `"csi"` | `"csi"` = kamera CSI via libcamera; `0` = webcam USB (V4L2); path file video = uji offline |
| `csi_width` / `csi_height` | 1296 / 972 | Resolusi capture CSI (1296×972 = mode native 4:3 ov5647) |
| `csi_warmup_detik` | 2.0 | Jeda sebelum capture agar auto-exposure/white-balance stabil (naikkan untuk kondisi malam) |
| `max_width` | 960 | Lebar frame setelah resize (hemat CPU analisis) |
| `interval_menit` | 10 | Jeda antar siklus capture + upload (hemat panas & kuota) |
| `kamera_warmup` | 5 | Jumlah frame dibuang saat warmup pada jalur `cv2.VideoCapture` |
| `bed_lost_max` | 3 | **Cadangan** — batas siklus gagal berturut-turut; belum dipakai `kangkung_pi.py` (pipeline laptop memakai penghitung + label `BED LOST` di HUD) |
| `suhu_maks_c` | 75.0 | Di atas suhu ini capture ditunda otomatis (thermal guard) |
| `outbox_dir` | `outbox` | Folder antrean lokal (snapshot + payload) |
| `firebase.storage_bucket` | — | Nama bucket Storage (Firebase Console → Storage → Files, mis. `proyek.firebasestorage.app`) |
| `firebase.collection` | `bed_readings` | Collection Firestore (lihat skema di `docs/`) |

## Kamera CSI (v2 / IR 5MP ov5647)

OpenCV **tidak bisa** membaca kamera CSI langsung dari `/dev/video0` pada
kernel Raspberry Pi/Debian modern: device legacy MMAL terbuka tapi tidak pernah
mengeluarkan frame (`dmesg` → `bcm2835-isp ... driver mismatch to MMAL`).
Karena itu frame diambil lewat stack libcamera (sama dengan `rpicam-*`),
otomatis oleh `camera_pi.py`:

1. **Picamera2** — jalur utama (`python3-picamera2`, dipasang `install.sh`).
2. **rpicam-jpeg** — cadangan otomatis bila Picamera2 tidak tersedia.

Aktifkan dengan `"video_source": "csi"` di `config.json`. USB webcam tetap
bisa pakai `"video_source": 0`, dan uji tanpa kamera pakai path file video.

Verifikasi cepat di Pi:

```
rpicam-hello --list-cameras                 # sensor terdeteksi? (ov5647 = IR 5MP)
~/kangkung_pi/venv/bin/python camera_pi.py  # 1 frame -> /tmp/camera_pi_test.jpg
```

Catatan resolusi: `1296x972` = mode native 4:3 ov5647, paling cepat
(~3 detik/frame termasuk warmup AE). `csi_warmup_detik` menaikkan kualitas
gambar saat cahaya rendah (malam + IR).

### Modul IR 5MP = NoIR (tanpa filter IR)

Modul ini **tidak punya IR-cut filter**, jadi:

- Warna bisa condong **ungu/magenta** bila ada sumber cahaya kuat/IR di frame
  (lampu, matahari langsung). Ini normal, bukan kerusakan.
- Hindari lampu langsung masuk frame — selain warna aneh, flare-nya bisa
  mengaburkan deteksi tepi bed.
- Saat malam, LED IR membuat gambar tetap terbaca, tetapi **mask HSV
  (hijau/kuning/coklat) di `kangkung_cv.py` perlu divalidasi ulang** pada
  kondisi pencahayaan lapangan. Bila coverage terlihat janggal (mis. 0% padahal
  bed penuh tanaman), jadwalkan kalibrasi HSV dengan gambar asli dari Pi
  (`files/kalibrasi_hsv.py`, atau evaluasi P/R/F1 dengan `gt/`).

### Fokus & bidikan (wajib sebelum uji pipeline)

1. Arahkan kamera ke seluruh bed — **keempat tepi bed harus terlihat** di frame
   (deteksi sudut butuh quad).
2. Putar lensa berulir sampai gambar tajam. Preview live di Pi (butuh monitor):
   `rpicam-hello -t 0` → `Ctrl+C` bila sudah.
3. Verifikasi ulang dari laptop tanpa monitor:
   `./venv/bin/python camera_pi.py` lalu ambil hasilnya
   (`scp aquaponic@<ip-pi>:/tmp/camera_pi_test.jpg .`) dan lihat isinya.
4. Baru jalankan `./venv/bin/python kangkung_pi.py --test` → harus `[OK]`.

## Remote dari jauh (admin): Tailscale (rekomendasi)

```
# di Pi dan di laptop Anda:
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
Lalu SSH dari mana saja: `ssh aquaponic@nama-pi` (nama/IP Tailscale, mis.
`ssh aquaponic@ecofarm`). Tidak perlu buka port router, aman, tembus NAT kampus.

Cek cepat status jaringan Tailscale (di Pi maupun laptop):

```
tailscale status      # daftar perangkat + status online/relay
tailscale ip -4       # alamat 100.x.y.z milik perangkat ini
tailscale ping <nama-pi>   # tes jalur langsung/relay
```

Sekali pasang kunci agar tidak diminta password lagi:

```
# di laptop (sekali):  copy public key ke authorized_keys Pi
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh aquaponic@nama-pi "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

Akses VS Code dari laptop: ekstensi **Remote - SSH** → tekan `F1` →
`Remote-SSH: Connect to Host` → pilih `ecofarm`. `~/.ssh/config`:

```
Host ecofarm
  HostName <ip-tailscale-atau-nama-pi>
  User aquaponic
```

## Troubleshooting (kasus nyata di lapangan)

| Gejala | Penyebab | Solusi |
|---|---|---|
| `cv2.VideoCapture(0).isOpened() == True` tapi `read()` selalu `False` (0 frame) | pada kernel Pi modern, stack kamera **legacy MMAL rusak** (`dmesg` → `bcm2835-isp ... driver mismatch to MMAL`) | gunakan `"video_source": "csi"` → frame diambil `camera_pi.py` via libcamera |
| `ModuleNotFoundError: matplotlib` saat start pipeline | matplotlib hanya untuk fungsi plot debug | sudah diperbaiki (import *lazy* di `visualisasi()`); cukup kirim ulang `scp raspi/modules/kangkung_cv.py aquaponic@<ip-pi>:~/kangkung_pi/modules/` |
| venv tidak bisa `import picamera2` / `libcamera` | paket apt hanya terlihat oleh Python sistem | buat venv dengan `--system-site-packages` (`install.sh` sudah begitu); venv lama → buat ulang |
| `import cv2` gagal di Pi | dependensi belum terpasang | `cd ~/kangkung_pi && ./venv/bin/pip install -r requirements-pi.txt` |
| Build numpy berjalan >10 menit | tidak ada wheel siap-pakai untuk Python 3.13 di aarch64 | normal & sekali saja (hasilnya di-cache pip). Alternatif: `sudo apt install python3-numpy` + venv `--system-site-packages` |
| `Permission denied (publickey)` saat SSH dari laptop | `~/.ssh/authorized_keys` di Pi kosong/terhapus (mis. OS di-flash ulang) | kirim ulang public key — lihat § Remote dari jauh |
| Pi mati total, LED merah PWR tidak menyala | daya masuk | tes stopkontak, ganti adaptor 5 V/3 A + kabel USB-C, lepas semua peripheral lalu nyalakan bertahap |
| Gambar ungu/magenta & blur | modul NoIR + lensa belum fokus | jauhkan sumber cahaya dari frame, putar lensa berulir sampai tajam |
| `[WARN] bed tidak terdeteksi` | tidak semua tepi bed masuk frame / terlalu miring / terlalu gelap | luruskan & dekatkan kamera, pastikan 4 tepi terlihat, naikkan `csi_warmup_detik` |
| `[UPLINK] service-account.json belum ada` | kredensial Firebase belum ditaruh | taruh `service-account.json` di `~/kangkung_pi/` — sementara itu payload tetap aman di `outbox/` |
| Service tidak jalan setelah reboot | belum di-`enable` | `sudo systemctl enable kangkung` |
| WiFi kampus (WPA2-Enterprise) sering putus / tidak bisa saling ping | idle-timeout + client isolation | pakai hotspot/router sendiri untuk Pi, dan Tailscale untuk akses admin jarak jauh |

## Catatan desain (kenapa dibuat begini)

- **Kenapa libcamera/Picamera2, bukan `cv2.VideoCapture`?** OpenCV tidak
  menyediakan jalur CSI yang andal di kernel Pi modern (lihat bagian Kamera
  CSI). Pipeline hanya butuh **1 frame per siklus**, jadi membuka-menutup
  kamera per capture justru lebih hemat panas dan RAM daripada streaming terus.
- **Kenapa `matplotlib` dijadikan import lazy?** Fungsinya hanya untuk plot
  debug di laptop; membuatnya opsional mengurangi ukuran SD, RAM, dan waktu
  start service di Pi.
- **Kenapa `--system-site-packages` pada venv?** `picamera2`/`libcamera` hanya
  tersedia sebagai paket apt (bukan pip), sementara `opencv`/`numpy`/`firebase-admin`
  tetap dari pip di dalam venv.
- **Kenapa 1 dokumen per ±10 menit?** Kompromi suhu CPU outdoor, kuota Firestore,
  dan bandwidth — sekaligus cukup rapat untuk memantau pertumbuhan harian.

## Multi-user tanpa login (dashboard)

Dashboard web siap pakai ada di folder [`web/`](../web/README.md) (statis, tanpa
build): heatmap 4×6, snapshot, grafik riwayat 24 jam, distribusi status &
kesehatan, serta `fuzzy_input` untuk pompa. Coba dulu tanpa Firebase:

```
cd web && python -m http.server 8080      # http://localhost:8080  (mode demo)
```

Untuk mode live: salin `web/firebase-config.example.js` → `web/firebase-config.js`
lalu isi `firebaseConfig` dari Firebase Console, dan pasang aturan di bawah.

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

## Live kamera privat via Tailscale

Pi menjalankan `camera_live.py` sebagai server MJPEG ringan (**640×480, 2 FPS**).
Server hanya bind ke **IP Tailscale `100.123.187.56`**, sehingga tidak bisa dibuka
dari WiFi biasa/internet publik. Trafik tetap terenkripsi oleh WireGuard Tailscale.

Kamera bersifat eksklusif; monitor periodik dan preview live tidak boleh aktif
bersamaan. Pilih salah satu:

```bash
# Monitor periodik + dashboard
sudo systemctl start kangkung
sudo systemctl stop kangkung-camera

# Preview live
sudo systemctl stop kangkung
sudo systemctl start kangkung-camera
```

Buka link ber-token berikut dari laptop yang sudah login ke akun Tailscale
yang sama (token ada di URL; jangan bagikan ke publik):

```text
http://100.123.187.56:8787/?token=<TOKEN-DARI-PI>
```

Jika link berhenti, ambil link lengkap langsung dari Pi:

```bash
echo "http://100.123.187.56:8787/?token=$(cat ~/.config/kangkung-camera.token)"
```

Untuk merotasi token (membatalkan semua link lama):

```bash
rm ~/.config/kangkung-camera.token
sudo systemctl restart kangkung-camera
```

Cek kondisi stream dari Pi/laptop:

```bash
curl "http://127.0.0.1:8787/health?token=$(cat ~/.config/kangkung-camera.token)"
journalctl -u kangkung-camera -f
```

> Jangan membagikan atau melakukan screenshot link karena URL tersebut berisi token
> rahasia. Tailscale yang membatasi siapa saja yang dapat masuk ke jaringan.

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

Modul di `raspi/modules/` adalah salinan dari `files/` (`adaptive_bed.py`,
`kangkung_cv.py`) — edit di laptop, lalu kirim ulang dari akar repo:

```
scp raspi/modules/kangkung_cv.py aquaponic@<ip-pi>:~/kangkung_pi/modules/
scp raspi/camera_pi.py raspi/kangkung_pi.py aquaponic@<ip-pi>:~/kangkung_pi/
```

lalu restart service:

```
ssh aquaponic@<ip-pi> "sudo systemctl restart kangkung"
```

Khusus `config.json`: setelah diubah di Pi, tidak perlu restart — dibaca ulang
tiap siklus baru (setelah `interval_menit`).

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
| `kangkung_pi.py` | Pipeline inti (capture → analisis → payload → kirim) + opsi `--test` |
| `camera_pi.py` | Akuisisi frame kamera CSI via libcamera (Picamera2 → fallback rpicam-jpeg) |
| `camera_live.py` | Preview MJPEG 640×480/2 FPS yang privat melalui Tailscale |
| `modules/` | Salinan `adaptive_bed.py` + `kangkung_cv.py` dari `files/` di repo |
| `firebase_uplink.py` | Upload Firestore/Storage + antrean offline (`outbox/` → `outbox/sent/`) |
| `fuzzy_export.py` | Membangun `fuzzy_input` untuk kontroler fuzzy: %klorosis, %nekrosis, `zona_sakit`, **PSI 0–100** (`psi`, `psi_maks`, `psi_versi`) + `indeks_sehat` legacy |
| `thermal_guard.py` | Baca suhu SoC; tunda capture saat panas |
| `install.sh` | Installer: copy paket → venv (`--system-site-packages`) → deps → systemd |
| `requirements-pi.txt` | Dependensi pip: `opencv-python-headless`, `numpy`, `firebase-admin` |
| `service/kangkung.service` | Unit systemd monitor periodik (auto-start + auto-restart) |
| `service/kangkung-camera.service` | Unit systemd preview live (manual; eksklusif dengan monitor) |
| `config.json` | Konfigurasi per perangkat (file utama yang diedit) — lihat § Konfigurasi |
| `service-account.json.EXAMPLE` | Kerangka kredensial Firebase (salin → `service-account.json`, jangan di-commit) |
| `README.md` | Dokumen ini |
