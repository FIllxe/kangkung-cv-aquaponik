"""
=============================================================================
  Paper Downloader Utility — Kangkung Aquaponics Project
  
  Bantu Felix download semua paper referensi dengan sekali run.
  Perlu: pip install requests
=============================================================================
"""

import os
import requests
from pathlib import Path
from datetime import datetime

# ─── DAFTAR PAPER ─────────────────────────────────────────────────────────

PAPERS = [
    {
        "id": "1",
        "title": "A Modularized IoT Monitoring System with Edge-Computing for Aquaponics",
        "year": 2022,
        "priority": "1 - PRIORITY",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9739085/pdf/sensors-22-09260.pdf",
        "filename": "01_Aquaponics_IoT_EdgeComputing_Wan2022.pdf"
    },
    {
        "id": "2",
        "title": "Automatic crop detection under field conditions using HSV colour space and morphological operations",
        "year": 2017,
        "priority": "1 - PRIORITY",
        "url": "https://www.sciencedirect.com/science/article/pii/S0168169916303714",
        "filename": "02_HSV_CropDetection_Morphology_Searson2017.pdf",
        "note": "Link mungkin perlu akses universitas. Coba ResearchGate sebagai alternatif."
    },
    {
        "id": "3",
        "title": "A New Vegetation Segmentation Approach for Cropped Fields Based on Threshold Detection from Hue Histograms",
        "year": 2018,
        "priority": "1 - PRIORITY",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5948827/pdf/sensors-18-01258.pdf",
        "filename": "03_VegetationSegmentation_HueHistogram_Hameed2018.pdf"
    },
    {
        "id": "4",
        "title": "Robust Leaf Disease Detection Using Complex Fuzzy Sets and HSV-Based Color Segmentation Techniques",
        "year": 2024,
        "priority": "1 - PRIORITY",
        "url": "https://www.acadlore.com/article/ATAIML/2024_3_3/ataiml030305",
        "filename": "04_HSV_LeafDisease_Detection_Raza2024.pdf"
    },
    {
        "id": "5",
        "title": "Using Deep Learning to Predict Plant Growth and Yield in Greenhouse Environments",
        "year": 2019,
        "priority": "2 - Future",
        "url": "https://arxiv.org/pdf/1907.00624.pdf",
        "filename": "05_DeepLearning_PlantGrowth_LSTM_Perez2019.pdf"
    },
    {
        "id": "6",
        "title": "Deep Learning for Image-Based Plant Growth Monitoring: A Review",
        "year": 2022,
        "priority": "2 - Future",
        "url": "https://www.researchgate.net/publication/361567510",
        "filename": "06_DL_PlantMonitoring_Review_Liu2022.pdf",
        "note": "Buka via ResearchGate, request PDF dari authors"
    },
    {
        "id": "7",
        "title": "Deep learning-based prediction of plant height and crown area of vegetable crops using LiDAR point cloud",
        "year": 2024,
        "priority": "2 - Future",
        "url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11213942/pdf/s41598-024-59643-8.pdf",
        "filename": "07_LSTM_PlantHeight_CrownArea_Mane2024.pdf"
    },
    {
        "id": "8",
        "title": "An autoencoder wavelet based deep neural network with attention mechanism for multistep prediction of plant growth",
        "year": 2020,
        "priority": "2 - Future",
        "url": "https://arxiv.org/pdf/2012.04041.pdf",
        "filename": "08_Autoencoder_Attention_PlantGrowth_Athanasiadis2020.pdf"
    },
    {
        "id": "9",
        "title": "Water IoT Monitoring System for Aquaponics Health and Fishery Applications",
        "year": 2022,
        "priority": "3 - Supporting",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9565948/pdf/sensors-22-07679.pdf",
        "filename": "09_WaterIoT_Aquaponics_Variyar2022.pdf"
    },
    {
        "id": "10",
        "title": "Trend Forecasting of Computer Vision Application in Aquaponic Cropping Systems Industry",
        "year": 2021,
        "priority": "3 - Supporting",
        "url": "https://www.academia.edu/55554307",
        "filename": "10_CVTrends_Aquaponics_Bayas2021.pdf",
        "note": "Buka via Academia.edu"
    },
    {
        "id": "12",
        "title": "Analysis of opportunities and challenges of smart aquaponic system",
        "year": 2025,
        "priority": "3 - Supporting",
        "url": "https://link.springer.com/article/10.1186/s42834-025-00255-z",
        "filename": "12_SmartAquaponics_Analysis_2025.pdf",
        "note": "Link Springer (possibly paywalled, coba universitas)"
    },
    {
        "id": "14",
        "title": "Deep Learning Meets Process-Based Models: A Hybrid Approach to Agricultural Challenges",
        "year": 2025,
        "priority": "4 - Bonus",
        "url": "https://arxiv.org/pdf/2504.16141.pdf",
        "filename": "14_PBM_DL_Hybrid_Agriculture_2025.pdf"
    }
]

# ─── UTILITY FUNCTIONS ─────────────────────────────────────────────────────

def download_file(url, filepath, timeout=30):
    """Download file dari URL dengan progress indicator."""
    try:
        print(f"  ⏳ Downloading: {filepath.name}")
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        pct = (downloaded / total_size) * 100
                        print(f"    {pct:.0f}% ({downloaded/1024/1024:.1f} MB)")
        
        print(f"  ✅ Selesai: {filepath.name} ({total_size/1024/1024:.1f} MB)")
        return True
        
    except requests.RequestException as e:
        print(f"  ❌ ERROR: {e}")
        return False


def list_papers(priority_filter=None):
    """List semua paper dengan filter priority."""
    print("\n" + "="*70)
    print("  DAFTAR PAPER REFERENSI — Kangkung Aquaponics Project")
    print("="*70)
    
    for p in PAPERS:
        if priority_filter and priority_filter not in p["priority"]:
            continue
        
        print(f"\n[{p['id']}] {p['title']}")
        print(f"     Tahun: {p['year']} | Priority: {p['priority']}")
        print(f"     File: {p['filename']}")
        if 'note' in p:
            print(f"     📌 Note: {p['note']}")


def download_all(output_dir="papers", priority_filter=None):
    """Download semua paper ke folder tertentu."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print(f"  MULAI DOWNLOAD — Output folder: {output_path.resolve()}")
    print("="*70)
    
    success = 0
    failed = 0
    skipped = 0
    
    for paper in PAPERS:
        if priority_filter and priority_filter not in paper["priority"]:
            continue
        
        filepath = output_path / paper["filename"]
        
        print(f"\n[{paper['id']}] {paper['title'][:60]}...")
        
        # Skip jika sudah ada
        if filepath.exists():
            print(f"  ⏭️  Sudah ada, skip.")
            skipped += 1
            continue
        
        # Skip untuk link yang memerlukan special access
        if "researchgate.net" in paper["url"] or "academia.edu" in paper["url"] or "springer" in paper["url"]:
            print(f"  ⚠️  Perlu manual access (ResearchGate/Academia.edu/Springer)")
            print(f"     👉 Buka: {paper['url']}")
            skipped += 1
            continue
        
        # Attempt download
        if download_file(paper["url"], filepath):
            success += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print("  RINGKASAN DOWNLOAD")
    print("="*70)
    print(f"  ✅ Berhasil: {success}")
    print(f"  ❌ Gagal: {failed}")
    print(f"  ⏭️  Skipped (manual/existing): {skipped}")
    print(f"  📁 Output: {output_path.resolve()}")
    print("="*70)
    
    if failed == 0 and success > 0:
        print("\n  🎉 Semua paper berhasil didownload!")
    elif failed > 0:
        print(f"\n  ⚠️  {failed} paper gagal. Coba manual via browser.")
    
    return success, failed, skipped


# ─── CLI INTERFACE ─────────────────────────────────────────────────────────

def main():
    import sys
    
    print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║          Paper Downloader — Kangkung Aquaponics Project              ║
    ║                                                                       ║
    ║  Usage:                                                               ║
    ║    python3 download_papers.py --list              (lihat semua)      ║
    ║    python3 download_papers.py --list-priority 1   (lihat PRIORITY)   ║
    ║    python3 download_papers.py --download          (download semua)   ║
    ║    python3 download_papers.py --download-priority 1  (download utama)║
    ║    python3 download_papers.py --help              (bantuan)          ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    if len(sys.argv) < 2:
        print("  📌 Jalankan dengan --help untuk bantuan")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "--help":
        print("""
  --list                      Tampilkan semua paper
  --list-priority 1           Tampilkan paper priority 1 saja
  --download                  Download SEMUA paper (otomatis)
  --download-priority 1       Download hanya priority 1
  --download-dir ./papers     Download ke folder custom
  --open                      Buka folder download di explorer
        """)
    
    elif cmd == "--list":
        list_papers()
    
    elif cmd == "--list-priority":
        priority = sys.argv[2] if len(sys.argv) > 2 else "1"
        list_papers(priority_filter=priority)
    
    elif cmd == "--download":
        output_dir = "./papers"
        if "--download-dir" in sys.argv:
            idx = sys.argv.index("--download-dir")
            output_dir = sys.argv[idx + 1]
        download_all(output_dir)
    
    elif cmd == "--download-priority":
        priority = sys.argv[2] if len(sys.argv) > 2 else "1"
        output_dir = "./papers"
        if "--download-dir" in sys.argv:
            idx = sys.argv.index("--download-dir")
            output_dir = sys.argv[idx + 1]
        
        filtered = [p for p in PAPERS if priority in p["priority"]]
        print(f"\n⏳ Akan download {len(filtered)} paper priority {priority}...")
        download_all(output_dir, priority_filter=priority)
    
    elif cmd == "--open":
        output_dir = Path("./papers")
        if output_dir.exists():
            import platform
            if platform.system() == "Windows":
                os.startfile(output_dir)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open {output_dir}")
            else:  # Linux
                os.system(f"xdg-open {output_dir}")
        else:
            print(f"  ❌ Folder {output_dir} tidak ada. Download dulu.")
    
    else:
        print(f"  ❌ Command tidak dikenal: {cmd}")
        print("     Gunakan --help untuk bantuan")


if __name__ == "__main__":
    main()
