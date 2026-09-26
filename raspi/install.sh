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

echo "[1/5] Update apt + dependensi sistem (libcamera/picamera2, video)..."
sudo apt-get update -qq
# Picamera2 + libcamera WAJIB untuk kamera CSI (OpenCV tak bisa baca /dev/video0
# pada kernel Pi modern). Hanya tersedia sebagai paket sistem, bukan lewat pip.
sudo apt-get install -y -qq python3-venv python3-pip python3-picamera2 \
    python3-libcamera python3-simplejpeg 2>/dev/null || true
sudo apt-get install -y -qq libatlas-base-dev || true

echo "[2/5] Virtual environment + paket Python..."
cd "$TARGET_DIR"
# --system-site-packages: agar venv bisa meng-import picamera2/libcamera
# yang dipasang apt di atas, sementara opencv/numpy/firebase dari pip menang.
python3 -m venv --system-site-packages venv
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
sudo cp service/kangkung-camera.service /etc/systemd/system/
sudo sed -i "s|/home/pi/kangkung_pi|$WORKDIR|g" /etc/systemd/system/kangkung-camera.service
sudo sed -i "s|User=pi|User=$USER|g" /etc/systemd/system/kangkung-camera.service
# Preview tidak di-enable: kamera CSI eksklusif dengan monitor periodik.
# Mulai manual saat dibutuhkan agar kangkung.service dan camera tidak berebut.
sudo systemctl daemon-reload
sudo systemctl enable kangkung

echo "[5/5] Selesai!"
echo "  Mulai monitor : sudo systemctl start kangkung"
echo "  Cek log       : journalctl -u kangkung -f"
echo "  Stop          : sudo systemctl stop kangkung"
echo "  Live camera   : sudo systemctl start kangkung-camera"
