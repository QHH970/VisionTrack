# -*- coding: utf-8 -*-
"""Optional OpenAI-compatible traffic analysis summary."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict


DEFAULT_API_BASE = "https://api.siliconflow.cn/v1/chat/completions"
DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"


def build_rule_based_advice(summary: Dict[str, Any]) -> str:
    total = int(summary.get("total", 0))
    counts = summary.get("counts", {}) or {}
    if total == 0:
        return "当前画面未检测到车辆，可继续保持监测。"

    parts = [f"当前共检测到 {total} 辆/类车辆目标"]
    if counts:
        detail = "，".join(f"{name} {num}" for name, num in counts.items())
        parts.append(f"其中 {detail}")

    if total >= 10:
        parts.append("车流较密集，建议关注拥堵和异常停车。")
    elif total >= 5:
        parts.append("车流处于中等水平，建议持续观察变化趋势。")
    else:
        parts.append("车流较少，通行状态整体平稳。")
    return "；".join(parts) + "。"


def ask_llm(summary: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("FREE_LLM_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
    api_url = os.getenv("FREE_LLM_API_URL", DEFAULT_API_BASE)
    model = os.getenv("FREE_LLM_MODEL", DEFAULT_MODEL)

    if not api_key:
        return {
            "provider": "local-rules",
            "text": build_rule_based_advice(summary),
            "enabled": False,
        }

    prompt = (
        "你是交通监测值班助手。请根据车辆检测结果，用中文给出一句简短态势分析和一条处置建议。"
        "不要编造未提供的信息。检测摘要如下："
        + json.dumps(summary, ensure_ascii=False)
    )
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你只输出简洁中文交通监测建议。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        api_url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip()
        return {"provider": model, "text": text, "enabled": True}
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
        return {
            "provider": "local-rules",
            "text": build_rule_based_advice(summary),
            "enabled": False,
            "error": str(exc),
        }
