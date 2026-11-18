# VisionSafe 车辆图像检测系统

这是在原脚本项目旁边新增的 Web 版本，不影响原有 PyQt5 桌面程序。

## 功能

- 使用当前项目根目录的 `yolo11n.pt` 做车辆检测。
- 支持图片上传检测。
- 支持视频上传后逐帧检测展示。
- 支持浏览器摄像头实时检测。
- 只统计车辆相关类别：自行车、汽车、摩托车、公交车、卡车、列车。
- 可选接入免费大模型 API，未配置 key 时自动使用本地规则生成交通态势建议。

## 启动

```bash
pip install -r requirements_web.txt
python web_app.py
```

启动后打开：

```text
http://127.0.0.1:7860
```

## 可选大模型配置

复制 `.env.example` 中的配置到你的环境变量，填入免费 API Key 即可。后端使用 OpenAI-compatible 的 `chat/completions` 协议，默认示例为 SiliconFlow：

```bash
set FREE_LLM_API_KEY=你的key
set FREE_LLM_API_URL=https://api.siliconflow.cn/v1/chat/completions
set FREE_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
python web_app.py
```

也可以换成其它兼容接口，只需要修改 `FREE_LLM_API_URL` 和 `FREE_LLM_MODEL`。

## 主要文件

- `vehicle_detector.py`：YOLO11 检测、车辆类别过滤、画框和统计。
- `web_app.py`：Flask 后端接口。
- `templates/index.html`：前端页面。
- `static/app.js`：图片、视频、摄像头交互逻辑。
- `static/styles.css`：页面样式。
- `llm_advisor.py`：可选大模型分析与本地规则兜底。
