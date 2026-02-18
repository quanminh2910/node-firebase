# face_service.py
import base64
import cv2
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

from detector import FaceDetectorDNN
from embedder import FaceEmbedder
from database import load_db, save_db
from liveness import LivenessMove

app = FastAPI()

det = FaceDetectorDNN(conf_th=0.6)          # uses your OpenCV DNN detector :contentReference[oaicite:5]{index=5}
emb = FaceEmbedder("models/facenet.tflite") # uses your TFLite embedder :contentReference[oaicite:6]{index=6}

# in-memory liveness sessions (simple)
_live_sessions = {}

class ImgReq(BaseModel):
    image_b64: str
    session_id: str | None = None
    thr: float = 0.55

class EnrollReq(BaseModel):
    name: str
    image_b64: str

def b64_to_bgr(image_b64: str):
    raw = base64.b64decode(image_b64)
    arr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

@app.get("/health")
def health():
    db = load_db()
    return {"ok": True, "users": len(db.keys())}

@app.post("/enroll")
def enroll(req: EnrollReq):
    db = load_db()
    db.setdefault(req.name, [])

    frame = b64_to_bgr(req.image_b64)
    box = det.detect_largest(frame)
    if box is None:
        return {"success": False, "reason": "no_face"}

    x1,y1,x2,y2 = box
    face = frame[y1:y2, x1:x2]
    if face.size == 0:
        return {"success": False, "reason": "bad_crop"}

    vec = emb.embed(face)  # normalized embedding :contentReference[oaicite:7]{index=7}
    db[req.name].append(vec.tolist())
    save_db(db)            # writes to face_db.json :contentReference[oaicite:8]{index=8}

    return {"success": True, "name": req.name, "samples": len(db[req.name])}

@app.post("/recognize")
def recognize(req: ImgReq):
    db = load_db()
    if not db:
        return {"success": False, "reason": "empty_db"}

    frame = b64_to_bgr(req.image_b64)
    box = det.detect_largest(frame)
    if box is None:
        return {"success": False, "reason": "no_face"}

    # liveness session (movement-based) :contentReference[oaicite:9]{index=9}
    sid = req.session_id or "default"
    live = _live_sessions.get(sid)
    if live is None:
        live = LivenessMove(time_window_s=6.0, move_px=25.0)
        _live_sessions[sid] = live
    lv = live.update(box)

    x1,y1,x2,y2 = box
    face = frame[y1:y2, x1:x2]
    if face.size == 0:
        return {"success": False, "reason": "bad_crop"}

    q = emb.embed(face)

    best_name = "unknown"
    best_score = -1.0
    for name, embs in db.items():
        for e in embs:
            s = float(np.dot(q, np.array(e, dtype=np.float32)))  # cosine :contentReference[oaicite:10]{index=10}
            if s > best_score:
                best_score = s
                best_name = name

    matched = best_score >= req.thr
    is_live = bool(lv["live"])

    if matched and is_live:
        live.reset()
        return {"success": True, "name": best_name, "score": best_score, "live": True, "moved": lv["moved"]}

    return {
        "success": False,
        "name": best_name if matched else "unknown",
        "score": best_score,
        "live": is_live,
        "moved": lv["moved"],
        "reason": "not_live" if matched and not is_live else "no_match"
    }
