import time
import argparse

from camera import Camera
from detector import FaceDetectorDNN
from embedder import FaceEmbedder
from database import load_db, save_db

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--samples", type=int, default=20)
    ap.add_argument("--cam", type=int, default=0)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=480)
    ap.add_argument("--model", default="models/facenet.tflite")
    ap.add_argument("--conf", type=float, default=0.6)
    ap.add_argument("--sleep", type=float, default=0.15)
    args = ap.parse_args()

    db = load_db()
    db.setdefault(args.name, [])

    cam = Camera(src=args.cam, width=args.width, height=args.height).start()
    det = FaceDetectorDNN(conf_th=args.conf)
    emb = FaceEmbedder(args.model)

    print(f"ENROLL '{args.name}' | need {args.samples} samples")
    print("Tips: đủ sáng, nhìn thẳng, hơi nghiêng trái/phải một chút.")

    try:
        while len(db[args.name]) < args.samples:
            frame = cam.read()
            if frame is None:
                continue

            box = det.detect_largest(frame)
            if box is None:
                print("No face...", end="\r")
                continue

            x1, y1, x2, y2 = box
            face = frame[y1:y2, x1:x2]
            if face.size == 0:
                continue

            vec = emb.embed(face)
            db[args.name].append(vec.tolist())
            print(f"Collected {len(db[args.name])}/{args.samples}   ", end="\r")
            time.sleep(args.sleep)

        save_db(db)
        print(f"\nSaved to face_db.json (user={args.name}, total={len(db[args.name])})")

    finally:
        cam.stop()

if __name__ == "__main__":
    main()
