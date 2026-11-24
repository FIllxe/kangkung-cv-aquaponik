#!/usr/bin/env python3
"""
========================================================================
SIMULATOR KAMERA STREAMING LOKAL (UNTUK PENGUJIAN SAAT RASPBERRY PI OFFLINE)
Teknik Komputer FT Universitas Negeri Semarang 2026
========================================================================
Fungsi:
- Mensimulasikan server streaming MJPEG Raspberry Pi di port 8787
- Endpoint sama persis: /stream.mjpg?token=iPcqot-pKrDzvImXynH_QDfq
- Sumber video otomatis:
  1. Webcam laptop (jika tersedia), ATAU
  2. Snapshot frame bed kangkung (latest_snapshot.jpg) berputar
========================================================================
"""

import sys
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from pathlib import Path
import cv2

PORT = 8787
TOKEN = "iPcqot-pKrDzvImXynH_QDfq"
ROOT_DIR = Path(__file__).resolve().parent

class FrameProvider:
    def __init__(self):
        self.lock = threading.Lock()
        self.current_frame = None
        self.cap = None

        # Coba buka webcam 0 laptop
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.cap = None
        except Exception:
            self.cap = None

        # Cari file gambar cadangan jika webcam tidak ada
        self.fallback_img = None
        possible_imgs = [
            ROOT_DIR / "web" / "latest_snapshot.jpg",
            ROOT_DIR / "latest_snapshot.jpg",
            ROOT_DIR.parent / "web" / "latest_snapshot.jpg",
            ROOT_DIR.parent / "web aquaponik" / "web aquaponik" / "latest_snapshot.jpg"
        ]
        for p in possible_imgs:
            if p.exists():
                self.fallback_img = cv2.imread(str(p))
                if self.fallback_img is not None:
                    break

        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            frame = None
            if self.cap and self.cap.isOpened():
                ret, img = self.cap.read()
                if ret:
                    frame = img

            if frame is None and self.fallback_img is not None:
                frame = self.fallback_img.copy()
                # Tambahkan overlay timestamp
                t_str = time.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, f"SIMULATOR MODE | {t_str}", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if frame is not None:
                # Resize untuk efisiensi stream
                h, w = frame.shape[:2]
                if w > 800:
                    frame = cv2.resize(frame, (800, int(h * 800 / w)))
                ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                if ok:
                    with self.lock:
                        self.current_frame = jpeg.tobytes()

            time.sleep(0.1)

    def get_frame(self):
        with self.lock:
            return self.current_frame

provider = FrameProvider()

class StreamHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        given_token = qs.get("token", [""])[0]

        if parsed.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true, "status": "simulator_running"}')
            return

        if parsed.path in ["/stream.mjpg", "/stream"]:
            boundary = "kangkungframe"
            self.send_response(200)
            self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={boundary}")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.end_headers()
            try:
                while True:
                    frame = provider.get_frame()
                    if frame:
                        header = (f"--{boundary}\r\nContent-Type: image/jpeg\r\n"
                                  f"Content-Length: {len(frame)}\r\n\r\n").encode()
                        self.wfile.write(header + frame + b"\r\n")
                        self.wfile.flush()
                    time.sleep(0.1)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        if parsed.path in ["/snapshot.jpg", "/snapshot"]:
            frame = provider.get_frame()
            if frame:
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(frame)))
                self.end_headers()
                self.wfile.write(frame)
            else:
                self.send_response(503)
                self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return

def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), StreamHandler)
    print(f"\n" + "=" * 65)
    print(f" SIMULATOR LIVE STREAM AKTIF DI PORT {PORT}")
    print(f"=" * 65)
    print(f"URL Stream Lokal : http://localhost:{PORT}/stream.mjpg?token={TOKEN}")
    print(f"Endpoint Health  : http://localhost:{PORT}/health")
    print(f"Untuk menguji di web: Klik 'Setup IP' lalu masukkan 'localhost'")
    print(f"=" * 65 + "\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Simulator dihentikan.")

if __name__ == "__main__":
    main()
