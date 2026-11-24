"""firebase_uplink — kirim payload + snapshot ke Firebase (offline-queue).

Alur per dokumen (idempotent, doc_id = '<device>_<timestamp>'):
  1. Upload snapshot JPG ke Storage  -> URL publik
  2. Isi payload['snapshot_url']     -> set() dokumen Firestore
  3. Pindahkan file ke outbox/sent/
Gagal koneksi: file tetap di outbox/ -> dikirim ulang pada siklus berikutnya.
"""
import json
import shutil
import base64
import cv2
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
    """Kirim semua payload di outbox/. Return jumlah dokumen terkirim.

    Upload snapshot ke Storage bersifat opsional — bila gagal (mis. bucket
    belum aktif / paket gratis), payload tetap dikirim ke Firestore dengan
    snapshot_url = null agar dashboard tetap bisa menampilkan data secara live.
    """
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

            # ── Upload snapshot (opsional) ──────────────────────────────
            if jpg.exists():
                try:
                    payload["snapshot_url"] = upload_snapshot(
                        jpg, payload["device_id"], doc_id)
                    jpg.replace(sent_dir / jpg.name)
                except Exception as e:
                    # Storage gagal (404 bucket, dll.) — fallback ke base64 thumbnail
                    # agar gambar snapshot tetap tampil langsung di web dashboard
                    try:
                        im = cv2.imread(str(jpg))
                        h, w = im.shape[:2]
                        if w > 480:
                            im = cv2.resize(im, (480, int(h * 480 / w)))
                        _, buf = cv2.imencode('.jpg', im, [cv2.IMWRITE_JPEG_QUALITY, 55])
                        b64 = base64.b64encode(buf.tobytes()).decode('ascii')
                        payload["snapshot_url"] = f"data:image/jpeg;base64,{b64}"
                        jpg.replace(sent_dir / jpg.name)
                        print(f"[UPLINK] storage gagal, memakai fallback base64 inline ({len(b64)} B)")
                    except Exception as e_b64:
                        payload["snapshot_url"] = None
                        print(f"[UPLINK] storage gagal {doc_id}: {e} (tanpa gambar)")

            # ── Push ke Firestore (wajib) ───────────────────────────────
            push_doc(payload, cfg["firebase"]["collection"])
            json_path.replace(sent_dir / json_path.name)
            terkirim += 1
            print(f"[UPLINK] OK {doc_id}")
        except Exception as e:
            print(f"[UPLINK] gagal {json_path.name}: {e} (dicoba ulang nanti)")
    return terkirim
