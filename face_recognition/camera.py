import cv2
import threading
import time

class Camera:
    """
    Threaded camera capture: luôn giữ frame mới nhất để xử lý mượt hơn (giống ý tưởng parallel capture).
    """
    def __init__(self, src=0, width=640, height=480):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self._lock = threading.Lock()
        self._frame = None
        self._running = False

    def start(self):
        self._running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()
        # đợi chút để có frame đầu
        time.sleep(0.2)
        return self

    def _loop(self):
        while self._running:
            ok, frame = self.cap.read()
            if ok:
                with self._lock:
                    self._frame = frame

    def read(self):
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def stop(self):
        self._running = False
        try:
            self.cap.release()
        except Exception:
            pass
