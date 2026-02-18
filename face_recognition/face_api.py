import os
import time
import threading
import numpy as np
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from camera import Camera
from detector import FaceDetectorDNN
from embedder import FaceEmbedder
from database import load_db, save_db
from liveness import LivenessMove

# ---- Security (Node -> Pi shared secret) ----
FACE_SERVICE_KEY = os.getenv("FACE_SERVICE_KEY", "")

def require_key(x_face_key: str | None):
    if FACE_SERVICE_KEY and x_face_key != FACE_SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Bad face service key")

# ---- Init heavy objects once ----
app = FastAPI()

det = FaceDetectorDNN(conf_th=0.6)
emb = FaceEmbedder("models/facenet.tflite", num_threads=2)

# Keep one camera open (USB webcam or /dev/video0)
cam = Camera(src=0, width=640, height=480).start()

# Prevent two requests using camera at the same time
cam_lock = threading.Lock()

class VerifyReq(BaseModel):
    thr: float = 0.55
    every: int = 3
    timeout_s: float = 10.0
    live_window: float = 6.0
    move_px: float = 25.0

class EnrollReq(BaseModel):
    name: str
    samples: int = 20
    sleep: float = 0.15

@app.get("/health")
def health():
    db = load_db()
    return {"ok": True, "users": len(db)}

@app.post("/enroll_camera")
def enroll_camera(req: EnrollReq, x_face_key: str | None = Header(default=None)):
    require_key(x_face_key)
    if not req.name:
        raise HTTPException(400, "name required")

    with cam_lock:
        db = load_db()
        db.setdefault(req.name, [])

        collected = 0
        while len(db[req.name]) < req.samples:
            frame = cam.read()
            if frame is None:
                continue

            box = det.detect_largest(frame)
            if box is None:
                continue

            x1, y1, x2, y2 = box
            face = frame[y1:y2, x1:x2]
            if face.size == 0:
                continue

            vec = emb.embed(face)
            db[req.name].append(vec.tolist())
            collected += 1
            time.sleep(req.sleep)

        save_db(db)
        return {"success": True, "name": req.name, "samples": len(db[req.name]), "added": collected}

@app.post("/verify_camera")
def verify_camera(req: VerifyReq, x_face_key: str | None = Header(default=None)):
    require_key(x_face_key)

    db = load_db()
    if not db:
        return {"success": False, "reason": "empty_db"}

    live = LivenessMove(time_window_s=req.live_window, move_px=req.move_px)

    best_name = "unknown"
    best_score = -1.0

    deadline = time.time() + req.timeout_s
    frame_id = 0

    with cam_lock:
        while time.time() < deadline:
            frame = cam.read()
            if frame is None:
                continue

            frame_id += 1
            if req.every > 1 and (frame_id % req.every != 0):
                continue

            box = det.detect_largest(frame)
            lv = live.update(box)

            if box is None:
                continue

            x1, y1, x2, y2 = box
            face = frame[y1:y2, x1:x2]
            if face.size == 0:
                continue

            q = emb.embed(face)

            # cosine = dot (because embeddings are L2-normalized)
            for name, embs in db.items():
                for e in embs:
                    s = float(np.dot(q, np.array(e, dtype=np.float32)))
                    if s > best_score:
                        best_score = s
                        best_name = name

            matched = best_score >= req.thr
            if matched and lv["live"]:
                live.reset()
                return {
                    "success": True,
                    "name": best_name,
                    "score": best_score,
                    "live": True,
                    "moved": lv["moved"]
                }

            # if timed out for liveness window, reset the challenge
            if lv["timeout"] and not lv["live"]:
                live.reset()

        # timeout
        return {
            "success": False,
            "reason": "timeout",
            "best_name": best_name if best_score >= req.thr else "unknown",
            "best_score": best_score,
        }
