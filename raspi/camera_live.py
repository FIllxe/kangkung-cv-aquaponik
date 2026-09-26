#!/usr/bin/env python3
"""Preview kamera CSI via MJPEG. Bind hanya ke IP Tailscale, URL ber-token."""
import argparse
import hmac
import json
import secrets
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import cv2

BASE = Path(__file__).resolve().parent


def token_aman(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if token:
            return token
    token = secrets.token_urlsafe(18)
    path.write_text(token + "\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return token


def tailscale_ip():
    try:
        result = subprocess.check_output(
            ["tailscale", "ip", "-4"], text=True, timeout=5)
        return result.strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        return "127.0.0.1"


class Kamera:
    def __init__(self, width, height, fps):
        from picamera2 import Picamera2
        self.period = 1 / max(0.2, min(fps, 10))
        self.cv = threading.Condition()
        self.jpeg, self.updated, self.error = None, 0.0, None
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_video_configuration(
            main={"size": (width, height), "format": "RGB888"}))
        self.cam.start()
        threading.Thread(target=self._loop, name="camera-capture", daemon=True).start()

    def _loop(self):
        try:
            while True:
                rgb = self.cam.capture_array()
                bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                ok, data = cv2.imencode(
                    ".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 72])
                if ok:
                    with self.cv:
                        self.jpeg = data.tobytes()
                        self.updated = time.monotonic()
                        self.error = None
                        self.cv.notify_all()
                time.sleep(self.period)
        except Exception as exc:
            with self.cv:
                self.error = str(exc)
                self.cv.notify_all()

    def get(self):
        with self.cv:
            self.cv.wait_for(lambda: self.jpeg is not None or self.error, 5)
            if self.jpeg is None:
                raise RuntimeError(self.error or "Kamera belum menghasilkan frame")
            return self.jpeg

    def health(self):
        with self.cv:
            return {
                "ok": self.jpeg is not None and self.error is None,
                "error": self.error,
                "frame_age_seconds": (round(time.monotonic() - self.updated, 2)
                                       if self.updated else None),
            }

    def close(self):
        self.cam.stop()
        self.cam.close()


def html(token):
    return f'''<!doctype html><html lang="id"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Live Kamera ecofarm</title><style>
body{{margin:0;background:#101426;color:#eef1ff;font:16px system-ui;text-align:center}}
header{{padding:16px}}small{{color:#9aa4cf}}img{{display:block;width:min(100%,960px);height:auto;margin:auto;border:1px solid #39456d;border-radius:12px}}
p{{color:#9aa4cf}}a{{color:#7dd3fc}}</style>
<header><h1>🌿 Live Kamera ecofarm</h1><small>via Tailscale · privat</small>
<img src="/stream.mjpg?token={token}" alt="Live camera Raspberry Pi">
<p>Jika gambar berhenti, muat ulang halaman.</p>
<p><a href="/snapshot.jpg?token={token}">Snapshot JPG terbaru</a></p>'''.encode()


class Handler(BaseHTTPRequestHandler):
    def allowed(self):
        given = parse_qs(urlparse(self.path).query).get("token", [""])[0]
        return hmac.compare_digest(given, self.server.token)

    def send(self, body, kind, status=200):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if not self.allowed():
            return self.send(b"Unauthorized", "text/plain", 401)
        if path == "/":
            return self.send(html(self.server.token), "text/html; charset=utf-8")
        if path == "/health":
            data = json.dumps(self.server.camera.health()).encode()
            return self.send(data, "application/json")
        if path == "/snapshot.jpg":
            return self.send(self.server.camera.get(), "image/jpeg")
        if path == "/stream.mjpg":
            return self.stream()
        self.send(b"Not found", "text/plain", 404)

    def stream(self):
        boundary = "kangkungframe"
        self.send_response(200)
        self.send_header("Content-Type",
                         f"multipart/x-mixed-replace; boundary={boundary}")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            while True:
                frame = self.server.camera.get()
                header = (f"--{boundary}\r\nContent-Type: image/jpeg\r\n"
                          f"Content-Length: {len(frame)}\r\n\r\n").encode()
                self.wfile.write(header + frame + b"\r\n")
                self.wfile.flush()
                time.sleep(self.server.camera.period)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            pass

    def log_message(self, fmt, *args):
        return


def main():
    # Config harus valid sebelum kamera dikunci oleh proses lain.
    json.loads((BASE / "config.json").read_text(encoding="utf-8"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="auto")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--fps", type=float, default=2)
    ap.add_argument("--token-file", type=Path,
                    default=Path.home() / ".config/kangkung-camera.token")
    args = ap.parse_args()
    host = tailscale_ip() if args.host == "auto" else args.host
    token = token_aman(args.token_file.expanduser())
    camera = Kamera(args.width, args.height, args.fps)
    server = ThreadingHTTPServer((host, args.port), Handler)
    server.camera, server.token = camera, token
    print(f"[CAMERA] http://{host}:{args.port}/?token={token}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        camera.close()
        server.server_close()


if __name__ == "__main__":
    main()

