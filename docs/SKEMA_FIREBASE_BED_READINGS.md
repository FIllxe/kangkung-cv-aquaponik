# Skema Firebase `bed_readings` — v1.0 (Tahap A)

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
| `zona` | map | ✅ | **24 entri** `R{1-4}C{1-6}` → `{coverage: number, status: string}` SAJA (ramping) |
| `snapshot_url` | string/null | ⬜ | URL foto di Storage (isi setelah upload PNG/JPG) |
| `suhu_pi_c` | number/null | ⬜ | suhu SoC Pi saat capture (untuk monitoring ketahanan hardware) |

**Doc ID:** `{device_id}_{YYYYmmddTHHMMSS}` — contoh: `pi-bed-01_20260903T211532`

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
