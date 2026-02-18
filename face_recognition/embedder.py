import cv2
import numpy as np
from tflite_runtime.interpreter import Interpreter

class FaceEmbedder:
    """
    TFLite embedding model (FaceNet/MobileFaceNet style).
    """
    def __init__(self, model_path: str, num_threads: int = 2):
        self.interpreter = Interpreter(model_path=model_path, num_threads=num_threads)
        self.interpreter.allocate_tensors()
        self.inp = self.interpreter.get_input_details()[0]
        self.out = self.interpreter.get_output_details()[0]

        shape = self.inp["shape"]  # [1,H,W,3]
        self.in_h = int(shape[1])
        self.in_w = int(shape[2])

    def _preprocess(self, face_bgr: np.ndarray) -> np.ndarray:
        face = cv2.resize(face_bgr, (self.in_w, self.in_h), interpolation=cv2.INTER_LINEAR)
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

        x = face.astype(np.float32)
        # Standardization (hay dùng cho FaceNet)
        x = (x - x.mean()) / (x.std() + 1e-6)
        x = np.expand_dims(x, axis=0)  # [1,H,W,3]
        return x

    def embed(self, face_bgr: np.ndarray) -> np.ndarray:
        x = self._preprocess(face_bgr)
        self.interpreter.set_tensor(self.inp["index"], x)
        self.interpreter.invoke()
        emb = self.interpreter.get_tensor(self.out["index"])[0].astype(np.float32)

        # L2 normalize
        return emb / (np.linalg.norm(emb) + 1e-9)
