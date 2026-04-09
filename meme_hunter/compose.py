"""梗图合成：在底图上烧录上联/下联文字 + 来源水印"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw

from . import config
from .wanxiang import _load_cjk_font
from .prompt_builder import MemeIdea


def compose_meme(idea: MemeIdea, base_image: Path) -> Path:
    """在底图上加上联/下联+水印，输出最终梗图"""
    img = Image.open(base_image).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)

    # 顶部黑条 + 上联
    bar_h = int(h * 0.13)
    draw.rectangle([0, 0, w, bar_h], fill=(26, 26, 26))
    draw.rectangle([0, bar_h, w, bar_h + 3], fill=(200, 168, 130))
    _draw_centered(draw, idea.top_text, (w // 2, bar_h // 2), w, font_size=int(h * 0.055), color=(250, 250, 250))

    # 底部黑条 + 下联
    draw.rectangle([0, h - bar_h, w, h], fill=(26, 26, 26))
    draw.rectangle([0, h - bar_h - 3, w, h - bar_h], fill=(200, 168, 130))
    _draw_centered(draw, idea.bottom_text, (w // 2, h - bar_h // 2), w, font_size=int(h * 0.055), color=(250, 250, 250))

    # 右下角水印
    wm = f"@虾评爆点 · 虾总 · {idea.source_item.source}"
    font = _load_cjk_font(int(h * 0.022))
    tw = draw.textlength(wm, font=font)
    draw.text((w - tw - 20, h - bar_h - 28), wm, fill=(200, 168, 130), font=font)

    safe_title = "".join(c for c in idea.source_item.title if c.isalnum() or c in "_-")[:30]
    out = config.MEME_DIR / f"{safe_title or 'meme'}_{base_image.stem}.png"
    img.save(out)
    return out


def _draw_centered(draw, text, center, max_w, font_size, color):
    font = _load_cjk_font(font_size)
    # 简易自动缩放，超宽则减小
    while font_size > 12 and draw.textlength(text, font=font) > max_w * 0.92:
        font_size -= 2
        font = _load_cjk_font(font_size)
    tw = draw.textlength(text, font=font)
    cx, cy = center
    draw.text((cx - tw / 2, cy - font_size / 2), text, fill=color, font=font)
