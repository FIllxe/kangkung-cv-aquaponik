#!/usr/bin/env python3
"""
UJI FOTO KE WEBSITE — Memproses foto dataset (HP/kamera) dan mengirimnya
langsung ke Firestore agar tampil secara realtime di dashboard website.

Cara pakai:
  python files/uji_foto_ke_website.py                          # default: Image_6islrm6islrm6isl.png (uji stres PSI)
  python files/uji_foto_ke_website.py --gambar dataset1/bed_05_mixed.jpg
  python files/uji_foto_ke_website.py --gambar "docs/images/Situasi 1.jpg"
  python files/uji_foto_ke_website.py --daftar                 # tampilkan daftar gambar yang bisa diuji
"""
import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

# Pastikan UTF-8 di Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "raspi"))
sys.path.insert(0, str(ROOT / "raspi" / "modules"))

from adaptive_bed import (deteksi_sudut_bed, CornerSmoother, matriks_warp,
                          warp_bed, mask_tanaman_warna)
from kangkung_cv import BED_CONFIG, get_status, get_kesehatan, PSI_VERSION
from fuzzy_export import hitung_fuzzy
import firebase_admin
from firebase_admin import credentials, firestore

SA_PATH = ROOT / "web" / "ecofarm-399c9-firebase-adminsdk-fbsvc-fa9b3d7da6.json"
COLLECTION_NAME = "bed_readings"


def init_firebase():
    if not SA_PATH.exists():
        raise FileNotFoundError(f"Service account tidak ditemukan di {SA_PATH}")
    if not firebase_admin._apps:
        cred = credentials.Certificate(str(SA_PATH))
        firebase_admin.initialize_app(cred)
    return firestore.client()


def proses_gambar(img_path):
    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"Gagal membaca gambar dari {img_path}")

    H, W = img.shape[:2]
    # Jika sudah kanvas 1200x660, gunakan langsung; jika belum, deteksi sudut atau warp
    if W == 1200 and H == 660:
        warped = img
    else:
        pts = deteksi_sudut_bed(img)
        if pts is None:
            print(f"[INFO] Bed quad tidak terdeteksi otomatis pada {img_path.name}, menggunakan full-frame.")
            pts = np.float32([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]])
        warped = warp_bed(img, matriks_warp(pts))

    masks = mask_tanaman_warna(warped)
    rows, cols = BED_CONFIG["grid_rows"], BED_CONFIG["grid_cols"]
    H_w, W_w = warped.shape[:2]
    ch, cw = H_w // rows, W_w // cols

    zona, covs, kuns, coks, st_kes = {}, [], [], [], []
    piksel = []

    for r in range(rows):
        for c in range(cols):
            y1, y2 = r * ch, (r + 1) * ch if r < rows - 1 else H_w
            x1, x2 = c * cw, (c + 1) * cw if c < cols - 1 else W_w
            h = int(masks["hijau"][y1:y2, x1:x2].sum()) // 255
            t = int(masks["tanaman"][y1:y2, x1:x2].sum()) // 255
            k = int(masks["kuning"][y1:y2, x1:x2].sum()) // 255
            b = int(masks["coklat"][y1:y2, x1:x2].sum()) // 255
            cov = h / (cw * ch) * 100
            pk = k / t * 100 if t else 0.0
            pc = b / t * 100 if t else 0.0
            kes = get_kesehatan(pk, pc)
            st = get_status(cov)

            zkey = f"R{r+1}C{c+1}"
            zona[zkey] = {
                "coverage": round(cov, 2),
                "status": st,
                "pct_kuning": round(pk, 2),
                "pct_coklat": round(pc, 2),
                "kesehatan": kes,
            }
            covs.append(cov)
            kuns.append(pk)
            coks.append(pc)
            st_kes.append(kes)

            k_zona = masks["kuning"][y1:y2, x1:x2]
            b_zona = masks["coklat"][y1:y2, x1:x2]
            h_zona = masks["hijau"][y1:y2, x1:x2]
            k_bukan_b = int(cv2.bitwise_and(k_zona, cv2.bitwise_not(b_zona)).sum()) // 255
            h_bukan_kb = int(cv2.bitwise_and(h_zona, cv2.bitwise_not(cv2.bitwise_or(k_zona, b_zona))).sum()) // 255
            piksel.append({
                "green": h_bukan_kb,
                "yellow": k_bukan_b,
                "brown": b,
                "plant_mask": t,
                "unclassified": max(0, t - (h_bukan_kb + k_bukan_b + b)),
            })

    dist = {"belum_siap": 0, "hampir_siap": 0, "siap_panen": 0, "harus_panen": 0}
    for z in zona.values():
        dist[z["status"]] += 1
    siap = dist["siap_panen"] + dist["harus_panen"]

    # Buat snapshot kanvas anotasi
    disp = warped.copy()
    overlay = disp.copy()
    for r in range(rows):
        for c in range(cols):
            y1, y2 = r * ch, (r + 1) * ch if r < rows - 1 else H_w
            x1, x2 = c * cw, (c + 1) * cw if c < cols - 1 else W_w
            z = zona[f"R{r+1}C{c+1}"]
            warna = {"belum_siap": (51, 152, 255),
                     "hampir_siap": (18, 156, 243),
                     "siap_panen": (113, 204, 46),
                     "harus_panen": (60, 76, 231)}[z["status"]]
            cv2.rectangle(overlay, (x1, y1), (x2, y2), warna, -1)
            cv2.rectangle(disp, (x1, y1), (x2, y2), warna, 2)
            cv2.putText(disp, f"{z['coverage']:.0f}%", (x1 + 4, y1 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    disp = cv2.addWeighted(disp, 0.75, overlay, 0.25, 0)
    cov_m = float(np.mean(covs))
    kun_m = float(np.mean(kuns))
    cok_m = float(np.mean(coks))
    cv2.putText(disp, f"Cov:{cov_m:.0f}% Kun:{kun_m:.1f}% Cok:{cok_m:.1f}%",
                (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 255, 150), 2)
    cv2.putText(disp, f"TEST: {img_path.name} | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                (12, disp.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    # Simpan juga file snapshot statis di folder web agar bisa langsung diakses
    web_snap_path = ROOT / "web" / "latest_snapshot.jpg"
    cv2.imwrite(str(web_snap_path), disp)

    # Encode snapshot thumbnail (maks lebar 480 untuk payload Firestore)
    th_h, th_w = disp.shape[:2]
    th_img = cv2.resize(disp, (480, int(th_h * 480 / th_w)))
    _, buf = cv2.imencode(".jpg", th_img, [cv2.IMWRITE_JPEG_QUALITY, 60])
    b64_snap = base64.b64encode(buf.tobytes()).decode("ascii")

    dt = datetime.now()
    captured_ms = int(dt.timestamp() * 1000)
    did = f"test_{img_path.stem}_{dt.strftime('%Y%m%dT%H%M%S')}"

    fuzzy = hitung_fuzzy(piksel, [z["kesehatan"] for z in zona.values()],
                         captured_at_ms=captured_ms, frame_id=did)

    # Buat rekomendasi cerdas
    psi_val = fuzzy.get("psi")
    if psi_val is not None:
        if psi_val > 30.0:
            reko = f"PERINGATAN STRES BERAT (PSI={psi_val:.1f}): Klorosis/nekrosis tinggi. Segera periksa nutrisi dan sirkulasi air."
        elif psi_val > 15.0:
            reko = f"WASPADA STRES SEDANG (PSI={psi_val:.1f}): Daun mulai menguning. Periksa kejernihan dan pH air."
        else:
            reko = f"KONDISI PRIMA (PSI={psi_val:.1f}): Tanaman sehat. Pertahankan nutrisi dan debit pompa normal."
    else:
        reko = "Data tanaman sedang dianalisis."

    payload = {
        "device_id": "test-dataset",
        "timestamp": dt.isoformat(timespec="seconds") + "+07:00",
        "doc_id": did,
        "frame_id": did,
        "captured_at_ms": captured_ms,
        "mode": "TEST-FOTO",
        "coverage_rata": round(cov_m, 2),
        "coverage_std": round(float(np.std(covs)), 2),
        "zona_siap_panen": siap,
        "persen_siap": round(siap / len(zona) * 100, 1),
        "status_distribusi": dist,
        "kesehatan": {
            "kuning_rata": round(kun_m, 2),
            "coklat_rata": round(cok_m, 2),
            "distribusi": {s: st_kes.count(s) for s in ("sehat", "waspada", "sakit")},
        },
        "fuzzy_input": fuzzy,
        "rekomendasi": reko,
        "zona": zona,
        "snapshot_url": f"data:image/jpeg;base64,{b64_snap}",
        "suhu_pi_c": 45.0,
    }

    return payload, did


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gambar", default="dataset1/Image_6islrm6islrm6isl.png",
                        help="Path ke file gambar yang ingin diuji")
    parser.add_argument("--daftar", action="store_true",
                        help="Tampilkan daftar gambar yang tersedia untuk uji")
    args = parser.parse_args()

    if args.daftar:
        print("\nDaftar foto yang tersedia untuk pengujian:")
        paths = list(ROOT.glob("dataset1/*.*")) + list(ROOT.glob("docs/images/*.jpg")) + list(ROOT.glob("output/dummy/*.png"))
        for p in paths:
            if p.suffix.lower() in [".jpg", ".png", ".jpeg"]:
                print(f"  - {p.relative_to(ROOT)}")
        return

    img_path = ROOT / args.gambar
    if not img_path.exists():
        print(f"[ERROR] File {img_path} tidak ditemukan!")
        sys.exit(1)

    print(f"\n[1/3] Membaca dan menganalisis gambar: {args.gambar}...")
    payload, did = proses_gambar(img_path)

    fuzz = payload["fuzzy_input"]
    print("\n--- HASIL ANALISIS COMPUTER VISION & PSI ---")
    print(f"  ID Dokumen         : {did}")
    print(f"  Coverage Rata-rata : {payload['coverage_rata']}% (Siap Panen: {payload['zona_siap_panen']}/24 zona)")
    print(f"  Indeks Stres (PSI) : {fuzz.get('psi')} / 100 (v{fuzz.get('psi_versi')})")
    print(f"  PSI Maks (Zona)    : {fuzz.get('psi_maks')}")
    print(f"  Kuning (Klorosis)  : {fuzz.get('kuning_pct')}%")
    print(f"  Coklat (Nekrosis)  : {fuzz.get('coklat_pct')}%")
    print(f"  Zona Sakit         : {fuzz.get('zona_sakit')} zona")
    print(f"  Indeks Sehat       : {fuzz.get('indeks_sehat')} / 100")
    print(f"  Rekomendasi        : {payload['rekomendasi']}")

    print("\n[2/3] Menghubungkan ke Firestore...")
    db = init_firebase()

    print(f"[3/3] Mengirim payload ke Firestore koleksi '{COLLECTION_NAME}'...")
    db.collection(COLLECTION_NAME).document(did).set(payload)
    print("\n[BERHASIL] Data uji coba berhasil dikirim ke website!")
    print("Silakan buka browser di: http://localhost:8080 (Tab 'Live Monitoring')")
    print("Dashboard akan langsung menampilkan peta zona, foto snapshot, dan nilai PSI baru secara realtime!\n")


if __name__ == "__main__":
    main()
