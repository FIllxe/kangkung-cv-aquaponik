"""Thermal guard — baca suhu SoC, tunda capture saat panas (proteksi outdoor)."""
import shutil
import subprocess
from pathlib import Path

# Path sensor suhu Linux (Raspberry Pi)
_ZONES = Path("/sys/class/thermal")


def suhu_soc():
    """Suhu SoC dalam Celsius (float) atau None bila tidak tersedia."""
    # 1) Linux thermal zone (Raspberry Pi)
    for zone in sorted(_ZONES.glob("thermal_zone*/temp")):
        try:
            return int(zone.read_text().strip()) / 1000.0
        except (OSError, ValueError):
            continue
    # 2) Fallback via vcgencmd
    if shutil.which("vcgencmd"):
        try:
            out = subprocess.run(
                ["vcgencmd", "measure_temp"], capture_output=True, text=True,
                timeout=5).stdout
            return float(out.split("=")[1].split("'")[0])
        except (IndexError, ValueError, subprocess.SubprocessError):
            return None
    return None   # di laptop/Windows simulasi → None (guard dilewati)


def dalam_batas(suhu_maks_c: float):
    """Return (ok: bool, suhu). None-suhu dianggap OK (tidak bisa diukur)."""
    s = suhu_soc()
    return (True if s is None else s < suhu_maks_c, s)


if __name__ == "__main__":
    s = suhu_soc()
    print(f"Suhu SoC: {s if s is not None else 'tidak tersedia (bukan Pi)'}")
