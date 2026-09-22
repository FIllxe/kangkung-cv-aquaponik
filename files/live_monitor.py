import cv2
import numpy as np
import sys
import time
import argparse
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adaptive_bed import (deteksi_sudut_bed, pilih_sudut_manual,
                          CornerSmoother, matriks_warp, warp_bed,
                          analisis_grid, resize_frame,
                          gambar_grid_dalam_box)
from kangkung_cv import BED_CONFIG, get_status


def live_monitor(cam_idx=0, manual=False, detect_every=10, no_gui=False, max_frames=None):
    cap = cv2.VideoCapture(cam_idx)
    if not cap.isOpened():
        print("[ERROR] Kamera tidak bisa dibuka.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    print("[INFO] Live monitor aktif.")
    print("[INFO] Tekan Q=keluar  S=snapshot  R=re-deteksi")

    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Tidak ada frame from kamera.")
        return
    frame = resize_frame(frame)
    h, w = frame.shape[:2]

    smoother = CornerSmoother(alpha=0.2)
    if manual:
        pts = pilih_sudut_manual(frame)
        mode = "MANUAL"
    else:
        pts = deteksi_sudut_bed(frame)
        mode = "AUTO"
        if pts is None:
            print("[WARN] Deteksi gagal - pindah ke manual.")
            pts = pilih_sudut_manual(frame)
            mode = "MANUAL"

    if pts is None:
        print("[ERROR] Sudut bed tidak terdeteksi. Keluar.")
        cap.release()
        return

    if mode == "AUTO":
        smoother.update(pts)
    print(f"[MODE] {mode} | sudut awal:")
    print(np.round(pts, 1))

    processed, frame_idx, bed_lost = 0, 0, 0
    t_proc = 0.0
    t0 = time.time()

    out_dir = Path(__file__).resolve().parent.parent / "output" / "video"
    snapshot_dir = out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    writer = None
    out_path = None
    if "--save" in sys.argv:
        stem = f"live_snapshot_{cam_idx}"
        out_path = out_dir / f"{stem}.mp4"
        cc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), cc, 20.0, (w, h))

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue
        frame_idx += 1
        frame = resize_frame(frame)
        processed += 1
        t1 = time.perf_counter()

        if mode == "AUTO" and processed % detect_every == 0:
            baru = deteksi_sudut_bed(frame)
            if baru is not None:
                pts = smoother.update(baru)
                bed_lost = 0
            else:
                bed_lost += 1

        warped = warp_bed(frame, matriks_warp(pts))
        annot, cov_rata, siap, n_zona, zona_list = analisis_grid(warped)
        t_proc += time.perf_counter() - t1

        disp = gambar_grid_dalam_box(frame.copy(), pts, zona_list)
        if bed_lost:
            cv2.putText(disp, "BED LOST!", (12, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(disp, f"Cov: {cov_rata:.1f}%  Siap: {siap}/{n_zona}",
                    (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 150), 2)

        fps_live = processed / (time.time() - t0 + 1e-9)
        cv2.putText(disp, f"FPS: {fps_live:.1f}", (w - 100, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

        if writer is not None:
            writer.write(disp)

        if not no_gui:
            cv2.imshow("Kangkung Live Monitor", 
                       cv2.resize(disp, (800, int(800 * h / w))))
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("[INFO] Dihentikan user.")
                break

    cap.release()
    if writer:
        writer.release()

    ms = (t_proc / processed * 1000) if processed else 0
    print(f"\n[RINGKASAN] frame={processed} {ms:.1f} ms/frame")
    print("[RINGKASAN] sudut akhir:")
    print(np.round(pts, 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Live monitor kangkung aquaponik")
    ap.add_argument("cam_idx", nargs="?", type=int, default=0)
    ap.add_argument("--manual", action="store_true")
    ap.add_argument("--detect-every", type=int, default=10)
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--no-gui", action="store_true")
    ap.add_argument("--max-frames", type=int, default=None)
    args = ap.parse_args()

    live_monitor(args.cam_idx, args.manual, args.detect_every,
                 args.no_gui, args.max_frames)
