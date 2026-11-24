#!/usr/bin/env python3
"""
========================================================================
EMULATOR DUMMY TELEMETRI ESP32 - CAPSTONE AKUAPONIK UNNES
Dibuat untuk Pengujian Cepat Tanpa Hardware Fisik
========================================================================
Fungsi:
1. Mengalirkan data sensor air dummy (pH, Kekeruhan, Suhu, Ketinggian)
   secara kontinu setiap 1 detik.
2. Otomatis mengirim data ke Endpoint REST API Dashboard:
   http://localhost:8080/api/aquaponik/data
3. Mendukung transmisi ke port Serial fisik (COM / /dev/ttyUSB0) jika diinginkan.
4. Menerima umpan balik status kanopi dari Raspberry Pi.
========================================================================
Cara Menjalankan:
  python mock_esp32.py
  (atau dengan opsi endpoint: python mock_esp32.py --url http://10.11.2.18:8080)
========================================================================
"""

import sys
import time
import math
import random
import json
import argparse
import urllib.request

DEFAULT_API_URL = "http://localhost:8080/api/aquaponik/data"

def main():
    parser = argparse.ArgumentParser(description="Emulator Dummy Telemetri ESP32")
    parser.add_argument("--url", default=DEFAULT_API_URL, help="URL endpoint API dashboard")
    parser.add_argument("--interval", type=float, default=1.0, help="Interval pengiriman (detik)")
    parser.add_argument("--count", type=int, default=0, help="Jumlah siklus pengiriman (0 = tanpa batas)")
    parser.add_argument("--serial-port", default=None, help="Port Serial opsional (misal COM3 atau /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate serial")
    args = parser.parse_args()

    ser = None
    if args.serial_port:
        try:
            import serial
            ser = serial.Serial(args.serial_port, args.baud, timeout=0.1)
            print(f"[SERIAL] Terhubung ke port fisik {args.serial_port} pada {args.baud} bps")
        except Exception as e:
            print(f"[WARN] Gagal membuka port serial {args.serial_port}: {e}")
            ser = None

    print("\n" + "=" * 70)
    print(" EMULATOR DUMMY TELEMETRI ESP32 AKTIF (SIMULASI AIR KOLAM)")
    print("=" * 70)
    print(f" Target Endpoint REST : {args.url}")
    print(f" Interval Pengiriman  : {args.interval} detik")
    print(f" Tekan Ctrl+C untuk menghentikan.")
    print("=" * 70 + "\n")

    seq = 0
    phase = 0.0
    valve_status = 0
    pump_status = 1

    while True:
        try:
            seq += 1
            phase += 0.08

            # Simulasi osilasi alami mutu air
            ph = round(7.02 + 0.18 * math.sin(phase) + (random.randint(-15, 15) / 1000.0), 2)
            ntu = round(max(3.0, 9.5 + 3.2 * math.sin(phase * 0.7) + (random.randint(-20, 20) / 100.0)), 1)
            temp = round(27.35 + 0.45 * math.cos(phase * 0.4), 1)
            level = round(68.2 + 0.6 * math.sin(phase * 1.2), 1)

            payload = {
                "node": "esp32",
                "seq": seq,
                "sensors": {
                    "pH": ph,
                    "turbidity": ntu,
                    "water_level_cm": level,
                    "temperature_c": temp,
                    "rain_detected": False
                },
                "actuators": {
                    "valve_out": bool(valve_status),
                    "pump": bool(pump_status)
                },
                "ph": ph,
                "ntu": ntu,
                "temp": temp,
                "lvl": level,
                "valve": valve_status
            }

            json_bytes = json.dumps(payload).encode("utf-8")

            # 1. Kirim via Serial jika aktif
            if ser:
                ser.write(json_bytes + b"\n")

            # 2. Kirim via HTTP REST POST ke Dashboard
            feedback = None
            try:
                req = urllib.request.Request(
                    args.url,
                    data=json_bytes,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    if resp.status == 200:
                        res_data = json.loads(resp.read().decode("utf-8"))
                        feedback = res_data.get("vision")
            except Exception:
                pass

            # Log status ke terminal
            fb_str = f" | Balasan Pi: PSI={feedback.get('psi', '–')}%" if feedback else ""
            print(f"[ESP32 -> DASHBOARD] seq={seq:04d} | pH={ph:.2f} | Kekeruhan={ntu:.1f} NTU | Suhu={temp:.1f} C | Level={level:.1f} cm{fb_str}")

            if args.count > 0 and seq >= args.count:
                print(f"\nSelesai mengirim {seq} siklus data dummy.")
                break

            time.sleep(args.interval)

        except KeyboardInterrupt:
            print("\nEmulator dummy dihentikan oleh pengguna.")
            break
        except Exception as e:
            print(f"[ERR] {e}")
            time.sleep(1.0)

if __name__ == "__main__":
    main()
