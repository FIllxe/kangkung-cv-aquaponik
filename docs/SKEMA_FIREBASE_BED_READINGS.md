# Skema Firebase `bed_readings` — v1.1 (Tahap A) + kontrak tim fuzzy

> Kontrak data antara pipeline CV (kangkung aquaponik) dan dashboard web yang sudah ada.
> Satu dokumen = satu sesi analisis bed. ID dokumen idempotent: upload ulang tidak menduplikasi.

## Collection: `bed_readings`

| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| `device_id` | string | ✅ | ID perangkat, mis. `pi-bed-01` |
| `timestamp` | string | ✅ | ISO-8601 + zona waktu, mis. `2026-09-03T21:15:32+07:00` |
| `mode` | string | ✅ | `STANDARD` \| `ADAPTIVE` \| `MANUAL` \| `AUTO` |
| `coverage_rata` | number | ✅ | rata-rata coverage 24 zona (%), 2 desimal |
| `coverage_std` | number | ✅ | simpangan baku coverage (%) |
| `zona_siap_panen` | number | ✅ | jumlah zona status `siap_panen`/`harus_panen` |
| `persen_siap` | number | ✅ | persen zona siap (0–100) |
| `status_distribusi` | map | ✅ | `{belum_siap, hampir_siap, siap_panen, harus_panen}` (jumlah zona) |
| `rekomendasi` | string | ✅ | teks rekomendasi, tanpa emoji |
| `zona` | map | ✅ | **24 entri** `R{1-4}C{1-6}` → `{coverage, status, pct_kuning, pct_coklat, kesehatan}` |
| `kesehatan` | map | ✅ | `{kuning_rata, coklat_rata, distribusi, rekomendasi}` — ringkasan gejala daun seluruh bed |
| `fuzzy_input` | map | ✅ | input crisp untuk tim fuzzy: `{kuning_pct, coklat_pct, zona_sakit, psi, psi_maks, psi_versi, indeks_sehat}` — definisi PSI di bawah |
| `snapshot_url` | string/null | ⬜ | URL foto di Storage (isi setelah upload PNG/JPG) |
| `suhu_pi_c` | number/null | ⬜ | suhu SoC Pi saat capture (untuk monitoring ketahanan hardware) |

**Doc ID:** `{device_id}_{YYYYmmddTHHMMSS}` — contoh: `pi-bed-01_20260903T211532`

## Kontrak PSI (Plant Stress Index) — baru di v1.1

`fuzzy_input.psi` = skalar **0–100, TINGGI = makin stres**, dihitung di satu
sumber tunggal: `kangkung_cv.hitung_psi()`.

```
PSI = 100 × min(1, 0.4·min(kuning/25, 1) + 0.6·min(coklat/8, 1))
     └ normalisasi ke ambang KESEHATAN: kuning_sakit = 25%, coklat_sakit = 8%
```

| Field | Arti |
|---|---|
| `psi` | severity agregat bed (rata-rata 24 zona) |
| `psi_maks` | PSI **zona terburuk**. 1 zona mati di 24 hanya menyumbang 1/24 ke rata-rata, jadi dikirim terpisah agar tidak hilang |
| `psi_versi` | versi rumus (`"1.0"`) — penerima wajib **menolak** versi tak dikenal |
| `indeks_sehat` | **legacy**, arah berlawanan = `100 − psi`. Jangan dipakai sebagai input fuzzy baru |

Mengapa bukan rumus lama `min(100, 2·kuning + 5·coklat)`: rumus itu **mentok di
20% coklat / 50% kuning**, sehingga fuzzy kehilangan gradien justru di area paling
penting (bukti: `python cek_psi.py` → kolom "jenuh?").

⚠ **Terminologi:** "PSI" di proyek ini = *Plant Stress Index*, **bukan**
*Photosystem I* (fisiologi tumbuhan). Selalu tulis lengkap di laporan.

Rekomendasi set fuzzy (untuk tim fuzzy — perlu disepakati bersama):

| Anteseden | Rentang | Fungsi |
|---|---|---|
| `psi` | 0–100 | severity agregat → membership {rendah, sedang, tinggi} |
| `psi_maks` | 0–100 | "ada zona xmmal" → menaikkan prioritas aksi |
| `zona_sakit` | 0–24 | extent (berapa luas bed yang terdampak) |

## Loop kedua: keputusan tim fuzzy (belum ada di repo)

```
Pi → bed_readings.psi → ESP32/tim fuzzy → keputusan_fuzzy → notif dashboard
                                                              → ACC manager
                                                                → audit
```

Koleksi baru **`keputusan_fuzzy`** (satu dokumen = satu usulan tindakan):

| Field | Tipe | Keterangan |
|---|---|---|
| `doc_id` | string | `{device_id}_{YYYYmmddTHHMMSS}` (idempotent) |
| `sumber_doc_id` | string | dokumen `bed_readings` yang jadi dasar keputusan |
| `psi_dipakai` | number | nilai PSI yang dibaca (0–100) |
| `psi_versi` | string | versi rumus yang dipakai pembaca |
| `aksi` | string | `ganti_air` \| `tambah_nutrisi` \| `cek_pH` \| `panen_selektif` \| `tidak_ada_tindakan` |
| `target` | string/null | zona/air yang jadi sasaran, mis. `R2C3` |
| `durasi_menit` | number/null | lama pompa menyala, bila ada |
| `alasan` | string | ringkasan rule yang menyala |
| `status` | string | `menunggu_acc` → `disetujui` \| `ditolak` → `dieksekusi` |
| `actor` | string/null | siapa yang ACC (audit) |
| `timestamp` | string | ISO-8601 +07:00 |

## Aturan keselamatan (wajib di sisi pembaca/ESP)

1. **Data basi (stale):** abaikan PSI bila `timestamp` dokumen > **30 menit**
   (siklus upload Pi = 10 menit, lihat `raspi/config.json`). Jangan bereaksi
   pada PSI lama — kondisi di lapangan bisa sudah berubah.
2. **Nilai hilang:** bila `psi` tidak ada (null/tidak terbaca) → ** tahan
   tindakan**, jangan perlakukan sebagai 0 (= sehat).
3. **Anti-spam:** hanya buat dokumen `keputusan_fuzzy` baru bila `aksi` atau
   `status` berubah, atau cooldown ≥ 60 menit untuk aksi yang sama.
4. **Tidak ada aktuasi otomatis:** `status` wajib `menunggu_acc` saat ditulis;
   perubahan ke `disetujui` dilakukan manusia. Ini yang membuat sistem aman
   intervensi: nekrosis tidak dapat "disembuhkan" pompa.
5. **Rujukan angka:** PSI = 60 berarti didominasi nekrosis (coklat ≥ 8%),
   PSI = 40 berarti didominasi klorosis (kuning ≥ 25%), PSI ≈ 0 saat bed
   sehat — bandingkan dengan data via `python cek_psi.py`.

## Batas ukuran & frekuensi

- Dokumen payload ± **2–3 KB** (zona ramping: hanya `coverage` + `status`).
- Frekuensi upload Pi outdoor: **1× per 5–10 menit** (bukan per frame) — hemat panas CPU, kuota write, dan bandwidth.
- TIDAK diupload ke Firestore: `*_timeseries.csv` (763 baris), `*_beranotasi.mp4` (44–100 MB), PNG mentah `*_segmentasi.png` (1,2–2,7 MB). Semua itu tetap di server/laptop lokal; hanya **snapshot JPEG terkompresi** (±200–400 KB) yang naik ke Storage bila dashboard butuh gambar.

## Contoh dokumen

Lihat `output\firebase\bed_readings_contoh.json` (dari `bed_04_ready_laporan.json`:
coverage 22,84%, distribusi 14/9/1/0, 1 zona siap).

## Cara membuat payload (lokal, tanpa Firebase)

```
cd files
python buat_payload_dashboard.py                     # semua laporan batch
python buat_payload_dashboard.py --file <path.json> --mode ADAPTIVE
```

Output: `output\firebase\<stem>_payload.json` → upload manual via Firestore Console
(payload ada di key `payload`; `doc_id` dipakai sebagai nama dokumen).

## Alur nanti (Tahap B — Oktober)

1. `firebase_uplink.py` (butuh `firebase-admin` + service-account JSON, TIDAK di-commit):
   baca payload terbaru → `set()` ke Firestore + upload snapshot ke Storage → isi `snapshot_url`.
2. Offline queue: koneksi putus → antrean lokal → kirim ulang saat online.
3. Thermal backoff: `suhu_pi_c` > 75°C → tunda capture/upload 5–10 menit.

## Status keputusan yang perlu dikonfirmasi pemilik dashboard

- [ ] Nama collection final (`bed_readings`?)
- [ ] Field cukup untuk grid 4×6 + grafik distribusi?
- [ ] Frekuensi upload 1×/5–10 menit OK?
- [ ] Path Storage untuk snapshot (mis. `snapshots/{device_id}/{doc_id}.jpg`)?
