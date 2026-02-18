import time
import argparse
import numpy as np

from camera import Camera
from detector import FaceDetectorDNN
from embedder import FaceEmbedder
from database import load_db
from liveness import LivenessMove

def cosine(a, b):
    # a,b đã normalize => dot = cosine similarity
    return float(np.dot(a, b))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam", type=int, default=0)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--model", default="models/facenet.tflite")
    ap.add_argument("--conf", type=float, default=0.6)
    ap.add_argument("--thr", type=float, default=0.55, help="cosine threshold")
    ap.add_argument("--every", type=int, default=3, help="process every N frames")
    ap.add_argument("--live_window", type=float, default=6.0)
    ap.add_argument("--move_px", type=float, default=25.0)
    args = ap.parse_args()

    db = load_db()
    if not db:
        print("DB rỗng. Hãy enroll trước: python enroll.py --name <ten>")
        return

    cam = Camera(src=args.cam, width=args.width, height=args.height).start()
    det = FaceDetectorDNN(conf_th=args.conf)
    emb = FaceEmbedder(args.model)
    live = LivenessMove(time_window_s=args.live_window, move_px=args.move_px)

    frame_id = 0
    print("RECOGNIZE + LIVENESS(move) | Ctrl+C to stop")
    print(f"- face_thr={args.thr} | live_window={args.live_window}s | move_px={args.move_px}px")

    try:
        while True:
            frame = cam.read()
            if frame is None:
                continue

            frame_id += 1
            if frame_id % args.every != 0:
                continue

            box = det.detect_largest(frame)
            lv = live.update(box)

            if lv["timeout"] and not lv["live"]:
                # quá thời gian mà chưa “live” => reset challenge
                live.reset()

            if box is None:
                print("No face")
                continue

            x1, y1, x2, y2 = box
            face = frame[y1:y2, x1:x2]
            if face.size == 0:
                continue

            q = emb.embed(face)

            best_name = "unknown"
            best_score = -1.0
            for name, embs in db.items():
                for e in embs:
                    s = cosine(q, np.array(e, dtype=np.float32))
                    if s > best_score:
                        best_score = s
                        best_name = name

            if best_score >= args.thr:
                if lv["live"]:
                    print(f"✅ AUTH OK: {best_name} score={best_score:.3f} | LIVE ✅ moved={lv['moved']:.1f}px")
                    # TODO: mở khóa tại đây (GPIO/ESP32)
                    live.reset()
                else:
                    print(f"🟡 MATCH: {best_name} score={best_score:.3f} | LIVE ❌ moved={lv['moved']:.1f}px (hãy dịch đầu nhẹ)")
            else:
                print(f"❌ unknown score={best_score:.3f} | moved={lv['moved']:.1f}px live={lv['live']}")

            time.sleep(0.03)

    except KeyboardInterrupt:
        pass
    finally:
        cam.stop()

if __name__ == "__main__":
    main()
