# -*- coding: utf-8 -*-
"""Generator PNG HD untuk laporan TUGAS AKHIR - render dari hardware/*.scad.

Pipeline per gambar (supersample 2x -> chroma-key -> downscale):
  1. tulis wrapper sementara hardware/_hd_<nama>.scad (override mode + include)
  2. render OpenSCAD: --preview=png (OpenCSG), imgsize 2x ukuran final
  3. chroma-key: warna latar OpenSCAD (disampling dari sudut gambar)
     diganti putih murni #FFFFFF dengan tepi lembut (anti halo abu-abu)
  4. downscale LANCZOS ke ukuran final -> tepi antialias halus
  5. simpan hardware/renders/HD_<nama>.png

MENGAPA --preview DAN BUKAN --render (penting, jangan diubah balik):
  CGAL (--render) di build OpenSCAD Windows ini MENGABAIKAN color() saat
  ekspor PNG - semua part keluar salah warna (DimGray jadi teal, interior
  jadi emas), dan alpha diabaikan sehingga mode xray jadi solid. OpenCSG
  (--preview) menghormati color() dan alpha apa adanya. STL tetap CGAL.

Jalankan : python hardware/buat_gambar_laporan.py
Output   : hardware/renders/HD_*.png  (latar putih, siap tempel ke halaman
           laporan lewat docs/buat_gambar_3d_laporan.py)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
RENDERS = ROOT / "renders"

# Kandidat lokasi openscad.com - konsisten dengan build.ps1 / preview.ps1
SCAD_CANDIDATES = [
    Path(r"C:\Program Files\OpenSCAD\openscad.com"),
    Path(r"C:\Program Files (x86)\OpenSCAD\openscad.com"),
    Path(__import__("os").environ.get("LOCALAPPDATA", "")) / "Programs" / "OpenSCAD" / "openscad.com",
]

# Supersample: render 2x lalu kecilkan -> antialias halus
SUPERSAMPLE = 2

# ---------------------------------------------------------------------------
# Daftar gambar. WxH = UKURAN FINAL (px). cam = gimbal OpenSCAD (rx,ry,rz).
# ---------------------------------------------------------------------------
SCENES = [
    # --- halaman rakitan ---
    dict(nama="rakit_iso",       src="preview", mode="rakit",   cam=(65, 0, 45),  w=2400, h=1600),
    dict(nama="rakit_samping",   src="preview", mode="rakit",   cam=(90, 0, 0),   w=2400, h=1300),
    dict(nama="rakit_miring",    src="preview", mode="rakit",   cam=(150, 0, 20), w=1800, h=1500),
    # --- halaman exploded / xray ---
    dict(nama="ledakan_iso",     src="preview", mode="ledakan", cam=(65, 0, 45),  w=2600, h=1700),
    dict(nama="ledakan_samping", src="preview", mode="ledakan", cam=(90, 0, 0),   w=2600, h=1400),
    dict(nama="xray_iso",        src="preview", mode="xray",    cam=(65, 0, 45),  w=2200, h=1500),
    # --- grid part cetak (render mandiri tiap file) ---
    dict(nama="part_klem",       src="mount_base.scad",      cam=(65, 0, 45), w=1400, h=1200),
    dict(nama="part_lengan",     src="arm.scad",             cam=(65, 0, 45), w=1600, h=1000),
    dict(nama="part_box",        src="enclosure.scad",       cam=(65, 0, 45), w=1400, h=1200),
    dict(nama="part_tutup",      src="enclosure_tutup.scad", cam=(65, 0, 45), w=1400, h=1200),
    dict(nama="part_jepit",      src="camera_holder.scad",   cam=(65, 0, 45), w=1400, h=1200),
]


def cari_openscad() -> Path:
    for c in SCAD_CANDIDATES:
        if c.exists():
            return c
    raise FileNotFoundError(
        "OpenSCAD tidak ditemukan di: " + ", ".join(str(c) for c in SCAD_CANDIDATES)
    )


def tulis_wrapper(sc: dict) -> Path:
    """Wrapper minimal - OpenSCAD 2021.01 tidak meneruskan -D ke include."""
    if sc["src"] == "preview":
        body = f'mode_ov = "{sc["mode"]}";\ninclude <preview.scad>\n'
    else:  # part tunggal: render mandiri guard-nya aktif sendiri
        body = f'include <{sc["src"]}>\n'
    p = ROOT / f"_hd_{sc['nama']}.scad"
    p.write_text(body, encoding="utf-8")
    return p


def chroma_key_putih(img: Image.Image) -> Image.Image:
    """Ganti latar OpenSCAD (disampling dari4 sudut) jadi putih murni.

    d = selisih maks per-pixel terhadap warna latar; f = clamp((d-6)/30).
    Hasil = 255 - (255 - p) * f, sehingga:
      d <= 6  (latar)  -> putih total (255)
      d >= 36 (objek)  -> warna asli dipertahankan
      di antaranya      -> blending lembut ke putih (anti halo abu-abu)
    """
    import numpy as np

    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    sudut = np.array([a[2, 2], a[2, -3], a[-3, 2], a[-3, -3]], dtype=np.float32)
    bg = np.median(sudut, axis=0)
    d = np.abs(a - bg).max(axis=2)
    f = np.clip((d - 6.0) / 30.0, 0.0, 1.0)[..., None]
    out = 255.0 - (255.0 - a) * f
    return Image.fromarray(out.round().astype("uint8"), "RGB")


def render(sc: dict, scad: Path) -> Path:
    wrapper = tulis_wrapper(sc)
    w2, h2 = sc["w"] * SUPERSAMPLE, sc["h"] * SUPERSAMPLE
    raw = ROOT / "_hd_raw.png"
    raw.unlink(missing_ok=True)
    rx, ry, rz = sc["cam"]
    cmd = [
        str(scad),
        "--preview=png",
        "--viewall", "--autocenter",
        "--projection=o",
        f"--camera=0,0,0,{rx},{ry},{rz},0",
        f"--imgsize={w2},{h2}",
        "--colorscheme=Tomorrow",
        "-o", str(raw),
        str(wrapper),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT))
    wrapper.unlink(missing_ok=True)
    err = (r.stderr or "") + (r.stdout or "")
    if "ERROR" in err or not raw.exists():
        raise RuntimeError(f"{sc['nama']}: OpenSCAD gagal:\n" + err[:2000])
    if "2-manifold" in err:
        print(f"  ! {sc['nama']}: peringatan manifold - cek hasil render")

    img = chroma_key_putih(Image.open(raw))
    img = img.resize((sc["w"], sc["h"]), Image.LANCZOS)
    dst = RENDERS / f"HD_{sc['nama']}.png"
    img.save(dst, optimize=True)
    raw.unlink(missing_ok=True)
    return dst


def main() -> int:
    only = set(sys.argv[1:])  # opsional: nama scene untuk render sebagian
    scad = cari_openscad()
    RENDERS.mkdir(exist_ok=True)
    scenes = [s for s in SCENES if not only or s["nama"] in only]
    print(f"OpenSCAD : {scad}")
    print(f"Scenes   : {len(scenes)} (supersample {SUPERSAMPLE}x)")
    for sc in scenes:
        dst = render(sc, scad)
        print(f"  OK {sc['nama']:<18} -> {dst.name}  {sc['w']}x{sc['h']}")
    print("Selesai.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
