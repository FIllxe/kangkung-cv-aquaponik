"""
=============================================================================
  KALIBRASI KAMERA — Simpan posisi tepi bed untuk kamera tetap (fixed mount)
  Dipasangkan dengan: proses_video.py, live_monitor.py
=============================================================================
  CARA PAKAI:
    python kalibrasi_kamera.py video_setup.mp4        # dari video/urutan setup
    python kalibrasi_kamera.py 0                      # dari kamera langsung
    python kalibrasi_kamera.py video.mp4 --manual     # paksa klik 4 sudut
    python kalibrasi_kamera.py --cek                  # cek kalibrasi tersimpan
    python kalibrasi_kamera.py ... --out path.json    # lokasi file kalibrasi

  ALUR:
    Deteksi otomatis 4 sudut bed (fallback klik manual) → preview warp + grid
    → S = simpan ke kalibrasi_kamera.json → dipakai operasional harian
    (warp saja per frame, tanpa deteksi ulang — hemat CPU di Raspberry Pi).

  Jika kamera digeser dari mount-nya → jalankan kalibrasi ulang (30 detik).
=============================================================================
"""

import cv2
import numpy as np
import json
import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adaptive_bed import (deteksi_sudut_bed, pilih_sudut_manual,
                          matriks_warp, warp_bed, analisis_grid,
                          gambar_quad, resize_frame, CornerSmoother,
                          KANVAS_W, KANVAS_H)

KALIBRASI_DEFAULT = Path("kalibrasi_kamera.json")


# ─── SIMPAN / MUAT KALIBRASI ─────────────────────────────────────────────────

def simpan_kalibrasi(path, pts, frame_w, frame_h, sumber, mode):
    """Simpan sudut bed + matriks homografi ke file JSON."""
    M = matriks_warp(pts)
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sumber": str(sumber),
        "mode": mode,
        "frame_w": int(frame_w),
        "frame_h": int(frame_h),
        "kanvas_w": KANVAS_W,
        "kanvas_h": KANVAS_H,
        "corners": np.round(pts, 2).tolist(),
        "matrix": np.round(M, 6).tolist(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Kalibrasi disimpan: {path}")
    print(f"     Sudut TL{tuple(np.round(pts[0],1))} TR{tuple(np.round(pts[1],1))} "
          f"BR{tuple(np.round(pts[2],1))} BL{tuple(np.round(pts[3],1))}")
    return data


def muat_kalibrasi(path, frame_w=None, frame_h=None):
    """
    Muat kalibrasi JSON. Jika resolusi frame sekarang berbeda dari saat
    kalibrasi, sudut di-skala proporsional dan matriks dihitung ulang.
    Return (M, corners) atau (None, None).
    """
    if not Path(path).exists():
        return None, None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    pts = np.float32(data["corners"])
    if frame_w and frame_h and (frame_w != data["frame_w"] or
                                frame_h != data["frame_h"]):
        sx = frame_w / data["frame_w"]
        sy = frame_h / data["frame_h"]
        pts = pts * np.float32([sx, sy])
        print(f"[INFO] Resolusi beda (kalibrasi {data['frame_w']}x{data['frame_h']} "
              f"vs sekarang {frame_w}x{frame_h}) → sudut di-skala.")
    M = matriks_warp(pts)
    return M, pts


# ─── PREVIEW ─────────────────────────────────────────────────────────────────

def tampil_preview(frame, pts, judul=""):
    """Tampilkan side-by-side: asli+quad | warp+grid. Return disp."""
    asli = gambar_quad(frame.copy(), pts)
    warped = warp_bed(frame, matriks_warp(pts))
    annot, cov, siap, n, _ = analisis_grid(warped)
    h, w = frame.shape[:2]
    annot = cv2.resize(annot, (w, h))
    cv2.putText(annot, f"Cov: {cov:.1f}%  Siap: {siap}/{n}", (12, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 150), 2)
    if judul:
        cv2.putText(asli, judul, (12, h - 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
    return np.hstack([asli, annot])


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Kalibrasi kamera tetap: simpan tepi bed ke file JSON")
    ap.add_argument("source", nargs="?", default=None,
                    help="Path video / index kamera (tidak perlu jika --cek)")
    ap.add_argument("--manual", action="store_true",
                    help="Paksa klik 4 sudut manual")
    ap.add_argument("--out", default=str(KALIBRASI_DEFAULT),
                    help=f"File output JSON (default: {KALIBRASI_DEFAULT})")
    ap.add_argument("--cek", action="store_true",
                    help="Mode cek: muat kalibrasi tersimpan & preview")
    ap.add_argument("--v-hi", type=int, default=110,
                    help="Value maksimum warna bed utk deteksi otomatis")
    ap.add_argument("--min-area", type=float, default=0.10,
                    help="Area kontur bed minimum (rasio frame)")
    args = ap.parse_args()

    # ── Mode cek: muat kalibrasi tersimpan, preview saja ──
    if args.cek:
        if not Path(args.out).exists():
            print(f"[ERROR] File kalibrasi tidak ada: {args.out}")
            print("        Jalankan kalibrasi dulu: python kalibrasi_kamera.py <video>")
            sys.exit(1)
        if args.source is None:
            print("[ERROR] --cek butuh sumber video/kamera untuk preview. "
                  "Contoh: python kalibrasi_kamera.py 0 --cek")
            sys.exit(1)
        try:
            src = int(args.source)
        except ValueError:
            src = args.source
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            print(f"[ERROR] Tidak bisa membuka sumber: {src}")
            sys.exit(1)
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Tidak ada frame.")
            sys.exit(1)
        frame = resize_frame(frame)
        h, w = frame.shape[:2]
        M, pts = muat_kalibrasi(args.out, w, h)
        if M is None:
            sys.exit(1)
        print("[CEK] Preview kalibrasi — grid harus menempel ke bed. "
              "Tekan Q untuk keluar.")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = resize_frame(frame)
            disp = tampil_preview(frame, pts, "MODE CEK KALIBRASI")
            cv2.imshow("Kalibrasi Kamera - CEK", cv2.resize(
                disp, (1600, int(1600 * h / (2 * w)))))
            if (cv2.waitKey(30) & 0xFF) == ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows()
        return

    # ── Mode kalibrasi ──
    if args.source is None:
        print("[ERROR] Berikan sumber video/kamera. Contoh: "
              "python kalibrasi_kamera.py video_setup.mp4")
        sys.exit(1)
    try:
        src = int(args.source)
    except ValueError:
        src = args.source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"[ERROR] Tidak bisa membuka sumber: {src}")
        sys.exit(1)
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Tidak ada frame yang bisa dibaca.")
        sys.exit(1)
    frame = resize_frame(frame)
    h, w = frame.shape[:2]

    # Deteksi sudut
    if args.manual:
        pts, mode = pilih_sudut_manual(frame), "MANUAL"
    else:
        pts = deteksi_sudut_bed(frame, v_hi=args.v_hi,
                                min_area_ratio=args.min_area)
        mode = "AUTO"
        if pts is None:
            print("[WARN] Deteksi otomatis gagal → klik manual 4 sudut.")
            pts, mode = pilih_sudut_manual(frame), "MANUAL"
    if pts is None:
        print("[ERROR] Sudut bed tidak didapat. Kalibrasi dibatalkan.")
        sys.exit(1)

    # Preview + konfirmasi
    print("[INFO] Preview: S=simpan  R=deteksi ulang  M=klik manual  Q=batal")
    while True:
        disp = tampil_preview(frame, pts, f"MODE {mode} — S=simpan, "
                              f"R=deteksi ulang, M=manual, Q=batal")
        cv2.imshow("Kalibrasi Kamera", cv2.resize(
            disp, (1600, int(1600 * h / (2 * w)))))
        k = cv2.waitKey(30) & 0xFF
        if k == ord("s"):
            simpan_kalibrasi(args.out, pts, w, h, src, mode)
            break
        elif k == ord("r"):
            baru = deteksi_sudut_bed(frame, v_hi=args.v_hi,
                                     min_area_ratio=args.min_area)
            if baru is not None:
                pts, mode = baru, "AUTO"
                print("[OK] Sudut terdeteksi ulang.")
            else:
                print("[WARN] Deteksi gagal, sudut lama dipertahankan.")
        elif k == ord("m"):
            baru = pilih_sudut_manual(frame)
            if baru is not None:
                pts, mode = baru, "MANUAL"
        elif k in (ord("q"), 27):
            print("[INFO] Kalibrasi dibatalkan (tidak disimpan).")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()