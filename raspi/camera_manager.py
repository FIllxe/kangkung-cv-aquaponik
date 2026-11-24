#!/usr/bin/env python3
"""CAMERA MANAGER — Pengatur Switch Mode Monitoring vs Live Streaming.

Fungsi:
  1. Mengelola pergantian mode antara:
     - MODE MONITORING : kangkung.service (AI/CV tiap jam -> Firebase, hemat daya/kuota)
     - MODE LIVE STREAM: kangkung-camera.service (MJPEG port 8787)
  2. Mencegah konflik perebutan kamera (/dev/video0) antar kedua mode.
  3. Fitur Keamanan Auto-Timeout (default 5 menit):
     Jika mode streaming menyala, sistem otomatis kembali ke mode monitoring
     setelah durasi habis untuk melindungi kuota dan suhu Raspberry Pi.
  4. Mendukung kontrol cloud via Firestore (koleksi: device_control/pi-bed-01)
     maupun kontrol lokal via CLI/API.
"""

import sys
import os
import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent

DEFAULT_DEVICE_ID = "pi-bed-01"
DEFAULT_STREAM_PORT = 8787
DEFAULT_TIMEOUT_SEC = 300  # 5 menit

STREAM_SERVICE = "kangkung-camera.service"
MONITOR_SERVICE = "kangkung.service"


def get_token():
    token_file = Path.home() / ".config/kangkung-camera.token"
    if token_file.exists():
        t = token_file.read_text(encoding="utf-8").strip()
        if t:
            return t
    return "iPcqot-pKrDzvImXynH_QDfq"


def get_tailscale_ip():
    try:
        out = subprocess.check_output(["tailscale", "ip", "-4"], text=True, timeout=3)
        return out.strip().splitlines()[0]
    except Exception:
        return "100.123.187.56"


def get_lan_ip():
    try:
        out = subprocess.check_output(["hostname", "-I"], text=True, timeout=3)
        ips = out.strip().split()
        for ip in ips:
            if not ip.startswith("100.") and not ip.startswith("127."):
                return ip
        return ips[0] if ips else "127.0.0.1"
    except Exception:
        return "127.0.0.1"


class CameraManager:
    def __init__(self, device_id=DEFAULT_DEVICE_ID):
        self.device_id = device_id
        self.state_file = BASE / "camera_mode_state.json"
        self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            try:
                self.state = json.loads(self.state_file.read_text(encoding="utf-8"))
                return
            except Exception:
                pass
        self.state = {
            "mode": "monitoring",
            "active_since": datetime.now().isoformat(),
            "expires_at": None,
            "stream_url": f"http://{get_tailscale_ip()}:{DEFAULT_STREAM_PORT}/stream.mjpg?token={get_token()}",
            "stream_url_lan": f"http://{get_lan_ip()}:{DEFAULT_STREAM_PORT}/stream.mjpg?token={get_token()}"
        }
        self._save_state()

    def _save_state(self):
        self.state_file.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def run_cmd(self, cmd_list):
        try:
            res = subprocess.run(cmd_list, capture_output=True, text=True, timeout=10)
            return res.returncode == 0
        except Exception as e:
            print(f"[ERR] Gagal menjalankan {cmd_list}: {e}")
            return False

    def switch_to_streaming(self, duration_sec=DEFAULT_TIMEOUT_SEC):
        """Beralih ke mode Live Streaming."""
        now = datetime.now()
        exp = now + timedelta(seconds=duration_sec)
        print(f"[SWITCH] Mengaktifkan LIVE STREAMING (Durasi: {duration_sec}s s/d {exp.strftime('%H:%M:%S')})...")

        # 1. Hentikan monitoring (lepaskan kamera)
        self.run_cmd(["sudo", "systemctl", "stop", MONITOR_SERVICE])
        time.sleep(0.5)

        # 2. Nyalakan service camera streaming
        self.run_cmd(["sudo", "systemctl", "start", STREAM_SERVICE])

        self.state["mode"] = "streaming"
        self.state["active_since"] = now.isoformat()
        self.state["expires_at"] = exp.isoformat()
        self.state["timeout_seconds"] = duration_sec
        self.state["stream_url"] = f"http://{get_tailscale_ip()}:{DEFAULT_STREAM_PORT}/stream.mjpg?token={get_token()}"
        self.state["stream_url_lan"] = f"http://{get_lan_ip()}:{DEFAULT_STREAM_PORT}/stream.mjpg?token={get_token()}"
        self._save_state()
        self.sync_to_firestore()
        print(f"[OK] Live streaming aktif di: {self.state['stream_url']}")
        return self.state

    def switch_to_monitoring(self):
        """Beralih kembali ke mode Monitoring."""
        now = datetime.now()
        print("[SWITCH] Mengaktifkan kembali MODE MONITORING OTOMATIS...")

        # 1. Hentikan camera stream (lepaskan kamera)
        self.run_cmd(["sudo", "systemctl", "stop", STREAM_SERVICE])
        time.sleep(0.5)

        # 2. Nyalakan service kangkung monitoring
        self.run_cmd(["sudo", "systemctl", "start", MONITOR_SERVICE])

        self.state["mode"] = "monitoring"
        self.state["active_since"] = now.isoformat()
        self.state["expires_at"] = None
        self._save_state()
        self.sync_to_firestore()
        print("[OK] Mode monitoring aktif. AI Computer Vision berjalan sesuai jadwal.")
        return self.state

    def check_timeout(self):
        """Cek apakah durasi streaming sudah habis -> jika ya, auto-revert ke monitoring."""
        if self.state.get("mode") == "streaming" and self.state.get("expires_at"):
            try:
                exp = datetime.fromisoformat(self.state["expires_at"])
                if datetime.now() >= exp:
                    print("[TIMEOUT] Durasi streaming 5 menit habis! Auto-revert ke mode monitoring.")
                    self.switch_to_monitoring()
            except Exception as e:
                print(f"[WARN] Error parse expires_at: {e}")

    def sync_to_firestore(self):
        """Sinkronkan status mode kamera ke Firestore koleksi device_control."""
        try:
            sa_path = BASE / "service-account.json"
            if not sa_path.exists():
                return
            import firebase_admin
            from firebase_admin import credentials, firestore
            if not firebase_admin._apps:
                firebase_admin.initialize_app(credentials.Certificate(str(sa_path)))
            db = firestore.client()
            db.collection("device_control").document(self.device_id).set({
                "device_id": self.device_id,
                "mode": self.state["mode"],
                "active_since": self.state["active_since"],
                "expires_at": self.state.get("expires_at"),
                "stream_url": self.state.get("stream_url"),
                "stream_url_lan": self.state.get("stream_url_lan"),
                "lan_ip": get_lan_ip(),
                "tailscale_ip": get_tailscale_ip(),
                "last_heartbeat": datetime.now().isoformat()
            }, merge=True)
        except Exception as e:
            # Opsional, tidak mengganggu operasi lokal
            pass

    def listen_firestore_loop(self):
        """Daemon listener: mendengarkan perintah switch dari web via Firestore."""
        print(f"[DAEMON] Mendengarkan perintah kontrol kamera untuk {self.device_id}...")
        while True:
            try:
                self.check_timeout()
                sa_path = BASE / "service-account.json"
                if sa_path.exists():
                    import firebase_admin
                    from firebase_admin import credentials, firestore
                    if not firebase_admin._apps:
                        firebase_admin.initialize_app(credentials.Certificate(str(sa_path)))
                    db = firestore.client()
                    doc = db.collection("device_control").document(self.device_id).get()
                    if doc.exists:
                        data = doc.to_dict()
                        req_mode = data.get("requested_mode")
                        if req_mode and req_mode != self.state.get("mode"):
                            dur = int(data.get("duration_seconds", DEFAULT_TIMEOUT_SEC))
                            print(f"[CLOUD-CMD] Perintah dari web: beralih ke {req_mode}")
                            if req_mode == "streaming":
                                self.switch_to_streaming(dur)
                            else:
                                self.switch_to_monitoring()
                            # Hapus requested_mode agar tidak berulang
                            db.collection("device_control").document(self.device_id).update({
                                "requested_mode": None,
                                "current_mode": self.state["mode"]
                            })
            except Exception as e:
                print(f"[DAEMON-LOOP] {e}")
            time.sleep(3)


def main():
    mgr = CameraManager()
    if "--stream" in sys.argv:
        dur = int(sys.argv[sys.argv.index("--stream") + 1]) if len(sys.argv) > sys.argv.index("--stream") + 1 and sys.argv[sys.argv.index("--stream") + 1].isdigit() else DEFAULT_TIMEOUT_SEC
        mgr.switch_to_streaming(dur)
    elif "--monitor" in sys.argv:
        mgr.switch_to_monitoring()
    elif "--status" in sys.argv:
        mgr.check_timeout()
        print(json.dumps(mgr.state, indent=2))
    elif "--daemon" in sys.argv:
        mgr.listen_firestore_loop()
    else:
        print("Penggunaan:")
        print("  python camera_manager.py --stream [durasi_detik]")
        print("  python camera_manager.py --monitor")
        print("  python camera_manager.py --status")
        print("  python camera_manager.py --daemon")


if __name__ == "__main__":
    main()
