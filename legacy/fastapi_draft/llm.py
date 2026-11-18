# -*- coding: utf-8 -*-
import os
import requests


def summarize_counts(counts: dict) -> str:
    """给定检测的类别计数，使用 Hugging Face Inference API（若提供 TOKEN）生成简短报告；否则返回本地生成的文本。"""
    hf_token = os.environ.get('HF_TOKEN')
    prompt = f"车辆检测结果统计：{counts}。请生成简短中文总结（1-2句）。"

    if not hf_token:
        # 本地简单总结
        parts = [f"类别{cls} {n}个" for cls, n in counts.items()]
        return "，".join(parts)

    headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
    model = os.environ.get('HF_MODEL', 'gpt2')
    url = f"https://api-inference.huggingface.co/models/{model}"
    try:
        resp = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # HF 文本生成返回可能在多个字段，根据模型不同而异
            if isinstance(data, list) and len(data) > 0 and 'generated_text' in data[0]:
                return data[0]['generated_text']
            # 退回到简单摘要
            parts = [f"类别{cls} {n}个" for cls, n in counts.items()]
            return "，".join(parts)
        else:
            return f"LLM 返回状态码 {resp.status_code}，使用本地摘要。"
    except Exception as e:
        return f"调用 LLM 失败：{e}，使用本地摘要。"
