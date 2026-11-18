# -*- coding: utf-8 -*-
"""Flask web application for YOLO11 vehicle monitoring."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any

import cv2
from flask import Flask, Response, jsonify, render_template, request
from werkzeug.utils import secure_filename

from llm_advisor import ask_llm
from vehicle_detector import VehicleDetector, image_from_data_url, image_from_upload


ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = ROOT / "uploads"
OUTPUT_DIR = ROOT / "outputs"
ALLOWED_VIDEO = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024

detector = VehicleDetector(
    model_path=os.getenv("YOLO_MODEL", str(ROOT / "yolo11n.pt")),
    confidence=float(os.getenv("YOLO_CONF", "0.35")),
)
video_sources: dict[str, Path] = {}
latest_summary: dict[str, Any] = {"total": 0, "counts": {}, "detections": []}


@app.get("/")
def index() -> str:
    return render_template("index.html")


@app.post("/api/detect-image")
def detect_image():
    if "image" not in request.files:
        return jsonify({"error": "请上传图片文件。"}), 400
    try:
        image = image_from_upload(request.files["image"])
        result = detector.detect(image)
        remember_summary(result.to_payload(include_image=False))
        return jsonify(result.to_payload())
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/detect-frame")
def detect_frame():
    data = request.get_json(silent=True) or {}
    if not data.get("image"):
        return jsonify({"error": "缺少摄像头画面。"}), 400
    try:
        image = image_from_data_url(data["image"])
        result = detector.detect(image)
        payload = result.to_payload()
        remember_summary(payload)
        return jsonify(payload)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/upload-video")
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "请上传视频文件。"}), 400
    file = request.files["video"]
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_VIDEO:
        return jsonify({"error": "请上传 mp4、avi、mov、mkv 或 webm 视频。"}), 400

    video_id = uuid.uuid4().hex
    filename = secure_filename(file.filename or f"video{suffix}")
    path = UPLOAD_DIR / f"{video_id}_{filename}"
    file.save(path)
    video_sources[video_id] = path
    return jsonify({"video_id": video_id, "stream_url": f"/api/stream-video/{video_id}"})


@app.get("/api/stream-video/<video_id>")
def stream_video(video_id: str):
    path = video_sources.get(video_id)
    if not path or not path.exists():
        return jsonify({"error": "视频不存在或已被清理。"}), 404
    return Response(
        generate_video_stream(path),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/camera-stream")
def camera_stream():
    camera_id = int(request.args.get("id", "0"))
    return Response(
        generate_camera_stream(camera_id),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/summary")
def summary():
    return jsonify(latest_summary)


@app.post("/api/ai-advice")
def ai_advice():
    data = request.get_json(silent=True) or latest_summary
    return jsonify(ask_llm(data))


def remember_summary(payload: dict[str, Any]) -> None:
    global latest_summary
    latest_summary = {
        "total": payload.get("total", 0),
        "counts": payload.get("counts", {}),
        "detections": payload.get("detections", []),
        "elapsed_ms": payload.get("elapsed_ms"),
        "updated_at": int(time.time()),
    }


def generate_video_stream(path: Path):
    capture = cv2.VideoCapture(str(path))
    try:
        while capture.isOpened():
            ok, frame = capture.read()
            if not ok:
                break
            result = detector.detect(frame)
            remember_summary(result.to_payload(include_image=False))
            yield multipart_jpeg(result.image)
    finally:
        capture.release()


def generate_camera_stream(camera_id: int):
    capture = cv2.VideoCapture(camera_id)
    try:
        while capture.isOpened():
            ok, frame = capture.read()
            if not ok:
                break
            result = detector.detect(frame)
            remember_summary(result.to_payload(include_image=False))
            yield multipart_jpeg(result.image)
    finally:
        capture.release()


def multipart_jpeg(image):
    ok, buffer = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        return b""
    return (
        b"--frame\r\n"
        b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
