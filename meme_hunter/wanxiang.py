"""通义万相 Wan2.7 客户端 (真实接入 + mock 降级)

真实模式：使用 dashscope SDK 调用 wan2.7-image 模型
  - 支持 enable_sequential=True 保证同一只虾总外形一致
  - 自动下载图片到本地

降级模式：DASHSCOPE_API_KEY 缺失或调用失败时生成占位渐变图
"""
from __future__ import annotations
import hashlib
import random
from pathlib import Path
from typing import List, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFilter

from . import config


WAN_MODEL = "wan2.7-image"  # 比赛指定模型


# ==================== 真实 Wan2.7 调用 ====================

def _generate_wan(prompt: str, size: str, n: int) -> List[Path]:
    """调用真实 Wan2.7 API，下载图片到本地，返回路径列表"""
    import dashscope
    from dashscope.aigc.image_generation import ImageGeneration
    from dashscope.api_entities.dashscope_response import Message

    dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

    # Wan2.7 size 接受 "2K" / "1K" / "1024*1024" 等
    wan_size = _normalize_size(size)

    msg = Message(role="user", content=[{"text": prompt}])

    rsp = ImageGeneration.call(
        model=WAN_MODEL,
        api_key=config.DASHSCOPE_API_KEY,
        messages=[msg],
        enable_sequential=(n > 1),  # 多图时启用序列模式保持一致性
        n=n,
        size=wan_size,
    )

    # 解析响应取出图片 URL
    urls = _extract_urls(rsp)
    if not urls:
        raise RuntimeError(f"Wan2.7 未返回图片: {rsp}")

    # 下载到本地
    paths: List[Path] = []
    seed = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:10]
    for i, url in enumerate(urls):
        out = config.RAW_DIR / f"{seed}_{i}.png"
        with httpx.stream("GET", url, timeout=120) as r:
            r.raise_for_status()
            with open(out, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
        paths.append(out)
    return paths


def _normalize_size(size: str) -> str:
    """把 '1024*1024' 之类映射到 Wan2.7 接受的尺寸"""
    s = size.lower().strip()
    if s in ("2k", "1k", "4k"):
        return s.upper()
    # 兼容 1024*1024 这类格式
    return size


def _extract_urls(rsp) -> List[str]:
    """从 dashscope 响应中提取图片 URL，兼容多种字段名"""
    urls: List[str] = []
    try:
        out = getattr(rsp, "output", None) or rsp.get("output", {})
        # 字段一：results
        for item in (out.get("results") or []):
            url = item.get("url") or item.get("image_url")
            if url:
                urls.append(url)
        # 字段二：images
        if not urls:
            for item in (out.get("images") or []):
                if isinstance(item, dict):
                    url = item.get("url") or item.get("image_url")
                    if url:
                        urls.append(url)
                elif isinstance(item, str):
                    urls.append(item)
        # 字段三：choices[].message.content[].image
        if not urls:
            for ch in (out.get("choices") or []):
                content = (ch.get("message") or {}).get("content", [])
                for c in content:
                    if isinstance(c, dict) and c.get("image"):
                        urls.append(c["image"])
    except Exception as e:
        print(f"  [wan2.7] 解析响应失败: {e}")
    return urls


# ==================== Mock 降级（保留）====================

PALETTES: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = [
    ((26, 26, 26), (200, 168, 130)),
    ((45, 45, 45), (232, 213, 192)),
    ((58, 58, 58), (245, 240, 235)),
    ((26, 26, 26), (85, 85, 85)),
]


def _seeded_rng(seed_str: str) -> random.Random:
    h = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest(), 16)
    return random.Random(h)


def _make_gradient(w: int, h: int, c1, c2) -> Image.Image:
    img = Image.new("RGB", (w, h), c1)
    top = Image.new("RGB", (w, h), c2)
    mask = Image.linear_gradient("L").resize((w, h))
    img.paste(top, (0, 0), mask)
    return img


def _generate_mock(prompt: str, size: str, n: int) -> List[Path]:
    try:
        w, h = (int(x) for x in size.lower().split("*"))
    except Exception:
        w, h = 1024, 1024
    rng = _seeded_rng(prompt)
    paths: List[Path] = []
    for i in range(n):
        c1, c2 = rng.choice(PALETTES)
        img = _make_gradient(w, h, c1, c2)
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, w, 4], fill=(200, 168, 130))
        cx, cy, r = w // 2, h // 2, min(w, h) // 5
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(250, 250, 250), width=2)
        try:
            font = _load_cjk_font(28)
            label = "[MOCK] " + prompt[:20]
            tw = draw.textlength(label, font=font)
            draw.text((cx - tw / 2, cy + r + 16), label, fill=(250, 250, 250), font=font)
        except Exception:
            pass
        out = config.RAW_DIR / f"{hashlib.md5(prompt.encode()).hexdigest()[:10]}_{i}.png"
        img.save(out)
        paths.append(out)
    return paths


def _load_cjk_font(size: int):
    from PIL import ImageFont
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


# ==================== 主入口 ====================

def generate(prompt: str, size: str = "1024*1024", n: int = 1, negative_prompt: str = "") -> List[Path]:
    """生成图片，优先真实 Wan2.7，失败则降级 mock"""
    if config.DASHSCOPE_API_KEY:
        try:
            print(f"  [wan2.7] 调用真实 API (size={size}, n={n})")
            return _generate_wan(prompt, size, n)
        except Exception as e:
            print(f"  [wan2.7] 真实调用失败，降级 mock: {e}")
    return _generate_mock(prompt, size, n)
