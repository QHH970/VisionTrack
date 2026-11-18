# -*- coding: utf-8 -*-
"""Vehicle detection helpers powered by YOLO11."""

from __future__ import annotations

import base64
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Union

import cv2
import numpy as np
from ultralytics import YOLO


VEHICLE_CLASS_NAMES = {
    "bicycle",
    "car",
    "motorcycle",
    "bus",
    "truck",
    "train",
}

CLASS_NAME_CN = {
    "bicycle": "自行车",
    "car": "汽车",
    "motorcycle": "摩托车",
    "bus": "公交车",
    "truck": "卡车",
    "train": "列车",
}


@dataclass
class DetectionResult:
    image: np.ndarray
    detections: List[Dict[str, Any]]
    counts: Dict[str, int]
    total: int
    elapsed_ms: int

    def to_payload(self, include_image: bool = True) -> Dict[str, Any]:
        payload = {
            "detections": self.detections,
            "counts": self.counts,
            "total": self.total,
            "elapsed_ms": self.elapsed_ms,
        }
        if include_image:
            payload["image"] = encode_jpeg_data_url(self.image)
        return payload


class VehicleDetector:
    def __init__(
        self,
        model_path: Union[str, Path] = "yolo11n.pt",
        confidence: float = 0.35,
        image_size: int = 640,
    ) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"未找到模型文件: {self.model_path.resolve()}")
        self.confidence = confidence
        self.image_size = image_size
        self.model = YOLO(str(self.model_path))
        self.names = self.model.names

    def detect(self, frame: np.ndarray) -> DetectionResult:
        started = time.perf_counter()
        result = self.model.predict(
            frame,
            conf=self.confidence,
            imgsz=self.image_size,
            verbose=False,
        )[0]
        annotated = frame.copy()
        detections: List[Dict[str, Any]] = []

        for box in result.boxes:
            cls_id = int(box.cls[0])
            name = str(self.names.get(cls_id, cls_id))
            if name not in VEHICLE_CLASS_NAMES:
                continue

            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            conf = float(box.conf[0])
            cn_name = CLASS_NAME_CN.get(name, name)
            detections.append(
                {
                    "class_id": cls_id,
                    "name": name,
                    "label": cn_name,
                    "confidence": round(conf, 4),
                    "box": [x1, y1, x2, y2],
                }
            )

            color = color_for_class(cls_id)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            text = f"{name} {conf:.2f}"
            draw_label(annotated, text, x1, y1, color)

        counts = Counter(item["label"] for item in detections)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return DetectionResult(
            image=annotated,
            detections=detections,
            counts=dict(counts),
            total=len(detections),
            elapsed_ms=elapsed_ms,
        )


def color_for_class(class_id: int):
    palette = [
        (24, 148, 255),
        (40, 180, 99),
        (244, 180, 0),
        (214, 64, 69),
        (127, 90, 240),
        (0, 170, 170),
    ]
    return palette[class_id % len(palette)]


def draw_label(
    image: np.ndarray,
    text: str,
    x: int,
    y: int,
    color,
) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.58
    thickness = 2
    (tw, th), baseline = cv2.getTextSize(text, font, scale, thickness)
    y0 = max(y - th - baseline - 8, 0)
    cv2.rectangle(image, (x, y0), (x + tw + 10, y0 + th + baseline + 8), color, -1)
    cv2.putText(
        image,
        text,
        (x + 5, y0 + th + 3),
        font,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


def image_from_upload(file_storage: Any) -> np.ndarray:
    data = np.frombuffer(file_storage.read(), dtype=np.uint8)
    return image_from_bytes(data)


def image_from_bytes(raw: Union[bytes, np.ndarray]) -> np.ndarray:
    data = raw if isinstance(raw, np.ndarray) else np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("无法读取图片，请上传 jpg、png 或 bmp 格式文件。")
    return image


def image_from_data_url(data_url: str) -> np.ndarray:
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    raw = base64.b64decode(data_url)
    data = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("无法解析摄像头画面。")
    return image


def encode_jpeg_data_url(image: np.ndarray, quality: int = 88) -> str:
    ok, buffer = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise ValueError("图片编码失败。")
    encoded = base64.b64encode(buffer).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"
