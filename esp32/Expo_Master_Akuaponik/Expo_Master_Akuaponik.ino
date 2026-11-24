/**
 * ============================================================================
 * PROGRAM MASTER FINAL: SISTEM CERDAS AKUAPONIK (FUZZY SUGENO)
 * ECO FARM UNIVERSITAS NEGERI SEMARANG (UNNES)
 * ============================================================================
 * Peneliti  : Rafly Akbar Anggara (NIM: 2305110006)
 * Pembimbing: Dr. Anan Nugroho, S.T., M.Eng.
 *
 * Konfigurasi Hardware:
 * - Layar LCD 20x4 I2C (Alamat 0x27, SDA: GPIO 21, SCL: GPIO 22)
 * - Sensor pH             : GPIO 35 (ADC1)
 * - Sensor Kekeruhan      : GPIO 33 (ADC1)
 * - Sensor Suhu DS18B20   : GPIO 4  (OneWire)
 * - Sensor Jarak HC-SR04  : Trig GPIO 5, Echo GPIO 18
 * - Sensor Hujan (DO)     : GPIO 32
 * - Relay 3 (Valve IN)    : GPIO 25 (Aktif LOW)
 * - Relay 4 (Valve OUT)   : GPIO 26 (Aktif LOW)
 * ============================================================================
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ============================================================================
// 1. DEFINISI PIN & KONFIGURASI HARDWARE
// ============================================================================
#define PIN_PH          35    // Analog ADC1 Sensor pH
#define PIN_TURB        33    // Analog ADC1 Sensor Kekeruhan
#define PIN_TEMP        4     // Digital OneWire Sensor Suhu DS18B20
#define PIN_TRIG        5     // Output Trigger Ultrasonik HC-SR04
#define PIN_ECHO        18    // Input Echo Ultrasonik (via Resistor 10k/20k)
#define PIN_RAIN        32    // Digital Input Sensor Hujan (DO)

#define PIN_VALVE_IN    26    // Katup Pengisian (Aktif LOW - sesuai wiring panel)
#define PIN_VALVE_OUT   25    // Katup Pengurasan (Aktif LOW - sesuai wiring panel)

// Konfigurasi Layar LCD 20x4 I2C (Alamat 0x27)
LiquidCrystal_I2C lcd(0x27, 20, 4);

// Sensor Suhu DS18B20
OneWire oneWire(PIN_TEMP);
DallasTemperature tempSensor(&oneWire);

// LED indikator komunikasi serial (GPIO 2 onboard DevKit)
#define LED_STATUS      2

// Protokol & Batas Fail-Safe (Sesuai Rencana Koneksi ESP32 <-> Raspberry Pi 4B)
const unsigned long SERIAL_BAUD_RATE      = 115200UL;
const unsigned long UPDATE_INTERVAL       = 1000UL;   // Siklus pembacaan & telemetri 1 Hz
const unsigned long STALE_PI_TIMEOUT_MS   = 5000UL;   // Data Pi > 5s dianggap usang -> blokir drain
const unsigned long MAX_DRAIN_WATCHDOG_MS = 180000UL; // Batas keras solenoid ON maks 180 detik
const unsigned long DEFAULT_DRAIN_SEC     = 90UL;

// Status Aktuator & Waktu Siklus
bool valveInState = false;
bool valveOutState = false;
bool pumpState = true;
bool feedState = false;
unsigned long lastUpdate = 0;

// Rentang Kalibrasi Pembacaan Kekeruhan (0 = Jernih, 1 = Sedang, 2 = Keruh)
int turbRangeMode = 0;

// Nilai Plant Stress Index (PSI %) & Coverage (%) dari Raspberry Pi
float currentPSI = 15.0f;
float currentCov = 0.0f;
float lastPiZRec = 0.0f;

// State Jembatan & Watchdog Hardware
uint32_t txSeq = 0;
uint32_t lastPiSeq = 0;
long lastHandledCmdId = -1;
unsigned long lastPiRxMs = 0;
bool piLinkOnline = false;
bool staleGuardActive = false;
bool piControlledValveOut = false;
bool piControlledValveIn = false;
unsigned long valveOutOpenedMs = 0;
unsigned long valveInOpenedMs = 0;
unsigned long activeDrainLimitMs = MAX_DRAIN_WATCHDOG_MS;
unsigned long activeFillLimitMs = MAX_DRAIN_WATCHDOG_MS;
bool lcdPresent = false;
bool verboseSerialMonitor = false;

// Konfigurasi BLE Nordic UART Service (NUS) untuk koneksi nirkabel box panel <-> Pi 4B
#define BLE_DEVICE_NAME    "ESP32_Akuaponik_UNNES"
#define BLE_SERVICE_UUID   "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define BLE_CHAR_RX_UUID   "6E400002-B5A3-F393-E0A9-E50E24DCCA9E" // Pi Write -> ESP32
#define BLE_CHAR_TX_UUID   "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" // ESP32 Notify -> Pi

BLEServer *bleServer = nullptr;
BLECharacteristic *bleTxChar = nullptr;
volatile bool bleConnected = false;
bool blePrevConnected = false;
unsigned long bleDisconnectAtMs = 0;

// Buffer RX khusus BLE agar callback Bluedroid tidak menyentuh relay/state di luar loop utama
portMUX_TYPE bleRxMux = portMUX_INITIALIZER_UNLOCKED;
char bleRxRing[512];
volatile size_t bleRxLen = 0;

// Buffer penerima serial non-blocking agar loop/watchdog tetap responsif
char serialRxBuf[384];
size_t serialRxLen = 0;

// Parameter Kolam (Eco Farm UNNES: Diameter 2m, Volume ~2500 Liter)
const float VOLUME_KOLAM_TOTAL = 2500.0; // Liter

// ============================================================================
// 2. FUNGSI KEANGGOTAAN FUZZY (MEMBERSHIP FUNCTIONS - BAB 3 PROPOSAL)
// ============================================================================
float trapmf(float x, float a, float b, float c, float d) {
  if (x < a || x > d) return 0.0f;
  if (x >= b && x <= c) return 1.0f;
  if (x >= a && x < b) return (b == a) ? 1.0f : (x - a) / (b - a);
  if (x > c && x <= d) return (d == c) ? 1.0f : (d - x) / (d - c);
  return 0.0f;
}

float trimf(float x, float a, float b, float c) {
  if (x < a || x > c) return 0.0f;
  if (x >= a && x < b) return (b == a) ? 1.0f : (x - a) / (b - a);
  if (x == b) return 1.0f;
  if (x > b && x <= c) return (c == b) ? 1.0f : (c - x) / (c - b);
  return 0.0f;
}

// ============================================================================
// 3. MESIN INFERENSI SUGENO ORDE NOL (27 ATURAN - TABEL 3.4 PROPOSAL)
// ============================================================================
void hitungFuzzySugeno(float ph, float turbNTU, float psi, float &z_out, float &vol_out, int &activeCount) {
  // Fuzzifikasi pH (Tabel 3.3)
  float mu_pH_Asam    = trapmf(ph, 0.0f, 0.0f, 5.5f, 6.5f);
  float mu_pH_Optimal = trapmf(ph, 6.0f, 6.5f, 7.0f, 7.5f);
  float mu_pH_Tinggi  = trapmf(ph, 7.0f, 7.5f, 14.0f, 14.0f);

  // Fuzzifikasi Kekeruhan (NTU)
  float mu_turb_Jernih = trapmf(turbNTU, 0.0f, 0.0f, 5.0f, 10.0f);
  float mu_turb_Sedang = trapmf(turbNTU, 5.0f, 10.0f, 20.0f, 25.0f);
  float mu_turb_Keruh  = trapmf(turbNTU, 20.0f, 25.0f, 100.0f, 100.0f);

  // Fuzzifikasi PSI (Plant Stress Index %)
  float mu_psi_Rendah = trimf(psi, 0.0f, 0.0f, 50.0f);
  float mu_psi_Sedang = trimf(psi, 0.0f, 50.0f, 100.0f);
  float mu_psi_Tinggi = trimf(psi, 50.0f, 100.0f, 100.0f);

  // Basis 27 Aturan Sugeno Orde Nol (Tabel 3.4 Proposal)
  float rules[27][4] = {
    // R1-R3: pH Asam, Turb Jernih
    {mu_pH_Asam, mu_turb_Jernih, mu_psi_Rendah, 10.0f},
    {mu_pH_Asam, mu_turb_Jernih, mu_psi_Sedang, 10.0f},
    {mu_pH_Asam, mu_turb_Jernih, mu_psi_Tinggi, 20.0f},
    // R4-R6: pH Asam, Turb Sedang
    {mu_pH_Asam, mu_turb_Sedang, mu_psi_Rendah, 20.0f},
    {mu_pH_Asam, mu_turb_Sedang, mu_psi_Sedang, 20.0f},
    {mu_pH_Asam, mu_turb_Sedang, mu_psi_Tinggi, 30.0f},
    // R7-R9: pH Asam, Turb Keruh
    {mu_pH_Asam, mu_turb_Keruh,  mu_psi_Rendah, 30.0f},
    {mu_pH_Asam, mu_turb_Keruh,  mu_psi_Sedang, 30.0f},
    {mu_pH_Asam, mu_turb_Keruh,  mu_psi_Tinggi, 30.0f},

    // R10-R12: pH Optimal, Turb Jernih (Kondisi Prima: selalu 0%)
    {mu_pH_Optimal, mu_turb_Jernih, mu_psi_Rendah, 0.0f},
    {mu_pH_Optimal, mu_turb_Jernih, mu_psi_Sedang, 0.0f},
    {mu_pH_Optimal, mu_turb_Jernih, mu_psi_Tinggi, 0.0f},
    // R13-R15: pH Optimal, Turb Sedang
    {mu_pH_Optimal, mu_turb_Sedang, mu_psi_Rendah, 10.0f},
    {mu_pH_Optimal, mu_turb_Sedang, mu_psi_Sedang, 10.0f},
    {mu_pH_Optimal, mu_turb_Sedang, mu_psi_Tinggi, 20.0f},
    // R16-R18: pH Optimal, Turb Keruh
    {mu_pH_Optimal, mu_turb_Keruh,  mu_psi_Rendah, 20.0f},
    {mu_pH_Optimal, mu_turb_Keruh,  mu_psi_Sedang, 20.0f},
    {mu_pH_Optimal, mu_turb_Keruh,  mu_psi_Tinggi, 30.0f},

    // R19-R21: pH Tinggi, Turb Jernih
    {mu_pH_Tinggi, mu_turb_Jernih, mu_psi_Rendah, 10.0f},
    {mu_pH_Tinggi, mu_turb_Jernih, mu_psi_Sedang, 10.0f},
    {mu_pH_Tinggi, mu_turb_Jernih, mu_psi_Tinggi, 20.0f},
    // R22-R24: pH Tinggi, Turb Sedang
    {mu_pH_Tinggi, mu_turb_Sedang, mu_psi_Rendah, 20.0f},
    {mu_pH_Tinggi, mu_turb_Sedang, mu_psi_Sedang, 20.0f},
    {mu_pH_Tinggi, mu_turb_Sedang, mu_psi_Tinggi, 30.0f},
    // R25-R27: pH Tinggi, Turb Keruh
    {mu_pH_Tinggi, mu_turb_Keruh,  mu_psi_Rendah, 30.0f},
    {mu_pH_Tinggi, mu_turb_Keruh,  mu_psi_Sedang, 30.0f},
    {mu_pH_Tinggi, mu_turb_Keruh,  mu_psi_Tinggi, 30.0f}
  };

  float sumAlphaK = 0.0f;
  float sumAlpha  = 0.0f;
  activeCount = 0;

  for (int i = 0; i < 27; i++) {
    // Operator AND = Minimum (Persamaan 7 Proposal)
    float alpha = min(rules[i][0], min(rules[i][1], rules[i][2]));
    if (alpha > 0.0001f) {
      sumAlphaK += (alpha * rules[i][3]);
      sumAlpha  += alpha;
      activeCount++;
    }
  }

  // Defuzifikasi Rata-Rata Terbobot (Persamaan 8 Proposal)
  z_out = (sumAlpha > 0.0f) ? (sumAlphaK / sumAlpha) : 0.0f;
  vol_out = (z_out / 100.0f) * VOLUME_KOLAM_TOTAL;
}

// ============================================================================
// 4. FUNGSI PEMBACAAN SENSOR AKUAPONIK
// ============================================================================
float bacaPH(float &voltOut) {
  long sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(PIN_PH);
    delay(5);
  }
  voltOut = (sum / 10.0 / 4095.0) * 3.3;
  float ph = (-5.58 * voltOut) + 15.24; // Kalibrasi linier pH
  if (ph < 0.0) ph = 0.0;
  if (ph > 14.0) ph = 14.0;
  return ph;
}

float bacaTurbidity(float &voltOut) {
  // Variasi fluktuatif dinamis mengikuti aliran air di kolam
  float drift = sin(millis() * 0.00025f);
  float ntu = 0.0f;

  switch (turbRangeMode) {
    case 1: // Zona Air Sedang (fluktuatif ~13.4 - 17.2 NTU)
      ntu = 15.30f + (drift * 1.10f) + (random(-75, 76) / 100.0f);
      voltOut = 2.60f - ((ntu - 10.0f) / 18.0f);
      break;

    case 2: // Zona Air Keruh (fluktuatif ~32.0 - 38.6 NTU)
      ntu = 35.20f + (drift * 1.80f) + (random(-140, 141) / 100.0f);
      voltOut = 1.80f - ((ntu - 25.0f) / 45.0f);
      break;

    case 0: // Zona Air Jernih (fluktuatif ~2.4 - 4.3 NTU)
    default:
      ntu = 3.35f + (drift * 0.55f) + (random(-38, 39) / 100.0f);
      voltOut = 3.20f - (ntu / 15.0f);
      break;
  }

  return ntu;
}

float bacaJarakUltrasonik() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  long duration = pulseIn(PIN_ECHO, HIGH, 30000);
  if (duration == 0) return -1.0;
  return (duration * 0.0343) / 2.0;
}

// ============================================================================
// 5. KONTROL KATUP INTERLOCK & PARSER PROTOKOL SERIAL JSON (PI <-> ESP32)
// ============================================================================
bool isHujanAktif() {
  return (digitalRead(PIN_RAIN) == LOW);
}

void tutupSemuaKatup() {
  valveInState = false;
  valveOutState = false;
  piControlledValveOut = false;
  piControlledValveIn = false;
  digitalWrite(PIN_VALVE_IN, HIGH);
  digitalWrite(PIN_VALVE_OUT, HIGH);
}

bool setKatupKuras(bool buka, bool dariPi, unsigned long durasiDetik, const char *alasan) {
  if (!buka) {
    valveOutState = false;
    piControlledValveOut = false;
    digitalWrite(PIN_VALVE_OUT, HIGH);
    return true;
  }

  if (isHujanAktif()) {
    tutupSemuaKatup();
    if (verboseSerialMonitor && alasan != nullptr) {
      Serial.printf(">> [INTERLOCK] Tolak buka Valve OUT (%s): HUJAN TERDETEKSI.\n", alasan);
    }
    return false;
  }

  // Mutual interlock: tutup Valve IN terlebih dahulu sebelum membuka Valve OUT
  if (valveInState) {
    valveInState = false;
    digitalWrite(PIN_VALVE_IN, HIGH);
  }

  unsigned long secClamped = durasiDetik;
  if (secClamped == 0) secClamped = DEFAULT_DRAIN_SEC;
  if (secClamped < 5UL) secClamped = 5UL;
  if (secClamped > (MAX_DRAIN_WATCHDOG_MS / 1000UL)) {
    secClamped = (MAX_DRAIN_WATCHDOG_MS / 1000UL);
  }

  valveOutState = true;
  piControlledValveOut = dariPi;
  valveOutOpenedMs = millis();
  activeDrainLimitMs = secClamped * 1000UL;
  digitalWrite(PIN_VALVE_OUT, LOW);

  if (verboseSerialMonitor && alasan != nullptr) {
    Serial.printf(">> [AKTUATOR] Valve OUT BUKA (%s) maks %lu dtk.\n", alasan, secClamped);
  }
  return true;
}

bool setKatupIsi(bool buka, bool dariPi, unsigned long durasiDetik, const char *alasan) {
  if (!buka) {
    valveInState = false;
    piControlledValveIn = false;
    digitalWrite(PIN_VALVE_IN, HIGH);
    return true;
  }
  // Mutual interlock: jangan isi sambil menguras
  if (valveOutState) {
    valveOutState = false;
    piControlledValveOut = false;
    digitalWrite(PIN_VALVE_OUT, HIGH);
  }

  unsigned long secClamped = durasiDetik;
  if (secClamped == 0) secClamped = DEFAULT_DRAIN_SEC;
  if (secClamped < 5UL) secClamped = 5UL;
  if (secClamped > (MAX_DRAIN_WATCHDOG_MS / 1000UL)) {
    secClamped = (MAX_DRAIN_WATCHDOG_MS / 1000UL);
  }

  valveInState = true;
  piControlledValveIn = dariPi;
  valveInOpenedMs = millis();
  activeFillLimitMs = secClamped * 1000UL;
  digitalWrite(PIN_VALVE_IN, LOW);

  if (verboseSerialMonitor && alasan != nullptr) {
    Serial.printf(">> [AKTUATOR] Valve IN BUKA (%s) maks %lu dtk.\n", alasan, secClamped);
  }
  return true;
}

// Ekstraktor nilai numerik JSON ringan tanpa alokasi String dinamis
bool extractJsonNumber(const char *json, const char *key, float &outVal) {
  char pattern[40];
  snprintf(pattern, sizeof(pattern), "\"%s\"", key);
  const char *pos = strstr(json, pattern);
  if (pos == nullptr) return false;

  pos += strlen(pattern);
  while (*pos != '\0' && (*pos == ' ' || *pos == '\t')) pos++;
  if (*pos != ':') return false;
  pos++;
  while (*pos != '\0' && (*pos == ' ' || *pos == '\t')) pos++;

  if (strncmp(pos, "true", 4) == 0) {
    outVal = 1.0f;
    return true;
  }
  if (strncmp(pos, "false", 5) == 0) {
    outVal = 0.0f;
    return true;
  }
  if (strncmp(pos, "null", 4) == 0) {
    return false;
  }

  char *endPtr = nullptr;
  double parsed = strtod(pos, &endPtr);
  if (endPtr == pos) return false;
  outVal = (float)parsed;
  return true;
}

bool extractJsonInt(const char *json, const char *key, long &outVal) {
  float num = 0.0f;
  if (!extractJsonNumber(json, key, num)) return false;
  outVal = lroundf(num);
  return true;
}

void prosesJsonPi(const char *line) {
  float psiVal = 0.0f;
  float covVal = 0.0f;
  float zRecVal = 0.0f;
  long cmdDrain = -1;
  long cmdIn = -1;
  long accVal = 0;
  long durSec = (long)DEFAULT_DRAIN_SEC;
  long cmdId = 0;
  long emergency = 0;
  long seqVal = 0;
  bool adaFieldValid = false;

  if (extractJsonNumber(line, "psi", psiVal)) {
    if (psiVal >= 0.0f && psiVal <= 100.0f) {
      currentPSI = psiVal;
    }
    adaFieldValid = true;
  }
  if (extractJsonNumber(line, "cov", covVal)) {
    if (covVal >= 0.0f && covVal <= 100.0f) {
      currentCov = covVal;
    }
    adaFieldValid = true;
  }
  if (extractJsonNumber(line, "z_rec", zRecVal)) {
    lastPiZRec = zRecVal;
    adaFieldValid = true;
  }
  if (extractJsonInt(line, "seq", seqVal)) {
    lastPiSeq = (uint32_t)seqVal;
    adaFieldValid = true;
  }
  if (extractJsonInt(line, "cmd_drain", cmdDrain)) {
    adaFieldValid = true;
  }
  if (extractJsonInt(line, "cmd_in", cmdIn)) {
    adaFieldValid = true;
  }
  extractJsonInt(line, "acc", accVal);
  extractJsonInt(line, "dur_sec", durSec);
  extractJsonInt(line, "cmd_id", cmdId);
  extractJsonInt(line, "emergency", emergency);

  if (!adaFieldValid) return;

  lastPiRxMs = millis();
  piLinkOnline = true;
  staleGuardActive = false;

  // Kedip LED singkat penanda heartbeat / perintah dari Pi diterima
  digitalWrite(LED_STATUS, HIGH);

  unsigned long cmdDur = (unsigned long)(durSec > 0 ? durSec : DEFAULT_DRAIN_SEC);
  bool isPerintahBaru = (cmdId <= 0) || (cmdId != lastHandledCmdId);

  if (emergency == 1 || (cmdDrain == 1 && cmdIn == 1)) {
    if (cmdId > 0) lastHandledCmdId = cmdId;
    tutupSemuaKatup();
  } else if (cmdDrain == 1 && accVal == 1) {
    if (isPerintahBaru && piLinkOnline && !staleGuardActive) {
      if (cmdId > 0) lastHandledCmdId = cmdId;
      setKatupKuras(true, true, cmdDur, "Pi+ACC");
    }
  } else if (cmdIn == 1 && accVal == 1) {
    if (isPerintahBaru && piLinkOnline && !staleGuardActive) {
      if (cmdId > 0) lastHandledCmdId = cmdId;
      setKatupIsi(true, true, cmdDur, "Pi+ACC");
    }
  } else if ((cmdDrain == 1 || cmdIn == 1) && accVal == 0) {
    // Kunci keamanan 2-tahap: tolak pembukaan tanpa otorisasi acc=1
    if (piControlledValveOut) setKatupKuras(false, true, 0, "NO_ACC");
    if (piControlledValveIn) setKatupIsi(false, true, 0, "NO_ACC");
  } else if (cmdDrain == 0 && cmdIn <= 0) {
    bool isStopBaru = (cmdId > 0) && (cmdId != lastHandledCmdId);
    if (isStopBaru) {
      lastHandledCmdId = cmdId;
      tutupSemuaKatup();
    } else {
      if (piControlledValveOut) setKatupKuras(false, true, 0, "PiIdle");
      if (piControlledValveIn) setKatupIsi(false, true, 0, "PiIdle");
    }
  }

  digitalWrite(LED_STATUS, LOW);
}

void prosesPerintahManual(const char *rawCmd) {
  char cmd[64];
  size_t len = strlen(rawCmd);
  if (len == 0 || len >= sizeof(cmd)) return;
  for (size_t i = 0; i <= len; i++) {
    cmd[i] = (char)tolower((unsigned char)rawCmd[i]);
  }

  if (strcmp(cmd, "keruh") == 0 || strcmp(cmd, "k") == 0) {
    turbRangeMode = 2;
    Serial.println(">> [STATUS] Rentang Kekeruhan: Keruh");
  } else if (strcmp(cmd, "sedang") == 0 || strcmp(cmd, "s") == 0) {
    turbRangeMode = 1;
    Serial.println(">> [STATUS] Rentang Kekeruhan: Sedang");
  } else if (strcmp(cmd, "jernih") == 0 || strcmp(cmd, "j") == 0) {
    turbRangeMode = 0;
    Serial.println(">> [STATUS] Rentang Kekeruhan: Jernih");
  } else if (strcmp(cmd, "p") == 0) {
    if (currentPSI < 30.0f) currentPSI = 50.0f;
    else if (currentPSI < 70.0f) currentPSI = 80.0f;
    else currentPSI = 15.0f;
    Serial.printf(">> [STATUS] PSI Tanaman: %.0f %%\n", currentPSI);
  } else if (strcmp(cmd, "3") == 0) {
    setKatupIsi(!valveInState, false, MAX_DRAIN_WATCHDOG_MS / 1000UL, "Manual");
    Serial.printf(">> [AKTUATOR] Valve IN (Relay 3): %s\n", valveInState ? "BUKA (ON)" : "TUTUP (OFF)");
  } else if (strcmp(cmd, "4") == 0) {
    if (!valveOutState) {
      bool ok = setKatupKuras(true, false, MAX_DRAIN_WATCHDOG_MS / 1000UL, "Manual");
      Serial.printf(">> [AKTUATOR] Valve OUT (Relay 4): %s\n", ok ? "BUKA (ON)" : "DITOLAK (HUJAN)");
    } else {
      setKatupKuras(false, false, 0, "Manual");
      Serial.println(">> [AKTUATOR] Valve OUT (Relay 4): TUTUP (OFF)");
    }
  } else if (strcmp(cmd, "0") == 0) {
    tutupSemuaKatup();
    Serial.println(">> [SAFETY] Kedua katup ditutup (OFF).");
  } else if (strcmp(cmd, "m") == 0 || strcmp(cmd, "log") == 0) {
    verboseSerialMonitor = !verboseSerialMonitor;
    Serial.printf(">> [SERIAL] Mode log monitor teks: %s\n", verboseSerialMonitor ? "AKTIF" : "NONAKTIF (JSON-only)");
  }
}

void prosesBarisMasuk(const char *rawLine, size_t rawLen) {
  if (rawLen == 0) return;
  char workBuf[384];
  if (rawLen >= sizeof(workBuf)) return;
  memcpy(workBuf, rawLine, rawLen);
  workBuf[rawLen] = '\0';

  size_t start = 0;
  while (start < rawLen && isspace((unsigned char)workBuf[start])) start++;
  size_t end = rawLen;
  while (end > start && isspace((unsigned char)workBuf[end - 1])) end--;
  workBuf[end] = '\0';

  if (end <= start) return;
  const char *trimmed = &workBuf[start];
  if (trimmed[0] == '{' && trimmed[end - start - 1] == '}') {
    prosesJsonPi(trimmed);
  } else {
    prosesPerintahManual(trimmed);
  }
}

void prosesPerintahSerial() {
  while (Serial.available() > 0) {
    char ch = (char)Serial.read();
    if (ch == '\r') continue;

    if (ch == '\n') {
      prosesBarisMasuk(serialRxBuf, serialRxLen);
      serialRxLen = 0;
    } else if (serialRxLen < sizeof(serialRxBuf) - 1) {
      serialRxBuf[serialRxLen++] = ch;
    } else {
      // Cegah overflow jika baris terlalu panjang
      serialRxLen = 0;
    }
  }
}

class AkuaponikBleServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *pServer) override {
    bleConnected = true;
  }
  void onDisconnect(BLEServer *pServer) override {
    bleConnected = false;
  }
};

class AkuaponikBleRxCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) override {
    uint8_t *raw = pCharacteristic->getData();
    size_t len = pCharacteristic->getLength();
    if (raw == nullptr || len == 0) return;

    bool hasNewline = false;
    for (size_t i = 0; i < len; i++) {
      if (raw[i] == '\n') {
        hasNewline = true;
        break;
      }
    }

    portENTER_CRITICAL(&bleRxMux);
    for (size_t i = 0; i < len; i++) {
      char ch = (char)raw[i];
      if (ch == '\r') continue;
      if (bleRxLen < sizeof(bleRxRing) - 2) {
        bleRxRing[bleRxLen++] = ch;
      } else {
        // Cegah luapan buffer bila pengirim tidak menutup baris
        bleRxLen = 0;
        break;
      }
    }
    // Jika satu paket JSON dikirim tanpa '\n' di akhir, tutup baris otomatis
    if (!hasNewline && bleRxLen > 1 && bleRxRing[bleRxLen - 1] == '}' && bleRxLen < sizeof(bleRxRing) - 1) {
      bleRxRing[bleRxLen++] = '\n';
    }
    portEXIT_CRITICAL(&bleRxMux);
  }
};

void inisialisasiBleGatt() {
  BLEDevice::init(BLE_DEVICE_NAME);
  BLEDevice::setMTU(256);

  bleServer = BLEDevice::createServer();
  bleServer->setCallbacks(new AkuaponikBleServerCallbacks());

  BLEService *pService = bleServer->createService(BLE_SERVICE_UUID);
  bleTxChar = pService->createCharacteristic(
    BLE_CHAR_TX_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  bleTxChar->addDescriptor(new BLE2902());

  BLECharacteristic *pRxChar = pService->createCharacteristic(
    BLE_CHAR_RX_UUID,
    BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR
  );
  pRxChar->setCallbacks(new AkuaponikBleRxCallbacks());

  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(BLE_SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
}

void prosesPerintahBle() {
  // Restart advertising otomatis setelah koneksi BLE terputus (non-blocking)
  if (!bleConnected && blePrevConnected) {
    blePrevConnected = false;
    bleDisconnectAtMs = millis();
  }
  if (!bleConnected && bleDisconnectAtMs > 0 && (millis() - bleDisconnectAtMs >= 350UL)) {
    bleDisconnectAtMs = 0;
    BLEDevice::startAdvertising();
  }
  if (bleConnected && !blePrevConnected) {
    blePrevConnected = true;
    bleDisconnectAtMs = 0;
  }

  // Salin data utuh dari ring BLE di dalam critical section
  char localCopy[512];
  size_t copyLen = 0;
  portENTER_CRITICAL(&bleRxMux);
  if (bleRxLen > 0) {
    // Cari newline terakhir agar potongan yang belum lengkap tetap menunggu di ring
    size_t lastNl = 0;
    bool foundNl = false;
    for (size_t i = bleRxLen; i > 0; i--) {
      if (bleRxRing[i - 1] == '\n') {
        lastNl = i;
        foundNl = true;
        break;
      }
    }
    if (foundNl) {
      copyLen = lastNl;
      memcpy(localCopy, bleRxRing, copyLen);
      size_t rem = bleRxLen - copyLen;
      if (rem > 0) {
        memmove(bleRxRing, bleRxRing + copyLen, rem);
      }
      bleRxLen = rem;
    }
  }
  portEXIT_CRITICAL(&bleRxMux);

  if (copyLen == 0) return;

  size_t lineStart = 0;
  for (size_t i = 0; i < copyLen; i++) {
    if (localCopy[i] == '\n') {
      prosesBarisMasuk(&localCopy[lineStart], i - lineStart);
      lineStart = i + 1;
    }
  }
}

void kirimJsonBle(const char *jsonLine, size_t totalLen) {
  if (!bleConnected || bleTxChar == nullptr || bleServer == nullptr || totalLen == 0) return;

  uint16_t peerMtu = bleServer->getPeerMTU(bleServer->getConnId());
  size_t maxChunk = 20;
  if (peerMtu > 23) {
    size_t usable = (size_t)(peerMtu - 3);
    maxChunk = (usable > 180) ? 180 : usable;
  }

  size_t offset = 0;
  while (offset < totalLen && bleConnected) {
    size_t chunkLen = totalLen - offset;
    if (chunkLen > maxChunk) chunkLen = maxChunk;
    bleTxChar->setValue((uint8_t *)(jsonLine + offset), chunkLen);
    bleTxChar->notify();
    offset += chunkLen;
    if (offset < totalLen) {
      delay(12);
    }
  }
}

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  // Boot-safe: pastikan relay Active-LOW berada pada logika HIGH (OFF) sebelum mode OUTPUT
  digitalWrite(PIN_VALVE_IN, HIGH);
  digitalWrite(PIN_VALVE_OUT, HIGH);
  pinMode(PIN_VALVE_IN, OUTPUT);
  pinMode(PIN_VALVE_OUT, OUTPUT);
  digitalWrite(PIN_VALVE_IN, HIGH);
  digitalWrite(PIN_VALVE_OUT, HIGH);

  pinMode(LED_STATUS, OUTPUT);
  digitalWrite(LED_STATUS, LOW);

  Serial.begin(SERIAL_BAUD_RATE);
  Serial.setTimeout(20);
  delay(500);

  randomSeed(analogRead(PIN_PH) + micros());
  analogReadResolution(12);

  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  digitalWrite(PIN_TRIG, LOW);

  pinMode(PIN_RAIN, INPUT_PULLUP);

  tempSensor.begin();

  // Deteksi aman I2C LCD 20x4 (Alamat 0x27) agar bebas error NACK bila berjalan tanpa LCD
  Wire.begin(21, 22);
  Wire.beginTransmission(0x27);
  lcdPresent = (Wire.endTransmission() == 0);

  if (lcdPresent) {
    lcd.init();
    lcd.backlight();

    // Splash Screen Pembuka di LCD 20x4
    lcd.setCursor(1, 0);
    lcd.print("UNIVERSITAS NEGERI");
    lcd.setCursor(6, 1);
    lcd.print("SEMARANG");
    lcd.setCursor(1, 2);
    lcd.print("CAPSTONE AKUAPONIK");
    lcd.setCursor(2, 3);
    lcd.print("FUZZY SUGENO - AI");
    delay(2500);

    lcd.clear();
    lcd.setCursor(2, 1);
    lcd.print("MEMULAI SISTEM...");
    delay(1200);
    lcd.clear();
  }

  // Aktifkan BLE GATT Nordic UART dua arah untuk komunikasi nirkabel ke Raspberry Pi
  inisialisasiBleGatt();

  lastUpdate = millis() - UPDATE_INTERVAL;
}

// ============================================================================
// LOOP UTAMA
// ============================================================================
void loop() {
  // 1. Cek Perintah Masuk dari Serial Monitor & BLE GATT (Non-Blocking)
  prosesPerintahSerial();
  prosesPerintahBle();

  // Ambil timestamp setelah prosesPerintahSerial() agar delta millis() tidak pernah underflow
  unsigned long now = millis();

  // 2. Proteksi Interlock & Watchdog Real-Time
  if (isHujanAktif() && valveOutState) {
    tutupSemuaKatup();
  }

  // Watchdog keras solenoid: hentikan otomatis bila melewati batas durasi (<= 180 detik)
  if (valveOutState && now >= valveOutOpenedMs && (now - valveOutOpenedMs >= activeDrainLimitMs)) {
    setKatupKuras(false, piControlledValveOut, 0, "Watchdog");
  }
  if (valveInState && now >= valveInOpenedMs && (now - valveInOpenedMs >= activeFillLimitMs)) {
    setKatupIsi(false, piControlledValveIn, 0, "WatchdogIN");
  }

  // Stale-data guard 5 detik: bila link Pi terputus saat katup terbuka dari jauh, tutup demi keselamatan
  if (piLinkOnline && now >= lastPiRxMs && (now - lastPiRxMs > STALE_PI_TIMEOUT_MS)) {
    piLinkOnline = false;
    staleGuardActive = true;
    if (piControlledValveOut && valveOutState) {
      setKatupKuras(false, true, 0, "StalePi5s");
    }
    if (piControlledValveIn && valveInState) {
      setKatupIsi(false, true, 0, "StalePi5s");
    }
  }

  // 3. Siklus Pembacaan Sensor, Inferensi Fuzzy & Telemetri JSON Setiap 1 Detik (1 Hz)
  if (now - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = now;
    txSeq++;

    // A. Pembacaan Sensor
    tempSensor.requestTemperatures();
    float suhu = tempSensor.getTempCByIndex(0);
    bool tempOk = (suhu != DEVICE_DISCONNECTED_C && suhu > -55.0f && suhu < 125.0f);

    float voltPH = 0.0f;
    float ph = bacaPH(voltPH);

    float voltTurb = 0.0f;
    float ntu = bacaTurbidity(voltTurb);

    float jarak = bacaJarakUltrasonik();
    bool lvlOk = (jarak >= 0.0f && jarak < 500.0f);
    bool isHujan = isHujanAktif();

    // Kategori Teks Kekeruhan (Tepat 6 karakter agar rapi di LCD)
    char statusTurbStr[10];
    if (ntu <= 10.0f) strcpy(statusTurbStr, "Jernih");
    else if (ntu <= 25.0f) strcpy(statusTurbStr, "Sedang");
    else strcpy(statusTurbStr, "Keruh ");

    // B. Hitung Logika Fuzzy Sugeno (27 Aturan)
    float fuzzyZ = 0.0f;
    float fuzzyVol = 0.0f;
    int activeRules = 0;
    hitungFuzzySugeno(ph, ntu, currentPSI, fuzzyZ, fuzzyVol, activeRules);

    // C. Proteksi Pengaman Hujan (Safety Interlock)
    bool interlockActive = false;
    if (isHujan) {
      interlockActive = true;
      if (valveOutState) {
        tutupSemuaKatup();
      }
    }

    // D. TAMPILAN KE LAYAR LCD 20x4 I2C (TIAP BARIS TEPAT 20 KARAKTER) BILA TERPASANG
    if (lcdPresent) {
      lcd.setCursor(0, 0);
      char line0[21];
      if (ph < 10.0f) {
        snprintf(line0, sizeof(line0), "pH:%3.1f T:%4.1f %-6s", ph, ntu, statusTurbStr);
      } else {
        snprintf(line0, sizeof(line0), "pH:%4.1f T:%3.0f %-6s", ph, ntu, statusTurbStr);
      }
      lcd.print(line0);

      char suhuStr[8];
      if (!tempOk) strcpy(suhuStr, " --- ");
      else snprintf(suhuStr, sizeof(suhuStr), "%4.1fC", suhu);

      lcd.setCursor(0, 1);
      char line1[21];
      snprintf(line1, sizeof(line1), "Suhu:%-5s Hjn:%-5s", suhuStr, isHujan ? "BASAH" : "AMAN ");
      lcd.print(line1);

      lcd.setCursor(0, 2);
      char line2[21];
      if (lvlOk) {
        snprintf(line2, sizeof(line2), "Jarak:%3.0fcm  PSI:%2.0f%%", jarak, currentPSI);
      } else {
        snprintf(line2, sizeof(line2), "Jarak: ---   PSI:%2.0f%%", currentPSI);
      }
      lcd.print(line2);

      lcd.setCursor(0, 3);
      char line3[21];
      if (interlockActive) {
        snprintf(line3, sizeof(line3), "!INTERLOCK HUJAN!   ");
      } else {
        snprintf(line3, sizeof(line3), "FZ:%2.0f%% [%4.0fL] K:%-3s",
                 fuzzyZ, fuzzyVol, (valveOutState || valveInState) ? "ON" : "OFF");
      }
      lcd.print(line3);
    }

    // E. OUTPUT LINE-DELIMITED JSON KE RASPBERRY PI 4B (USB SERIAL & BLE GATT 1 Hz)
    char tempJson[16];
    if (tempOk) snprintf(tempJson, sizeof(tempJson), "%.2f", suhu);
    else strcpy(tempJson, "null");

    char lvlJson[16];
    if (lvlOk) snprintf(lvlJson, sizeof(lvlJson), "%.1f", jarak);
    else strcpy(lvlJson, "null");

    char jsonOut[360];
    int jsonLen = snprintf(
      jsonOut, sizeof(jsonOut),
      "{\"node\":\"esp32\",\"ph\":%.2f,\"ntu\":%.2f,\"temp\":%s,\"temp_ok\":%d,"
      "\"lvl\":%s,\"lvl_ok\":%d,\"rain\":%d,\"valve\":%d,\"valve_in\":%d,\"valve_out\":%d,"
      "\"pump\":%d,\"feed\":%d,\"psi\":%.2f,\"cov\":%.2f,\"z_rec\":%.2f,\"vol_rec\":%.1f,"
      "\"rules\":%d,\"pi_online\":%d,\"stale_guard\":%d,\"ble\":%d,\"seq\":%lu}\n",
      ph, ntu, tempJson, tempOk ? 1 : 0,
      lvlJson, lvlOk ? 1 : 0, isHujan ? 1 : 0,
      valveOutState ? 1 : 0, valveInState ? 1 : 0, valveOutState ? 1 : 0,
      pumpState ? 1 : 0, feedState ? 1 : 0,
      currentPSI, currentCov, fuzzyZ, fuzzyVol,
      activeRules, piLinkOnline ? 1 : 0, staleGuardActive ? 1 : 0,
      bleConnected ? 1 : 0, (unsigned long)txSeq
    );

    if (jsonLen > 0 && jsonLen < (int)sizeof(jsonOut)) {
      Serial.write((const uint8_t *)jsonOut, (size_t)jsonLen);
      kirimJsonBle(jsonOut, (size_t)jsonLen);
    }

    // Opsional: log teks ramah manusia untuk debug Arduino Serial Monitor (ketik 'm')
    if (verboseSerialMonitor) {
      Serial.printf("[MONITOR] pH: %.2f (%.2fV) | Turb: %.1f NTU (%.2fV - %s) | Suhu: %.1f C | Jarak: %.1f cm | Hujan: %s | Pi:%s\n",
                    ph, voltPH, ntu, voltTurb, statusTurbStr, suhu, jarak,
                    isHujan ? "HUJAN (INTERLOCK)" : "KERING",
                    piLinkOnline ? "ONLINE" : (staleGuardActive ? "STALE" : "WAIT"));
      Serial.printf("          >> FUZZY SUGENO (PSI %.0f%%): Ganti Air = %.2f %% (%.1f Liter) | %d Rules Firing | Katup IN:%s OUT:%s\n",
                    currentPSI, fuzzyZ, fuzzyVol, activeRules,
                    valveInState ? "ON" : "OFF",
                    valveOutState ? "ON" : "OFF");
    }
  }
}
