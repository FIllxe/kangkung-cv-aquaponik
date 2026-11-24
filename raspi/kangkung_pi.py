#!/usr/bin/env python3
"""KANGKUNG PI LIVE — capture -> analisis -> payload -> Firebase.

Mode hemat panas: 1 siklus capture tiap `interval_menit`, idle di antaranya.
Output per siklus (folder outbox/):
  <doc_id>.jpg    snapshot beranotasi (grid + HUD) untuk dashboard
  <doc_id>.json   payload skema bed_readings v1.0 (+ fuzzy_input)
Uji sekali tanpa service:  python kangkung_pi.py --test
Sumber video file (uji tanpa kamera): isi "video_source" di config.json.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "modules"))

from adaptive_bed import (deteksi_sudut_bed, CornerSmoother, matriks_warp,
                          warp_bed, resize_frame, gambar_grid_dalam_box,
                          analisis_bed_lengkap)
from kangkung_cv import get_status, get_kesehatan, BED_CONFIG
from fuzzy_export import hitung_fuzzy
from thermal_guard import dalam_batas
import camera_pi
import firebase_uplink
try:
    from growth_tracker import GrowthTracker
    _tracker = GrowthTracker(storage_dir=BASE / "growth_cycles", max_cycles=3, days_per_cycle=30)
except Exception as _e_tr:
    _tracker = None
    print(f"[INFO] GrowthTracker tidak aktif: {_e_tr}")



# ─── Util ────────────────────────────────────────────────────────────────────

def load_config():
    cfg = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
    (BASE / cfg["outbox_dir"]).mkdir(parents=True, exist_ok=True)
    return cfg


def iso_ts(dt):
    return dt.isoformat(timespec="seconds") + "+07:00"


def doc_id(device_id, dt):
    return f"{device_id}_{dt.strftime('%Y%m%dT%H%M%S')}"


CSI_SOURCE = ("csi", "picamera2", "libcamera")


def ambil_frame(cfg):
    """Baca 1 frame dari kamera/video (dengan warmup). None bila gagal.

    Prioritas:
    1. Jika camera_live aktif di port 8787 (stream live web), ambil frame snapshot
       langsung via HTTP agar tidak berebut device /dev/video0 dengan camera_live.
    2. Jika camera_live tidak aktif, buka kamera CSI atau cv2.VideoCapture seperti biasa.
    """
    src = cfg["video_source"]
    if isinstance(src, int) or str(src).strip() in ("0", "/dev/video0"):
        try:
            import urllib.request
            tok_file = Path.home() / ".config/kangkung-camera.token"
            tok = tok_file.read_text(encoding="utf-8").strip() if tok_file.exists() else ""
            url = f"http://127.0.0.1:8787/snapshot.jpg?token={tok}"
            with urllib.request.urlopen(url, timeout=2.5) as resp:
                arr = np.asarray(bytearray(resp.read()), dtype=np.uint8)
                fr_live = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if fr_live is not None:
                    fr_live = resize_frame(fr_live)
                    mw = cfg.get("max_width", 960)
                    if fr_live.shape[1] > mw:
                        s = mw / fr_live.shape[1]
                        fr_live = cv2.resize(fr_live, (mw, int(fr_live.shape[0] * s)))
                    return fr_live
        except Exception:
            pass

    if isinstance(src, str) and src.lower() in CSI_SOURCE:
        try:
            frame = camera_pi.ambil_frame_csi(cfg)
        except Exception as e:
            print(f"[WARN] kamera CSI gagal: {e}")
            return None
    else:
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            return None
        try:
            if isinstance(src, int):
                cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(cfg.get("usb_width", 1920)))
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(cfg.get("usb_height", 1080)))
            for _ in range(cfg.get("kamera_warmup", 5)):
                cap.read()
            ok, frame = cap.read()
            if not ok:
                return None
        finally:
            cap.release()

    frame = camera_pi.putar_frame(frame, cfg.get("camera_rotate", 0))
    frame = resize_frame(frame)
    mw = cfg.get("max_width", 960)
    if frame.shape[1] > mw:
        s = mw / frame.shape[1]
        frame = cv2.resize(frame, (mw, int(frame.shape[0] * s)))
    return frame


def analisis(frame, smoother):
    """Deteksi bed -> warp -> mask warna -> hasil per zona + global."""
    pts = deteksi_sudut_bed(frame)
    if pts is None:
        print("[INFO] Kontur bed belum terdeteksi, fallback menggunakan area frame penuh.")
        H, W = frame.shape[:2]
        pts = np.float32([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]])
    else:
        pts = smoother.update(pts)
    warped = warp_bed(frame, matriks_warp(pts))
    return analisis_bed_lengkap(warped, adaptif=True)


def gambar_snapshot(warped, zona):
    """Snapshot beranotasi (kanvas warp top-down) + HUD untuk dashboard."""
    disp = warped.copy()
    rows, cols = BED_CONFIG["grid_rows"], BED_CONFIG["grid_cols"]
    H, W = disp.shape[:2]
    ch, cw = H // rows, W // cols
    overlay = disp.copy()
    for r in range(rows):
        for c in range(cols):
            y1, y2 = r * ch, (r + 1) * ch if r < rows - 1 else H
            x1, x2 = c * cw, (c + 1) * cw if c < cols - 1 else W
            z = zona[f"R{r+1}C{c+1}"]
            warna = {"belum_siap": (51, 152, 255),
                     "hampir_siap": (18, 156, 243),
                     "siap_panen": (113, 204, 46),
                     "harus_panen": (60, 76, 231)}[z["status"]]
            cv2.rectangle(overlay, (x1, y1), (x2, y2), warna, -1)
            cv2.rectangle(disp, (x1, y1), (x2, y2), warna, 2)
            cv2.putText(disp, f"{z['coverage']:.0f}%", (x1 + 4, y1 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    disp = cv2.addWeighted(disp, 0.75, overlay, 0.25, 0)
    cov = float(np.mean([v["coverage"] for v in zona.values()]))
    kun = float(np.mean([v["pct_kuning"] for v in zona.values()]))
    cok = float(np.mean([v["pct_coklat"] for v in zona.values()]))
    cv2.putText(disp, f"Cov:{cov:.0f}% Kun:{kun:.1f}% Cok:{cok:.1f}%",
                (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 150), 2)
    cv2.putText(disp, datetime.now().strftime("%Y-%m-%d %H:%M"),
                (12, disp.shape[0] - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
    return disp


def buat_payload(cfg, hasil, suhu):
    dt = datetime.now()
    did = doc_id(cfg["device_id"], dt)
    # frame_id & captured_at_ms: kontrak minimum PSI. Waktu pengambilan dipakai
    # (bukan waktu publikasi) agar pembaca bisa menolak data usang.
    captured_ms = int(dt.timestamp() * 1000)
    fuzzy = hitung_fuzzy(hasil["piksel_zona"],
                         [z["kesehatan"] for z in hasil["zona"].values()],
                         captured_at_ms=captured_ms, frame_id=did)
    return {
        "device_id": cfg["device_id"],
        "timestamp": iso_ts(dt),
        "doc_id": did,
        "frame_id": did,
        "captured_at_ms": captured_ms,
        "mode": "PI-LIVE",
        "coverage_rata": hasil["coverage_rata"],
        "coverage_std": hasil["coverage_std"],
        "zona_siap_panen": hasil["zona_siap_panen"],
        "persen_siap": hasil["persen_siap"],
        "status_distribusi": hasil["status_distribusi"],
        "kesehatan": {
            "kuning_rata": hasil["kuning_rata"],
            "coklat_rata": hasil["coklat_rata"],
            "distribusi": hasil["kesehatan_distribusi"],
        },
        "fuzzy_input": fuzzy,
        "rekomendasi": "",
        "zona": hasil["zona"],
        "snapshot_url": None,
        "suhu_pi_c": round(suhu, 1) if suhu is not None else None,
    }, did


# ─── Siklus utama ────────────────────────────────────────────────────────────

def siklus(cfg, smoother):
    ok, suhu = dalam_batas(cfg["suhu_maks_c"])
    if not ok:
        print(f"[GUARD] Suhu {suhu:.1f}C > {cfg['suhu_maks_c']}C — "
              f"capture ditunda")
        return False

    frame = ambil_frame(cfg)
    if frame is None:
        print("[WARN] kamera/video tidak bisa dibaca")
        return False

    hasil = analisis(frame, smoother)
    if hasil is None:
        print("[WARN] bed tidak terdeteksi — coba siklus berikutnya")
        return False

    payload, did = buat_payload(cfg, hasil, suhu)
    outbox = BASE / cfg["outbox_dir"]
    outbox.mkdir(parents=True, exist_ok=True)
    snap_annotated = gambar_snapshot(hasil["canvas"], hasil["zona"])
    cv2.imwrite(str(outbox / f"{did}.jpg"), snap_annotated)
    (outbox / f"{did}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Rekam frame harian terbaik & kelola retensi siklus (FIFO maks 3 siklus)
    if _tracker is not None:
        try:
            _tracker.process_reading(did, snap_annotated, payload)
        except Exception as _e_proc:
            print(f"[WARN] Gagal update siklus pertumbuhan: {_e_proc}")

    print(f"[OK] {did}  cov={hasil['coverage_rata']}%  "
          f"kuning={payload['fuzzy_input']['kuning_pct']}%  "
          f"coklat={payload['fuzzy_input']['coklat_pct']}%  "
          f"suhu={payload['suhu_pi_c']}")
    return True


def main():
    cfg = load_config()
    smoother = CornerSmoother(alpha=0.2)
    print(f"[START] {cfg['device_id']}  interval={cfg['interval_menit']}m  "
          f"maks suhu={cfg['suhu_maks_c']}C")

    if "--test" in sys.argv:
        siklus(cfg, smoother)
        n = firebase_uplink.sync_outbox(cfg)
        print(f"[TEST] selesai. terkirim={n} (sisanya di outbox/)")
        return

    while True:
        try:
            siklus(cfg, smoother)
            n = firebase_uplink.sync_outbox(cfg)
            if n:
                print(f"[UPLINK] {n} dokumen terkirim")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[ERROR] {e} (lanjut siklus berikutnya)")
        time.sleep(cfg["interval_menit"] * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOP] dihentikan user")