# 📦 hardware/files/ — Box Pi4B pasangan (produk terpisah, sudah final)

Bodi box alternatif yang **sudah final** + skrip pembuatnya. Pasangannya
adalah `../tutup_pi4b.scad` (bukan `../enclosure_tutup.scad` — itu untuk box
parametrik lain, jangan dicampur).

| File | Peran |
|---|---|
| `build_pi4b_enclosure.py` | Skrip pembuat bodi (perlu `trimesh` + `shapely`; output: `pi4b_camera_enclosure_bottom.stl`) |
| `pi4b_camera_enclosure_bottom.stl` | Bodi 93,0 × 99,5 × 40,0 mm (kavitas 89 × 95,5) — **final, jangan bangun ulang** |
| `pi4b_fit_check_sections.png` | Gambar verifikasi penampang pas-fit tutup |

Verifikasi tutup (hasil harus irisan 0,0 mm³, lihat `../README.md`):

```powershell
cd ..\hardware
openscad.com -o stl\tutup_pi4b.stl tutup_pi4b.scad
.\cek_mesh.ps1 -File (Resolve-Path .\stl\tutup_pi4b.stl)
```
