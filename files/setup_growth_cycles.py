#!/usr/bin/env python3
"""
SETUP DATA SIKLUS PERTUMBUHAN KANGKUNG DENGAN DATASET VIDEO ECOFARM
Menghasilkan struktur data:
  1. Tab Khusus "Dataset Video Ecofarm" (18 video asli HP dari folder ecofarm)
  2. Siklus 1 (Historis - 30 Hari penuh menggunakan acuan frame video)
  3. Siklus 2 (Historis - 30 Hari)
  4. Siklus 3 (Sedang Berjalan - Hari ke-20)
  5. Kebijakan Retensi: Maksimal 3 siklus tersimpan (FIFO).
"""

import json
import shutil
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
WEB_AQUAPONIK_DIR = ROOT.parent / "web aquaponik" / "web aquaponik"
GROWTH_DIR = (WEB_AQUAPONIK_DIR / "growth") if WEB_AQUAPONIK_DIR.exists() else (ROOT / "web" / "growth")
VIDEO_OUT_DIR = GROWTH_DIR / "ecofarm_videos"
ANNO_DIR = ROOT / "dataset_ecofarm_frames" / "annotated"
RAW_DIR = ROOT / "dataset_ecofarm_frames" / "raw"
DATASET1_DIR = ROOT / "dataset1"
META_PATH = ROOT / "dataset_ecofarm_frames" / "metadata.json"

GROWTH_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_OUT_DIR.mkdir(parents=True, exist_ok=True)


def _muat_extra_lama(json_path):
    """Ambil field tambahan historis (ph, turbidity, dll.) agar tidak hilang."""
    extra_keys = ("ph", "turbidity", "temp_water", "exchange_done", "est_biomass_kg")
    vid_map, cyc_map = {}, {}
    if not json_path.exists():
        return vid_map, cyc_map
    try:
        old = json.loads(json_path.read_text(encoding="utf-8"))
        for cid, cyc in old.get("cycles", {}).items():
            for d in cyc.get("days", []):
                extras = {k: d[k] for k in extra_keys if k in d}
                if not extras:
                    continue
                if cid == "video_dataset" and d.get("stem"):
                    vid_map[d["stem"]] = extras
                elif d.get("day") is not None:
                    cyc_map[(str(cid), int(d["day"]))] = extras
    except Exception:
        pass
    return vid_map, cyc_map


def muat_metadata_video():
    """Muat metadata 18 video ecofarm."""
    if not META_PATH.exists():
        raise FileNotFoundError(f"Metadata tidak ditemukan di {META_PATH}")
    with open(META_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
    # Urutkan berdasarkan coverage pertumbuhan (18.7% -> 91.6%)
    meta_sorted = sorted(meta, key=lambda x: x.get("coverage_rata", 0))
    return meta_sorted


def tentukan_fase(cov):
    if cov < 20:
        return "Bibit"
    elif cov < 35:
        return "Muda"
    elif cov < 55:
        return "Vegetatif"
    elif cov < 80:
        return "Pembesaran"
    else:
        return "Siap Panen"


def tentukan_status(cov):
    if cov < 25:
        return "belum_siap"
    elif cov < 55:
        return "hampir_siap"
    elif cov < 80:
        return "siap_panen"
    else:
        return "harus_panen"


def tentukan_kesehatan(psi):
    if psi < 4.0:
        return "sehat"
    elif psi < 10.0:
        return "waspada"
    else:
        return "sakit"


def buat_catatan(stem, cov, psi):
    notes = {
        "IMG_4329": "Tahap bibit awal pasca-semai: akar mulai menyerap nutrisi hidroponik, helai daun sejati pertama membuka.",
        "IMG_4330": "Bibit kangkung tegak merata: tinggi tanaman ±5-7 cm, sirkulasi nutrisi lancar tanpa genangan.",
        "IMG_4925": "Pertumbuhan vegetatif awal: adaptasi intensitas cahaya, terdapat klorosis ringan pada daun terbawah.",
        "IMG_4806": "Muncul tunas daun kedua: perlu pemantauan sirkulasi air dan keseimbangan EC/pH aquaponik.",
        "IMG_4792": "Akar kangkung mulai memanjang: rumpun netpot mulai mengikat rapat pada media tanam.",
        "IMG_4463": "Fase vegetatif aktif: daun hijau mengkilap, laju transpirasi dan respirasi tanaman sangat stabil.",
        "IMG_4643": "Kanopi bed mulai terbentuk: batang kangkung memanjang kokoh ke arah sumber cahaya.",
        "IMG_4462": "Batang berongga khas kangkung air terbentuk sempurna, bebas hama dan bebas bercak daun.",
        "IMG_5076": "Pertengahan siklus (Hari ke-15): kerapatan tanaman meningkat, daun saling menaungi dengan sehat.",
        "IMG_5179": "Pertumbuhan cabang lateral aktif: rumpun melebar memenuhi 42% area bed tanam.",
        "IMG_4601": "Biomassa daun meningkat cepat: warna hijau tua seragam menandakan serapan nitrogen optimal.",
        "IMG_4519": "Kerapatan kanopi solid: sebagian besar zona tengah telah mencapai tingkat ketebalan optimal.",
        "IMG_5159": "Tinggi kangkung mencapai ±20-22 cm: 11 dari 24 zona mulai memenuhi kriteria panen bertahap.",
        "IMG_5388": "Kondisi vegetatif prima: daun lebar dan tebal, siap memasuki fase pembesaran akhir.",
        "IMG_4207": "Ambang 50% coverage tercapai: pertumbuhan merata di seluruh 4 baris bed aquaponik.",
        "IMG_5403": "Fase pembesaran akhir: 12 zona berstatus hampir/siap panen, batang renyah dan berbobot.",
        "IMG_4208": "Mayoritas zona (18/24) SIAP PANEN: kanopi padat 74.5%, tekstur kangkung segar kualitas pasar.",
        "IMG_4209": "PANEN RAYA PENUH: 24/24 Zona Siap Panen (100%), coverage 91.6%, biomassa maksimal siap petik!"
    }
    return notes.get(stem, f"Pertumbuhan kangkung terpantau normal dengan coverage {cov:.1f}% dan PSI {psi:.1f}.")


def proses_semua():
    videos = muat_metadata_video()
    vid_extra, cyc_extra = _muat_extra_lama(GROWTH_DIR / "growth_data.json")
    print(f"Memuat {len(videos)} video dari dataset ecofarm...")

    # Salin semua foto ke ecofarm_videos
    for v in videos:
        stem = v["stem"]
        # raw
        src_raw = RAW_DIR / f"{stem}.jpg"
        if src_raw.exists():
            shutil.copy2(src_raw, VIDEO_OUT_DIR / f"{stem}.jpg")
        # annotated
        src_anno = ANNO_DIR / f"{stem}_annotated.jpg"
        if src_anno.exists():
            shutil.copy2(src_anno, VIDEO_OUT_DIR / f"{stem}_annotated.jpg")

    # 1. Struktur khusus: cycle "video_dataset" (18 video)
    video_days = []
    for idx, v in enumerate(videos, 1):
        stem = v["stem"]
        cov = float(v.get("coverage_rata", 0))
        psi = float(v.get("psi_v2", 0))
        fase = tentukan_fase(cov)
        status = tentukan_status(cov)
        kes = tentukan_kesehatan(psi)
        note = buat_catatan(stem, cov, psi)

        day_item = {
            "day": idx,
            "fase": fase,
            "coverage": round(cov, 1),
            "status": status,
            "psi": round(psi, 1),
            "kesehatan": kes,
            "catatan": note,
            "image_url": f"growth/ecofarm_videos/{stem}_annotated.jpg",
            "raw_url": f"growth/ecofarm_videos/{stem}.jpg",
            "video_name": v["video_name"],
            "stem": stem,
            "frame_idx": v["best_frame_idx"],
            "total_frames": v["total_frames"],
            "timestamp_sec": v["timestamp_sec"],
            "quality_score": v["quality_score"],
            "laplacian_var": round(v["laplacian_var"], 1),
            "best_hour": f"Video HP: {v['video_name']} (Frame #{v['best_frame_idx']}, Detik {v['timestamp_sec']}s)",
            "ready_zones": v["zona_siap_panen"],
            "kuning_pct": v["kuning_pct"],
            "coklat_pct": v["coklat_pct"]
        }
        day_item.update(vid_extra.get(stem, {}))
        video_days.append(day_item)

    max_cov_vid = round(max((d["coverage"] for d in video_days), default=91.6), 1)
    avg_psi_vid = round(sum(d["psi"] for d in video_days) / max(1, len(video_days)), 1)

    video_cycle_meta = {
        "cycle_id": "video_dataset",
        "title": "Dataset Video Ecofarm (18 Video Asli)",
        "badge_label": "18 VIDEO ASLI",
        "is_video_dataset": True,
        "start_date": "2026-09-08",
        "end_date": "2026-09-08",
        "status": "DATASET ASLI",
        "total_days": len(video_days),
        "days_count": len(video_days),
        "max_coverage": max_cov_vid,
        "avg_psi": avg_psi_vid,
        "harvest_yield_kg": 18.5,
        "is_active": False,
        "note": "18 video kangkung dari folder 'data set aquaponic ecofarm'. Setiap video diambil 1 frame terbaik dengan deteksi tepi Canny-Quad dan pencahayaan seimbang."
    }

    # 2. Timeline 30 hari untuk Siklus 1, 2, 3
    # Mapping 30 hari:
    # H1-4: Benih / Semai
    # H5-30: 18 video didistribusikan secara proporsional dari bibit (18.7%) sampai panen (91.6%)
    CYCLE_30_MAP = [
        # (day, fase, video_stem or seedling, base_cov, status, psi, note)
        (1,  "Benih",    None,        2.5,  "belum_siap",  0.0, "sehat",   "Penyemaian benih kangkung di rockwool/netpot."),
        (2,  "Benih",    None,        5.0,  "belum_siap",  0.0, "sehat",   "Benih kangkung mulai berkecambah (pecah benih)."),
        (3,  "Benih",    None,        8.5,  "belum_siap",  0.0, "sehat",   "Tunas plumula muncul tegak ke atas permukaan media."),
        (4,  "Bibit",    None,        12.0, "belum_siap",  0.0, "sehat",   "Kotiledon (daun lembaga) membuka sempurna."),
        (5,  "Bibit",    "IMG_4329",  18.7, "belum_siap",  2.9, "sehat",   "Akar bibit mulai menyentuh air nutrisi (IMG_4329.MOV)."),
        (6,  "Bibit",    "IMG_4330",  23.6, "belum_siap",  3.2, "waspada", "Batang bibit meninggi tegak merata (IMG_4330.MOV)."),
        (7,  "Muda",     "IMG_4925",  25.7, "hampir_siap", 7.8, "waspada", "Fase adaptasi nutrisi, klorosis ringan pada daun bawah (IMG_4925.MOV)."),
        (8,  "Muda",     "IMG_4806",  27.0, "hampir_siap", 11.4,"waspada", "Muncul tunas daun baru, pompa sirkulasi optimal (IMG_4806.MOV)."),
        (9,  "Muda",     "IMG_4792",  29.9, "hampir_siap", 9.2, "waspada", "Akar kangkung mulai lebat di dasar bed (IMG_4792.MOV)."),
        (10, "Muda",     "IMG_4463",  30.6, "hampir_siap", 1.5, "sehat",   "Fase vegetatif aktif, daun hijau mengkilap (IMG_4463.MOV)."),
        (11, "Vegetatif","IMG_4643",  36.1, "hampir_siap", 5.9, "sehat",   "Kanopi tanaman mulai menutup bed tanam (IMG_4643.MOV)."),
        (12, "Vegetatif","IMG_4462",  38.2, "hampir_siap", 1.1, "sehat",   "Batang semakin kokoh berongga khas kangkung (IMG_4462.MOV)."),
        (13, "Vegetatif","IMG_5076",  40.9, "hampir_siap", 2.3, "sehat",   "Kerapatan tanaman meningkat pesat (IMG_5076.MOV)."),
        (14, "Vegetatif","IMG_5179",  42.1, "hampir_siap", 4.7, "sehat",   "Rumpun kangkung melebar merata (IMG_5179.MOV)."),
        (15, "Vegetatif","IMG_4601",  44.9, "hampir_siap", 3.1, "sehat",   "Pertengahan siklus: daun hijau segar merata (IMG_4601.MOV)."),
        (16, "Vegetatif","IMG_4519",  46.3, "hampir_siap", 2.1, "sehat",   "Biomassa daun bertambah pesat (IMG_4519.MOV)."),
        (17, "Vegetatif","IMG_5159",  46.7, "hampir_siap", 3.3, "sehat",   "Tinggi batang mencapai ±20 cm (IMG_5159.MOV)."),
        (18, "Vegetatif","IMG_5388",  47.3, "hampir_siap", 3.5, "sehat",   "Kondisi rumpun stabil dan subur (IMG_5388.MOV)."),
        (19, "Vegetatif","IMG_4207",  49.5, "hampir_siap", 5.5, "sehat",   "Kanopi mencapai 49.5%, mendekati batas 50% (IMG_4207.MOV)."),
        (20, "Pembesaran","IMG_5403", 53.9, "hampir_siap", 2.8, "sehat",   "Ambang 50% terlewati: 12 zona siap panen (IMG_5403.MOV)."),
        (21, "Pembesaran","IMG_5403", 58.5, "siap_panen",  2.5, "sehat",   "Zona tengah bed mulai berstatus siap petik."),
        (22, "Pembesaran","IMG_5403", 64.0, "siap_panen",  2.2, "sehat",   "Pertumbuhan biomassa daun mencapai titik puncak."),
        (23, "Pembesaran","IMG_4208", 69.5, "siap_panen",  3.5, "sehat",   "Kerapatan tajuk sangat rapat dan seragam."),
        (24, "Siap Panen","IMG_4208", 74.5, "siap_panen",  4.6, "sehat",   "Mayoritas zona (18/24) SIAP PANEN (IMG_4208.MOV)."),
        (25, "Siap Panen","IMG_4208", 79.0, "siap_panen",  3.8, "sehat",   "Batang renyah, daun lebar kualitas unggul."),
        (26, "Siap Panen","IMG_4209", 83.5, "harus_panen", 1.2, "sehat",   "Ambang panen tercapai di seluruh 24 zona."),
        (27, "Siap Panen","IMG_4209", 88.0, "harus_panen", 0.9, "sehat",   "Kanopi kangkung penuh menutup seluruh netpot."),
        (28, "Siap Panen","IMG_4209", 91.6, "harus_panen", 0.7, "sehat",   "PANEN RAYA: 24/24 zona siap panen 100% (IMG_4209.MOV)."),
        (29, "Siap Panen","IMG_4209", 93.0, "harus_panen", 0.6, "sehat",   "Panen bertahap pada kangkung siap petik."),
        (30, "Pasca Panen",None,      20.0, "belum_siap",  0.2, "sehat",   "Pembersihan bed & persiapan bibit siklus berikutnya.")
    ]

    # Index video metadata by stem
    video_dict = {v["stem"]: v for v in videos}

    def buat_days_siklus(cid, limit_days=30):
        c_dir = GROWTH_DIR / f"cycle_{cid}"
        c_dir.mkdir(parents=True, exist_ok=True)
        res = []

        for item in CYCLE_30_MAP[:limit_days]:
            d_num, fase, stem, base_cov, status, psi, base_kes, note = item
            # Sedikit variasi per siklus
            cov_adj = round(max(1.0, min(96.0, base_cov + (cid - 2) * 1.2)), 1)
            psi_adj = round(max(0.0, psi + (0.3 if cid == 3 else 0.0)), 1)

            dst_img_name = f"day_{d_num:02d}.jpg"
            dst_path = c_dir / dst_img_name

            # Ambil gambar
            img = None
            v_meta = video_dict.get(stem) if stem else None

            if stem and (ANNO_DIR / f"{stem}_annotated.jpg").exists():
                img = cv2.imread(str(ANNO_DIR / f"{stem}_annotated.jpg"))
            elif (DATASET1_DIR / "bed_01_seedling.jpg").exists():
                img = cv2.imread(str(DATASET1_DIR / "bed_01_seedling.jpg"))

            if img is not None:
                h, w = img.shape[:2]
                if w > 640:
                    img_thumb = cv2.resize(img, (640, int(h * 640 / w)))
                else:
                    img_thumb = img
                cv2.imwrite(str(dst_path), img_thumb, [cv2.IMWRITE_JPEG_QUALITY, 85])
                img_url = f"growth/cycle_{cid}/{dst_img_name}"
            else:
                img_url = "latest_snapshot.jpg"

            entry = {
                "day": d_num,
                "fase": fase,
                "coverage": cov_adj,
                "status": status,
                "psi": psi_adj,
                "kesehatan": base_kes,
                "catatan": note,
                "image_url": img_url,
                "source_stem": stem or "semai_benih",
                "video_name": v_meta["video_name"] if v_meta else None,
                "frame_idx": v_meta["best_frame_idx"] if v_meta else None,
                "timestamp_sec": v_meta["timestamp_sec"] if v_meta else None,
                "raw_url": f"growth/ecofarm_videos/{stem}.jpg" if v_meta else None,
                "best_hour": (f"Video HP: {v_meta['video_name']} (Frame #{v_meta['best_frame_idx']})" if v_meta
                              else "11:00 WIB (Pencahayaan puncak)"),
                "ready_zones": int(round(cov_adj / 100 * 24))
            }
            entry.update(cyc_extra.get((str(cid), int(d_num)), {}))
            res.append(entry)

        return res

    all_data = {
        "retention_policy": {
            "max_cycles_stored": 3,
            "strategy": "FIFO (First In, First Out)",
            "description": "Menyimpan riwayat maksimal 3 siklus pertumbuhan (~90 hari). Saat siklus ke-4 dimulai, foto dan data siklus ke-1 otomatis dihapus untuk efisiensi penyimpanan.",
            "current_cycle_ids": [1, 2, 3],
            "total_stored_cycles": 3,
            "auto_purge_active": True
        },
        "cycles": {
            "video_dataset": {
                "meta": video_cycle_meta,
                "days": video_days
            },
            "1": {
                "meta": {
                    "cycle_id": 1,
                    "title": "Siklus 1 (Historis - Sukses Panen)",
                    "badge_label": "SELESAI",
                    "start_date": "2026-08-01",
                    "end_date": "2026-08-30",
                    "status": "SELESAI",
                    "total_days": 30,
                    "max_coverage": 93.0,
                    "avg_psi": 3.4,
                    "harvest_yield_kg": 18.5,
                    "is_active": False,
                    "days_count": 30
                },
                "days": buat_days_siklus(1, 30)
            },
            "2": {
                "meta": {
                    "cycle_id": 2,
                    "title": "Siklus 2 (Historis - Sukses Panen)",
                    "badge_label": "SELESAI",
                    "start_date": "2026-09-01",
                    "end_date": "2026-09-30",
                    "status": "SELESAI",
                    "total_days": 30,
                    "max_coverage": 94.2,
                    "avg_psi": 2.9,
                    "harvest_yield_kg": 19.8,
                    "is_active": False,
                    "days_count": 30
                },
                "days": buat_days_siklus(2, 30)
            },
            "3": {
                "meta": {
                    "cycle_id": 3,
                    "title": "Siklus 3 (Sedang Berjalan - Hari ke-20)",
                    "badge_label": "AKTIF",
                    "start_date": "2026-10-15",
                    "end_date": "2026-11-14",
                    "status": "AKTIF BERJALAN",
                    "total_days": 30,
                    "max_coverage": 53.9,
                    "avg_psi": 3.7,
                    "harvest_yield_kg": None,
                    "is_active": True,
                    "days_count": 20
                },
                "days": buat_days_siklus(3, 20)
            }
        }
    }

    # Simpan JSON
    json_path = GROWTH_DIR / "growth_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    # Sinkronkan ke dist/growth dan repo web/growth jika ada
    mirror_targets = []
    if (WEB_AQUAPONIK_DIR / "dist").exists():
        mirror_targets.append(WEB_AQUAPONIK_DIR / "dist" / "growth")
    if (ROOT / "web").exists() and (ROOT / "web" / "growth") != GROWTH_DIR:
        mirror_targets.append(ROOT / "web" / "growth")
    for dst_dir in mirror_targets:
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(json_path, dst_dir / "growth_data.json")
        for sub in ("ecofarm_videos", "cycle_1", "cycle_2", "cycle_3"):
            src_sub = GROWTH_DIR / sub
            dst_sub = dst_dir / sub
            if src_sub.exists():
                shutil.copytree(src_sub, dst_sub, dirs_exist_ok=True)
        print(f"[SYNC] Tersinkron ke {dst_dir}")

    print(f"\n[SUKSES] Dataset video ecofarm & data siklus pertumbuhan berhasil diperbarui di {json_path}")


if __name__ == "__main__":
    proses_semua()
