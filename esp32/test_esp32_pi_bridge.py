#!/usr/bin/env python3
"""Pengujian otomatis protokol & jembatan dua arah ESP32 <-> Raspberry Pi 4B <-> Web Server."""
from __future__ import annotations

import http.server
import json
import socket
import socketserver
import sys
import threading
import time
import unittest
import urllib.request
from pathlib import Path

ROOT_CV = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT_CV.parent / "web aquaponik" / "web aquaponik"

sys.path.insert(0, str(ROOT_CV / "raspi"))
sys.path.insert(0, str(WEB_DIR))

from esp32_bridge import (  # noqa: E402
    Esp32Bridge,
    bangun_paket_pi,
    normalisasi_telemetri_esp32,
)
import server as web_server  # noqa: E402


class TestEsp32BridgeProtocol(unittest.TestCase):
    def test_normalisasi_sensor_lengkap_dan_terputus(self):
        raw = {
            "node": "esp32",
            "ph": 0.0,
            "ntu": 14.5,
            "temp": None,
            "temp_ok": 0,
            "lvl": None,
            "lvl_ok": 0,
            "rain": 1,
            "valve": 1,
            "valve_in": 0,
            "valve_out": 1,
            "pump": 1,
            "feed": 0,
            "z_rec": 20.0,
            "vol_rec": 500.0,
            "rules": 4,
            "pi_online": 1,
            "stale_guard": 0,
            "seq": 42,
        }
        out = normalisasi_telemetri_esp32(raw, transport="usb_serial", port="/dev/ttyUSB0")
        self.assertEqual(out["sensors"]["pH"], 0.0)
        self.assertEqual(out["sensors"]["turbidity"], 14.5)
        self.assertNotIn("temperature_c", out["sensors"])
        self.assertFalse(out["sensors"]["temp_ok"])
        self.assertNotIn("water_level_cm", out["sensors"])
        self.assertFalse(out["sensors"]["lvl_ok"])
        self.assertTrue(out["sensors"]["rain_detected"])
        self.assertTrue(out["actuators"]["valve_out"])
        self.assertFalse(out["actuators"]["valve_in"])
        self.assertEqual(out["sugeno"]["z_rec"], 20.0)
        self.assertEqual(out["esp32_link"]["seq"], 42)

    def test_bangun_paket_pi_clamp(self):
        pkt = bangun_paket_pi(
            {"psi": 125.0, "coverage": 84.5},
            {"cmd_id": 7, "cmd_drain": 1, "cmd_in": 0, "acc": 1, "dur_sec": 999, "z_rec": 30.0},
            seq=104,
        )
        text = pkt.decode("utf-8")
        self.assertTrue(text.endswith("\n"))
        obj = json.loads(text)
        self.assertEqual(obj["node"], "pi4")
        self.assertEqual(obj["psi"], 100.0)
        self.assertEqual(obj["cov"], 84.5)
        self.assertEqual(obj["cmd_drain"], 1)
        self.assertEqual(obj["cmd_in"], 0)
        self.assertEqual(obj["acc"], 1)
        self.assertEqual(obj["dur_sec"], 180)
        self.assertEqual(obj["cmd_id"], 7)
        self.assertEqual(obj["seq"], 104)

    def test_bangun_paket_pi_valve_in(self):
        pkt = bangun_paket_pi(
            {"psi": 12.0, "coverage": 80.0},
            {"cmd_id": 8, "cmd_drain": 0, "cmd_in": 1, "acc": 1, "dur_sec": 120},
            seq=105,
        )
        obj = json.loads(pkt.decode("utf-8"))
        self.assertEqual(obj["cmd_drain"], 0)
        self.assertEqual(obj["cmd_in"], 1)
        self.assertEqual(obj["acc"], 1)
        self.assertEqual(obj["dur_sec"], 120)


class TestEndToEndBridgeAndServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class ThreadedHTTP(socketserver.ThreadingMixIn, http.server.HTTPServer):
            daemon_threads = True

        handler = lambda *a, **kw: web_server.AquaponikRequestHandler(
            *a, directory=str(WEB_DIR), **kw
        )
        cls.httpd = ThreadedHTTP(("127.0.0.1", 0), handler)
        cls.port = cls.httpd.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _req(self, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method="POST" if body is not None else "GET",
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_two_step_lock_and_udp_roundtrip(self):
        # 1. Kunci 2-tahap: cmd_drain=1 atau cmd_in=1 tanpa acc=1 harus ditolak, serta larang keduanya aktif bersamaan
        rej = self._req("/api/aquaponik/command", {"cmd_drain": 1, "acc": 0, "volume_l": 300})
        self.assertEqual(rej["command"]["cmd_drain"], 0)
        rej_in = self._req("/api/aquaponik/command", {"cmd_in": 1, "acc": 0})
        self.assertEqual(rej_in["command"]["cmd_in"], 0)
        rej_both = self._req("/api/aquaponik/command", {"cmd_drain": 1, "cmd_in": 1, "acc": 1})
        self.assertEqual(rej_both["command"]["cmd_drain"], 0)
        self.assertEqual(rej_both["command"]["cmd_in"], 0)
        ok_in = self._req("/api/aquaponik/command", {"cmd_in": 1, "cmd_drain": 0, "acc": 1, "dur_sec": 45})
        self.assertEqual(ok_in["command"]["cmd_in"], 1)
        self.assertEqual(ok_in["command"]["cmd_drain"], 0)
        self.assertEqual(ok_in["command"]["dur_sec"], 45)

        # 2. Cari port UDP bebas dan jalankan bridge + mock ESP32 via UDP
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.bind(("127.0.0.1", 0))
        udp_port = probe.getsockname()[1]
        probe.close()

        bridge = Esp32Bridge(
            api_base=self.base_url,
            port="NONE",
            enable_udp=True,
            udp_port=udp_port,
            heartbeat_sec=0.35,
            outbox_dir=None,
            verbose=False,
        )
        t_bridge = threading.Thread(target=bridge.run, kwargs={"max_seconds": 3.0}, daemon=True)
        t_bridge.start()
        time.sleep(0.25)

        mock_esp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        mock_esp.settimeout(2.0)
        rx_cmds = []
        try:
            # Update CV vision di server
            self._req("/api/aquaponik/vision", {"psi": 42.5, "coverage": 79.0, "source": "test_cv"})

            # Mock ESP32 kirim telemetri -> bridge -> server
            esp_pkt = json.dumps({
                "node": "esp32", "ph": 6.42, "ntu": 28.4, "temp": 27.6, "temp_ok": 1,
                "lvl": 67.5, "lvl_ok": 1, "rain": 0, "valve": 0, "valve_in": 0, "valve_out": 0,
                "pump": 1, "feed": 0, "z_rec": 20.0, "vol_rec": 500.0, "rules": 6, "seq": 101
            }).encode("utf-8") + b"\n"
            mock_esp.sendto(esp_pkt, ("127.0.0.1", udp_port))

            # Tunggu hingga server mencatat telemetri ESP32
            snap = None
            for _ in range(20):
                snap = self._req("/api/aquaponik/data")
                if snap["esp32_link"]["seq"] == 101:
                    break
                time.sleep(0.08)
            self.assertIsNotNone(snap)
            self.assertTrue(snap["esp32_link"]["connected"])
            self.assertAlmostEqual(snap["sensors"]["pH"], 6.42, places=2)
            self.assertAlmostEqual(snap["vision"]["psi"], 42.5, places=1)

            # Dashboard kirim konfirmasi kuras (2-step: cmd_drain=1, acc=1)
            self._req("/api/aquaponik/data", {
                "cmd_drain": 1, "acc": 1, "volume_l": 500, "z_rec": 20.0, "dur_sec": 60
            })

            # Mock ESP32 menerima paket perintah JSON dari bridge
            deadline = time.time() + 2.0
            while time.time() < deadline:
                try:
                    data, _ = mock_esp.recvfrom(2048)
                    msg = json.loads(data.decode("utf-8").strip())
                    rx_cmds.append(msg)
                    if msg.get("cmd_drain") == 1 and msg.get("acc") == 1:
                        break
                except socket.timeout:
                    break

            matching = [m for m in rx_cmds if m.get("cmd_drain") == 1 and m.get("acc") == 1]
            self.assertTrue(matching, f"Perintah drain terkonfirmasi tidak diterima mock ESP32: {rx_cmds}")
            self.assertEqual(matching[0]["dur_sec"], 60)
            self.assertAlmostEqual(matching[0]["psi"], 42.5, places=1)
        finally:
            mock_esp.close()
            bridge.stop()
            t_bridge.join(timeout=2.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
