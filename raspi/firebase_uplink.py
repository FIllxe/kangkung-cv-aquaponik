"""firebase_uplink — kirim payload + snapshot ke Firebase (offline-queue).

Alur per dokumen (idempotent, doc_id = '<device>_<timestamp>'):
  1. Upload snapshot JPG ke Storage  -> URL publik
  2. Isi payload['snapshot_url']     -> set() dokumen Firestore
  3. Pindahkan file ke outbox/sent/
Gagal koneksi: file tetap di outbox/ -> dikirim ulang pada siklus berikutnya.
"""
import json
import shutil
from pathlib import Path

_firebase_ready = False
_bucket = None
_db = None


def init(cfg):
    """Inisialisasi firebase_admin. Return True bila siap kirim."""
    global _firebase_ready, _bucket, _db
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage
        sa = cfg["firebase"]["service_account"]
        if not Path(sa).exists():
            print("[UPLINK] service-account.json belum ada -> mode offline-queue")
            return False
        app = firebase_admin.get_app() if firebase_admin._apps \
            else firebase_admin.initialize_app(credentials.Certificate(sa))
        _bucket = storage.bucket(cfg["firebase"]["storage_bucket"])
        _db = firestore.client(app)
        _firebase_ready = True
        return True
    except Exception as e:                      # ImportError / kredensial
        print(f"[UPLINK] Firebase tidak siap ({e}) -> mode offline-queue")
        return False


def upload_snapshot(jpg_path: Path, device_id: str, doc_id: str) -> str:
    """Upload JPEG ke Storage, return URL publik (tanpa login untuk read)."""
    blob = _bucket.blob(f"snapshots/{device_id}/{doc_id}.jpg")
    blob.upload_from_filename(str(jpg_path), content_type="image/jpeg")
    blob.make_public()
    return blob.public_url


def push_doc(payload: dict, collection: str):
    _db.collection(collection).document(payload["doc_id"]).set(payload)


def sync_outbox(cfg) -> int:
    """Kirim semua payload di outbox/. Return jumlah dokumen terkirim."""
    outbox = Path(cfg["outbox_dir"])
    if not outbox.exists() or not init(cfg):
        return 0
    sent_dir = outbox / "sent"
    sent_dir.mkdir(exist_ok=True)
    terkirim = 0
    for json_path in sorted(outbox.glob("*.json")):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            doc_id = payload["doc_id"]
            jpg = outbox / f"{doc_id}.jpg"
            if jpg.exists():
                payload["snapshot_url"] = upload_snapshot(
                    jpg, payload["device_id"], doc_id)
                jpg.replace(sent_dir / jpg.name)
            push_doc(payload, cfg["firebase"]["collection"])
            json_path.replace(sent_dir / json_path.name)
            terkirim += 1
            print(f"[UPLINK] OK {doc_id}")
        except Exception as e:
            print(f"[UPLINK] gagal {json_path.name}: {e} (dicoba ulang nanti)")
    return terkirim
