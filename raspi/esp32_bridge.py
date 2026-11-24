#!/usr/bin/env python3
"""Jembatan dua arah ESP32 <-> Raspberry Pi 4B <-> Web Server Akuaponik.

Protokol utama: USB Serial (/dev/ttyUSB* / /dev/ttyACM* / COM*) 115200 bps
Protokol cadangan opsional: UDP socket (port 5005)
Format pertukaran: Line-Delimited JSON (satu baris JSON diakhiri ``\\n``).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import queue
import signal
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

DEFAULT_API_BASE = "http://127.0.0.1:8080"
DEFAULT_BAUD = 115200
DEFAULT_UDP_PORT = 5005
DEFAULT_OUTBOX_MAX_AGE_SEC = 900.0
BLE_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
BLE_CHAR_RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
BLE_CHAR_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
BLE_NAME_KEYWORDS = ("ESP32_AKUAPONIK", "ESP32S3_AKUAPONIK", "AKUAPONIK_UNNES")


def _import_serial():
    try:
        import serial  # type: ignore
        import serial.tools.list_ports  # type: ignore
        return serial
    except ImportError:
        return None


def list_candidate_serial_ports() -> list[str]:
    """Mengurutkan kandidat port USB-Serial ESP32 berdasarkan prioritas perangkat."""
    serial_mod = _import_serial()
    if serial_mod is None:
        return []

    scored: list[tuple[int, str]] = []
    for p in serial_mod.tools.list_ports.comports():
        dev = p.device or ""
        desc = f"{p.description or ''} {p.manufacturer or ''} {p.hwid or ''}".upper()
        # Abaikan Bluetooth SPP & konsol serial internal non-USB
        if "BLUETOOTH" in desc or dev.startswith("/dev/ttyAMA") or dev.startswith("/dev/ttyS"):
            continue

        score = 0
        if "TTYUSB" in dev.upper() or "TTYACM" in dev.upper():
            score += 40
        elif dev.upper().startswith("COM"):
            score += 20

        if any(tag in desc for tag in ("CH910", "CH340", "CP210", "FTDI", "SILABS", "ESP32", "JTAG")):
            score += 50
        if "VID_1A86" in desc or "VID_10C4" in desc or "VID_303A" in desc or "VID_0403" in desc:
            score += 30

        if score > 0:
            scored.append((score, dev))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [dev for _, dev in scored]


def normalisasi_telemetri_esp32(
    raw: dict[str, Any],
    transport: str = "usb_serial",
    port: str = "",
) -> dict[str, Any]:
    """Mengonversi paket JSON ringkas ESP32 menjadi payload standar REST dashboard."""
    sensors: dict[str, Any] = {}
    if raw.get("ph") is not None:
        sensors["pH"] = float(raw["ph"])
    if raw.get("ntu") is not None:
        sensors["turbidity"] = float(raw["ntu"])

    temp_val = raw.get("temp")
    if temp_val is not None and float(temp_val) > -55.0:
        sensors["temperature_c"] = float(temp_val)
        sensors["temp_ok"] = bool(raw.get("temp_ok", 1))
    else:
        sensors["temp_ok"] = False

    lvl_val = raw.get("lvl")
    if lvl_val is not None and float(lvl_val) >= 0.0:
        sensors["water_level_cm"] = float(lvl_val)
        sensors["lvl_ok"] = bool(raw.get("lvl_ok", 1))
    else:
        sensors["lvl_ok"] = False

    if "rain" in raw or "rain_detected" in raw:
        sensors["rain_detected"] = bool(raw.get("rain_detected", raw.get("rain", 0)))

    actuators = {
        "valve_in": bool(raw.get("valve_in", 0)),
        "valve_out": bool(raw.get("valve_out", raw.get("valve", 0))),
        "pump": bool(raw.get("pump", 1)),
        "feeder": bool(raw.get("feed", raw.get("feeder", 0))),
    }

    sugeno = {}
    if raw.get("z_rec") is not None:
        sugeno["z_rec"] = float(raw["z_rec"])
    if raw.get("vol_rec") is not None:
        sugeno["vol_rec"] = float(raw["vol_rec"])
    if raw.get("rules") is not None:
        sugeno["rules"] = int(raw["rules"])

    return {
        "node": str(raw.get("node") or "esp32"),
        "seq": int(raw.get("seq") or 0),
        "sensors": sensors,
        "actuators": actuators,
        "sugeno": sugeno,
        "esp32_link": {
            "connected": True,
            "transport": transport,
            "port": port,
            "seq": int(raw.get("seq") or 0),
            "pi_online": bool(raw.get("pi_online", 0)),
            "stale_guard": bool(raw.get("stale_guard", 0)),
        },
    }


def bangun_paket_pi(
    vision: dict[str, Any] | None,
    command: dict[str, Any] | None,
    seq: int,
) -> bytes:
    """Membentuk baris JSON Pi -> ESP32 untuk dikirim via UART/UDP."""
    vis = vision or {}
    cmd = command or {}
    psi = float(vis.get("psi", 15.0) or 15.0)
    cov = float(vis.get("coverage", vis.get("green_pct", 0.0)) or 0.0)
    z_rec = float(cmd.get("z_rec", 0.0) or 0.0)
    cmd_drain = 1 if int(cmd.get("cmd_drain", 0) or 0) == 1 else 0
    cmd_in = 1 if int(cmd.get("cmd_in", 0) or 0) == 1 else 0
    acc = 1 if int(cmd.get("acc", 0) or 0) == 1 else 0
    dur_sec = int(cmd.get("dur_sec", 0) or 0)
    cmd_id = int(cmd.get("cmd_id", 0) or 0)
    emergency = 1 if int(cmd.get("emergency", 0) or 0) == 1 else 0

    frame = {
        "node": "pi4",
        "psi": round(max(0.0, min(100.0, psi)), 2),
        "cov": round(max(0.0, min(100.0, cov)), 2),
        "z_rec": round(max(0.0, min(100.0, z_rec)), 2),
        "cmd_drain": cmd_drain,
        "cmd_in": cmd_in,
        "dur_sec": max(0, min(180, dur_sec)),
        "acc": acc,
        "cmd_id": cmd_id,
        "emergency": emergency,
        "seq": int(seq),
    }
    return (json.dumps(frame, separators=(",", ":")) + "\n").encode("utf-8")


def _http_json(
    url: str,
    payload: Optional[dict[str, Any]] = None,
    timeout: float = 1.5,
) -> Optional[dict[str, Any]]:
    data = None
    headers = {}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if 200 <= resp.status < 300:
                return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    return None


def baca_visi_outbox_terbaru(outbox_dir: Path, max_age_sec: float = DEFAULT_OUTBOX_MAX_AGE_SEC) -> Optional[dict[str, Any]]:
    """Membaca file outbox CV terbaru (< 15 menit) bila kangkung_pi menghasilkan data segar."""
    if not outbox_dir.is_dir():
        return None
    now = time.time()
    newest: Optional[Path] = None
    newest_mtime = 0.0
    for jf in outbox_dir.glob("*.json"):
        try:
            st = jf.stat()
            if st.st_mtime > newest_mtime:
                newest_mtime = st.st_mtime
                newest = jf
        except OSError:
            continue
    if newest is None or (now - newest_mtime) > max_age_sec:
        return None
    try:
        doc = json.loads(newest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    fuzzy = doc.get("fuzzy_input") or {}
    psi = fuzzy.get("psi")
    if psi is None:
        return None
    kes = doc.get("kesehatan") or {}
    cov = float(doc.get("coverage_rata") or 0.0)
    kun = float(fuzzy.get("kuning_pct", kes.get("kuning_rata", 0.0)) or 0.0)
    cok = float(fuzzy.get("coklat_pct", kes.get("coklat_rata", 0.0)) or 0.0)
    green = round(max(0.0, 100.0 - kun - cok), 2)
    return {
        "psi": round(float(psi), 2),
        "coverage": round(cov, 2),
        "green_pct": green,
        "yellow_pct": round(kun, 2),
        "brown_pct": round(cok, 2),
        "source": f"outbox:{newest.name}",
    }


class Esp32Bridge:
    """Mengelola koneksi USB Serial, BLE GATT dua arah, serta UDP opsional ke ESP32."""

    def __init__(
        self,
        api_base: str = DEFAULT_API_BASE,
        port: str = "auto",
        baud: int = DEFAULT_BAUD,
        enable_ble: bool = False,
        ble_name: Optional[str] = None,
        enable_udp: bool = False,
        udp_port: int = DEFAULT_UDP_PORT,
        esp_ip: Optional[str] = None,
        heartbeat_sec: float = 1.0,
        outbox_dir: Optional[Path] = None,
        verbose: bool = True,
    ) -> None:
        self.api_data_url = api_base.rstrip("/") + "/api/aquaponik/data"
        self.api_cmd_url = api_base.rstrip("/") + "/api/aquaponik/command"
        self.api_vision_url = api_base.rstrip("/") + "/api/aquaponik/vision"
        self.requested_port = port
        self.baud = baud
        self.enable_ble = enable_ble
        self.ble_name = ble_name
        self.enable_udp = enable_udp
        self.udp_port = udp_port
        self.esp_ip = esp_ip
        self.heartbeat_sec = max(0.3, heartbeat_sec)
        self.outbox_dir = outbox_dir
        self.verbose = verbose

        self.running = False
        self._ser = None
        self._active_port = ""
        self._rx_buf = ""
        self._udp_sock: Optional[socket.socket] = None
        self._last_udp_peer: Optional[tuple[str, int]] = (esp_ip, udp_port) if esp_ip else None

        self._ble_thread: Optional[threading.Thread] = None
        self._ble_connected = False
        self._ble_peer = ""
        self._ble_tx_queue: queue.Queue[bytes] = queue.Queue(maxsize=16)

        self._tx_seq = 0
        self._last_hb_ts = 0.0
        self._last_cmd_poll_ts = 0.0
        self._last_outbox_sync_ts = 0.0
        self._last_sent_cmd_id = -1
        self._cached_vision: dict[str, Any] = {"psi": 15.0, "coverage": 82.4}
        self._cached_command: dict[str, Any] = {"cmd_id": 0, "cmd_drain": 0, "acc": 0, "dur_sec": 0}

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg, flush=True)

    def _open_serial(self) -> bool:
        serial_mod = _import_serial()
        if serial_mod is None:
            return False

        candidates = list_candidate_serial_ports() if self.requested_port == "auto" else [self.requested_port]
        for cand in candidates:
            try:
                ser = serial_mod.Serial()
                ser.port = cand
                ser.baudrate = self.baud
                ser.timeout = 0.08
                ser.dtr = False
                ser.rts = False
                ser.open()
                self._ser = ser
                self._active_port = cand
                self._log(f"[SERIAL] Terhubung ke {cand} @ {self.baud} bps")
                return True
            except Exception:
                continue
        return False

    def _close_serial(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
            self._active_port = ""

    def _setup_udp(self) -> None:
        if not self.enable_udp or self._udp_sock is not None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", self.udp_port))
        sock.setblocking(False)
        self._udp_sock = sock
        self._log(f"[UDP] Cadangan aktif mendengarkan port {self.udp_port}")

    def _send_packet_to_esp32(self, frame_bytes: bytes) -> bool:
        sent = False
        if self._ser is not None:
            try:
                self._ser.write(frame_bytes)
                self._ser.flush()
                sent = True
            except Exception as e:
                self._log(f"[WARN] Gagal menulis Serial ({e}), menutup port untuk reconnect.")
                self._rx_buf = ""
                self._close_serial()

        if not sent and self._ble_connected:
            try:
                if self._ble_tx_queue.full():
                    try:
                        self._ble_tx_queue.get_nowait()
                    except queue.Empty:
                        pass
                self._ble_tx_queue.put_nowait(frame_bytes)
                sent = True
            except queue.Full:
                pass

        if not sent and self._udp_sock is not None and self._last_udp_peer is not None:
            try:
                self._udp_sock.sendto(frame_bytes, self._last_udp_peer)
                sent = True
            except OSError:
                pass
        return sent

    def _matches_ble_device(self, device, adv_data) -> bool:
        uuids = [u.lower() for u in (getattr(adv_data, "service_uuids", None) or [])]
        if BLE_SERVICE_UUID.lower() in uuids:
            return True
        name = (getattr(device, "name", None) or getattr(adv_data, "local_name", None) or "").upper()
        if self.ble_name:
            return self.ble_name.upper() in name
        return any(tag in name for tag in BLE_NAME_KEYWORDS)

    async def _ble_session_loop(self) -> None:
        try:
            from bleak import BleakClient, BleakScanner  # type: ignore
        except ImportError:
            self._log("[WARN] Pustaka bleak tidak tersedia; mode BLE dinonaktifkan.")
            return

        scan_logged = False
        while self.running:
            if self._ser is not None:
                await asyncio.sleep(0.5)
                continue

            if not scan_logged:
                self._log("[BLE] Memindai ESP32 GATT Nordic UART...")
                scan_logged = True

            device = None
            try:
                device = await BleakScanner.find_device_by_filter(self._matches_ble_device, timeout=5.0)
            except Exception as e:
                self._log(f"[BLE] Gagal memindai ({e}); ulangi 3 detik...")
                await asyncio.sleep(3.0)
                continue

            if device is None:
                await asyncio.sleep(1.5)
                continue

            disc_ev = asyncio.Event()
            ble_rx_buf = ""
            peer_label = f"{device.name or 'ESP32'} [{device.address}]"

            def _on_disc(_client):
                disc_ev.set()

            def _on_notify(_sender, data: bytearray):
                nonlocal ble_rx_buf
                ble_rx_buf += data.decode("utf-8", errors="ignore")
                while "\n" in ble_rx_buf:
                    line, ble_rx_buf = ble_rx_buf.split("\n", 1)
                    self._handle_incoming_line(line, "ble_gatt", device.address)

            try:
                async with BleakClient(device, timeout=12.0, disconnected_callback=_on_disc) as client:
                    self._ble_connected = True
                    self._ble_peer = device.address
                    self._last_hb_ts = 0.0
                    use_write_resp = False
                    self._log(f"[BLE] Terhubung dua arah ke {peer_label} (MTU={getattr(client, 'mtu_size', 23)})")

                    await client.start_notify(BLE_CHAR_TX_UUID, _on_notify)
                    while self.running and not disc_ev.is_set() and self._ser is None:
                        try:
                            frame = self._ble_tx_queue.get_nowait()
                        except queue.Empty:
                            await asyncio.sleep(0.04)
                            continue

                        mtu_now = int(getattr(client, "mtu_size", 23) or 23)
                        chunk_sz = max(20, min(mtu_now - 3, 180))
                        for idx in range(0, len(frame), chunk_sz):
                            chunk = frame[idx:idx + chunk_sz]
                            try:
                                await client.write_gatt_char(BLE_CHAR_RX_UUID, chunk, response=use_write_resp)
                            except Exception:
                                if not use_write_resp:
                                    use_write_resp = True
                                    await client.write_gatt_char(BLE_CHAR_RX_UUID, chunk, response=True)
                                else:
                                    raise
                            if idx + chunk_sz < len(frame):
                                await asyncio.sleep(0.01)
            except Exception as e:
                self._log(f"[BLE] Koneksi {peer_label} terputus ({e}); scan ulang...")
            finally:
                self._ble_connected = False
                self._ble_peer = ""
                scan_logged = False
                while not self._ble_tx_queue.empty():
                    try:
                        self._ble_tx_queue.get_nowait()
                    except queue.Empty:
                        break
            await asyncio.sleep(1.5)

    def _start_ble_thread(self) -> None:
        if not self.enable_ble or self._ble_thread is not None:
            return
        self._ble_thread = threading.Thread(
            target=lambda: asyncio.run(self._ble_session_loop()),
            name="esp32-ble-worker",
            daemon=True,
        )
        self._ble_thread.start()

    def _handle_incoming_line(self, raw_line: str, transport: str, port_label: str) -> None:
        line = raw_line.strip()
        if not line:
            return
        if not (line.startswith("{") and line.endswith("}")):
            return
        try:
            doc = json.loads(line)
        except json.JSONDecodeError:
            return
        if not isinstance(doc, dict):
            return

        payload = normalisasi_telemetri_esp32(doc, transport=transport, port=port_label)
        resp = _http_json(self.api_data_url, payload=payload, timeout=1.0)
        if resp:
            if isinstance(resp.get("vision"), dict):
                self._cached_vision = resp["vision"]
            if isinstance(resp.get("command"), dict):
                self._cached_command = resp["command"]

    def _maybe_sync_outbox(self, now: float) -> None:
        if self.outbox_dir is None or (now - self._last_outbox_sync_ts) < 5.0:
            return
        self._last_outbox_sync_ts = now
        fresh = baca_visi_outbox_terbaru(self.outbox_dir)
        if fresh:
            resp = _http_json(self.api_vision_url, payload=fresh, timeout=1.0)
            if resp and isinstance(resp.get("vision"), dict):
                self._cached_vision = resp["vision"]

    def _maybe_poll_command_and_heartbeat(self, now: float) -> None:
        if (now - self._last_cmd_poll_ts) >= 0.25:
            self._last_cmd_poll_ts = now
            state = _http_json(self.api_cmd_url, timeout=0.8)
            if state:
                if isinstance(state.get("vision"), dict):
                    self._cached_vision = state["vision"]
                if isinstance(state.get("command"), dict):
                    self._cached_command = state["command"]

        cmd_id = int(self._cached_command.get("cmd_id", 0) or 0)
        new_command = (cmd_id > 0) and (cmd_id != self._last_sent_cmd_id)
        hb_due = (now - self._last_hb_ts) >= self.heartbeat_sec

        if new_command or hb_due:
            self._tx_seq += 1
            pkt = bangun_paket_pi(self._cached_vision, self._cached_command, self._tx_seq)
            if self._send_packet_to_esp32(pkt):
                self._last_hb_ts = now
                if new_command:
                    self._last_sent_cmd_id = cmd_id
                    self._log(
                        f"[TX->ESP32] cmd_id={cmd_id} cmd_drain={self._cached_command.get('cmd_drain')} "
                        f"acc={self._cached_command.get('acc')} dur={self._cached_command.get('dur_sec')}s"
                    )

    def run(self, max_seconds: float = 0.0) -> None:
        self.running = True
        self._setup_udp()
        self._start_ble_thread()
        start_ts = time.monotonic()
        last_retry_ts = 0.0

        self._log(f"[BRIDGE] Memulai ESP32 Bridge -> API {self.api_data_url}")
        try:
            while self.running:
                now = time.monotonic()
                if max_seconds > 0.0 and (now - start_ts) >= max_seconds:
                    break

                if self._ser is None and self.requested_port.upper() != "NONE" and (now - last_retry_ts) >= 2.0:
                    last_retry_ts = now
                    if not self._open_serial() and self.verbose and self._tx_seq == 0 and not self.enable_ble:
                        self._log("[SERIAL] Menunggu perangkat ESP32 tercolok (USB Serial)...")

                if self._ser is not None:
                    try:
                        waiting = self._ser.in_waiting
                        if waiting > 0:
                            chunk = self._ser.read(waiting).decode("utf-8", errors="ignore")
                            self._rx_buf += chunk
                            while "\n" in self._rx_buf:
                                line, self._rx_buf = self._rx_buf.split("\n", 1)
                                self._handle_incoming_line(line, "usb_serial", self._active_port)
                    except Exception as e:
                        self._log(f"[WARN] Koneksi Serial terputus ({e}), mencoba ulang...")
                        self._rx_buf = ""
                        self._close_serial()

                if self._udp_sock is not None:
                    try:
                        while True:
                            data, addr = self._udp_sock.recvfrom(2048)
                            self._last_udp_peer = addr
                            for line in data.decode("utf-8", errors="ignore").splitlines():
                                self._handle_incoming_line(line, "udp_wifi", f"{addr[0]}:{addr[1]}")
                    except BlockingIOError:
                        pass
                    except OSError:
                        pass

                self._maybe_sync_outbox(now)
                self._maybe_poll_command_and_heartbeat(now)
                time.sleep(0.05)
        finally:
            self.stop()

    def stop(self) -> None:
        self.running = False
        self._close_serial()
        if self._udp_sock is not None:
            try:
                self._udp_sock.close()
            except OSError:
                pass
            self._udp_sock = None


def main() -> int:
    ap = argparse.ArgumentParser(description="Jembatan ESP32 <-> Raspberry Pi <-> Web Aquaponik")
    ap.add_argument("--port", default="auto", help="Port Serial ESP32 (auto, /dev/ttyUSB0, COM6, NONE)")
    ap.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="Baud rate Serial (default 115200)")
    ap.add_argument("--api-url", default=DEFAULT_API_BASE, help="Base URL Web Server Lokal")
    ap.add_argument("--ble", action="store_true", help="Aktifkan transport nirkabel BLE GATT dua arah")
    ap.add_argument("--ble-name", default=None, help="Filter nama perangkat BLE opsional")
    ap.add_argument("--udp", action="store_true", help="Aktifkan cadangan Wi-Fi UDP")
    ap.add_argument("--udp-port", type=int, default=DEFAULT_UDP_PORT, help="Port UDP (default 5005)")
    ap.add_argument("--esp-ip", default=None, help="IP tujuan UDP ESP32 opsional")
    ap.add_argument("--outbox-dir", default=str(Path(__file__).resolve().parent / "outbox"),
                    help="Folder outbox CV kangkung_pi")
    ap.add_argument("--quiet", action="store_true", help="Minimalkan log stdout")
    ap.add_argument("--seconds", type=float, default=0.0, help="Batas durasi jalan untuk uji coba")
    args = ap.parse_args()

    bridge = Esp32Bridge(
        api_base=args.api_url,
        port=args.port,
        baud=args.baud,
        enable_ble=args.ble,
        ble_name=args.ble_name,
        enable_udp=args.udp,
        udp_port=args.udp_port,
        esp_ip=args.esp_ip,
        outbox_dir=Path(args.outbox_dir) if args.outbox_dir else None,
        verbose=not args.quiet,
    )

    def _handle_sig(signum, frame):
        bridge.stop()

    signal.signal(signal.SIGINT, _handle_sig)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_sig)

    bridge.run(max_seconds=args.seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
