import re

path = "/home/aquaponic/kangkung_pi/kangkung_pi.py"
src = open(path).read()

# 1. Import timedelta
src = src.replace(
    "from datetime import datetime",
    "from datetime import datetime, timedelta"
)

# 2. Add helper function before main()
helper = '''
def hitung_tidur_hingga_jam_berikutnya(jam_list):
    """Hitung detik harus tidur sampai jam capture berikutnya."""
    now = datetime.now()
    today_hours = sorted(jam_list)
    for h in today_hours:
        target = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if target > now:
            return int((target - now).total_seconds())
    # Semua jam lewat hari ini, tidur sampai jam pertama besok pagi
    target = now.replace(hour=today_hours[0], minute=0, second=0, microsecond=0) + timedelta(days=1)
    return int((target - now).total_seconds())


'''

# Insert before "def main():"
src = src.replace("\ndef main():", helper + "def main():")

# 3. Replace the while loop inside main()
old_loop = """    while True:
        try:
            siklus(cfg, smoother)
            n = firebase_uplink.sync_outbox(cfg)
            if n:
                print(f"[UPLINK] {n} dokumen terkirim")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[ERROR] {e} (lanjut siklus berikutnya)")
            time.sleep(cfg["interval_menit"] * 60)"""

new_loop = """    jam_list = cfg.get("jam_capture", [8, 15])
    print(f"[JADWAL] Capture pada jam: {jam_list} WIB")

    while True:
        try:
            jam_sekarang = datetime.now().hour
            if jam_sekarang in jam_list:
                siklus(cfg, smoother)
                n = firebase_uplink.sync_outbox(cfg)
                if n:
                    print(f"[UPLINK] {n} dokumen terkirim")
            else:
                print(f"[IDLE] Jam {jam_sekarang}:00, tunggu jadwal {jam_list}")

            tidur_detik = hitung_tidur_hingga_jam_berikutnya(jam_list)
            jam_tidur = tidur_detik // 60
            print(f"[TIDUR] {jam_tidur} menit sampai jadwal berikutnya")
            time.sleep(tidur_detik)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"[ERROR] {e} (coba lagi 5 menit)")
            time.sleep(300)"""

src = src.replace(old_loop, new_loop)

open(path, "w").write(src)
print("kangkung_pi.py modified successfully")