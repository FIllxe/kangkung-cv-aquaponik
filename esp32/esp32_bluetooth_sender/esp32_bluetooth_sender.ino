/*
 ========================================================================
 PENGIRIM TELEMETRI MULTI-SKENARIO BLE 5.0 - ESP32-S3 AKUAPONIK UNNES
 Chipset Hardware: ESP32-S3 (Dual-Core Xtensa LX7 + BLE 5.0)
 Peneliti 2 (Fuzzy Sugeno & ESP32): Rafly Akbar Anggara (NIM 2305110006)
 Pembimbing / Mitra: Felix Enrique (NIM 2305110019)
 ========================================================================
 Skenario Uji Terpadu:
 1. SKENARIO 1: Kondisi Prima / Optimal (pH 7.15, NTU 8.2, Suhu 27.4 C, PSI 8.5% -> z = 0%)
 2. SKENARIO 2: Mutu Air Menurun (pH 6.65, NTU 28.4, Suhu 28.1 C, PSI 18.2% -> z = 15-20%)
 3. SKENARIO 3: Kondisi Kritis / Darurat (pH 5.45, NTU 62.0, Suhu 29.8 C, PSI 54.0% -> z = 30%)
 4. SKENARIO 4: Hujan Deras & Ancaman Luapan (Level 78.5 cm, Rain=True, Interlock Valve IN)
 
 Kontrol Skenario:
 - Kirim '1', '2', '3', '4' via Serial / BLE untuk memilih skenario manual.
 - Kirim 'a' atau 'A' untuk mengaktifkan Demo Otomatis (berganti tiap 15 detik).
 ========================================================================
*/

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <ArduinoJson.h>
#include <math.h>

#define SERVICE_UUID           "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_RX "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_TX "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

#define LED_PIN 2
#define SERIAL_BAUD 115200
#define INTERVAL_TRANSMISI_MS 1000
#define DURASI_SKENARIO_AUTO_MS 15000 // 15 detik per skenario pada mode auto

BLEServer *pServer = NULL;
BLECharacteristic *pTxCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

unsigned long lastSendTime = 0;
unsigned long lastScenarioSwitch = 0;
uint16_t packetSeq = 0;
float phaseSinus = 0.0;

// Konfigurasi Skenario
int skenarioAktif = 1;
bool modeAutoLoop = true; // Default aktif berputar otomatis untuk demo pengujian

// Target Parameter per Skenario
struct ScenarioParam {
  const char* nama;
  float phBase;
  float ntuBase;
  float tempBase;
  float levelBase;
  float psiBase;
  bool rain;
  const char* deskripsi;
};

ScenarioParam skenarioList[4] = {
  {
    "OPTIMAL_PRIMA",
    7.15, 8.2, 27.4, 68.2, 8.5, false,
    "Kondisi Air & Kanopi Sehat. SPK: z = 0% (Tanpa Kuras)"
  },
  {
    "KERUH_SEDANG",
    6.65, 28.4, 28.1, 67.0, 18.2, false,
    "Kekeruhan Meningkat. SPK: z = 15-20% (Kuras Parsial)"
  },
  {
    "KRITIS_ASIDIFIKASI",
    5.45, 62.0, 29.8, 64.0, 54.0, false,
    "Air Sangat Asam & Keruh. SPK: z = 30% (FLUSH DARURAT)"
  },
  {
    "HUJAN_DERAS_OVERFLOW",
    6.30, 16.5, 25.2, 78.5, 12.0, true,
    "Hujan Deras, Kolam Penuh. INTERLOCK: Valve IN Terkunci"
  }
};

// State Aktuator Kolam
bool valveDrainOpen = false;
bool valveInOpen = false;
bool pumpCirculationActive = true;
unsigned long valveOpenedAt = 0;
const unsigned long MAX_VALVE_DURATION_MS = 60000;

void setSkenario(int no) {
  if (no >= 1 && no <= 4) {
    skenarioAktif = no;
    Serial.println("\n-------------------------------------------------------");
    Serial.print("[SKENARIO BERGANTI] -> SKENARIO ");
    Serial.print(skenarioAktif);
    Serial.print(": ");
    Serial.println(skenarioList[skenarioAktif - 1].nama);
    Serial.print("Keterangan: ");
    Serial.println(skenarioList[skenarioAktif - 1].deskripsi);
    Serial.println("-------------------------------------------------------");
  }
}

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      Serial.println("[BLE] Raspberry Pi / Klien TERHUBUNG!");
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      Serial.println("[BLE] Klien TERPUTUS. Menunggu koneksi kembali...");
    }
};

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String rxValue = pCharacteristic->getValue().c_str();

      if (rxValue.length() > 0) {
        Serial.print("[BLE RX] Perintah Masuk: ");
        Serial.println(rxValue);

        // Perintah ganti skenario lewat BLE
        if (rxValue == "1") { modeAutoLoop = false; setSkenario(1); }
        else if (rxValue == "2") { modeAutoLoop = false; setSkenario(2); }
        else if (rxValue == "3") { modeAutoLoop = false; setSkenario(3); }
        else if (rxValue == "4") { modeAutoLoop = false; setSkenario(4); }
        else if (rxValue == "a" || rxValue == "A") {
          modeAutoLoop = true;
          Serial.println("[MODE] Demo Auto-Loop DIAKTIFKAN (Berganti tiap 15 detik)");
        }

        // Parsing JSON jika payload terstruktur
        if (rxValue.startsWith("{") && rxValue.endsWith("}")) {
          StaticJsonDocument<256> docIn;
          DeserializationError err = deserializeJson(docIn, rxValue);
          if (!err) {
            if (docIn.containsKey("scenario")) {
              modeAutoLoop = false;
              setSkenario(docIn["scenario"]);
            }
            int cmd_drain = docIn["cmd_drain"] | 0;
            int acc = docIn["acc"] | 0;

            if (cmd_drain == 1 && acc == 1) {
              valveDrainOpen = true;
              valveOpenedAt = millis();
              Serial.println("[ACTUATOR] Katup Pengurasan Kolam DIBUKA.");
            } else if (cmd_drain == 0) {
              valveDrainOpen = false;
              Serial.println("[ACTUATOR] Katup Pengurasan Kolam DITUTUP.");
            }
          }
        }
      }
    }
};

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(SERIAL_BAUD);
  delay(1000);

  Serial.println("\n=======================================================");
  Serial.println(" SISTEM TELEMETRI MULTI-SKENARIO - ESP32-S3 FT UNNES   ");
  Serial.println("=======================================================");
  Serial.println("Panduan Kontrol Manual Skenario via Serial / BLE:");
  Serial.println("  Ketik '1' : Skenario 1 - Kondisi Prima (z = 0%)");
  Serial.println("  Ketik '2' : Skenario 2 - Keruh Sedang (z = 15-20%)");
  Serial.println("  Ketik '3' : Skenario 3 - Kritis Asam & Keruh (z = 30%)");
  Serial.println("  Ketik '4' : Skenario 4 - Hujan Deras & Kolam Penuh");
  Serial.println("  Ketik 'a' : Mode Demo Berputar Otomatis (Default)");
  Serial.println("=======================================================");

  BLEDevice::init("ESP32S3_Akuaponik_UNNES");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  pTxCharacteristic = pService->createCharacteristic(
                        CHARACTERISTIC_UUID_TX,
                        BLECharacteristic::PROPERTY_NOTIFY
                      );
  pTxCharacteristic->addDescriptor(new BLE2902());

  BLECharacteristic *pRxCharacteristic = pService->createCharacteristic(
                                           CHARACTERISTIC_UUID_RX,
                                           BLECharacteristic::PROPERTY_WRITE
                                         );
  pRxCharacteristic->setCallbacks(new MyCallbacks());

  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();

  Serial.println("[BLE] Advertising aktif sebagai 'ESP32S3_Akuaponik_UNNES'");
  setSkenario(1);
  lastScenarioSwitch = millis();
}

void loop() {
  unsigned long now = millis();

  // ------------------------------------------------------------------
  // 1. INPUT SERIAL DARI PENGUJI / TERMINAL VS CODE
  // ------------------------------------------------------------------
  if (Serial.available() > 0) {
    char ch = Serial.read();
    if (ch == '1') { modeAutoLoop = false; setSkenario(1); }
    else if (ch == '2') { modeAutoLoop = false; setSkenario(2); }
    else if (ch == '3') { modeAutoLoop = false; setSkenario(3); }
    else if (ch == '4') { modeAutoLoop = false; setSkenario(4); }
    else if (ch == 'a' || ch == 'A') {
      modeAutoLoop = true;
      lastScenarioSwitch = now;
      Serial.println("[MODE] Demo Auto-Loop DIAKTIFKAN kembali.");
    }
  }

  // ------------------------------------------------------------------
  // 2. LOGIKA ROTASI SKENARIO OTOMATIS (DEMO MODE)
  // ------------------------------------------------------------------
  if (modeAutoLoop && (now - lastScenarioSwitch >= DURASI_SKENARIO_AUTO_MS)) {
    lastScenarioSwitch = now;
    int nextScenario = (skenarioAktif % 4) + 1;
    setSkenario(nextScenario);
  }

  // ------------------------------------------------------------------
  // 3. SAFETY & INTERLOCK AKTUATOR
  // ------------------------------------------------------------------
  if (valveDrainOpen && (now - valveOpenedAt >= MAX_VALVE_DURATION_MS)) {
    valveDrainOpen = false;
    Serial.println("[SAFETY] Batas waktu katup kuras 60s tercapai. Katup DITUTUP!");
  }

  // Jika Skenario 4 (Hujan), kunci katup penambah air
  if (skenarioList[skenarioAktif - 1].rain) {
    valveInOpen = false;
  }

  // ------------------------------------------------------------------
  // 4. TRANSMISI TELEMETRI BERKALA (Setiap 1 Detik)
  // ------------------------------------------------------------------
  if (now - lastSendTime >= INTERVAL_TRANSMISI_MS) {
    lastSendTime = now;
    packetSeq++;
    phaseSinus += 0.12;

    ScenarioParam cur = skenarioList[skenarioAktif - 1];

    // Variasi dinamis halus di sekitar nilai dasar skenario
    float ph = round((cur.phBase + 0.05 * sin(phaseSinus) + (random(-5, 5) / 1000.0)) * 100.0) / 100.0;
    float ntu = round((cur.ntuBase + 0.8 * sin(phaseSinus * 0.8) + (random(-10, 10) / 100.0)) * 10.0) / 10.0;
    float temp = round((cur.tempBase + 0.15 * cos(phaseSinus * 0.5)) * 10.0) / 10.0;
    float level = round((cur.levelBase + 0.2 * sin(phaseSinus * 1.5)) * 10.0) / 10.0;
    float psi = round((cur.psiBase + 0.4 * sin(phaseSinus)) * 10.0) / 10.0;

    StaticJsonDocument<384> docOut;
    docOut["node"] = "esp32s3";
    docOut["seq"] = packetSeq;
    docOut["scenario_id"] = skenarioAktif;
    docOut["scenario_name"] = cur.nama;
    docOut["auto_mode"] = modeAutoLoop;
    
    JsonObject sensors = docOut.createNestedObject("sensors");
    sensors["pH"] = ph;
    sensors["turbidity"] = ntu;
    sensors["water_level_cm"] = level;
    sensors["temperature_c"] = temp;
    sensors["rain_detected"] = cur.rain;

    JsonObject vision = docOut.createNestedObject("vision");
    vision["psi"] = psi;
    vision["green_pct"] = round((100.0 - psi * 1.2) * 10.0) / 10.0;
    vision["yellow_pct"] = round((psi * 0.8) * 10.0) / 10.0;
    vision["brown_pct"] = round((psi * 0.4) * 10.0) / 10.0;

    JsonObject actuators = docOut.createNestedObject("actuators");
    actuators["valve_out"] = valveDrainOpen;
    actuators["valve_in"] = valveInOpen;
    actuators["pump"] = pumpCirculationActive;

    docOut["ph"] = ph;
    docOut["ntu"] = ntu;
    docOut["temp"] = temp;
    docOut["lvl"] = level;
    docOut["psi"] = psi;

    String jsonString;
    serializeJson(docOut, jsonString);

    // Kirim via BLE jika client terhubung
    if (deviceConnected && pTxCharacteristic != NULL) {
      pTxCharacteristic->setValue(jsonString.c_str());
      pTxCharacteristic->notify();
    }

    // Output Serial USB Monitor
    Serial.print("[S");
    Serial.print(skenarioAktif);
    Serial.print(modeAutoLoop ? "-AUTO]" : "-MANUAL]");
    Serial.print(" seq=");
    Serial.print(packetSeq);
    Serial.print(" | pH=");
    Serial.print(ph, 2);
    Serial.print(" | NTU=");
    Serial.print(ntu, 1);
    Serial.print(" | Suhu=");
    Serial.print(temp, 1);
    Serial.print(" C | Lvl=");
    Serial.print(level, 1);
    Serial.print(" cm | PSI=");
    Serial.print(psi, 1);
    Serial.print("% | Hujan=");
    Serial.print(cur.rain ? "YA" : "TIDAK");
    Serial.print(" | BLE: ");
    Serial.println(deviceConnected ? "CONNECTED" : "ADVERTISING");

    digitalWrite(LED_PIN, HIGH);
    delay(30);
    if (!deviceConnected) {
      digitalWrite(LED_PIN, LOW);
    }
  }
}
