"""SOUL - 用户笑点画像存储

文件：项目根目录 soul.md
格式：Markdown + frontmatter + 嵌入 JSON 数据块（兼容 OpenClaw SOUL.md）

数据结构：
  profile: 笑点维度评分 {dim: score}
  liked:   用户点赞过的梗图列表（最多 50 条）
"""
from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from . import config

SOUL_PATH = config.ROOT / "soul.md"

DIM_LABELS = {
    "dark": "黑色幽默",
    "workplace": "职场吐槽",
    "technical": "技术自嘲",
    "absurd": "无厘头/抽象",
    "pun": "谐音文字梗",
    "contrast": "反差萌",
    "cold": "冷幽默",
    "self_deprecating": "自嘲",
}


def load() -> dict:
    if not SOUL_PATH.exists():
        return {"profile": {}, "liked": []}
    txt = SOUL_PATH.read_text(encoding="utf-8")
    m = re.search(r"```json\s*\n(.*?)\n```", txt, re.DOTALL)
    if not m:
        return {"profile": {}, "liked": []}
    try:
        return json.loads(m.group(1))
    except Exception:
        return {"profile": {}, "liked": []}


def save(data: dict) -> None:
    profile = data.get("profile", {})
    liked = data.get("liked", [])
    body = _format_profile_md(profile)
    md = f"""---
name: 用户笑点画像
type: user-memory
schema: openclaw-soul-v1
updated: {datetime.now().isoformat(timespec='seconds')}
---

# 虾总笑点画像 · SOUL

> 本文件由「虾评爆点」自动维护，记录你的笑点偏好与梗倾向。
> 兼容 OpenClaw SOUL.md 规范，会被注入到 LLM prompt 中影响后续梗图生成方向。

## 维度评分（0-10）

{body}

## 最近喜欢的梗（共 {len(liked)} 条，最多保留 50）

{_format_liked_md(liked)}

## 原始数据

```json
{json.dumps(data, ensure_ascii=False, indent=2)}
```
"""
    SOUL_PATH.write_text(md, encoding="utf-8")


def _format_profile_md(profile: dict) -> str:
    if not profile:
        return "_尚未完成笑点测试，运行 `python -m meme_hunter quiz` 开始_"
    lines = []
    for k, v in sorted(profile.items(), key=lambda x: -x[1]):
        label = DIM_LABELS.get(k, k)
        bar = "█" * int(v) + "·" * (10 - int(v))
        lines.append(f"- **{label}** ({k}): `{bar}` {v}")
    return "\n".join(lines)


def _format_liked_md(liked: list) -> str:
    if not liked:
        return "_暂无。打开梗图墙点「戳到我了」按钮即可记入_"
    lines = []
    for m in liked[:10]:
        lines.append(f"- 「{m.get('top','')}」/「{m.get('bottom','')}」 — _{m.get('title','')[:30]}_")
    if len(liked) > 10:
        lines.append(f"- ……（另有 {len(liked) - 10} 条）")
    return "\n".join(lines)


def add_liked(meme: dict) -> int:
    data = load()
    liked = data.get("liked", [])
    key = (meme.get("title", ""), meme.get("top", ""), meme.get("bottom", ""))
    liked = [m for m in liked if (m.get("title", ""), m.get("top", ""), m.get("bottom", "")) != key]
    liked.insert(0, {**meme, "ts": datetime.now().isoformat(timespec="seconds")})
    data["liked"] = liked[:50]
    save(data)

    # 自循环触发：每 5 次点赞自动 reflect 一次
    if len(data["liked"]) % 5 == 0:
        try:
            reflect_and_update()
        except Exception as e:
            print(f"  [reflect] 失败: {e}")
    return len(data["liked"])


def reflect_and_update() -> dict:
    """自循环核心：用 LLM 分析全部 liked，重新校准 profile + 提取风格关键词

    每次会更新：
      - profile: 维度评分
      - style_keywords: 用户最爱的梗风格关键词
      - iterations: 自循环次数
    """
    from .llm import chat  # 延迟导入避免循环

    data = load()
    liked = data.get("liked", [])
    if len(liked) < 3:
        print("  [reflect] 样本不足，跳过")
        return data

    samples = "\n".join(
        f"- 梗{i+1}：「{m.get('top','')}」/「{m.get('bottom','')}」 (源自 {m.get('title','')[:20]})"
        for i, m in enumerate(liked[:20])
    )
    dims_str = "、".join(f"{k}({v})" for k, v in DIM_LABELS.items())

    sys = "你是用户笑点画像分析师。根据用户喜欢的梗，输出严格 JSON。"
    usr = f"""以下是用户最近赞过的梗：
{samples}

请分析后输出 JSON（不要 markdown，不要解释）：
{{
  "profile": {{ "dark": 0-10, "workplace": 0-10, "technical": 0-10, "absurd": 0-10, "pun": 0-10, "contrast": 0-10, "cold": 0-10, "self_deprecating": 0-10 }},
  "style_keywords": ["最具代表性的 5-8 个风格关键词，如：黑色幽默、职场反差、自嘲式凡尔赛"],
  "summary": "一句话总结用户的笑点偏好"
}}

维度参考：{dims_str}"""

    raw = chat(sys, usr)
    parsed = _extract_json_loose(raw)
    if not parsed:
        print("  [reflect] LLM 返回无法解析，保持原画像")
        return data

    data["profile"] = parsed.get("profile", data.get("profile", {}))
    data["style_keywords"] = parsed.get("style_keywords", [])
    data["summary"] = parsed.get("summary", "")
    data["iterations"] = data.get("iterations", 0) + 1
    save(data)
    print(f"  [reflect] 第 {data['iterations']} 轮自循环完成 — {data.get('summary','')}")
    return data


def _extract_json_loose(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


def update_profile(profile: dict) -> None:
    data = load()
    data["profile"] = profile
    save(data)


def get_preference_hint() -> str:
    """生成给 LLM 的偏好提示，无数据则返回空串"""
    data = load()
    profile = data.get("profile", {})
    liked = data.get("liked", [])
    keywords = data.get("style_keywords", [])
    summary = data.get("summary", "")
    iterations = data.get("iterations", 0)

    if not profile and not liked:
        return ""

    parts = ["", "【用户笑点画像 · 必须参考（自循环已迭代 %d 轮）】" % iterations]
    if summary:
        parts.append(f"画像总结: {summary}")
    if profile:
        top = sorted(profile.items(), key=lambda x: -x[1])[:3]
        names = [f"{DIM_LABELS.get(k, k)}({v}/10)" for k, v in top]
        parts.append("最爱笑点维度: " + "、".join(names))
    if keywords:
        parts.append("风格关键词: " + "、".join(keywords))
    if liked:
        parts.append("近期赞过的梗（参考风格）:")
        for m in liked[:5]:
            parts.append(f"  · 「{m.get('top','')}」/「{m.get('bottom','')}」")
    parts.append("请让本次梗图明显朝以上方向倾斜。")
    return "\n".join(parts)
