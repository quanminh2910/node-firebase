import cv2

class FaceDetectorDNN:
    """
    OpenCV DNN ResNet-10 SSD face detector.
    """
    def __init__(self,
                 prototxt="models/opencv_fd/deploy.prototxt",
                 model="models/opencv_fd/res10.caffemodel",
                 conf_th=0.6):
        self.net = cv2.dnn.readNetFromCaffe(prototxt, model)
        self.conf_th = conf_th

    def detect_largest(self, frame_bgr):
        """
        Return (x1,y1,x2,y2) of largest face or None
        """
        h, w = frame_bgr.shape[:2]
        blob = cv2.dnn.blobFromImage(
            frame_bgr, 1.0, (300, 300),
            (104.0, 177.0, 123.0), swapRB=False, crop=False
        )
        self.net.setInput(blob)
        dets = self.net.forward()  # (1,1,N,7)

        best = None
        best_area = 0

        for i in range(dets.shape[2]):
            conf = float(dets[0, 0, i, 2])
            if conf < self.conf_th:
                continue

            x1 = int(dets[0, 0, i, 3] * w)
            y1 = int(dets[0, 0, i, 4] * h)
            x2 = int(dets[0, 0, i, 5] * w)
            y2 = int(dets[0, 0, i, 6] * h)

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)

            area = max(0, x2 - x1) * max(0, y2 - y1)
            if area > best_area:
                best_area = area
                best = (x1, y1, x2, y2)

        return best
