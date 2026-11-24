#!/usr/bin/env python3
"""GROWTH TRACKER — Pelacak Siklus Pertumbuhan Tanaman Kangkung Aquaponik.

Fitur:
  1. Pelacakan Harian (Hari 1 s/d Hari 30):
     - Memilih "Frame Terbaik" per hari berdasarkan ketajaman (Laplacian variance)
       dan jendela pencahayaan optimal (10:00 - 14:00 WIB).
     - Menyimpan foto beranotasi harian (day_01.jpg s/d day_30.jpg).
  2. Multi-Siklus:
     - Mendukung siklus tanam berulang (dari semai/benih hingga siap panen ~30 hari).
  3. Kebijakan Retensi Maksimal 3 Siklus (FIFO):
     - Hanya menyimpan data dan foto untuk MAKSIMAL 3 SIKLUS terakhir.
     - Saat siklus baru masuk dan total siklus > 3, siklus terlama otomatis
       dihapus dari media penyimpanan (SD card / disk) untuk mencegah kepenuhan.
"""

import os
import sys
import json
import shutil
import cv2
import numpy as np
from datetime import datetime, date
from pathlib import Path

DEFAULT_MAX_CYCLES = 3
DEFAULT_DAYS_PER_CYCLE = 30


class GrowthTracker:
    def __init__(self, storage_dir=None, max_cycles=DEFAULT_MAX_CYCLES, days_per_cycle=DEFAULT_DAYS_PER_CYCLE):
        if storage_dir is None:
            self.storage_dir = Path(__file__).resolve().parent / "growth_cycles"
        else:
            self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_cycles = max_cycles
        self.days_per_cycle = days_per_cycle
        self.meta_file = self.storage_dir / "growth_data.json"
        self._load_or_init_data()

    def _load_or_init_data(self):
        if self.meta_file.exists():
            try:
                self.data = json.loads(self.meta_file.read_text(encoding="utf-8"))
                return
            except Exception as e:
                print(f"[WARN] Gagal membaca {self.meta_file}: {e}. Membuat baru.")

        self.data = {
            "retention_policy": {
                "max_cycles_stored": self.max_cycles,
                "strategy": "FIFO (First In, First Out)",
                "description": f"Menyimpan riwayat maksimal {self.max_cycles} siklus pertumbuhan. Saat siklus ke-{self.max_cycles+1} dimulai, foto dan data siklus tertua otomatis dihapus.",
                "current_cycle_ids": [1],
                "total_stored_cycles": 1,
                "auto_purge_active": True
            },
            "cycles": {
                "1": {
                    "meta": {
                        "cycle_id": 1,
                        "title": "Siklus 1 (Aktif)",
                        "start_date": datetime.now().strftime("%Y-%m-%d"),
                        "end_date": None,
                        "status": "AKTIF",
                        "total_days": self.days_per_cycle,
                        "max_coverage": 0.0,
                        "avg_psi": 0.0,
                        "harvest_yield_kg": None,
                        "is_active": True,
                        "days_count": 0
                    },
                    "days": []
                }
            }
        }
        self.save_data()

    def save_data(self):
        """Simpan data ke JSON dengan format rapi."""
        self.meta_file.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def get_active_cycle_id(self):
        """Ambil ID siklus yang saat ini sedang aktif."""
        cycles = self.data.get("cycles", {})
        for cid_str, cdata in cycles.items():
            if cdata.get("meta", {}).get("is_active", False):
                return int(cid_str)
        # Jika tidak ada yang aktif, ambil cycle_id terbesar
        if cycles:
            return max(int(k) for k in cycles.keys())
        return 1

    def calculate_frame_quality(self, frame_bgr, dt=None):
        """Hitung skor kualitas frame:
        1. Ketajaman (Laplacian variance pada grayscale)
        2. Faktor jam: pembobotan lebih tinggi pada 10:00 - 14:00 WIB (cahaya terbaik)
        """
        if frame_bgr is None:
            return 0.0
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        hour_bonus = 1.0
        if dt is not None:
            hour = dt.hour
            if 10 <= hour <= 14:
                hour_bonus = 1.35  # Jendela cahaya matahari/lampu paling merata
            elif 7 <= hour <= 17:
                hour_bonus = 1.15
            else:
                hour_bonus = 0.7   # Malam / senja

        return round(lap_var * hour_bonus, 2)

    def determine_fase(self, day):
        """Klasifikasi fase pertumbuhan kangkung berdasarkan hari ke-N."""
        if day <= 5:
            return "Benih"
        elif day <= 12:
            return "Bibit"
        elif day <= 21:
            return "Vegetatif"
        else:
            return "Siap Panen"

    def process_reading(self, doc_id, snapshot_img, payload):
        """Dipanggil setiap kali kamera menghasilkan snapshot dan payload baru.
        Mengecek apakah frame ini merupakan frame terbaik untuk hari ini.
        """
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        cycle_id = self.get_active_cycle_id()
        cycle_str = str(cycle_id)

        if cycle_str not in self.data["cycles"]:
            self.data["cycles"][cycle_str] = {
                "meta": {
                    "cycle_id": cycle_id,
                    "title": f"Siklus {cycle_id} (Aktif)",
                    "start_date": today_str,
                    "end_date": None,
                    "status": "AKTIF",
                    "total_days": self.days_per_cycle,
                    "max_coverage": 0.0,
                    "avg_psi": 0.0,
                    "harvest_yield_kg": None,
                    "is_active": True,
                    "days_count": 0
                },
                "days": []
            }

        cycle_data = self.data["cycles"][cycle_str]
        days_list = cycle_data["days"]

        # Hitung hari ke berapa sejak siklus dimulai
        try:
            start_dt = datetime.strptime(cycle_data["meta"]["start_date"], "%Y-%m-%d").date()
            diff_days = (now.date() - start_dt).days + 1
        except Exception:
            diff_days = len(days_list) + 1

        day_num = max(1, min(self.days_per_cycle, diff_days))

        # Folder foto siklus ini
        cycle_folder = self.storage_dir / f"cycle_{cycle_id}"
        cycle_folder.mkdir(parents=True, exist_ok=True)
        img_filename = f"day_{day_num:02d}.jpg"
        img_path = cycle_folder / img_filename
        relative_img_url = f"growth/cycle_{cycle_id}/{img_filename}"

        # Hitung skor kualitas frame baru
        quality = self.calculate_frame_quality(snapshot_img, now)

        # Cek apakah hari ini sudah ada catatan
        existing_day_idx = None
        for i, d in enumerate(days_list):
            if d.get("day") == day_num:
                existing_day_idx = i
                break

        coverage = float(payload.get("coverage_rata", 0.0))
        psi_val = float(payload.get("fuzzy_input", {}).get("psi_score", 0.0))
        ready_zones = int(payload.get("zona_siap_panen", 0))

        status = "siap_panen" if coverage >= 55 else ("hampir_siap" if coverage >= 25 else "belum_siap")
        kesehatan = "sehat" if psi_val < 35 else ("waspada" if psi_val < 70 else "sakit")

        is_better = False
        if existing_day_idx is None:
            is_better = True
        else:
            old_score = days_list[existing_day_idx].get("quality_score", 0.0)
            if quality > old_score:
                is_better = True

        if is_better:
            # Simpan foto berkualitas tinggi
            if snapshot_img is not None:
                cv2.imwrite(str(img_path), snapshot_img, [cv2.IMWRITE_JPEG_QUALITY, 90])

            catatan = (
                f"Penyemaian bibit kangkung di rockwool/netpot." if day_num <= 5 else
                f"Daun sejati berkembang, bibit tegak merata." if day_num <= 12 else
                f"Pertumbuhan vegetatif aktif, kanopi mulai rapat." if day_num <= 21 else
                f"Rumpun kangkung rimbun dan seragam, siap dipanen."
            )

            day_entry = {
                "day": day_num,
                "date": today_str,
                "fase": self.determine_fase(day_num),
                "coverage": round(coverage, 1),
                "status": status,
                "psi": round(psi_val, 1),
                "kesehatan": kesehatan,
                "catatan": catatan,
                "image_url": relative_img_url,
                "source_doc_id": doc_id,
                "best_hour": f"{now.strftime('%H:%M')} WIB (Skor Kualitas: {quality})",
                "quality_score": quality,
                "ready_zones": ready_zones
            }

            if existing_day_idx is None:
                days_list.append(day_entry)
            else:
                days_list[existing_day_idx] = day_entry

            # Urutkan days berdasarkan hari ke-N
            days_list.sort(key=lambda x: x["day"])
            cycle_data["meta"]["days_count"] = len(days_list)
            cycle_data["meta"]["max_coverage"] = max([d["coverage"] for d in days_list] or [0.0])
            cycle_data["meta"]["avg_psi"] = round(sum([d["psi"] for d in days_list]) / max(1, len(days_list)), 1)

            print(f"[GROWTH] Hari {day_num} (Siklus {cycle_id}) diperbarui: cov={coverage}%, psi={psi_val}, score={quality}")
            self.save_data()

        # Cek apakah sudah genap 30 hari -> siklus selesai
        if day_num >= self.days_per_cycle and cycle_data["meta"]["is_active"]:
            self.finish_cycle(cycle_id)

        # Jalankan kebijakan retensi (FIFO max 3 siklus)
        self.enforce_retention()

    def finish_cycle(self, cycle_id, harvest_yield_kg=None):
        """Menandai siklus sebagai selesai."""
        cycle_str = str(cycle_id)
        if cycle_str in self.data["cycles"]:
            meta = self.data["cycles"][cycle_str]["meta"]
            meta["status"] = "SELESAI"
            meta["is_active"] = False
            meta["end_date"] = datetime.now().strftime("%Y-%m-%d")
            if harvest_yield_kg is not None:
                meta["harvest_yield_kg"] = harvest_yield_kg
            print(f"[GROWTH] Siklus {cycle_id} telah SELESAI ({meta['days_count']} hari).")
            self.save_data()

    def start_new_cycle(self):
        """Mulai siklus tanam baru."""
        # Nonaktifkan semua siklus sebelumnya
        for cdata in self.data["cycles"].values():
            cdata["meta"]["is_active"] = False
            if cdata["meta"]["status"] == "AKTIF":
                cdata["meta"]["status"] = "SELESAI"

        existing_ids = [int(k) for k in self.data["cycles"].keys()]
        new_id = (max(existing_ids) + 1) if existing_ids else 1
        today_str = datetime.now().strftime("%Y-%m-%d")

        self.data["cycles"][str(new_id)] = {
            "meta": {
                "cycle_id": new_id,
                "title": f"Siklus {new_id} (Aktif)",
                "start_date": today_str,
                "end_date": None,
                "status": "AKTIF",
                "total_days": self.days_per_cycle,
                "max_coverage": 0.0,
                "avg_psi": 0.0,
                "harvest_yield_kg": None,
                "is_active": True,
                "days_count": 0
            },
            "days": []
        }

        print(f"[GROWTH] Memulai Siklus Baru: Siklus {new_id}")
        self.save_data()
        self.enforce_retention()
        return new_id

    def enforce_retention(self):
        """Kebijakan Retensi Maksimal 3 Siklus (FIFO):
        Jika total siklus yang tersimpan > max_cycles (3),
        hapus siklus paling tua dari data dan folder fisik foto di disk.
        """
        cycles = self.data.get("cycles", {})
        cycle_ids = sorted([int(k) for k in cycles.keys()])

        purged_count = 0
        while len(cycle_ids) > self.max_cycles:
            oldest_id = cycle_ids.pop(0)  # FIFO: ambil yang paling awal
            oldest_str = str(oldest_id)

            print(f"[RETENTION] Membersihkan siklus lama ID={oldest_id} (Kebijakan FIFO maks {self.max_cycles} siklus)...")

            # 1. Hapus folder foto fisik
            folder_to_delete = self.storage_dir / f"cycle_{oldest_id}"
            if folder_to_delete.exists() and folder_to_delete.is_dir():
                try:
                    shutil.rmtree(folder_to_delete)
                    print(f"  -> Folder fisik {folder_to_delete} berhasil dihapus.")
                except Exception as e:
                    print(f"  -> [ERR] Gagal menghapus folder {folder_to_delete}: {e}")

            # 2. Hapus dari struktur JSON
            if oldest_str in self.data["cycles"]:
                del self.data["cycles"][oldest_str]
                purged_count += 1

        # Perbarui metadata retensi
        remaining_ids = sorted([int(k) for k in self.data["cycles"].keys()])
        self.data["retention_policy"]["current_cycle_ids"] = remaining_ids
        self.data["retention_policy"]["total_stored_cycles"] = len(remaining_ids)
        self.save_data()

        if purged_count > 0:
            print(f"[RETENTION] {purged_count} siklus terlama telah dihapus. Sisa tersimpan: {remaining_ids}")

        return purged_count

    def get_summary(self):
        """Ambil ringkasan status siklus dan retensi."""
        cycles = self.data.get("cycles", {})
        active_id = self.get_active_cycle_id()
        summary = {
            "total_cycles": len(cycles),
            "max_cycles_allowed": self.max_cycles,
            "active_cycle_id": active_id,
            "stored_cycle_ids": sorted([int(k) for k in cycles.keys()]),
            "cycles_detail": []
        }
        for cid_str in sorted(cycles.keys(), key=lambda x: int(x)):
            meta = cycles[cid_str]["meta"]
            summary["cycles_detail"].append({
                "cycle_id": meta["cycle_id"],
                "status": meta["status"],
                "days_count": meta["days_count"],
                "max_coverage": meta["max_coverage"],
                "avg_psi": meta["avg_psi"],
                "start_date": meta["start_date"],
                "end_date": meta.get("end_date")
            })
        return summary


# ─── Mode CLI & Pengujian ───────────────────────────────────────────────────

def test_retention_simulation():
    """Uji simulasi retensi FIFO 3 siklus."""
    print("=" * 60)
    print("SIMULASI PENGUJIAN KEBIJAKAN RETENSI MAKS 3 SIKLUS (FIFO)")
    print("=" * 60)
    test_dir = Path("growth_test_sandbox")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    tracker = GrowthTracker(storage_dir=test_dir, max_cycles=3, days_per_cycle=30)
    print(f"[INIT] Storage sementara dibuat di: {test_dir}")

    # Buat dummy foto
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(dummy_img, "TEST FRAME", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)

    # Simulasikan Siklus 1, 2, 3, 4, 5
    for c in range(1, 6):
        print(f"\n--- Memproses Siklus {c} ---")
        if c > 1:
            tracker.start_new_cycle()

        # Masukkan 3 hari per siklus sebagai sampel
        for d in range(1, 4):
            payload = {
                "coverage_rata": 10.0 * d,
                "zona_siap_panen": d * 2,
                "fuzzy_input": {"psi_score": 5.0}
            }
            tracker.process_reading(f"doc_c{c}_d{d}", dummy_img, payload)

        summary = tracker.get_summary()
        print(f"Status saat ini: {summary['total_cycles']}/{summary['max_cycles_allowed']} siklus tersimpan: {summary['stored_cycle_ids']}")

        # Verifikasi fisik folder
        subdirs = [f.name for f in test_dir.iterdir() if f.is_dir()]
        print(f"Folder fisik yang ada: {subdirs}")

    print("\n--- Verifikasi Akhir Kebijakan Retensi ---")
    final_summary = tracker.get_summary()
    assert len(final_summary["stored_cycle_ids"]) <= 3, "ERROR: Jumlah siklus melebihi 3!"
    assert 1 not in final_summary["stored_cycle_ids"], "ERROR: Siklus 1 harusnya sudah terhapus (FIFO)!"
    assert 2 not in final_summary["stored_cycle_ids"], "ERROR: Siklus 2 harusnya sudah terhapus (FIFO)!"
    assert 3 in final_summary["stored_cycle_ids"], "Siklus 3 harus tersimpan"
    assert 4 in final_summary["stored_cycle_ids"], "Siklus 4 harus tersimpan"
    assert 5 in final_summary["stored_cycle_ids"], "Siklus 5 harus tersimpan"
    print("[SUKSES] Verifikasi FIFO lolos 100%! Siklus 1 & 2 terhapus otomatis, siklus 3, 4, 5 tersimpan rapi.")

    # Bersihkan sandbox tes
    shutil.rmtree(test_dir)
    print(f"[CLEANUP] Sandbox tes {test_dir} dibersihkan.")


if __name__ == "__main__":
    if "--test-retention" in sys.argv:
        test_retention_simulation()
    elif "--status" in sys.argv:
        t = GrowthTracker()
        print(json.dumps(t.get_summary(), indent=2))
    elif "--next-cycle" in sys.argv:
        t = GrowthTracker()
        nid = t.start_new_cycle()
        print(f"Siklus baru dimulai: {nid}")
    else:
        print("Penggunaan:")
        print("  python growth_tracker.py --test-retention   (Uji simulasi FIFO retensi)")
        print("  python growth_tracker.py --status           (Tampilkan status siklus)")
        print("  python growth_tracker.py --next-cycle       (Mulai siklus baru)")
