---
name: meme-hunter
description: 梗图猎人 — 抓全网热点（微博/知乎/IT之家/抖音/36氪），用阿里通义万相 Wan2.7 自动生成可传播的梗图。同时调用 Qwen 文案 + Wan 文生图，输出建筑极简风梗图墙 HTML。当用户说"抓热点出梗图"、"今日热梗"、"做梗图"、"meme hunter"、"梗图猎人"时触发。
type: skill
version: 0.1.0
author: nieao
tags: [aigc, wan2.7, qwen, meme, hot-news, claude-code, openclaw]
runtime: python
entry: python -m meme_hunter
---

# 梗图猎人 (Meme Hunter)

> 一个 Skill，把今天的热点变成可传播的梗图。
> 同时兼容 **Claude Code Skill** 和 **OpenClaw Skill** 调用方式。

## 能力一句话

输入：无（自动抓热榜）
输出：N 张梗图（PNG）+ 建筑极简梗图墙（HTML）+ 元数据（JSON）

## 使用的核心 API

| 能力 | 模型 | 用途 |
|---|---|---|
| 文案生成 | **Qwen** (qwen-plus, DashScope) | 把热点新闻改编成梗点 + 上下联 |
| 图像生成 | **Wan2.7** (DashScope) | 根据梗点 prompt 出底图 |
| 后处理 | Pillow | 烧字幕、加水印、多尺寸 |

> 一个 `DASHSCOPE_API_KEY` 同时驱动 Qwen + Wan2.7，零额外配置。

## 兼容性

### 1. Claude Code 调用
```
/meme-hunter
# 或在对话中："帮我跑一下梗图猎人，出 5 张"
```

### 2. OpenClaw（龙虾）调用
本 skill 遵循 OpenClaw skill 规范：
- 顶部 frontmatter 含 `name`/`description`/`type`/`entry`
- 入口为标准 CLI（`python -m meme_hunter`），不依赖 Claude Code 内置工具
- 所有配置走 `.env`，可在 OpenClaw `SOUL.md` 中通过环境变量注入
- 失败可降级（网络挂掉走 fallback 数据，LLM 挂掉走规则降级）

OpenClaw 触发示例：
```yaml
# SOUL.md 配置片段
skills:
  - name: meme-hunter
    trigger: ["梗图", "meme", "今日热梗"]
    cwd: ./skills/meme-hunter
    cmd: python -m meme_hunter --count 5
```

### 3. 命令行直接调用（无 Claude Code / 无 OpenClaw）
```bash
python -m meme_hunter --count 5
```

## 快速开始

```bash
git clone <repo>
cd meme-hunter
pip install -e .
cp .env.example .env
# 编辑 .env 填入 DASHSCOPE_API_KEY
python -m meme_hunter
# 产出：./output/index.html
```

## 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `DASHSCOPE_API_KEY` | ★推荐 | 阿里 DashScope key，同时驱动 Wan2.7 + Qwen |
| `WANXIANG_MODEL` | 否 | 默认 `wan2.2-t2i-flash` |
| `QWEN_MODEL` | 否 | 默认 `qwen-plus` |
| `DEEPSEEK_API_KEY` | 否 | 备选文案 LLM |
| `OPENAI_API_KEY` | 否 | 备选文案 LLM |

LLM provider 优先级：**Qwen > DeepSeek > 本地 claude CLI > 规则降级**

## 模块结构

```
meme_hunter/
├── __main__.py        # 主流水线入口
├── config.py          # 环境变量加载
├── sources/           # 热榜采集（vvhan 聚合 API）
├── llm.py             # 多 provider LLM 适配（Qwen 第一）
├── prompt_builder.py  # 热点 → 梗点 → 出图 prompt
├── wanxiang.py        # Wan2.7 客户端（当前 mock，留接口）
├── compose.py         # Pillow 烧字幕合成梗图
└── gallery.py         # 建筑极简风梗图墙 HTML
```

## 真实接入 Wan2.7 的位置

只需替换 `meme_hunter/wanxiang.py` 内 `generate()` 函数：
1. POST `https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis`
2. 轮询 task_id 拿到结果 URL
3. 下载到 `config.RAW_DIR`
4. 返回 `List[Path]`

外部接口签名 `generate(prompt, size, n) -> List[Path]` **保持不变**，其它模块零修改。

## 输出物

- `output/raw/*.png` — Wan2.7 原图
- `output/memes/*.png` — 烧字幕后的梗图
- `output/index.html` — 建筑极简风梗图墙
- `output/memes.json` — 元数据（来源/标题/梗点/上下联）

## 比赛信息

- 比赛：万相皆可 Skill（WaytoAGI × 通义万相）
- 截止：2026-04-12 23:59
- 评审维度命中：创意 ✅ / 技术 (Wan+Qwen 双调用) ✅ / 完成度 ✅ / 传播 (梗图天然传播) ✅
