"""camera_pi — ambil 1 frame dari kamera CSI Raspberry Pi (ov5647, imx219, ...).

OpenCV (`opencv-python-headless`) TIDAK bisa membaca kamera CSI lewat
`/dev/video0` pada kernel Raspberry Pi modern: device legacy MMAL terbuka tapi
tidak pernah mengeluarkan frame
(`dmesg`: "bcm2835-isp ... driver mismatch to MMAL").
Karena itu frame diambil lewat stack libcamera (yang sama dipakai `rpicam-*`):

  1. Picamera2   -> utama (paket apt `python3-picamera2` + `python3-libcamera`)
  2. rpicam-jpeg -> cadangan bila Picamera2 tidak tersedia

Keduanya mengembalikan frame BGR, siap dipakai pipeline `kangkung_pi.py`.
Diaktifkan lewat `config.json`: `"video_source": "csi"`.
"""
from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path

import cv2

# Default bila tidak ada di config.json
LEBAR_DEFAULT = 1296      # mode native 4:3 sensor ov5647 (cocok untuk warp bed)
TINGGI_DEFAULT = 972
WARMUP_DEFAULT = 2.0      # detik: beri waktu auto-exposure/white-balance stabil


def _ukuran(cfg):
    """Resolusi capture (lebar, tinggi) dari config.json."""
    return (int(cfg.get("csi_width", LEBAR_DEFAULT)),
            int(cfg.get("csi_height", TINGGI_DEFAULT)))


def ambil_frame_picamera2(cfg):
    """Capture 1 frame via Picamera2 (libcamera). Return frame BGR."""
    from picamera2 import Picamera2

    lebar, tinggi = _ukuran(cfg)
    cam = Picamera2()
    cam.configure(cam.create_still_configuration(
        main={"size": (lebar, tinggi), "format": "RGB888"}))
    try:
        cam.start()
        time.sleep(float(cfg.get("csi_warmup_detik", WARMUP_DEFAULT)))
        return cv2.cvtColor(cam.capture_array(), cv2.COLOR_RGB2BGR)
    finally:
        cam.stop()
        cam.close()


def ambil_frame_rpicam(cfg):
    """Cadangan: jepret JPEG via `rpicam-jpeg`, lalu baca dengan OpenCV."""
    lebar, tinggi = _ukuran(cfg)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        path = Path(tmp.name)
    try:
        subprocess.run(
            ["rpicam-jpeg", "-o", str(path), "--width", str(lebar),
             "--height", str(tinggi), "--nopreview", "--timeout",
             str(int(float(cfg.get("csi_warmup_detik", WARMUP_DEFAULT)) * 1000))],
            check=True, capture_output=True, text=True, timeout=60)
        frame = cv2.imread(str(path))
        if frame is None:
            raise RuntimeError("rpicam-jpeg menghasilkan file tak terbaca")
        return frame
    finally:
        path.unlink(missing_ok=True)


def ambil_frame_csi(cfg):
    """Ambil 1 frame kamera CSI: Picamera2 dulu, `rpicam-jpeg` bila gagal."""
    try:
        return ambil_frame_picamera2(cfg)
    except Exception as e:                      # ImportError / kamera sibuk
        print(f"[CAM] Picamera2 gagal ({e}) -> coba rpicam-jpeg")
    return ambil_frame_rpicam(cfg)


if __name__ == "__main__":
    import json

    base = Path(__file__).resolve().parent
    cfg = json.loads((base / "config.json").read_text(encoding="utf-8"))
    t0 = time.time()
    frame = ambil_frame_csi(cfg)
    print(f"frame: {frame.shape}  ({time.time() - t0:.1f}s)")
    keluar = Path("/tmp/camera_pi_test.jpg")
    cv2.imwrite(str(keluar), frame)
    print(f"tersimpan: {keluar}")
