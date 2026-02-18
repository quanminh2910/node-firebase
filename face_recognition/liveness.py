import time
import math

class LivenessMove:
    """
    Live nếu trong time_window_s, tâm bounding box di chuyển >= move_px.
    """
    def __init__(self, time_window_s=6.0, move_px=25):
        self.time_window_s = float(time_window_s)
        self.move_px = float(move_px)
        self.reset()

    def reset(self):
        self.start_t = time.time()
        self.first_center = None
        self.live = False

    def update(self, box):
        """
        box: (x1,y1,x2,y2) hoặc None
        return: dict(live, moved, timeout)
        """
        now = time.time()
        timeout = (now - self.start_t) > self.time_window_s

        if box is None:
            return {"live": self.live, "moved": 0.0, "timeout": timeout}

        x1, y1, x2, y2 = box
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        if self.first_center is None:
            self.first_center = (cx, cy)

        moved = math.hypot(cx - self.first_center[0], cy - self.first_center[1])

        if moved >= self.move_px:
            self.live = True

        return {"live": self.live, "moved": moved, "timeout": timeout}
