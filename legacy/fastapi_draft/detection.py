# -*- coding: utf-8 -*-
import cv2
import numpy as np
from ultralytics import YOLO
import threading


class YOLODetector:
    def __init__(self, model_path="yolo11n.pt", conf=0.4):
        self.model_path = model_path
        self.conf = conf
        self.model = None
        self.lock = threading.Lock()
        self._load()

    def _load(self):
        try:
            self.model = YOLO(self.model_path)
            print(f"Loaded model: {self.model_path}")
        except Exception as e:
            print("Failed to load model:", e)
            self.model = None

    def predict(self, frame):
        """Run detection on a BGR OpenCV frame. Returns dict with boxes, scores, classes and annotated image bytes."""
        if self.model is None:
            return {"boxes": [], "scores": [], "classes": [], "image": None}

        # ultralytics expects RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        with self.lock:
            results = self.model.predict(rgb, conf=self.conf, verbose=False)

        boxes = []
        scores = []
        classes = []
        # results[0].boxes contains Box objects
        for box in results[0].boxes:
            xyxy = box.xyxy[0].cpu().numpy() if hasattr(box.xyxy[0], 'cpu') else box.xyxy[0].numpy()
            x1, y1, x2, y2 = [int(v) for v in xyxy]
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            boxes.append([x1, y1, x2, y2])
            scores.append(conf)
            classes.append(cls)

        ann = frame.copy()
        for (b, s, c) in zip(boxes, scores, classes):
            x1, y1, x2, y2 = b
            color = (0, 255, 0)
            cv2.rectangle(ann, (x1, y1), (x2, y2), color, 2)
            label = f"{c}:{s:.2f}"
            cv2.putText(ann, label, (x1, max(10, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        ret, jpeg = cv2.imencode('.jpg', ann)
        img_bytes = jpeg.tobytes() if ret else None

        return {"boxes": boxes, "scores": scores, "classes": classes, "image": img_bytes}


def mjpeg_stream(camera_source=0, detector=None):
    """Generator yielding MJPEG frames with detections overlayed."""
    cap = cv2.VideoCapture(camera_source)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera or video source")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if detector is not None:
                res = detector.predict(frame)
                frame_bytes = res.get('image')
                if frame_bytes is None:
                    # fallback: encode original
                    ret2, jpeg = cv2.imencode('.jpg', frame)
                    frame_bytes = jpeg.tobytes()
            else:
                ret2, jpeg = cv2.imencode('.jpg', frame)
                frame_bytes = jpeg.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()
