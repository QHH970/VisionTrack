# 瞰途 · 智能车辆视觉监测平台（VisionTrack）

> 毕业设计题目：**《基于 YOLO11 的智能车辆视觉检测与交通态势分析平台设计与实现》**
>
> 基于 Python、FastAPI、YOLO11 的车辆视觉检测系统。默认使用 `models/yolo11n.pt`，支持图片检测、视频检测流、浏览器摄像头实时检测，以及可选的 AI 交通态势分析。

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 图片检测 | 上传道路图片，返回带标注框的检测结果与车辆分类统计 |
| 视频检测 | 上传视频后逐帧推理，以 MJPEG 流实时输出检测画面 |
| 实时摄像头 | 浏览器调用本地摄像头，每 0.7 秒抽取一帧送后端检测 |
| 分类统计 | 实时统计汽车、公交车、卡车、摩托车、自行车、列车六类目标 |
| AI 态势分析 | 基于检测结果生成交通态势建议，未配置 API 时使用本地规则兜底 |

前端采用蓝色主题 Dashboard 设计：深蓝侧边导航、数据概览卡片、暗色检测画布与实时洞察栏，完整适配桌面与移动端。

## 项目结构

```text
visionsafe修改版/
├─ app.py                     # FastAPI 主入口，运行 uvicorn app:app
├─ vehicle_detector.py        # YOLO11 车辆检测、画框、统计
├─ llm_advisor.py             # 可选大模型分析，本地规则兜底
├─ requirements.txt           # Web 系统依赖
├─ templates/
│  └─ index.html              # 前端页面（瞰途 VisionTrack 蓝色主题）
├─ static/
│  ├─ app.js                  # 前端交互逻辑
│  └─ styles.css              # 前端样式（蓝色主题设计系统）
├─ models/
│  ├─ yolo11n.pt              # 当前默认模型
│  └─ best.pt                 # 备用/训练模型
├─ data/
│  ├─ images/                 # 样例图片
│  └─ videos/                 # 样例视频与历史检测视频
├─ runtime/
│  └─ uploads/                # Web 上传视频临时保存目录
└─ legacy/                    # 早期 PyQt / FastAPI / Flask 版本备份
```

## 启动

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

若 `8000` 端口被占用，可换用其他端口：

```bash
uvicorn app:app --host 0.0.0.0 --port 8001
```

浏览器访问：

```text
http://127.0.0.1:8000
```

## 后端接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 渲染监测平台首页 |
| POST | `/api/detect-image` | 上传图片并返回标注结果 |
| POST | `/api/detect-frame` | 接收 base64 帧（摄像头）并返回检测结果 |
| POST | `/api/upload-video` | 上传视频，返回视频流地址 |
| GET | `/api/stream-video/{video_id}` | 视频逐帧检测流 |
| GET | `/api/camera-stream` | 摄像头检测流 |
| GET | `/api/summary` | 最新检测统计摘要 |
| POST | `/api/ai-advice` | 生成交通态势建议 |

## 版本控制约定

仓库只提交**源码、配置与轻量必需资源**，忽略运行环境、密钥与超大文件（详见 `.gitignore`）。

| 类别 | 入库内容 | 说明 |
| --- | --- | --- |
| 核心源码 | `app.py`、`vehicle_detector.py`、`llm_advisor.py` | 主程序与检测/分析模块 |
| 前端资源 | `templates/index.html`、`static/app.js`、`static/styles.css` | 蓝色主题界面 |
| 配置文档 | `requirements.txt`、`.env.example`、`README.md`、`.gitignore` | 依赖清单与环境变量模板 |
| 必需模型 | `models/yolo11n.pt`、`models/best.pt` | 约 12MB，保证克隆后可直接运行 |
| 演示样例 | `data/images/samples/`、`data/videos/samples/` 中的两个轻量视频 | 用于功能演示 |
| 历史版本 | `legacy/` 下的 `.py`、`.cfg`、`.names` 等文本文件 | 保留技术演进过程 |

以下内容**不入库**，需本地自行准备：

- `.venv/`（约 6GB）与根目录的 `torch-*.whl`（约 2.4GB）：用 `pip install -r requirements.txt` 重建
- `.env`：复制 `.env.example` 后填写自己的 API Key
- `data/videos/samples/` 中的大视频、`legacy/**/*.weights`：单文件超 100MB，超出主流托管平台限制
- `.idea/`、`.vscode/`、`__pycache__/`、`runtime/uploads/`、`runtime/_edgeprofile/`：IDE 配置与运行临时文件


```

## 可选大模型 API

系统默认不强依赖大模型。未配置 API Key 时，会使用本地规则生成交通态势建议。

如需接入免费或兼容 OpenAI 的接口，可设置：

```bash
set FREE_LLM_API_KEY=你的key
set FREE_LLM_API_URL=https://api.siliconflow.cn/v1/chat/completions
set FREE_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```

也兼容 `SILICONFLOW_API_KEY` 作为 Key 环境变量。
