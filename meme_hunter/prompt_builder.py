"""把热点新闻 → 拟人龙虾梗点 → 出图 prompt + 上下联文案

主题：虾评爆点 (Lobster Hot Take)
主角：一只拟人化的红色龙虾，戴着小眼镜/领带/工牌等道具，
     根据热点新闻扮演不同角色（CEO、程序员、HR、00后实习生……）
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from typing import List

from .llm import chat
from .sources import HotItem
from . import soul


# 拟人龙虾 IP 设定，所有梗图必须围绕它展开
LOBSTER_PERSONA = """【主角设定 · 必须遵守】
所有梗图的主角都是同一只拟人化龙虾，叫"虾总"：
- 外形：红色硬壳、两只大钳子、圆眼睛、直立行走
- 风格：表情夸张、肢体语言丰富、自带喜感
- 着装/道具：根据热点角色变化（西装+领带=CEO；卫衣+耳机=00后；白大褂=医生；
  键盘+黑眼圈=程序员；工牌+咖啡=HR；按摩椅+保温杯=养生青年……）
- 出现方式：占据画面 C 位，钳子做出与梗点呼应的动作（端蛋糕/敲键盘/比 V/掏心窝）

风格关键词：电影感打光、写实+轻微卡通夸张、3D 渲染质感、皮克斯角色海报风
"""


SYSTEM = f"""你是「虾评爆点」的中文段子手。给你一条热点新闻，你要让"虾总"
（一只拟人化龙虾）扮演新闻里的角色，把它改编成一张梗图。

{LOBSTER_PERSONA}

返回 JSON 对象，字段如下：
- meme_point: 一句话梗点（虾总在这条新闻里扮演谁、为什么好笑）
- image_prompt: 给文生图模型的中文 prompt，必须显式描述"拟人龙虾虾总"的外形/动作/道具/场景/打光，不要带任何文字
- top_text: 梗图上联（不超过15字，吐槽风）
- bottom_text: 梗图下联（不超过15字，与上联呼应制造反差）

只返回 JSON，不要任何额外说明、不要 markdown 代码块。"""


@dataclass
class MemeIdea:
    source_item: HotItem
    meme_point: str
    image_prompt: str
    top_text: str
    bottom_text: str

    def to_dict(self):
        return {
            "source": self.source_item.source,
            "title": self.source_item.title,
            "url": self.source_item.url,
            "hot": self.source_item.hot,
            "meme_point": self.meme_point,
            "image_prompt": self.image_prompt,
            "top_text": self.top_text,
            "bottom_text": self.bottom_text,
        }


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"LLM 返回无法解析为 JSON: {text[:200]}")
    return json.loads(m.group(0))


def build_meme_idea(item: HotItem) -> MemeIdea:
    # 注入用户笑点画像（如有），实现"自循环越跑越准"
    sys_prompt = SYSTEM + soul.get_preference_hint()
    user = f"热点来源：{item.source}\n标题：{item.title}\n热度：{item.hot}\n请让虾总扮演这条新闻里的角色，给我一个 JSON 梗图方案。"
    raw = chat(sys_prompt, user)
    try:
        data = _extract_json(raw)
    except Exception as e:
        print(f"  [warn] 解析失败 fallback: {e}")
        data = {
            "meme_point": f"虾总围观「{item.title[:20]}」",
            "image_prompt": (
                "一只拟人化红色龙虾「虾总」站在画面中央，圆眼睛瞪大，"
                f"两只大钳子比划出惊讶表情，背景是与「{item.title}」相关的场景，"
                "电影感打光，3D 渲染，皮克斯角色海报风"
            ),
            "top_text": "虾总也看不下去了",
            "bottom_text": "钳子一夹一个准",
        }
    return MemeIdea(
        source_item=item,
        meme_point=data.get("meme_point", ""),
        image_prompt=data.get("image_prompt", ""),
        top_text=data.get("top_text", ""),
        bottom_text=data.get("bottom_text", ""),
    )


def build_batch(items: List[HotItem], max_count: int = 5) -> List[MemeIdea]:
    ideas = []
    for i, it in enumerate(items[:max_count], 1):
        print(f"  [{i}/{min(len(items), max_count)}] 虾总改编：{it.title[:30]}")
        try:
            ideas.append(build_meme_idea(it))
        except Exception as e:
            print(f"    [skip] {e}")
    return ideas
