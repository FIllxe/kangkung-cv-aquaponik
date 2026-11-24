#!/usr/bin/env python3
"""
========================================================================
SERVER LOKAL TERPADU — CAPSTONE AQUAPONIK & MONITORING KANGKUNG
Teknik Komputer FT Universitas Negeri Semarang 2026
========================================================================
Fitur Server:
1. Multi-threaded (Dapat diakses bersamaan oleh Felix, teman, & HP).
2. Binding ke 0.0.0.0 (Dapat diakses via Wi-Fi lokal, LAN, & Tailscale).
3. MIME Type Fixer (Mendukung .glb 3D Three.js, ES Module JS, JSON).
4. CORS Enabled (Memungkinkan integrasi API ESP32, Firebase, & RPi).
5. Auto Clean URL (contoh: /monitoring otomatis memuat monitoring.html).
========================================================================
"""

import http.server
import socket
import socketserver
import os
import sys
import re
import json
import time
import subprocess
import mimetypes
import webbrowser
from pathlib import Path

# Basis data telemetri real-time dalam memori (ESP32 & Raspberry Pi)
LIVE_TELEMETRY = {
    "node": "esp32",
    "sensors": {
        "pH": 6.85,
        "turbidity": 8.4,
        "water_level_cm": 68.0,
        "temperature_c": 27.5,
        "rain_detected": False
    },
    "actuators": {
        "valve_in": False,
        "valve_out": False,
        "pump": True,
        "feeder": False
    },
    "vision": {
        "psi": 11.8,
        "coverage": 82.4
    },
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
}

# Daftarkan MIME types khusus agar Three.js & Modern JS berjalan lancar
mimetypes.init()
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("model/gltf-binary", ".glb")
mimetypes.add_type("model/gltf+json", ".gltf")
mimetypes.add_type("text/plain", ".obj")
mimetypes.add_type("text/plain", ".mtl")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("image/webp", ".webp")

def get_network_interfaces():
    """Mendeteksi seluruh IP address antarmuka jaringan yang aktif."""
    interfaces = []
    
    # 1. Coba deteksi via ipconfig (Windows)
    try:
        out = subprocess.check_output("ipconfig", shell=True, text=True, errors="ignore")
        curr_adapter = "Jaringan Lokal"
        for line in out.splitlines():
            line_str = line.strip()
            if "adapter" in line_str.lower() and ":" in line_str:
                curr_adapter = line_str.split("adapter")[-1].replace(":", "").strip()
            m = re.search(r"IPv4 Address[ .]*:[ ]*([0-9.]+)", line_str)
            if m:
                ip = m.group(1)
                if not ip.startswith("127.") and not ip.startswith("169.254"):
                    interfaces.append((ip, curr_adapter))
    except Exception:
        pass

    # 2. Cadangan via socket hostname
    if not interfaces:
        try:
            host = socket.gethostname()
            for ip in socket.gethostbyname_ex(host)[2]:
                if not ip.startswith("127.") and not ip.startswith("169.254"):
                    interfaces.append((ip, "Wi-Fi / LAN"))
        except Exception:
            pass

    return interfaces

def cari_port_tersedia(port_awal=8080, maks_percobaan=20):
    """Mencari port yang kosong jika port default 8080 sedang digunakan."""
    for p in range(port_awal, port_awal + maks_percobaan):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return port_awal

class AquaponikRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler khusus dengan CORS, MIME types fix, dan clean URL rewrite."""
    
    def end_headers(self):
        # Header CORS agar dapat diakses dari domain/aplikasi lain
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        # Header anti-cache untuk snapshot & telemetri terbaru
        if any(self.path.endswith(ext) for ext in [".json", ".jpg", ".png"]):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        raw_path = self.path.split("?")[0].split("#")[0]
        # Endpoint API telemetri live untuk ESP32 / Mock Data
        if raw_path == "/api/aquaponik/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(LIVE_TELEMETRY).encode("utf-8"))
            return

        # Rewrite clean URL: misal /monitoring diarahkan ke /monitoring.html
        if raw_path != "/" and not "." in os.path.basename(raw_path):
            file_html = raw_path.lstrip("/") + ".html"
            if os.path.isfile(os.path.join(self.directory, file_html)):
                query = self.path[len(raw_path):]
                self.path = "/" + file_html + query
        return super().do_GET()

    def do_POST(self):
        raw_path = self.path.split("?")[0].split("#")[0]
        # Endpoint penerima update telemetri dari ESP32 atau emulator dummy
        if raw_path == "/api/aquaponik/data":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8"))
                if "sensors" in data and isinstance(data["sensors"], dict):
                    LIVE_TELEMETRY["sensors"].update(data["sensors"])
                if "ph" in data or "pH" in data:
                    LIVE_TELEMETRY["sensors"]["pH"] = float(data.get("ph") or data.get("pH"))
                if "ntu" in data or "turbidity" in data:
                    LIVE_TELEMETRY["sensors"]["turbidity"] = float(data.get("ntu") or data.get("turbidity"))
                if "temp" in data or "temperature_c" in data:
                    LIVE_TELEMETRY["sensors"]["temperature_c"] = float(data.get("temp") or data.get("temperature_c"))
                if "lvl" in data or "water_level_cm" in data:
                    LIVE_TELEMETRY["sensors"]["water_level_cm"] = float(data.get("lvl") or data.get("water_level_cm"))
                if "actuators" in data and isinstance(data["actuators"], dict):
                    LIVE_TELEMETRY["actuators"].update(data["actuators"])
                LIVE_TELEMETRY["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "ack": True, "vision": LIVE_TELEMETRY["vision"]}).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))
                return

        self.send_response(404)
        self.end_headers()

    def guess_type(self, path):
        # Pastikan ekstensi .js, .glb dll selalu memiliki Content-Type yang valid
        ext = os.path.splitext(path)[1].lower()
        if ext in [".js", ".mjs"]:
            return "application/javascript; charset=utf-8"
        if ext == ".glb":
            return "model/gltf-binary"
        if ext == ".gltf":
            return "model/gltf+json"
        if ext == ".json":
            return "application/json; charset=utf-8"
        if ext == ".css":
            return "text/css; charset=utf-8"
        return super().guess_type(path)

    def log_message(self, format, *args):
        # Sembunyikan polling log jika berhasil 200/304 agar terminal tetap bersih
        if len(args) > 1 and str(args[1]) in ["200", "304"]:
            return
        super().log_message(format, *args)

def jalankan_server():
    # Tentukan direktori kerja (utamakan dist jika tersedia)
    base_dir = Path(__file__).resolve().parent
    if (base_dir / "dist").is_dir() and (base_dir / "dist" / "index.html").is_file():
        web_dir = base_dir / "dist"
    else:
        web_dir = base_dir

    port = cari_port_tersedia(8080)
    host = "0.0.0.0"

    class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    handler = lambda *args, **kwargs: AquaponikRequestHandler(*args, directory=str(web_dir), **kwargs)

    try:
        httpd = ThreadedServer((host, port), handler)
    except Exception as e:
        print(f"[!] Gagal menjalankan server pada port {port}: {e}")
        return

    interfaces = get_network_interfaces()

    # Cetak banner terminal interaktif & panduan lengkap
    print("\n" + "=" * 76)
    print("🌱 SERVER LOKAL CAPSTONE AQUAPONIK & MONITORING KANGKUNG AKTIF 🌱")
    print("   Teknik Komputer FT Universitas Negeri Semarang 2026")
    print("=" * 76)
    print(f"📁 Melayani direktori: {web_dir}")
    print(f"⚡ Status Server     : AKTIF (Multi-threaded & CORS Enabled)")
    print("-" * 76)
    print("🌐 ALAMAT URL UNTUK DIAKSES:")
    print(f"  [1] Komputer Ini (Localhost)  : http://localhost:{port}/")
    print(f"                                : http://127.0.0.1:{port}/")

    # Tampilkan antarmuka Wi-Fi dan Tailscale
    wifi_shown = False
    for ip, name in interfaces:
        if "tailscale" in name.lower():
            print(f"  [2] Akses Teman via Tailscale : http://{ip}:{port}/")
            print(f"      (Bisa diakses teman meski beda Wi-Fi/jarak jauh)")
        else:
            print(f"  [3] Akses Teman / HP 1 Wi-Fi   : http://{ip}:{port}/")
            print(f"      (Nama Adaptor: {name})")
            wifi_shown = True

    if not wifi_shown:
        print(f"  [*] Tips: Sambungkan ke Wi-Fi yang sama untuk berbagi akses ke teman.")

    print("-" * 76)
    print("📑 DAFTAR HALAMAN UTAMA TERINTEGRASI:")
    print(f"  • Beranda & Riset Capstone   : http://localhost:{port}/index.html")
    print(f"  • Live Monitoring Kangkung   : http://localhost:{port}/monitoring.html")
    print(f"  • Dashboard Pengelola Sugeno : http://localhost:{port}/dashboard.html")
    print(f"  • Simulator 3D Digital Twin  : http://localhost:{port}/simulasi.html")
    print("-" * 76)
    print("💡 CARA AGAR ORANG LAIN DI INTERNET JUGA BISA MENGAKSES (BEBAS PORT FORWARD):")
    print("  A. Gunakan Tailscale (Gratis & Terpasang):")
    print("     Ajak teman menginstall Tailscale, lalu mereka cukup buka IP Tailscale Anda di atas.")
    print("  B. Gunakan Cloudflare Tunnel (Tanpa Install di Teman):")
    print(f"     Jalankan di terminal: cloudflared tunnel --url http://localhost:{port}")
    print("     Cloudflare akan memberikan URL publik HTTPS yang bisa dibuka siapa saja.")
    print("  C. Gunakan Ngrok / Localtunnel:")
    print(f"     npx localtunnel --port {port}")
    print("=" * 76)
    print("Tekan [Ctrl + C] di terminal ini kapan saja untuk menghentikan server.\n")

    # Buka browser otomatis jika dipanggil langsung
    if "--no-open" not in sys.argv:
        try:
            webbrowser.open(f"http://localhost:{port}/monitoring.html")
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Menghentikan server lokal... Sampai jumpa!")
        httpd.server_close()

if __name__ == "__main__":
    jalankan_server()
