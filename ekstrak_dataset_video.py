#!/usr/bin/env python3
"""
EKSTRAK DATASET VIDEO ECOFARM — Mengambil frame terbaik dari setiap video
dalam folder 'data set aquaponic ecofarm'.

Kriteria Frame Terbaik:
  1. Ketajaman (Sharpness): Laplacian variance (menghindari frame blur / motion blur).
  2. Kualitas Deteksi Bed: Kontur bed terdeteksi quad 4 sudut (bukan miring/terpotong).
  3. Kualitas Pencahayaan: Nilai V (Value) seimbang (tidak over/under-exposed).
  4. Stabilitas Posisi: Posisi tengah video (menghindari goyangan awal/akhir rekaman HP).

Output disimpan di:
  dataset_ecofarm_frames/
    ├── raw/         -> Frame asli resolusi penuh (1920x1080)
    ├── warped/      -> Kanvas standar 1200x660 (top-down siap segmentasi/analisis)
    ├── annotated/   -> Visualisasi grid 4x6, status kematangan & HUD
    ├── dataset_summary.csv
    └── metadata.json
"""
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

# Pastikan output terminal UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "files"))
sys.path.insert(0, str(ROOT / "raspi"))
sys.path.insert(0, str(ROOT / "raspi" / "modules"))

from proses_video import detek_sudut_robust
from adaptive_bed import (deteksi_sudut_canny, matriks_warp, warp_bed,
                          mask_tanaman_warna, proyeksi_grid_ke_frame,
                          resize_frame)
from kangkung_cv import (BED_CONFIG, get_status, get_kesehatan, PSI_VERSION)
from fuzzy_export import hitung_fuzzy

VIDEO_DIR = ROOT / "dataset1" / "data set aquaponic ecofarm-20260908T053214Z-1-001" / "data set aquaponic ecofarm"
OUT_DIR = ROOT / "dataset_ecofarm_frames"
RAW_DIR = OUT_DIR / "raw"
WARP_DIR = OUT_DIR / "warped"
ANNO_DIR = OUT_DIR / "annotated"


def buat_anotasi(frame, pts, zona, stem, frame_idx, fps, score, warp_mode="canny_quad"):
    """Gambar grid 4x6 perspektif DI DALAM poligon bed pada frame asli."""
    h0, w0 = frame.shape[:2]
    disp = resize_frame(frame.copy())
    h, w = disp.shape[:2]
    scale = w / float(w0)
    pts_s = np.asarray(pts, dtype=np.float32) * scale

    rows, cols = BED_CONFIG["grid_rows"], BED_CONFIG["grid_cols"]
    zona_quads = proyeksi_grid_ke_frame(pts_s, rows=rows, cols=cols)

    # Gelapkan area di luar poligon bed agar fokus batas bed terlihat jelas
    poly = pts_s.astype(np.int32).reshape(-1, 1, 2)
    mask_bed = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask_bed, [poly], 255)
    outside = mask_bed == 0
    dark_bg = disp.copy()
    dark_bg[outside] = (dark_bg[outside] * 0.45).astype(np.uint8)
    disp = dark_bg

    palette = {
        "belum_siap": (255, 152, 51),
        "hampir_siap": (18, 156, 243),
        "siap_panen": (113, 204, 46),
        "harus_panen": (60, 76, 231),
    }

    overlay = disp.copy()
    covs, kuns, coks = [], [], []
    for i, quad in enumerate(zona_quads):
        r, c = divmod(i, cols)
        z = zona[f"R{r+1}C{c+1}"]
        warna = palette.get(z["status"], (200, 200, 200))
        q_int = quad.astype(np.int32)
        cv2.fillPoly(overlay, [q_int], warna)
        covs.append(z["coverage"])
        kuns.append(z["pct_kuning"])
        coks.append(z["pct_coklat"])

    disp = cv2.addWeighted(disp, 0.72, overlay, 0.28, 0)

    for i, quad in enumerate(zona_quads):
        r, c = divmod(i, cols)
        z = zona[f"R{r+1}C{c+1}"]
        q_int = quad.astype(np.int32)
        cv2.polylines(disp, [q_int], True, (240, 255, 240), 1, cv2.LINE_AA)
        cx = int(quad[:, 0, 0].mean())
        cy = int(quad[:, 0, 1].mean())
        if 8 <= cx <= w - 8 and 8 <= cy <= h - 8:
            cv2.putText(disp, f"{z['coverage']:.0f}%", (cx - 18, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    # Garis luar tepi bed hasil deteksi
    border_col = (0, 255, 255) if warp_mode != "fallback_full" else (0, 165, 255)
    cv2.polylines(disp, [poly], True, border_col, 3, cv2.LINE_AA)
    for pt in pts_s.astype(int):
        cv2.circle(disp, (int(np.clip(pt[0], 0, w - 1)), int(np.clip(pt[1], 0, h - 1))),
                   5, (0, 255, 0), -1)

    cov_m = float(np.mean(covs))
    kun_m = float(np.mean(kuns))
    cok_m = float(np.mean(coks))
    waktu_s = frame_idx / fps if fps > 0 else 0

    # HUD bar atas & bawah dengan latar gelap transparan
    hud = disp.copy()
    cv2.rectangle(hud, (0, 0), (w, 34), (10, 18, 16), -1)
    cv2.rectangle(hud, (0, h - 32), (w, h), (10, 18, 16), -1)
    disp = cv2.addWeighted(disp, 0.35, hud, 0.65, 0)

    cv2.putText(disp, f"{stem} | F#{frame_idx} ({waktu_s:.1f}s) | {warp_mode} | Score:{score:.2f}",
                (12, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(disp, f"Cov:{cov_m:.1f}%  Kun:{kun_m:.1f}%  Cok:{cok_m:.1f}%",
                (12, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (100, 255, 150), 1, cv2.LINE_AA)
    return disp


def proses_analisis_bed(warped):
    masks = mask_tanaman_warna(warped)
    rows, cols = BED_CONFIG["grid_rows"], BED_CONFIG["grid_cols"]
    H, W = warped.shape[:2]
    ch, cw = H // rows, W // cols

    zona, covs, kuns, coks, st_kes = {}, [], [], [], []
    piksel = []

    for r in range(rows):
        for c in range(cols):
            y1, y2 = r * ch, (r + 1) * ch if r < rows - 1 else H
            x1, x2 = c * cw, (c + 1) * cw if c < cols - 1 else W
            h = int(masks["hijau"][y1:y2, x1:x2].sum()) // 255
            t = int(masks["tanaman"][y1:y2, x1:x2].sum()) // 255
            k = int(masks["kuning"][y1:y2, x1:x2].sum()) // 255
            b = int(masks["coklat"][y1:y2, x1:x2].sum()) // 255
            cov = h / (cw * ch) * 100
            pk = k / t * 100 if t else 0.0
            pc = b / t * 100 if t else 0.0
            kes = get_kesehatan(pk, pc)
            st = get_status(cov)

            zkey = f"R{r+1}C{c+1}"
            zona[zkey] = {
                "coverage": round(cov, 2),
                "status": st,
                "pct_kuning": round(pk, 2),
                "pct_coklat": round(pc, 2),
                "kesehatan": kes,
            }
            covs.append(cov)
            kuns.append(pk)
            coks.append(pc)
            st_kes.append(kes)

            k_zona = masks["kuning"][y1:y2, x1:x2]
            b_zona = masks["coklat"][y1:y2, x1:x2]
            h_zona = masks["hijau"][y1:y2, x1:x2]
            k_bukan_b = int(cv2.bitwise_and(k_zona, cv2.bitwise_not(b_zona)).sum()) // 255
            h_bukan_kb = int(cv2.bitwise_and(h_zona, cv2.bitwise_not(cv2.bitwise_or(k_zona, b_zona))).sum()) // 255
            piksel.append({
                "green": h_bukan_kb,
                "yellow": k_bukan_b,
                "brown": b,
                "plant_mask": t,
                "unclassified": max(0, t - (h_bukan_kb + k_bukan_b + b)),
            })

    dist = {"belum_siap": 0, "hampir_siap": 0, "siap_panen": 0, "harus_panen": 0}
    for z in zona.values():
        dist[z["status"]] += 1
    siap = dist["siap_panen"] + dist["harus_panen"]

    fuzzy = hitung_fuzzy(piksel, [z["kesehatan"] for z in zona.values()])

    return {
        "zona": zona,
        "coverage_rata": round(float(np.mean(covs)), 2),
        "coverage_std": round(float(np.std(covs)), 2),
        "zona_siap_panen": siap,
        "persen_siap": round(siap / len(zona) * 100, 1),
        "status_distribusi": dist,
        "kuning_rata": round(float(np.mean(kuns)), 2),
        "coklat_rata": round(float(np.mean(coks)), 2),
        "kesehatan_distribusi": {s: st_kes.count(s) for s in ("sehat", "waspada", "sakit")},
        "fuzzy_input": fuzzy,
    }


def cari_frame_terbaik(video_path, step=6):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[ERROR] Tidak bisa membuka video: {video_path.name}")
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    best_idx = 0
    best_score = -1.0
    best_frame = None
    best_pts = None
    best_mode = "fallback_full"
    best_metrics = {}

    # Abaikan 10% awal dan 10% akhir video (biasanya goyang saat tekan start/stop)
    start_f = int(total_frames * 0.10)
    end_f = int(total_frames * 0.90)
    if end_f <= start_f:
        start_f, end_f = 0, total_frames

    # Tahap 1 (cepat): kumpulkan ~24 kandidat tajam & pencahayaan seimbang
    scan_step = max(step, (end_f - start_f) // 24)
    kandidat = []
    curr = 0
    while True:
        ret = cap.grab()
        if not ret:
            break
        if curr >= start_f and curr <= end_f and ((curr - start_f) % scan_step == 0):
            ret, frame = cap.retrieve()
            if not ret or frame is None:
                curr += 1
                continue
            small = cv2.resize(frame, (640, int(frame.shape[0] * 640 / frame.shape[1])))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            s_sharp = min(1.0, lap_var / 220.0)

            hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
            mean_v = float(hsv[:, :, 2].mean())
            if 80 <= mean_v <= 170:
                s_exp = 1.0
            elif mean_v < 80:
                s_exp = max(0.2, mean_v / 80.0)
            else:
                s_exp = max(0.2, (255 - mean_v) / 85.0)

            fast_score = 0.72 * s_sharp + 0.28 * s_exp
            kandidat.append((fast_score, curr, lap_var, mean_v, s_sharp, s_exp, frame))
        curr += 1

    cap.release()

    # Tahap 2: jalankan Canny-Quad pada 8 kandidat teratas (prioritas deteksi Canny)
    kandidat.sort(key=lambda x: x[0], reverse=True)
    for _, f_idx, lap_var, mean_v, s_sharp, s_exp, frame in kandidat[:8]:
        H0, W0 = frame.shape[:2]
        fr_r = resize_frame(frame)
        sc_r = W0 / float(fr_r.shape[1])

        pts_c = deteksi_sudut_canny(fr_r, min_area_ratio=0.12)
        if pts_c is not None:
            pts_full = pts_c * sc_r
            warp_m = "canny_quad"
            s_bed = 1.0
        else:
            pts_fb, q_score = detek_sudut_robust(fr_r)
            pts_full = (pts_fb * sc_r) if pts_fb is not None else None
            warp_m = "hsv_fallback" if pts_full is not None else "fallback_full"
            s_bed = (q_score * 0.65) if pts_full is not None else 0.1

        total_score = (0.40 * s_sharp) + (0.45 * s_bed) + (0.15 * s_exp)
        if total_score > best_score:
            best_score = total_score
            best_idx = f_idx
            best_frame = frame
            best_pts = pts_full
            best_mode = warp_m
            best_metrics = {
                "laplacian_var": round(lap_var, 1),
                "mean_v": round(mean_v, 1),
                "bed_score": round(s_bed, 3),
                "pts_detected": pts_full is not None,
                "detector": warp_m,
            }

    if best_frame is None:
        cap = cv2.VideoCapture(str(video_path))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total_frames * 0.5))
        _, best_frame = cap.read()
        cap.release()
        if best_frame is not None:
            H0, W0 = best_frame.shape[:2]
            fr_r = resize_frame(best_frame)
            pts_fb, _ = detek_sudut_robust(fr_r)
            best_pts = (pts_fb * (W0 / float(fr_r.shape[1]))) if pts_fb is not None else None
            best_mode = "canny_quad" if deteksi_sudut_canny(fr_r) is not None else (
                "hsv_fallback" if best_pts is not None else "fallback_full")
        best_idx = int(total_frames * 0.5)
        best_score = 0.5

    return {
        "frame_idx": best_idx,
        "total_frames": total_frames,
        "fps": fps,
        "timestamp_sec": round(best_idx / fps, 2),
        "score": round(best_score, 3),
        "frame": best_frame,
        "pts": best_pts,
        "warp_mode": best_mode,
        "metrics": best_metrics
    }


def main():
    print("=" * 70)
    print("  EKSTRAK DATASET FRAME TERBAIK DARI VIDEO ECOFARM AQUAPONIK")
    print("=" * 70)

    if not VIDEO_DIR.exists():
        print(f"[ERROR] Folder video tidak ditemukan: {VIDEO_DIR}")
        sys.exit(1)

    for d in [RAW_DIR, WARP_DIR, ANNO_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    videos = sorted(list(VIDEO_DIR.glob("*.MOV")) + list(VIDEO_DIR.glob("*.mp4")))
    print(f"\nDitemukan {len(videos)} video dalam folder dataset:")
    for v in videos:
        print(f"  - {v.name} ({v.stat().st_size / (1024*1024):.1f} MB)")

    print("\nMemulai proses ekstraksi frame terbaik (Canny-Quad + HSV fallback)...\n")

    hasil_semua = []
    t_start = time.time()

    for i, v_path in enumerate(videos, 1):
        stem = v_path.stem
        print(f"[{i:02d}/{len(videos):02d}] Memproses {v_path.name} ...", end=" ", flush=True)

        res = cari_frame_terbaik(v_path, step=6)
        if res is None or res["frame"] is None:
            print("GAGAL BACA")
            continue

        frame = res["frame"]
        pts = res["pts"]
        H, W = frame.shape[:2]

        # 1. Simpan Frame Raw Asli
        raw_path = RAW_DIR / f"{stem}.jpg"
        cv2.imwrite(str(raw_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

        # 2. Warp Bed Canvas (1200x660)
        if pts is None:
            pts = np.float32([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]])
            warp_mode = "fallback_full"
        else:
            warp_mode = res.get("warp_mode", "canny_quad")

        M = matriks_warp(pts)
        warped = warp_bed(frame, M)
        warp_path = WARP_DIR / f"{stem}_warped.jpg"
        cv2.imwrite(str(warp_path), warped, [cv2.IMWRITE_JPEG_QUALITY, 92])

        # 3. Analisis Computer Vision (Grid 4x6, Coverage, PSI)
        analisis = proses_analisis_bed(warped)
        fz = analisis["fuzzy_input"]

        # 4. Simpan Anotasi Grid 4x6 tepat DI DALAM kotak bed pada frame asli
        annotated = buat_anotasi(
            frame, pts, analisis["zona"], stem,
            res["frame_idx"], res["fps"], res["score"], warp_mode=warp_mode
        )
        anno_path = ANNO_DIR / f"{stem}_annotated.jpg"
        cv2.imwrite(str(anno_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])

        info = {
            "video_name": v_path.name,
            "stem": stem,
            "best_frame_idx": res["frame_idx"],
            "total_frames": res["total_frames"],
            "timestamp_sec": res["timestamp_sec"],
            "quality_score": res["score"],
            "laplacian_var": res["metrics"].get("laplacian_var", 0),
            "mean_v": res["metrics"].get("mean_v", 0),
            "warp_mode": warp_mode,
            "corners": np.round(pts, 1).tolist(),
            "coverage_rata": analisis["coverage_rata"],
            "zona_siap_panen": analisis["zona_siap_panen"],
            "persen_siap": analisis["persen_siap"],
            "psi_v2": fz.get("psi"),
            "psi_maks": fz.get("psi_maks"),
            "kuning_pct": fz.get("kuning_pct"),
            "coklat_pct": fz.get("coklat_pct"),
            "zona_sakit": fz.get("zona_sakit"),
            "raw_file": f"raw/{stem}.jpg",
            "warped_file": f"warped/{stem}_warped.jpg",
            "annotated_file": f"annotated/{stem}_annotated.jpg",
        }
        hasil_semua.append(info)

        print(f"OK! [{warp_mode}] F#{res['frame_idx']} ({res['timestamp_sec']}s) | "
              f"Cov: {analisis['coverage_rata']}% | PSI: {fz.get('psi')}")

    # Simpan Metadata JSON
    with open(OUT_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(hasil_semua, f, indent=2, ensure_ascii=False)

    # Simpan Dataset Summary CSV
    csv_path = OUT_DIR / "dataset_summary.csv"
    if hasil_semua:
        fieldnames = [
            "video_name", "stem", "best_frame_idx", "total_frames", "timestamp_sec",
            "quality_score", "laplacian_var", "mean_v", "warp_mode", "corners",
            "coverage_rata", "zona_siap_panen", "persen_siap",
            "psi_v2", "psi_maks", "kuning_pct", "coklat_pct", "zona_sakit",
            "raw_file", "warped_file", "annotated_file"
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(hasil_semua)

    durasi = time.time() - t_start
    print("\n" + "=" * 70)
    print(f"SELESAI! Berhasil mengekstrak {len(hasil_semua)} frame terbaik dalam {durasi:.1f} detik.")
    print(f"Hasil tersimpan di folder: {OUT_DIR.relative_to(ROOT)}/")
    print(f"  - Frame Raw Asli       : {RAW_DIR.relative_to(ROOT)}/ (1920x1080)")
    print(f"  - Kanvas Warp Top-Down : {WARP_DIR.relative_to(ROOT)}/ (1200x660)")
    print(f"  - Frame Beranotasi     : {ANNO_DIR.relative_to(ROOT)}/")
    print(f"  - Ringkasan Dataset CSV: {csv_path.relative_to(ROOT)}")
    print(f"  - Ringkasan JSON       : {OUT_DIR.relative_to(ROOT)}/metadata.json")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
