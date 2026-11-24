#!/usr/bin/env python3
"""Preview kamera CSI via MJPEG. Bind hanya ke IP Tailscale, URL ber-token."""
import argparse
import hmac
import json
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import cv2
from camera_pi import putar_frame

BASE = Path(__file__).resolve().parent
MODULES_DIR = BASE / "modules"
if MODULES_DIR.is_dir():
    sys.path.insert(0, str(MODULES_DIR))
sys.path.insert(0, str(BASE))

try:
    from adaptive_bed import (
        CornerSmoother,
        analisis_bed_lengkap,
        deteksi_sudut_bed,
        gambar_grid_dalam_box,
        matriks_warp,
        resize_frame,
        warp_bed,
    )
    from fuzzy_export import hitung_fuzzy
    from kangkung_cv import parameter_adaptif
    _CV_READY = True
except Exception as _cv_err:
    _CV_READY = False
    print(f"[WARN] Modul CV live tidak aktif: {_cv_err}", flush=True)


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
    def __init__(self, width, height, fps, rotate=0, vision_enabled=True,
                 vision_interval=1.5, api_vision_url="http://127.0.0.1:8080/api/aquaponik/vision"):
        from picamera2 import Picamera2
        self.period = 1 / max(0.2, min(fps, 10))
        self.rotate = int(rotate or 0) % 360
        self.vision_enabled = bool(vision_enabled and _CV_READY)
        self.vision_interval = max(0.8, float(vision_interval))
        self.api_vision_url = api_vision_url
        self.cv = threading.Condition()
        self.jpeg, self.vision_jpeg, self.updated, self.error = None, None, 0.0, None
        self._frame_lock = threading.Lock()
        self._latest_bgr = None
        self._latest_seq = 0
        self.latest_vision = {
            "bed_detected": False,
            "hsv_info": {},
            "source": "live_adaptive_hsv_standby",
            "updated_at": "",
        }
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_video_configuration(
            main={"size": (width, height), "format": "RGB888"}))
        self.cam.start()
        threading.Thread(target=self._loop, name="camera-capture", daemon=True).start()
        if self.vision_enabled:
            threading.Thread(target=self._vision_loop, name="vision-analyzer", daemon=True).start()

    def _loop(self):
        try:
            while True:
                rgb = self.cam.capture_array()
                bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                if self.rotate:
                    bgr = putar_frame(bgr, self.rotate)
                if self.vision_enabled:
                    with self._frame_lock:
                        self._latest_bgr = bgr.copy()
                        self._latest_seq += 1
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

    def _post_vision(self, payload):
        try:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            req = urllib.request.Request(
                self.api_vision_url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=0.9):
                pass
        except (urllib.error.URLError, TimeoutError, OSError):
            pass

    def _vision_loop(self):
        smoother = CornerSmoother(alpha=0.25)
        cached_pts = None
        ticks = 0
        miss_count = 0
        last_seq = 0

        while True:
            time.sleep(self.vision_interval)
            with self._frame_lock:
                if self._latest_bgr is None or self._latest_seq == last_seq:
                    continue
                bgr = self._latest_bgr.copy()
                last_seq = self._latest_seq

            try:
                fr = resize_frame(bgr)
                if fr.shape[1] > 960:
                    scale = 960.0 / fr.shape[1]
                    fr = cv2.resize(fr, (960, int(fr.shape[0] * scale)))

                ticks += 1
                pts = None
                # Deteksi adaptif kontinu: deteksi tepi bed di setiap siklus tanpa modulo jeda
                det = deteksi_sudut_bed(fr)
                if det is not None:
                    pts = smoother.update(det)
                    cached_pts = pts
                    miss_count = 0
                else:
                    # Graceful holdover: jika sesaat frame buram / ada oklusi, pertahankan
                    # koordinat terakhir sampai maks 8 siklus (12s) sambil terus mencari di siklus berikutnya
                    if cached_pts is not None and miss_count < 8:
                        pts = cached_pts
                        miss_count += 1
                    else:
                        pts = None
                        cached_pts = None

                now_str = time.strftime("%Y-%m-%d %H:%M:%S")
                if pts is None:
                    hsv_tmp = cv2.cvtColor(fr, cv2.COLOR_BGR2HSV)
                    info = parameter_adaptif(hsv_tmp).get("info", {})
                    payload = {
                        "bed_detected": False,
                        "hsv_info": info,
                        "source": "live_adaptive_hsv_standby",
                        "updated_at": now_str,
                    }
                    disp = fr
                    cv2.putText(
                        disp,
                        f"HSV Adaptif Standby | S_lo:{info.get('s_lo')} V_lo:{info.get('v_lo')} f:{info.get('f')}",
                        (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (56, 189, 248), 2,
                    )
                else:
                    warped = warp_bed(fr, matriks_warp(pts))
                    hasil = analisis_bed_lengkap(warped, adaptif=True)
                    captured_ms = int(time.time() * 1000)
                    fid = f"live-{captured_ms}"
                    fz = hitung_fuzzy(
                        hasil["piksel_zona"],
                        [z["kesehatan"] for z in hasil["zona"].values()],
                        captured_at_ms=captured_ms,
                        frame_id=fid,
                    )
                    psi_val = fz.get("psi")
                    kun = float(fz.get("kuning_pct") or 0.0)
                    cok = float(fz.get("coklat_pct") or 0.0)
                    green = round(max(0.0, 100.0 - kun - cok), 2)
                    info = hasil.get("info_adaptif", {})

                    rekomen = "Kanopi sehat, kondisi optimal."
                    if psi_val is not None and psi_val >= 35.0:
                        rekomen = f"Terdeteksi stres daun tinggi (PSI {psi_val:.1f}%), cek pH & nutrisi."
                    elif kun >= 10.0 or cok >= 3.0:
                        rekomen = f"Waspada klorosis ({kun:.1f}%) / nekrosis ({cok:.1f}%)."

                    payload = {
                        "bed_detected": True,
                        "psi": round(float(psi_val), 2) if psi_val is not None else None,
                        "coverage": hasil["coverage_rata"],
                        "green_pct": green,
                        "yellow_pct": round(kun, 2),
                        "brown_pct": round(cok, 2),
                        "zona": hasil["zona"],
                        "fuzzy_input": fz,
                        "hsv_info": info,
                        "rekomendasi": rekomen,
                        "source": "live_adaptive_hsv",
                        "updated_at": now_str,
                    }
                    zona_list = [dict(z, zona=zid) for zid, z in hasil["zona"].items()]
                    disp = gambar_grid_dalam_box(fr.copy(), pts, zona_list)
                    cv2.putText(
                        disp,
                        f"HSV Adaptif | Cov:{hasil['coverage_rata']:.1f}% PSI:{psi_val if psi_val is not None else '-'}% S>={info.get('s_lo')} V>={info.get('v_lo')} WB:{'Fix' if info.get('wb_cast') else 'OK'}",
                        (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (74, 222, 128), 2,
                    )

                ok_v, v_jpg = cv2.imencode(".jpg", disp, [cv2.IMWRITE_JPEG_QUALITY, 75])
                with self._frame_lock:
                    self.latest_vision = payload
                    if ok_v:
                        self.vision_jpeg = v_jpg.tobytes()

                if self.api_vision_url:
                    self._post_vision(payload)
            except Exception as exc:
                print(f"[WARN] Analisis vision live gagal: {exc}", flush=True)

    def get(self):
        with self.cv:
            self.cv.wait_for(lambda: self.jpeg is not None or self.error, 5)
            if self.jpeg is None:
                raise RuntimeError(self.error or "Kamera belum menghasilkan frame")
            return self.jpeg

    def get_vision(self):
        with self._frame_lock:
            return dict(self.latest_vision), self.vision_jpeg

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
        if path == "/vision":
            vis, _ = self.server.camera.get_vision()
            return self.send(json.dumps(vis).encode("utf-8"), "application/json")
        if path == "/vision.jpg":
            _, vjpg = self.server.camera.get_vision()
            return self.send(vjpg if vjpg is not None else self.server.camera.get(), "image/jpeg")
        if path == "/snapshot.jpg":
            return self.send(self.server.camera.get(), "image/jpeg")
        if path == "/stream.mjpg":
            return self.stream()
        self.send(b"Not found", "text/plain", 404)

    def stream(self):
        boundary = "kangkungframe"
        self.connection.settimeout(12)
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
    cfg = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="auto")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--width", type=int, default=int(cfg.get("usb_width", 1920)))
    ap.add_argument("--height", type=int, default=int(cfg.get("usb_height", 1080)))
    ap.add_argument("--fps", type=float, default=2)
    ap.add_argument("--rotate", type=int, default=None,
                    help="Putar frame 0/90/180/270 derajat (default baca config.json)")
    ap.add_argument("--no-vision", action="store_true",
                    help="Matikan analisis HSV adaptif live di background")
    ap.add_argument("--vision-interval", type=float, default=1.5,
                    help="Interval analisis HSV adaptif live (detik)")
    ap.add_argument("--api-vision-url", default="http://127.0.0.1:8080/api/aquaponik/vision",
                    help="Endpoint API vision server lokal")
    ap.add_argument("--token-file", type=Path,
                    default=Path.home() / ".config/kangkung-camera.token")
    args = ap.parse_args()
    # Jika 'auto' atau '0.0.0.0', bind ke 0.0.0.0 agar dapat diakses dari LAN/WiFi lokal maupun Tailscale VPN
    host = "0.0.0.0" if args.host in ("auto", "0.0.0.0") else args.host
    rotate = int(args.rotate if args.rotate is not None else cfg.get("camera_rotate", 180)) % 360
    token = token_aman(args.token_file.expanduser())
    camera = Kamera(
        args.width,
        args.height,
        args.fps,
        rotate=rotate,
        vision_enabled=not args.no_vision,
        vision_interval=args.vision_interval,
        api_vision_url=args.api_vision_url,
    )
    server = ThreadingHTTPServer((host, args.port), Handler)
    server.camera, server.token = camera, token
    ts_ip = tailscale_ip()
    print(f"[CAMERA] Server berjalan di port {args.port} ({args.width}x{args.height}, rotate={rotate} deg)")
    print(f"  - Tailscale VPN : http://{ts_ip}:{args.port}/?token={token}")
    print(f"  - Lokal LAN/WiFi: http://<IP_WIFI_RASPI>:{args.port}/?token={token}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        camera.close()
        server.server_close()


if __name__ == "__main__":
    main()

