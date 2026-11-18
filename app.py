# -*- coding: utf-8 -*-
"""瞰途 VisionTrack · 智能车辆视觉监测平台 FastAPI 入口。"""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.requests import Request

from llm_advisor import ask_llm
from vehicle_detector import VehicleDetector, image_from_bytes, image_from_data_url


ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models"
UPLOAD_DIR = ROOT / "runtime" / "uploads"
ALLOWED_VIDEO = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="瞰途 VisionTrack · 智能车辆视觉监测平台")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")


def default_model_path() -> Path:
    configured = os.getenv("YOLO_MODEL") or os.getenv("MODEL_PATH")
    if configured:
        return Path(configured)
    model_in_models = MODEL_DIR / "yolo11n.pt"
    if model_in_models.exists():
        return model_in_models
    return ROOT / "yolo11n.pt"


detector = VehicleDetector(
    model_path=default_model_path(),
    confidence=float(os.getenv("YOLO_CONF", os.getenv("CONF", "0.35"))),
)
video_sources: Dict[str, Path] = {}
latest_summary: Dict[str, Any] = {"total": 0, "counts": {}, "detections": []}


class FramePayload(BaseModel):
    image: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/detect-image")
async def detect_image(image: UploadFile = File(...)):
    try:
        frame = image_from_bytes(await image.read())
        result = detector.detect(frame)
        payload = result.to_payload()
        remember_summary(payload)
        return JSONResponse(payload)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@app.post("/api/detect-frame")
async def detect_frame(payload: FramePayload):
    try:
        frame = image_from_data_url(payload.image)
        result = detector.detect(frame)
        data = result.to_payload()
        remember_summary(data)
        return JSONResponse(data)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@app.post("/api/upload-video")
async def upload_video(video: UploadFile = File(...)):
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in ALLOWED_VIDEO:
        return JSONResponse(
            {"error": "请上传 mp4、avi、mov、mkv 或 webm 视频。"},
            status_code=400,
        )

    video_id = uuid.uuid4().hex
    safe_name = Path(video.filename or f"video{suffix}").name
    target = UPLOAD_DIR / f"{video_id}_{safe_name}"
    target.write_bytes(await video.read())
    video_sources[video_id] = target
    return {"video_id": video_id, "stream_url": f"/api/stream-video/{video_id}"}


@app.get("/api/stream-video/{video_id}")
async def stream_video(video_id: str):
    path = video_sources.get(video_id)
    if not path or not path.exists():
        return JSONResponse({"error": "视频不存在或已被清理。"}, status_code=404)
    return StreamingResponse(
        generate_video_stream(path),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/camera-stream")
async def camera_stream(camera_id: int = 0):
    return StreamingResponse(
        generate_camera_stream(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/summary")
async def summary():
    return latest_summary


@app.post("/api/ai-advice")
async def ai_advice(summary_payload: Optional[Dict[str, Any]] = None):
    return ask_llm(summary_payload or latest_summary)


def remember_summary(payload: Dict[str, Any]) -> None:
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
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
