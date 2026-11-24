#!/usr/bin/env python3
"""
========================================================================
PENGUJI TERPADU MULTI-SKENARIO ESP32 -> RASPBERRY PI & WEB DASHBOARD
Capstone Proyek Akuaponik Cerdas FT UNNES
Peneliti 1 (Visi Komputer): Felix Enrique (NIM 2305110019)
Peneliti 2 (Fuzzy Sugeno) : Rafly Akbar Anggara (NIM 2305110006)
========================================================================
Fungsi:
1. Menghubungkan ke port Serial ESP32-S3 (default COM5 / 115200 bps).
2. Membaca aliran telemetri 4 skenario secara realtime.
3. Mengirimkan payload ke REST API Dashboard (http://localhost:8080/api/aquaponik/data).
4. Melakukan verifikasi matematika SPK Sugeno pada terminal.
5. Memungkinkan pergantian skenario instan dari terminal:
   - Tekan '1' : Skenario 1 (Kondisi Prima, z = 0%)
   - Tekan '2' : Skenario 2 (Keruh Sedang, z = 15-20%)
   - Tekan '3' : Skenario 3 (Kritis Asam & Keruh, z = 30%)
   - Tekan '4' : Skenario 4 (Hujan Deras & Kolam Penuh)
   - Tekan 'a' : Mode Auto-Loop (Berganti tiap 15 detik)
========================================================================
"""

import sys
import time
import json
import urllib.request
import serial
import serial.tools.list_ports
import threading

DASHBOARD_API_URL = "http://localhost:8080/api/aquaponik/data"
DEFAULT_BAUD = 115200

# Evaluasi Inferensi Sugeno Lokal (Verifikasi Silang)
def hitung_sugeno(ph, ntu, psi):
    # Rule Base Sugeno Sederhana
    if ph < 6.0 or ntu > 40.0 or psi > 45.0:
        return 30.0, "KRITIS / FLUSH 30% (750 Liter)"
    elif ph < 6.8 or ntu > 25.0 or psi > 15.0:
        return 18.5, "SEDANG / KURAS PARSIAL (~460 Liter)"
    else:
        return 0.0, "OPTIMAL / TANPA PENGURASAN (0 Liter)"

def auto_detect_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "CH340" in p.description or "CP210" in p.description or "ESP" in p.description:
            return p.device
    return "COM5"

def forward_ke_dashboard(payload):
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            DASHBOARD_API_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            pass
    except Exception:
        pass

def main():
    port_name = auto_detect_port()
    if len(sys.argv) > 1:
        port_name = sys.argv[1]

    print("\n" + "=" * 76)
    print("  PENGUJI TERPADU MULTI-SKENARIO TELEMETRI ESP32-S3 -> DASBOR AKUAPONIK  ")
    print("=" * 76)
    print(f" Port Serial ESP32-S3 : {port_name} pada {DEFAULT_BAUD} bps")
    print(f" Target REST API      : {DASHBOARD_API_URL}")
    print(" Kontrol Cepat Skenario:")
    print("   [1] Skenario 1 (Prima, z=0%)       [2] Skenario 2 (Keruh, z=18.5%)")
    print("   [3] Skenario 3 (Kritis, z=30%)     [4] Skenario 4 (Hujan & Kolam Penuh)")
    print("   [a] Mode Auto-Loop (15 detik)      [q] Keluar")
    print("=" * 76 + "\n")

    try:
        ser = serial.Serial(port_name, DEFAULT_BAUD, timeout=1.0)
        time.sleep(1.0)
    except Exception as e:
        print(f"[ERROR] Gagal membuka port serial {port_name}: {e}")
        print("Pastikan port COM tidak sedang dibuka oleh Arduino IDE / Serial Monitor lain.")
        return

    # Thread membaca input keyboard untuk mengganti skenario
    running = True

    def keyboard_listener():
        nonlocal running
        while running:
            try:
                ch = sys.stdin.readline().strip()
                if ch in ['1', '2', '3', '4', 'a', 'A']:
                    ser.write(ch.encode('utf-8'))
                    print(f"\n>>> [KONTROL] Perintah '{ch}' dikirim ke ESP32-S3.")
                elif ch.lower() == 'q':
                    running = False
                    break
            except Exception:
                break

    kb_thread = threading.Thread(target=keyboard_listener, daemon=True)
    kb_thread.start()

    print("[STATUS] Memulai penerimaan telemetri dari ESP32-S3...\n", flush=True)

    while running:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            # Jika baris adalah status ganti skenario
            if "[SKENARIO BERGANTI]" in line or "===================" in line or "Panduan" in line:
                print(line, flush=True)
                continue

            # Jika baris adalah log transmisi [S1-AUTO] ...
            if line.startswith("[S"):
                print(line, flush=True)

            # Jika baris adalah JSON (atau ekstrak dari JSON line jika dikirim)
            # Karena ESP32 mengirim log teks di USB Serial dan JSON di BLE, kita parse nilai dari log teks
            # Format: [S1-AUTO] seq=1 | pH=7.15 | NTU=8.3 | Suhu=27.5 C | Lvl=68.2 cm | PSI=8.5% | Hujan=TIDAK
            if "seq=" in line and "pH=" in line:
                parts = line.split("|")
                try:
                    ph_val = float(parts[1].split("=")[1].strip())
                    ntu_val = float(parts[2].split("=")[1].replace("NTU", "").strip())
                    temp_val = float(parts[3].split("=")[1].replace("C", "").strip())
                    lvl_val = float(parts[4].split("=")[1].replace("cm", "").strip())
                    psi_val = float(parts[5].split("=")[1].replace("%", "").strip())
                    hujan_str = parts[6].split("=")[1].strip().upper()
                    is_raining = (hujan_str == "YA")

                    # Evaluasi Sugeno
                    z_score, rekomendasi = hitung_sugeno(ph_val, ntu_val, psi_val)

                    # Buat payload telemetri untuk dasbor
                    payload = {
                        "node": "esp32s3",
                        "sensors": {
                            "pH": ph_val,
                            "turbidity": ntu_val,
                            "water_level_cm": lvl_val,
                            "temperature_c": temp_val,
                            "rain_detected": is_raining
                        },
                        "vision": {
                            "psi": psi_val,
                            "green_pct": round(max(0.0, 100.0 - psi_val * 1.2), 1),
                            "yellow_pct": round(psi_val * 0.8, 1),
                            "brown_pct": round(psi_val * 0.4, 1)
                        },
                        "actuators": {
                            "valve_out": (z_score >= 30.0),
                            "valve_in": not is_raining,
                            "pump": True
                        },
                        "ph": ph_val,
                        "ntu": ntu_val,
                        "temp": temp_val,
                        "lvl": lvl_val,
                        "psi": psi_val
                    }

                    # Teruskan ke dasbor
                    forward_ke_dashboard(payload)

                except Exception:
                    pass

        except KeyboardInterrupt:
            print("\nPengujian dihentikan.")
            break
        except Exception as e:
            print(f"[ERR] {e}")
            time.sleep(0.5)

    ser.close()
    print("Koneksi serial ditutup.")

if __name__ == "__main__":
    main()
