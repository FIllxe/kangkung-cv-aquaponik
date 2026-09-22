"""
=============================================================================
  BUAT GROUND TRUTH — Tool anotasi mask manual (brush painting)
  Untuk membuat mask ground truth yang dipakai evaluasi_segmentasi.py
=============================================================================
  CARA PAKAI:
    python buat_gt.py bed_04_ready.jpg
    python buat_gt.py images/bed_04_ready.jpg --out gt

  KONTROL:
    Klik / drag kiri  : cat area (putih)
    E                 : toggle cat <-> hapus (eraser)
    + / -  (atau ]/[) : perbesar / perkecil brush
    Z                 : undo terakhir
    C                 : reset mask kelas aktif (kosongkan)
    N                 : ganti kelas GT (Total -> Kuning -> Coklat)
    S                 : simpan mask kelas aktif
    Q / ESC           : keluar

  KELAS GT & KONVENSI NAMA FILE (folder gt/):
    Tanaman total : <stem>_gt.png        (putih = semua jaringan tanaman)
    Kuning        : <stem>_kuning_gt.png (klorosis)
    Coklat        : <stem>_coklat_gt.png (nekrosis / mati)
  Semua disimpan biner: putih (255) = termasuk kelas, hitam (0) = bukan.
=============================================================================
"""

import cv2
import numpy as np
import argparse
import sys
from pathlib import Path

# ─── Kelas GT ────────────────────────────────────────────────────────────────
KELAS = [
    ("",        "Tanaman Total"),
    ("_kuning", "Kuning (Klorosis)"),
    ("_coklat", "Coklat (Nekrosis)"),
]
WARNA_OVERLAY = [(0, 0, 255), (0, 255, 255), (60, 80, 160)]  # BGR per kelas

# ─── State global (dibagikan ke mouse callback) ──────────────────────────────
STATE = {
    "drawing": False,
    "erase":   False,
    "brush":   20,
    "undo_stack": [],
    "masks":    {},       # suffix -> mask
    "kelas_idx": 0,
}


def _kelas():
    sfx, nama = KELAS[STATE["kelas_idx"]]
    return sfx, nama, STATE["masks"][sfx]


def _tampilkan(img, window):
    _, nama, mask = _kelas()
    warna = WARNA_OVERLAY[STATE["kelas_idx"]]
    ov = img.copy()
    ov[mask > 0] = warna
    view = cv2.addWeighted(img, 0.6, ov, 0.4, 0)

    mode = "HAPUS" if STATE["erase"] else "CAT"
    cv2.putText(view, f"[{STATE['kelas_idx']+1}/3] {nama}  |  Mode: {mode}  "
                      f"Brush: {STATE['brush']}  "
                      f"Coverage: {mask.sum()/255/mask.size*100:.1f}%",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(view, "E:mode  +/-:brush  Z:undo  C:reset  N:ganti kelas  "
                      "S:simpan  Q:keluar",
                (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.imshow(window, view)


def _mouse(event, x, y, flags, param):
    img, window = param
    if event == cv2.EVENT_LBUTTONDOWN:
        STATE["drawing"] = True
        _, _, mask = _kelas()
        STATE["undo_stack"].append(mask.copy())
        if len(STATE["undo_stack"]) > 30:
            STATE["undo_stack"].pop(0)
    elif event == cv2.EVENT_MOUSEWHEEL:
        STATE["brush"] = int(np.clip(
            STATE["brush"] + (5 if flags > 0 else -5), 2, 100))
    if STATE["drawing"]:
        _, _, mask = _kelas()
        if event in (cv2.EVENT_LBUTTONUP, cv2.EVENT_MOUSEMOVE,
                     cv2.EVENT_LBUTTONDOWN):
            val = 0 if STATE["erase"] else 255
            cv2.circle(mask, (x, y), STATE["brush"], val, -1)
            if event == cv2.EVENT_LBUTTONUP:
                STATE["drawing"] = False
        _tampilkan(img, window)


def main():
    parser = argparse.ArgumentParser(
        description="Tool anotasi ground truth mask (brush painting, 3 kelas)")
    parser.add_argument("image", type=str, help="Path gambar yang dianotasi")
    parser.add_argument("--out", type=str, default="gt",
                        help="Folder output mask GT (default: gt/)")
    args = parser.parse_args()

    fpath = Path(args.image)
    if not fpath.exists():
        print(f"[ERROR] File tidak ditemukan: {fpath}")
        sys.exit(1)

    img = cv2.imread(str(fpath))
    if img is None:
        print(f"[ERROR] Tidak bisa membaca gambar: {fpath}")
        sys.exit(1)

    # Resize agar muat layar (maks lebar 1280), proporsional
    max_w = 1280
    if img.shape[1] > max_w:
        scale = max_w / img.shape[1]
        img = cv2.resize(img, (max_w, int(img.shape[0] * scale)))
    # Mask di-resize otomatis oleh evaluasi_segmentasi.py — cukup simpan
    # pada resolusi tampilan.

    STATE["masks"] = {sfx: np.zeros(img.shape[:2], dtype=np.uint8)
                      for sfx, _ in KELAS}
    STATE["kelas_idx"] = 0
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    window = "Buat Ground Truth - Kangkung"
    cv2.namedWindow(window, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(window, _mouse, (img, window))
    _tampilkan(img, window)

    sfx0, nama0, _ = _kelas()
    print(f"[INFO] Anotasi: {fpath.name}")
    print(f"[INFO] Kelas aktif: {nama0} -> "
          f"{out_dir / (fpath.stem + sfx0 + '_gt.png')}")
    print("[INFO] N = ganti kelas, S = simpan kelas aktif, Q = keluar.")

    while True:
        key = cv2.waitKey(20) & 0xFF
        if key in (ord("q"), 27):                      # q / ESC
            break
        elif key in (ord("+"), ord("]")):
            STATE["brush"] = min(100, STATE["brush"] + 5)
            _tampilkan(img, window)
        elif key in (ord("-"), ord("[")):
            STATE["brush"] = max(2, STATE["brush"] - 5)
            _tampilkan(img, window)
        elif key == ord("e"):
            STATE["erase"] = not STATE["erase"]
            _tampilkan(img, window)
        elif key == ord("z"):
            if STATE["undo_stack"]:
                sfx_cur, _, _ = _kelas()
                STATE["masks"][sfx_cur][:] = STATE["undo_stack"].pop()
                _tampilkan(img, window)
        elif key == ord("c"):
            _, _, mask = _kelas()
            STATE["undo_stack"].append(mask.copy())
            mask[:] = 0
            _tampilkan(img, window)
        elif key == ord("n"):
            STATE["kelas_idx"] = (STATE["kelas_idx"] + 1) % len(KELAS)
            STATE["undo_stack"].clear()
            sfx, nama, _ = _kelas()
            print(f"[INFO] Kelas aktif: {nama} -> "
                  f"{out_dir / (fpath.stem + sfx + '_gt.png')}")
            _tampilkan(img, window)
        elif key == ord("s"):
            sfx, nama, mask = _kelas()
            out_path = out_dir / f"{fpath.stem}{sfx}_gt.png"
            cv2.imwrite(str(out_path), mask)
            cov = mask.sum() / 255 / mask.size * 100
            print(f"[OK] GT [{nama}] disimpan: {out_path} (coverage {cov:.1f}%)")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()