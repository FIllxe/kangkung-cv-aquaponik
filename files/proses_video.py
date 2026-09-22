"""
=============================================================================
  PROSES VIDEO — Pemroses video end-to-end kangkung aquaponik
  Deteksi bed (fixed/adaptive/manual) + warp + segmentasi HSV + grid 4x6
=============================================================================
  MODE OTOMATIS:
    1. Ada kalibrasi_kamera.json                -> MODE FIXED (muat matriks,
       --kalibrasi path.json                       warp saja, hemat CPU)
    2. --adaptive                               -> MODE ADAPTIVE (deteksi ulang
                                                   per N frame + EMA smooth)
    3. --manual                                 -> MODE MANUAL (klik 4 sudut)
    4. Default tanpa kalibrasi                  -> MODE AUTO (deteksi robust)

  OUTPUT (di folder output/video/):
    <nama>_beranotasi.mp4   video side-by-side: asli+quad | grid warp+overlay
    <nama>_timeseries.csv   coverage global + per zona (24) per frame
    <nama>_ringkasan.json   statistik rata-rata, distribusi status, metrik

  CARA PAKAI:
    python proses_video.py video.mp4
    python proses_video.py video.mp4 --adaptive --step 5 --no-gui --save
    python proses_video.py video.mp4 --manual
    python proses_video.py 0                      # kamera
    python proses_video.py video.mp4 --v-hi 150   # tune deteksi gelap

  KONTROL (GUI): Q = keluar
=============================================================================
"""

import cv2
import numpy as np
import argparse
import json
import os
import sys
import time
import csv
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adaptive_bed import (deteksi_sudut_bed, pilih_sudut_manual,
                          CornerSmoother, matriks_warp, warp_bed,
                          analisis_grid, gambar_quad, resize_frame,
                          gambar_grid_dalam_box)
from kalibrasi_kamera import muat_kalibrasi, KALIBRASI_DEFAULT


# ─── DETEKSI ROBUST (multi-threshold + fallback) ─────────────────────────────

def detek_sudut_robust(frame, v_his=(110, 130, 150, 170), min_area_ratio=0.12):
    """Coba beberapa threshold V gelap + validasi area. Return (pts, score)."""
    h, w = frame.shape[:2]
    full = w * h
    best, best_score = None, 0.0
    for v_hi in v_his:
        pts = deteksi_sudut_bed(frame, v_hi=v_hi, min_area_ratio=min_area_ratio)
        if pts is None:
            continue
        area = cv2.contourArea(pts)
        frac = area / full
        xs, ys = pts[:, 0], pts[:, 1]
        if xs.min() < -30 or ys.min() < -30 or xs.max() > w + 30 or ys.max() > h + 30:
            continue
        score = min(1.0, frac / 0.85) if frac < 0.93 else (1.0 - frac) * 3.0
        touches = int(xs.min() <= 5 or ys.min() <= 5 or
                      xs.max() >= w - 5 or ys.max() >= h - 5)
        score *= (0.85 ** touches)
        if score > best_score:
            best, best_score = pts, score
    return best, best_score


def _v_his_list(v_hi):
    """Jika user beri --v-hi, pakai itu; jika 0, auto multi-threshold."""
    if v_hi:
        return (v_hi,)
    return (110, 130, 150, 170)


# ─── RINGKASAN / CSV ─────────────────────────────────────────────────────────

ZONA_IDS = [f"R{r}C{c}" for r in range(1, 5) for c in range(1, 7)]


def nuevo_ringkasan():
    rows = len(ZONA_IDS)
    return {
        "sum_coverage": np.zeros(rows),
        "sum_cov2": np.zeros(rows),
        "status_count": {},
        "n": 0,
        "n_siap": 0,
        "tot_cov": 0.0,
    }


def update_ringkasan(rk, detail, cov_rata):
    for d in detail:
        z = d["zona"]
        i = ZONA_IDS.index(z)
        rk["sum_coverage"][i] += d["coverage"]
        rk["sum_cov2"][i] += d["coverage"] ** 2
        st = d["status"]
        rk["status_count"][st] = rk["status_count"].get(st, 0) + 1
        if st in ("siap_panen", "harus_panen"):
            rk["n_siap"] += 1
    rk["tot_cov"] += cov_rata
    rk["n"] += 1
    return rk


def close_ringkasan(rk, source, mode, durasi, fps_proc, out_dir, path_csv):
    stem = os.path.splitext(os.path.basename(str(source)))[0]
    path_json = os.path.join(out_dir, f"ringkasan_{stem}.json")
    rk_out = dict(rk)
    rk_out["sum_coverage"] = [float(x) for x in rk["sum_coverage"]]
    rk_out["sum_cov2"] = [float(x) for x in rk["sum_cov2"]]
    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(rk_out, f, indent=2, ensure_ascii=False)
    return path_json


def pemroses(source, args):
    try:
        src = int(source)
    except ValueError:
        src = source

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"[ERROR] Tidak bisa membuka sumber: {source}")
        sys.exit(1)

    ret0, frame0 = cap.read()
    if not ret0:
        print("[ERROR] Tidak ada frame yang bisa dibaca.")
        sys.exit(1)
    frame0 = resize_frame(frame0)
    h, w = frame0.shape[:2]

    M = None
    pts = None
    smoother = CornerSmoother(alpha=args.smooth)

    if args.manual:
        mode = "MANUAL"
        print("[INFO] Klik 4 sudut bed (TL->TR->BR->BL). 'Z'=undo, 'Q'=batal.")
        pts = pilih_sudut_manual(frame0)
        if pts is None:
            print("[ERROR] Manual tidak diselesa. Abandi.")
            sys.exit(1)
    elif args.adaptive:
        mode = "ADAPTIVE"
        print("[INFO] Mode ADAPTIVE -- deteksi bed ulang tiap "
              f"{args.detect_every} frame + EMA smooth.")
        pts, sc0 = detek_sudut_robust(frame0, v_his=_v_his_list(args.v_hi))
        if pts is None:
            print("[WARN] Deteksi frame awal gagal -- video mungkin perlu "
                  "klik manual (python proses_video.py ... --manual).")
            cap.release()
            sys.exit(2)
        smoother.update(pts)
    else:
        kal_path = Path(args.kalibrasi) if args.kalibrasi else KALIBRASI_DEFAULT
        M, pts = muat_kalibrasi(kal_path, w, h)
        if M is not None:
            mode = "FIXED"
            print(f"[INFO] Mode FIXED -- kalibrasi: {kal_path}")
        else:
            mode = "AUTO"
            print("[INFO] Mode AUTO -- deteksi robust sudut bed (fallback "
                  "kalibrasi manual jika gagal).")
            pts, sc0 = detek_sudut_robust(frame0, v_his=_v_his_list(args.v_hi))
            if pts is None:
                print("[ERROR] Deteksi otomatis gagal. Video ini memerlukan "
                      "kalibrasi manual:\n"
                      f"  python kalibrasi_kamera.py '{source}' --manual\n"
                      f"  python proses_video.py '{source}' --kalibrasi "
                      f"kalibrasi_kamera.json")
                cap.release()
                sys.exit(2)
            print(f"[INFO] Sudut auto (konfidenci {sc0:.2f}).")

    if pts is None:
        print("[ERROR] Sudut bed tidak didapatnya.")
        cap.release()
        sys.exit(1)

    # ── Prep output ──
    stem = str(Path(source).stem) if isinstance(source, str) else "kamera"
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path_csv = out_dir / f"{stem}_timeseries.csv"
    fcsv = open(path_csv, "w", newline="", encoding="utf-8")
    cw = csv.writer(fcsv)
    cols = (["timestamp_s", "frame", "coverage_global", "mode", "conf"]
            + ZONA_IDS + [f"Y_{z}" for z in ZONA_IDS]
            + [f"B_{z}" for z in ZONA_IDS]
            + [f"status_{z}" for z in ZONA_IDS])
    cw.writerow(cols)

    # ─── [PATCH 1] Inisialisasi variabel output + writer ─────────────
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(str(source)))[0]
    vout = os.path.join(out_dir, f"{stem}_beranotasi.mp4")

    video_writer = None
    writer_initialized = False
    if args.save:
        fps_cap = cap.get(cv2.CAP_PROP_FPS)
        if not fps_cap or fps_cap != fps_cap:  # NaN check
            fps_cap = 15.0
    else:
        fps_cap = 15.0
    # ─── end PATCH 1 ──────────────────────────────────────────────────
        # (Patch 1 sudah inisialisasi vout dengan os.path.join di atas)
    # --- end vout initialization ---
# ── Loop ──
    rk = nuevo_ringkasan()
    t0 = time.time()
    frame_idx = 0
    processed = 0
    bed_lost = 0
    t_proc = 0.0
    sc_conf = 1.0
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[INFO] Video selesai.")
            break
        frame_idx += 1
        if args.step > 1 and (frame_idx - 1) % args.step:
            continue
        frame = resize_frame(frame)
        processed += 1
        t1 = time.perf_counter()

        if mode in ("ADAPTIVE", "AUTO"):
            if processed == 1 or processed % args.detect_every == 0:
                baru, sc = detek_sudut_robust(frame, v_his=_v_his_list(args.v_hi))
                if baru is not None:
                    pts = smoother.update(baru)
                    sc_conf = sc
                    bed_lost = 0
                else:
                    bed_lost += 1
            warped = warp_bed(frame, matriks_warp(pts))
            pts_cur = pts
        else:  # FIXED
            warped = warp_bed(frame, M)
            pts_cur = pts
            sc_conf = 1.0

        res = analisis_grid(warped)
        annot = res[0]
        cov_rata = float(res[1])
        siap = int(res[2])
        n_zona = int(res[3])
        detail = res[4]
        update_ringkasan(rk, detail, cov_rata)
        t_proc += time.perf_counter() - t1

        # CSV
        row = [round((frame_idx - 1) / fps, 3), frame_idx, round(cov_rata, 2),
               mode, round(sc_conf, 2)]
        cov_by = {d["zona"]: round(d["coverage"], 2) for d in detail}
        kng_by = {d["zona"]: round(d.get("pct_kuning", 0.0), 2) for d in detail}
        cok_by = {d["zona"]: round(d.get("pct_coklat", 0.0), 2) for d in detail}
        st_by = {d["zona"]: d["status"] for d in detail}
        row += [cov_by[z] for z in ZONA_IDS]
        row += [kng_by[z] for z in ZONA_IDS]
        row += [cok_by[z] for z in ZONA_IDS]
        row += [st_by[z] for z in ZONA_IDS]
        cw.writerow(row)

        # Tampilan
        # SINGLE VIEW: grid di dalam box di frame asli
        _, _, _, _, zona_list = analisis_grid(warped)
        disp = gambar_grid_dalam_box(frame.copy(), pts_cur, zona_list)
        if bed_lost:
            cv2.putText(disp, "BED LOST", (12, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 0, 255), 2)
        cv2.putText(disp, f"mode={mode} conf={sc_conf:.2f}",
                    (12, h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (180, 180, 180), 1)
        cv2.putText(disp, f"Cov: {cov_rata:.1f}%  Siap: {siap}/{n_zona}",
                    (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 150), 2)
        kng_rata = (sum(d.get("pct_kuning", 0.0) for d in detail)
                    / max(1, len(detail)))
        cok_rata = (sum(d.get("pct_coklat", 0.0) for d in detail)
                    / max(1, len(detail)))
        cv2.putText(disp, f"Kuning: {kng_rata:.1f}%  Coklat: {cok_rata:.1f}%",
                    (12, h - 44), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (60, 220, 230), 2)
        cv2.putText(disp, f"frame {frame_idx}", (w - 160, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

                # ─── [PATCH 2] Inisialisasi VideoWriter pada frame pertama valid ────
        if args.save and not writer_initialized:
            h_out, w_out = disp.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(vout, fourcc, fps_cap, (w_out, h_out))
            if not video_writer.isOpened():
                for cc in ('XVID', 'X264', 'MJPG'):
                    video_writer = cv2.VideoWriter(
                        vout, cv2.VideoWriter_fourcc(*cc), fps_cap, (w_out, h_out)
                    )
                    if video_writer.isOpened():
                        print(f"[INFO] Video ditulis ({cc}): {vout}")
                        break
                else:
                    video_writer = None
                    print("[WARN] Gagal inisialisasi VideoWriter, lanjut tanpa rekam.")
            else:
                print(f"[INFO] Video ditulis (mp4v): {vout}")
            writer_initialized = True

        if video_writer is not None:
            video_writer.write(disp)
        # ─── end PATCH 2 ────────────────────────────────────────────────────

        if not args.no_gui:
            cv2.imshow("Proses Video - KANGKUNG AQUAPONIK",
                       cv2.resize(disp, (800, int(800 * h / w))))
            k = cv2.waitKey(1) & 0xFF
            if k == ord("q"):
                print("[INFO] Dihentikan user.")
                break
            if k in (ord("r"), ord("R")):
                baru, sc = detek_sudut_robust(frame)
                if baru is not None:
                    pts = smoother.update(baru)
                    sc_conf = sc
                    print(f"[OK] Deteksi baru aksep (conf {sc_conf:.2f}).")

        if args.max_frames and processed >= args.max_frames:
            print(f"[INFO] Batas {args.max_frames} frame tercapai.")
            break

    cap.release()
    if video_writer:
        video_writer.release()
        print(f"[INFO] Video tersimpan: {vout}")
    fcsv.close()

    durasi = time.time() - t0
    fps_proc = processed / durasi if durasi else 0
    close_ringkasan(rk, source, mode, durasi, fps_proc,
                    out_dir, path_csv)
    ms = (t_proc / processed * 1000) if processed else 0
    print(f"\n[RINGKASAN] mode={mode} frame_terproses={processed} "
          f"waktu={ms:.1f} ms/frame  ({fps_proc:.1f} fps proses)")
    print(f"[RINGKASAN] coverage_rata={rk['tot_cov']/max(1, rk['n']):.1f}%")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Proses video kangkung: deteksi bed + warp + grid HSV")
    ap.add_argument("source", help="path video atau index kamera (0)")
    ap.add_argument("--adaptive", action="store_true",
                    help="deteksi bed ulang tiap frame (video handheld)")
    ap.add_argument("--manual", action="store_true",
                    help="klik 4 sudut bed pada frame pertama")
    ap.add_argument("--kalibrasi", default=None,
                    help="path file kalibrasi kamera (default kalibrasi_kamera.json)")
    ap.add_argument("--step", type=int, default=1,
                    help="proses tiap frame ke-N (default 1)")
    ap.add_argument("--detect-every", type=int, default=10,
                    help="re-deteksi tiap N frame (mode adaptive)")
    ap.add_argument("--smooth", type=float, default=0.2,
                    help="alpha EMA stabilisasi sudut (default 0.2)")
    ap.add_argument("--v-hi", type=int, default=0,
                    help="threshold V gelap (0=auto multi-threshold)")
    ap.add_argument("--save", action="store_true",
                    help="simpan video beranotasi mp4")
    ap.add_argument("--no-gui", action="store_true",
                    help="headless (server / Raspberry Pi)")
    ap.add_argument("--max-frames", type=int, default=0,
                    help="proses max N frame (0=selesai)")
    ap.add_argument("--out-dir",
                    default=str(Path(__file__).resolve().parent.parent
                                / "output" / "video"),
                    help="folder output (default <root>/output/video)")
    args = ap.parse_args()
    pemroses(args.source, args)


if __name__ == "__main__":
    main()
