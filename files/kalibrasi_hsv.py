"""
=============================================================================
  TOOL KALIBRASI HSV — Kangkung Aquaponik
  Jalankan ini untuk menyesuaikan threshold warna hijau dengan kondisi
  pencahayaan dan kamera spesifik Anda.
=============================================================================
  Cara pakai:
    python kalibrasi_hsv.py gambar_kangkung.jpg
    python kalibrasi_hsv.py 0          ← kamera index 0
=============================================================================
"""

import cv2
import numpy as np
import sys

# Parameter default (sama dengan kangkung_cv.py)
params = {
    "H_lo": 35, "H_hi": 85,
    "S_lo": 40, "S_hi": 255,
    "V_lo": 40, "V_hi": 255,
}


def nothing(x):
    pass


def kalibrasi(source):
    # Load gambar
    if isinstance(source, int):
        cap = cv2.VideoCapture(source)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print("[ERROR] Tidak bisa akses kamera"); return
    else:
        frame = cv2.imread(source)
        if frame is None:
            print(f"[ERROR] File tidak ditemukan: {source}"); return

    frame = cv2.resize(frame, (800, 480))
    hsv   = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    win = "Kalibrasi HSV — Kangkung"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, 900, 600)

    # Trackbars
    cv2.createTrackbar("H Min", win, params["H_lo"], 179, nothing)
    cv2.createTrackbar("H Max", win, params["H_hi"], 179, nothing)
    cv2.createTrackbar("S Min", win, params["S_lo"], 255, nothing)
    cv2.createTrackbar("S Max", win, params["S_hi"], 255, nothing)
    cv2.createTrackbar("V Min", win, params["V_lo"], 255, nothing)
    cv2.createTrackbar("V Max", win, params["V_hi"], 255, nothing)

    print("[INFO] Geser slider untuk menyesuaikan threshold.")
    print("[INFO] Tekan 'S' untuk simpan ke kangkung_cv.py — tekan 'Q' untuk keluar.")

    while True:
        h_lo = cv2.getTrackbarPos("H Min", win)
        h_hi = cv2.getTrackbarPos("H Max", win)
        s_lo = cv2.getTrackbarPos("S Min", win)
        s_hi = cv2.getTrackbarPos("S Max", win)
        v_lo = cv2.getTrackbarPos("V Min", win)
        v_hi = cv2.getTrackbarPos("V Max", win)

        lower = np.array([h_lo, s_lo, v_lo])
        upper = np.array([h_hi, s_hi, v_hi])

        mask   = cv2.inRange(hsv, lower, upper)
        result = cv2.bitwise_and(frame, frame, mask=mask)

        combined = np.hstack([frame, result])
        info = (f"H:[{h_lo}-{h_hi}]  S:[{s_lo}-{s_hi}]  V:[{v_lo}-{v_hi}]  "
                f"Coverage: {mask.sum()/255/mask.size*100:.1f}%")
        cv2.putText(combined, info, (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
        cv2.imshow(win, combined)

        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            print(f"\n[HASIL KALIBRASI]")
            print(f'  "lower": np.array([{h_lo}, {s_lo}, {v_lo}]),')
            print(f'  "upper": np.array([{h_hi}, {s_hi}, {v_hi}]),')
            print("[INFO] Salin nilai di atas ke HSV_KANGKUNG di kangkung_cv.py")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else None
    if src is None:
        print("[ERROR] Berikan path gambar atau index kamera!")
        print("  Contoh: python kalibrasi_hsv.py foto_bed.jpg")
        sys.exit(1)
    try:
        src = int(src)
    except ValueError:
        pass
    kalibrasi(src)
