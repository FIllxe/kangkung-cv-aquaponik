# Dashboard Web — Monitor Kangkung Live

Halaman statis (HTML/CSS/JS murni, **tanpa build/npm**) untuk memantau hasil
analisis Raspberry Pi secara live. Dashboard **hanya membaca** Firestore &
Storage — tidak mengirim perintah apa pun ke Pi (Pi tetap *push-only*).

## Fitur

| Bagian | Isi |
|---|---|
| Kartu ringkasan | Coverage rata-rata (+simpangan baku), zona siap panen, indeks sehat, suhu Pi (warna mengikuti ambang 70/75 °C) |
| Peta zona 4×6 | 24 kotak berwarna sesuai status (belum/hampir/siap/harus panen) + titik kecil status kesehatan; klik untuk detail zona |
| Snapshot terakhir | Gambar beranotasi dari Firebase Storage (`snapshot_url`) |
| Grafik riwayat | Kurva `coverage_rata` dari maks 144 dokumen terakhir (±24 jam) + garis ambang 25/55/80%, hover untuk nilai |
| Distribusi | Jumlah zona per status panen & per status kesehatan daun |
| Rekomendasi & fuzzy | Teks rekomendasi + `fuzzy_input` (`kuning_pct`, `coklat_pct`, `zona_sakit`, `psi`, `psi_maks`, `psi_versi`, `indeks_sehat` legacy) sebagai input kontroler fuzzy. Kartu utama menampilkan **PSI 0–100, makin tinggi = makin stres** (bukan "makin sehat") |
| Zona perlu perhatian | Daftar prioritas: sakit → waspada → over-dense |
| Indikator | `LIVE` / `TERPUTUS` / `MENUNGGU DATA` / `MODE DEMO` + “update x menit lalu” |

Warna status disalin persis dari `files/kangkung_cv.py` (`WARNA_STATUS`) dan
ambang kesehatan dari `KESEHATAN` — jadi tampilan dashboard = hasil backend.

## 1. Lihat dulu tanpa Firebase (mode demo)

```bash
cd web
python -m http.server 8080          # buka http://localhost:8080
# atau paksa demo:  http://localhost:8080/?demo=1
```

Mode demo juga aktif otomatis bila `firebase-config.js` belum ada atau SDK
Firebase tidak bisa dimuat (offline). Data yang tampil adalah **contoh**.

## 2. Hubungkan ke Firebase (mode live)

1. Firebase Console → ⚙ **Project settings** → General → *Your apps* →
   daftarkan **Web app** (`</>`) → salin objek `firebaseConfig`.
2. Salin template konfigurasi, lalu isi nilainya:
   ```bash
   cd web
   cp firebase-config.example.js firebase-config.js     # Windows: copy
   ```
3. Pastikan Firestore sudah memberi izin baca publik (Firestore → Rules):
   ```
   match /bed_readings/{doc} {
     allow read: if true;
     allow write: if false;      // tulis hanya lewat service-account (Pi)
   }
   ```
   Dan Storage (agar snapshot tampil):
   ```
   match /snapshots/{all=**} {
     allow read: if true;
     allow write: if false;
   }
   ```
4. Muat ulang halaman → badge berubah menjadi `LIVE`.

Nama collection diambil dari `window.FIREBASE_COLLECTION` (default
`bed_readings`) — samakan dengan `firebase.collection` di `raspi/config.json`.

## 3. Publikasi (opsional)

**A. Firebase Hosting** (paling mudah, satu project dengan Firestore):

```bash
npm install -g firebase-tools
firebase login
firebase init hosting      # public directory: web  (jangan "single-page app")
firebase deploy --only hosting
```

**B. GitHub Pages / server statis lain:** unggah isi folder `web/` apa adanya
(tanpa `firebase-config.js` bila repo publik → isi config manual di server).
Jangan lupa `firebase-config.js` ada di `.gitignore`.

## Struktur

| File | Fungsi |
|---|---|
| `index.html` | Struktur halaman + slot elemen |
| `style.css` | Tema gelap (palet sama dengan skrip Python) + layout responsif |
| `app.js` | Logika: ambil data, hitung cadangan agregat, render, grafik, mode demo/live |
| `firebase-config.example.js` | Template config (disalin jadi `firebase-config.js`) |
| `README.md` | Dokumen ini |

## Catatan teknis

- **Tahan dokumen ringkas**: `lengkapiPayload()` menghitung ulang agregat
  (coverage rata-rata/std, distribusi, `fuzzy_input`) bila field-nya tidak ada,
  jadi dashboard tetap benar meski skema dokumen berubah.
- **Tanpa indeks komposit**: kueri hanya `orderBy("timestamp")` + `limit(144)`.
  Bila nanti multi-bed (`where("device_id","==",…)` + `orderBy`), Firestore akan
  meminta *composite index* — buat lewat tautan yang muncul di console.
- **Tanpa library chart**: grafik digambar di `<canvas>` supaya ringan dan bisa
  dibuka di HP.
- **Snapshot**: URL ditambah parameter anti-cache agar gambar baru langsung
  tampil saat dokumen berubah.

## Troubleshooting

| Gejala | Penyebab & solusi |
|---|---|
| Badge `MODE DEMO` padahal config sudah diisi | `firebase-config.js` salah nama/letak (harus di folder `web/`), atau `projectId` kosong |
| Badge `GAGAL MEMBACA` (`permission-denied`) | Aturan Firestore belum `allow read: if true`, atau `FIREBASE_COLLECTION` salah |
| `MENUNGGU DATA` | Collection kosong — Pi belum jalan / `outbox/` belum terkirim (`journalctl -u kangkung -f`) |
| Snapshot tidak muncul | `snapshot_url` kosong (upload Storage gagal) atau aturan Storage menolak baca |
| Grafik kosong | Dokumen < 2 → normal pada awal deploy |
