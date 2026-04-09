"""热榜聚合采集器

多源 fallback 策略，保证最大成功率：
  1. vvhan 聚合 API（https://api.vvhan.com）
  2. DailyHotApi 公共节点（https://api-hot.efox.cc）
  3. 内置兜底数据（保证 demo 不中断）
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Callable
import httpx


@dataclass
class HotItem:
    source: str        # 来源平台中文名
    title: str         # 标题
    url: str           # 原文链接
    hot: str = ""      # 热度

    def to_dict(self):
        return asdict(self)


# ==================== 数据源 1: vvhan ====================
VVHAN_API = "https://api.vvhan.com/api/hotlist/{type}"
VVHAN_SOURCES = {
    "weibo": "微博热搜",
    "zhihu": "知乎热榜",
    "ithome": "IT之家",
    "douyinHot": "抖音热点",
    "36Ke": "36氪",
}


def _fetch_vvhan(timeout: float = 8.0) -> List[HotItem]:
    out: List[HotItem] = []
    for key, label in VVHAN_SOURCES.items():
        try:
            r = httpx.get(VVHAN_API.format(type=key), timeout=timeout)
            data = r.json().get("data", []) or []
            for it in data[:10]:
                if it.get("title"):
                    out.append(HotItem(
                        source=label,
                        title=str(it["title"]).strip(),
                        url=str(it.get("url", "")),
                        hot=str(it.get("hot", "")),
                    ))
            print(f"  [vvhan/{label}] +{len(data[:10])}")
        except Exception as e:
            print(f"  [vvhan/{label}] 失败: {e}")
    return out


# ==================== 数据源 2: DailyHotApi ====================
DAILYHOT_API = "https://api-hot.efox.cc/{type}"
DAILYHOT_SOURCES = {
    "weibo": "微博热搜",
    "zhihu": "知乎热榜",
    "ithome": "IT之家",
    "douyin": "抖音热点",
    "36kr": "36氪",
    "baidu": "百度热搜",
    "bilibili": "B站热门",
}


def _fetch_dailyhot(timeout: float = 8.0) -> List[HotItem]:
    out: List[HotItem] = []
    for key, label in DAILYHOT_SOURCES.items():
        try:
            r = httpx.get(DAILYHOT_API.format(type=key), timeout=timeout)
            data = r.json().get("data", []) or []
            for it in data[:10]:
                title = it.get("title") or it.get("name")
                if title:
                    out.append(HotItem(
                        source=label,
                        title=str(title).strip(),
                        url=str(it.get("url") or it.get("mobileUrl") or ""),
                        hot=str(it.get("hot") or ""),
                    ))
            print(f"  [dailyhot/{label}] +{len(data[:10])}")
        except Exception as e:
            print(f"  [dailyhot/{label}] 失败: {e}")
    return out


# ==================== 数据源 3: 兜底 ====================
def _fallback_items() -> List[HotItem]:
    return [
        HotItem("微博热搜", "某AI公司一夜裁员50%创始人发蛋糕庆生", "https://example.com/1", "999万"),
        HotItem("微博热搜", "00后整顿职场新姿势上班自带按摩椅", "https://example.com/2", "888万"),
        HotItem("知乎热榜", "为什么程序员越来越喜欢用AI写代码了", "https://example.com/3", "777万"),
        HotItem("IT之家", "苹果发布新款MacBook起售价突破天际", "https://example.com/4", "666万"),
        HotItem("抖音热点", "大学生在图书馆开启AI辅导新模式", "https://example.com/5", "555万"),
    ]


# ==================== 主入口 ====================
SOURCES_CHAIN: List[tuple[str, Callable]] = [
    ("vvhan", _fetch_vvhan),
    ("dailyhot", _fetch_dailyhot),
]


def fetch_all_hotlists(limit_per_source: int = 10) -> List[HotItem]:
    """按顺序尝试多个数据源，第一个返回非空结果就使用"""
    for name, fn in SOURCES_CHAIN:
        print(f"  尝试数据源: {name}")
        try:
            items = fn()
        except Exception as e:
            print(f"  [X] {name} 整体异常: {e}")
            items = []
        if items:
            print(f"  [OK] {name} 成功，共 {len(items)} 条")
            return items
        print(f"  [X] {name} 无结果，尝试下一个")

    print("  [warn] 所有源都失败，使用兜底数据")
    return _fallback_items()
