# 在项目根目录运行：
#   powershell -ExecutionPolicy Bypass -File .\整理项目.ps1

$ErrorActionPreference = "Stop"

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Move-IfExists {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        Write-Host "SKIP  $Source"
        return
    }

    if (Test-Path -LiteralPath $Destination) {
        Write-Host "KEEP  $Destination"
        return
    }

    $parent = Split-Path -Parent $Destination
    if ($parent) {
        Ensure-Dir $parent
    }

    Move-Item -LiteralPath $Source -Destination $Destination
    Write-Host "MOVE  $Source -> $Destination"
}

Ensure-Dir "models"
Ensure-Dir "data\images"
Ensure-Dir "data\videos"
Ensure-Dir "runtime\uploads"
Ensure-Dir "legacy\pyqt_yolov4"
Ensure-Dir "legacy\fastapi_draft"
Ensure-Dir "legacy\flask_version"

Move-IfExists "yolo11n.pt" "models\yolo11n.pt"
Move-IfExists "best.pt" "models\best.pt"
Move-IfExists "imgs" "data\images\samples"
Move-IfExists "video" "data\videos\samples"

Move-IfExists "DetectionTracking.py" "legacy\pyqt_yolov4\DetectionTracking.py"
Move-IfExists "Detector_Model.py" "legacy\pyqt_yolov4\Detector_Model.py"
Move-IfExists "Detector_Model-原件.py" "legacy\pyqt_yolov4\Detector_Model-原件.py"
Move-IfExists "camera_detection_tracking.py" "legacy\pyqt_yolov4\camera_detection_tracking.py"
Move-IfExists "video_detection_tracking.py" "legacy\pyqt_yolov4\video_detection_tracking.py"
Move-IfExists "main.py" "legacy\pyqt_yolov4\main.py"
Move-IfExists "image1_rc.py" "legacy\pyqt_yolov4\image1_rc.py"
Move-IfExists "logo.py" "legacy\pyqt_yolov4\logo.py"
Move-IfExists "sort.py" "legacy\pyqt_yolov4\sort.py"
Move-IfExists "yolo-obj" "legacy\pyqt_yolov4\yolo-obj"

Move-IfExists "detection.py" "legacy\fastapi_draft\detection.py"
Move-IfExists "llm.py" "legacy\fastapi_draft\llm.py"

Move-IfExists "web_app.py" "legacy\flask_version\web_app.py"
Move-IfExists "WEB_README.md" "legacy\flask_version\WEB_README.md"
Move-IfExists "requirements_web.txt" "legacy\flask_version\requirements_web.txt"

Write-Host ""
Write-Host "整理完成。当前主项目入口：uvicorn app:app --host 0.0.0.0 --port 8000"
