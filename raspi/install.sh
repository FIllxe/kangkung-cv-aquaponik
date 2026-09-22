#!/bin/bash
# ============================================================================
# INSTALL KANGKUNG LIVE MONITOR — Raspberry Pi (jalankan sekali)
#
# MODE A (dari repo clone):
#   git clone https://github.com/<USER>/kangkung-cv-aquaponik.git ~/src
#   cd ~/src/raspi && bash install.sh
#   → paket otomatis di-copy ke ~/kangkung_pi lalu di-setup
#
# MODE B (folder ~/kangkung_pi sudah ada / hasil SCP):
#   cd ~/kangkung_pi && bash install.sh
# ============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET_DIR="$HOME/kangkung_pi"

if [ "$SCRIPT_DIR" != "$TARGET_DIR" ]; then
    echo "[0/5] Copy paket dari repo -> $TARGET_DIR ..."
    mkdir -p "$TARGET_DIR"
    cp -r "$SCRIPT_DIR"/. "$TARGET_DIR"/
    rm -rf "$TARGET_DIR/.git"
    cd "$TARGET_DIR"
fi

echo "[1/5] Update apt + dependensi sistem (opencv, video)..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip libatlas-base-base libjasper1 2>/dev/null || true
sudo apt-get install -y -qq libatlas-base-dev || true

echo "[2/5] Virtual environment + paket Python..."
cd "$TARGET_DIR"
python3 -m venv venv
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements-pi.txt -q

echo "[3/5] Cek service-account Firebase..."
if [ ! -f service-account.json ]; then
    cp service-account.json.EXAMPLE service-account.json
    echo "  >>> PENTING: isi service-account.json (kredensial Firebase Console)."
    echo "  >>> Monitor tetap bisa jalan lokal (mode offline) sampai diisi."
fi

echo "[4/5] Pasang systemd service (auto-start + auto-restart)..."
sudo cp service/kangkung.service /etc/systemd/system/
WORKDIR="$TARGET_DIR"
sudo sed -i "s|/home/pi/kangkung_pi|$WORKDIR|g" /etc/systemd/system/kangkung.service
sudo sed -i "s|User=pi|User=$USER|g" /etc/systemd/system/kangkung.service
sudo systemctl daemon-reload
sudo systemctl enable kangkung

echo "[5/5] Selesai!"
echo "  Mulai monitor : sudo systemctl start kangkung"
echo "  Cek log       : journalctl -u kangkung -f"
echo "  Stop          : sudo systemctl stop kangkung"
