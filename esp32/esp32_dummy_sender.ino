/*
 ========================================================================
 PENGIRIM DATA DUMMY TELEMETRI ESP32 - CAPSTONE AKUAPONIK UNNES
 Peneliti ESP32 & Fuzzy Sugeno: Rafly Akbar Anggara (NIM 2305110006)
 ========================================================================
 Deskripsi:
 Sketch ini menghasilkan data telemetri dummy kolam yang dinamis dan realistis
 tanpa perlu sensor fisik terpasang. Cocok untuk pengujian koneksi ke
 Raspberry Pi 4B dan verifikasi antarmuka Dasbor Web.

 Fitur:
 1. Simulasi matematis pH (6.80 - 7.35) dengan fluktuasi alami.
 2. Simulasi kekeruhan SEN0189 (5.0 - 18.0 NTU) mensimulasikan metabolisme ikan.
 3. Simulasi suhu air DS18B20 (26.5 - 28.5 °C).
 4. Simulasi ketinggian air JSN-SR04T (67.0 - 69.5 cm).
 5. Output via Serial USB (Baud 115200 bps) format Line-Delimited JSON.
 6. Menerima umpan balik kanopi kangkung (PSI, Coverage) dan perintah katup.
 7. Indikator LED onboard (GPIO 2) berkedip setiap paket data terkirim.
 ========================================================================
*/

#include <Arduino.h>
#include <ArduinoJson.h>
#include <math.h>

// Konfigurasi Pin & Interval
#define LED_PIN 2               // LED bawaan ESP32 (NodeMCU / DevKit V1)
#define SERIAL_BAUD 115200      // Baud rate komunikasi ke Raspberry Pi
#define INTERVAL_KIRIM_MS 1000  // Kirim data setiap 1 detik (1 Hz)

// Variabel Waktu & State
unsigned long waktuTerakhirKirim = 0;
uint16_t nomorUrutPaket = 0;
float phaseSinus = 0.0;

// Status Aktuator Lokal
bool statusKatupKuras = false;
bool statusPompaSirkulasi = true;
bool statusDispenserPakan = false;
unsigned long waktuBukaKatup = 0;
const unsigned long MAKS_DURASI_KATUP_MS = 60000; // Pengaman darurat 60 detik

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Inisialisasi Serial ke Raspberry Pi
  Serial.begin(SERIAL_BAUD);
  delay(1000);

  // Indikator boot selesai (kedip 3 kali)
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }
}

void loop() {
  unsigned long now = millis();

  // ------------------------------------------------------------------
  // 1. TERIMA DATA & PERINTAH DARI RASPBERRY PI (Non-Blocking)
  // ------------------------------------------------------------------
  if (Serial.available() > 0) {
    String barisMasuk = Serial.readStringUntil('\n');
    barisMasuk.trim();

    if (barisMasuk.length() > 0 && barisMasuk.startsWith("{") && barisMasuk.endsWith("}")) {
      StaticJsonDocument<256> docIn;
      DeserializationError err = deserializeJson(docIn, barisMasuk);

      if (!err) {
        // Baca data visi kanopi kangkung dari Raspberry Pi
        float psi = docIn["psi"] | 0.0;
        float cov = docIn["cov"] | 0.0;
        int cmd_drain = docIn["cmd_drain"] | 0;
        int acc = docIn["acc"] | 0;

        // Logika keselamatan aktuasi katup solenoid
        if (cmd_drain == 1 && acc == 1) {
          statusKatupKuras = true;
          waktuBukaKatup = now;
        } else if (cmd_drain == 0) {
          statusKatupKuras = false;
        }

        // Kedipkan LED tanda perintah diterima
        digitalWrite(LED_PIN, HIGH);
        delay(30);
        digitalWrite(LED_PIN, LOW);
      }
    }
  }

  // Pengaman hardware: otomatis tutup katup jika melebihi batas waktu
  if (statusKatupKuras && (now - waktuBukaKatup >= MAKS_DURASI_KATUP_MS)) {
    statusKatupKuras = false;
  }

  // ------------------------------------------------------------------
  // 2. GENERATE & KIRIM DATA DUMMY TELEMETRI (Tiap 1 Detik)
  // ------------------------------------------------------------------
  if (now - waktuTerakhirKirim >= INTERVAL_KIRIM_MS) {
    waktuTerakhirKirim = now;
    nomorUrutPaket++;
    phaseSinus += 0.08;

    // Rumus variasi matematis alami kolam:
    // pH berkisar antara 6.80 s/d 7.25 dengan osilasi lambat
    float dummyPH = 7.02 + 0.18 * sin(phaseSinus) + ((random(-15, 15)) / 1000.0);
    
    // Kekeruhan berkisar antara 6.0 s/d 14.5 NTU
    float dummyNTU = 9.5 + 3.2 * sin(phaseSinus * 0.7) + ((random(-20, 20)) / 100.0);
    if (statusKatupKuras) {
      dummyNTU = max(3.5, dummyNTU - 4.0); // Kekeruhan turun saat katup kuras aktif
    }

    // Suhu air berkisar antara 26.8 s/d 27.9 °C
    float dummyTemp = 27.35 + 0.45 * cos(phaseSinus * 0.4);

    // Ketinggian air berkisar antara 67.5 s/d 68.8 cm
    float dummyLevel = 68.2 + 0.6 * sin(phaseSinus * 1.2);

    // Susun dokumen JSON
    StaticJsonDocument<256> docOut;
    docOut["node"] = "esp32";
    docOut["ph"] = round(dummyPH * 100) / 100.0;
    docOut["ntu"] = round(dummyNTU * 10) / 10.0;
    docOut["temp"] = round(dummyTemp * 10) / 10.0;
    docOut["lvl"] = round(dummyLevel * 10) / 10.0;
    docOut["valve"] = statusKatupKuras ? 1 : 0;
    docOut["pump"] = statusPompaSirkulasi ? 1 : 0;
    docOut["feed"] = statusDispenserPakan ? 1 : 0;
    docOut["seq"] = nomorUrutPaket;

    // Kirim via USB Serial
    serializeJson(docOut, Serial);
    Serial.println(); // Karakter pembatas \n

    // Indikasi kedipan LED pengiriman
    digitalWrite(LED_PIN, HIGH);
    delay(15);
    digitalWrite(LED_PIN, LOW);
  }
}
