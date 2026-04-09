"""LLM 适配层

优先级：Qwen (DashScope) > DeepSeek API > 本地 claude CLI > 内置规则降级
所有调用通过 chat(system, user) -> str 统一接口。

兼容多 provider，便于在比赛环境（DashScope key）和本地开发（claude CLI）无缝切换。
"""
from __future__ import annotations
import json
import shutil
import subprocess
from typing import Optional
import httpx

from . import config


def chat(system: str, user: str, model: Optional[str] = None) -> str:
    """统一 LLM 入口，自动选择可用 provider

    优先使用 DashScope Qwen（与 Wan2.7 共用同一个 API Key，最方便）
    """
    providers = []
    if config.DASHSCOPE_API_KEY:
        providers.append(("qwen", lambda: _chat_qwen(system, user, model or config.QWEN_MODEL)))
    if config.DEEPSEEK_API_KEY:
        providers.append(("deepseek", lambda: _chat_deepseek(system, user, model or "deepseek-chat")))
    if getattr(config, "MINIMAX_API_KEY", ""):
        providers.append(("minimax", lambda: _chat_openai_compat(
            system, user, model or "abab7-chat",
            config.MINIMAX_API_KEY, "https://api.minimax.chat/v1/text/chatcompletion_v2")))
    if getattr(config, "GLM_API_KEY", ""):
        providers.append(("glm", lambda: _chat_openai_compat(
            system, user, model or "glm-4-plus",
            config.GLM_API_KEY, "https://open.bigmodel.cn/api/paas/v4/chat/completions")))
    if getattr(config, "NANO_BANANA_API_KEY", ""):
        providers.append(("nano-banana", lambda: _chat_openai_compat(
            system, user, model or "step-2-16k",
            config.NANO_BANANA_API_KEY, "https://api.stepfun.com/v1/chat/completions")))
    if config.OPENAI_API_KEY:
        providers.append(("openai", lambda: _chat_openai_compat(
            system, user, model or "gpt-4o",
            config.OPENAI_API_KEY, "https://api.openai.com/v1/chat/completions")))
    if shutil.which("claude"):
        providers.append(("claude-cli", lambda: _chat_claude_cli(system, user, model or "claude-sonnet-4-5-20250514")))

    for name, fn in providers:
        try:
            return fn()
        except Exception as e:
            print(f"  [warn] {name} 调用失败: {e}")
            continue

    print("  [warn] 所有 LLM provider 不可用，使用规则降级")
    return _rule_fallback(user)


def _chat_qwen(system: str, user: str, model: str) -> str:
    """阿里 DashScope Qwen 系列（OpenAI 兼容模式）

    支持的 model：qwen-plus / qwen-max / qwen-turbo / qwen3-* 等
    与 Wan2.7 共用同一个 DASHSCOPE_API_KEY，零额外配置
    """
    r = httpx.post(
        f"{config.DASHSCOPE_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {config.DASHSCOPE_API_KEY}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.9,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _chat_deepseek(system: str, user: str, model: str) -> str:
    r = httpx.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.9,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _chat_claude_cli(system: str, user: str, model: str) -> str:
    cmd = ["claude", "-p", "--model", model, "--output-format", "text",
           "--system-prompt", system]
    proc = subprocess.run(
        cmd, input=user.encode("utf-8"),
        capture_output=True, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"claude CLI 失败: {proc.stderr.decode('utf-8', errors='replace')}")
    return proc.stdout.decode("utf-8").strip()


def _chat_openai_compat(system: str, user: str, model: str, api_key: str, base_url: str) -> str:
    """OpenAI 兼容 API（MiniMax / GLM / Nano Banana / OpenAI 通用）"""
    r = httpx.post(
        base_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.9,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _rule_fallback(user: str) -> str:
    """无 LLM 时的兜底，返回简单 JSON 格式梗图方案"""
    return json.dumps({
        "meme_point": "现实和理想的反差",
        "image_prompt": "一个充满黑色幽默的场景，电影感打光，写实风格",
        "top_text": "理想很丰满",
        "bottom_text": "现实很骨感",
    }, ensure_ascii=False)
