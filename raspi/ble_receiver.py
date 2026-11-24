#!/usr/bin/env python3
"""
========================================================================
PENERIMA TELEMETRI BLE 5.0 RASPBERRY PI 4B - CAPSTONE AKUAPONIK UNNES
Menghubungkan Raspberry Pi 4B ke ESP32-S3 via Nordic UART Service (NUS)
========================================================================
"""

import asyncio
import json
import sys
import time
import urllib.request
from bleak import BleakScanner, BleakClient

TARGET_DEVICE_NAME = "ESP32S3_Akuaponik_UNNES"
SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" # ESP32 Notify -> Pi
UART_RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E" # Pi Write -> ESP32

DASHBOARD_API_URL = "http://localhost:8080/api/aquaponik/data"

def forward_to_dashboard(payload_dict):
    try:
        data = json.dumps(payload_dict).encode("utf-8")
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

def handle_rx_notification(sender, data: bytearray):
    try:
        text = data.decode("utf-8").strip()
        if text.startswith("{") and text.endswith("}"):
            payload = json.loads(text)
            ph = payload.get("ph") or payload.get("sensors", {}).get("pH", "-")
            ntu = payload.get("ntu") or payload.get("sensors", {}).get("turbidity", "-")
            temp = payload.get("temp") or payload.get("sensors", {}).get("temperature_c", "-")
            level = payload.get("lvl") or payload.get("sensors", {}).get("water_level_cm", "-")
            seq = payload.get("seq", 0)

            print(f"[BLE <- ESP32-S3] seq={seq:04d} | pH={ph} | Kekeruhan={ntu} NTU | Suhu={temp} C | Level={level} cm")
            forward_to_dashboard(payload)
    except Exception as e:
        print(f"[ERR] Gagal parsing paket BLE: {e}")

async def main():
    print("=" * 70)
    print(" PENERIMA TELEMETRI BLE 5.0 RASPBERRY PI 4B (ECO FARM UNNES)")
    print("=" * 70)
    print(f" Mencari perangkat BLE: '{TARGET_DEVICE_NAME}'...")
    print("=" * 70)

    device = None
    try:
        device = await BleakScanner.find_device_by_filter(
            lambda d, ad: d.name and TARGET_DEVICE_NAME in d.name,
            timeout=8.0
        )
    except Exception as e:
        print(f"[ERR] Pemindaian Bluetooth gagal: {e}")
        return

    if not device:
        print(f"[WARN] Perangkat '{TARGET_DEVICE_NAME}' belum terdeteksi.")
        print("Pastikan ESP32-S3 menyala dan berada dalam jangkauan Bluetooth.")
        return

    print(f"[INFO] Perangkat ditemukan: {device.name} [{device.address}]")
    print("[INFO] Menghubungkan ke ESP32-S3...")

    async with BleakClient(device) as client:
        print(f"[SUCCESS] Terhubung ke {device.name}!")
        print("[INFO] Berlangganan (Subscribe) ke Nordic UART TX...")

        await client.start_notify(UART_TX_UUID, handle_rx_notification)
        print("[INFO] Menerima aliran data sensor secara realtime (Ctrl+C untuk keluar)...\n")

        # Kirim status inisialisasi dari Pi ke ESP32
        init_cmd = json.dumps({"pi_online": True, "psi": 11.8, "cmd_drain": 0}).encode("utf-8")
        try:
            await client.write_gatt_char(UART_RX_UUID, init_cmd)
        except Exception:
            pass

        while True:
            await asyncio.sleep(1.0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
