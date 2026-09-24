# gt/ — Ground Truth Mask

Folder ini untuk mask anotasi manual dari `files/buat_gt.py`.
Kosong saat ini — mask GT belum dibuat (lihat `../docs/PANDUAN_GT.md`).

Konvensi nama (output otomatis dari tool, jangan diubah):

| File | Kelas |
|---|---|
| `<stem>_gt.png` | Tanaman total (putih = tanaman) |
| `<stem>_kuning_gt.png` | Kuning / klorosis |
| `<stem>_coklat_gt.png` | Coklat / nekrosis |

Sumber gambar: `../dataset1/` (bed_01_seedling … bed_05_mixed + 2 PNG).

Cara membuat:

```
cd ../files
python buat_gt.py ../dataset1/bed_04_ready.jpg --out ../gt
```

Setelah ≥ 5 gambar dianotasi:

```
python evaluasi_segmentasi.py --images ../dataset1 --gt ../gt
python bandingkan_metode.py   --images ../dataset1 --gt ../gt
```

Catatan: mask `.png` hasil anotasi tidak di-commit (lihat `.gitignore`).
