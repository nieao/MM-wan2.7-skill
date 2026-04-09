# MM-wan2.7-skill · 虾评爆点

> 让拟人龙虾「虾总」点评今日全网热点，用 **通义万相 Wan2.7** 自动生成可传播的梗图。

[![Wan2.7](https://img.shields.io/badge/Wan-2.7-c8a882)]()
[![Qwen](https://img.shields.io/badge/Qwen-Plus-c8a882)]()
[![Skill](https://img.shields.io/badge/Claude%20Code-Skill-1a1a1a)]()
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-1a1a1a)]()

**在线 Demo** → [nieao.site/MM-wan2.7-skill](https://nieao.site/MM-wan2.7-skill)

---

## 它做了什么

```
微博热搜 / 知乎热榜 / IT之家 / 抖音 / 36氪 / 百度 / B站
                        ↓
                 【Qwen 改编梗点】
                        ↓
            拟人龙虾「虾总」扮演新闻角色
                        ↓
               【Wan2.7 文生图】
                        ↓
              Pillow 烧字幕上下联
                        ↓
            建筑极简风梗图墙 + 一键拷贝
```

## 核心特性

- **一个 Key 全搞定** — `DASHSCOPE_API_KEY` 同时驱动 Wan2.7 + Qwen，零额外成本
- **虾总 IP** — 所有梗图主角都是拟人龙虾「虾总」，扮演不同新闻角色，自带传播性
- **笑点画像 + 自循环** — 首次做 8 题笑点测试 → 写入 soul.md → 点赞反馈 → 每 5 次自动 reflect → 越用越懂你
- **6 种 LLM 支持** — Qwen / DeepSeek / MiniMax / GLM 5.1 / Nano Banana 2 / OpenAI
- **3 种使用模式** — CLI / Claude Code Skill / OpenClaw Skill / Web App（公开 Demo）
- **建筑极简风** — 黑白 + 暖色点缀，截图即海报
- **一键拷贝** — 每张梗图支持复制文案、下载图片，带来源标记和原文链接

## 30 秒上手

### 方式 A：CLI 直跑

```bash
git clone https://github.com/nieao/MM-wan2.7-skill.git
cd MM-wan2.7-skill
pip install -e .
cp .env.example .env       # 填入 DASHSCOPE_API_KEY
python -m meme_hunter       # 出 5 张梗图，打开 output/index.html
```

### 方式 B：Web App（适合分享给朋友）

```bash
python -m meme_hunter web --port 8080
# 浏览器打开 http://localhost:8080
# 在页面上填入 API Key → 点击生成
```

### 方式 C：Claude Code Skill

```
# 在 Claude Code 对话中
/meme-hunter
```

### 方式 D：OpenClaw（龙虾）

```yaml
# SOUL.md
skills:
  - name: meme-hunter
    trigger: ["梗图", "meme", "今日热梗"]
    cmd: python -m meme_hunter --count 5
```

## 完整命令

```bash
python -m meme_hunter                  # 默认生成 5 张
python -m meme_hunter generate --count 10 --qwen-model qwen-max
python -m meme_hunter quiz             # 跑笑点测试（写入 soul.md）
python -m meme_hunter serve            # 启动本地服务器（可点赞）
python -m meme_hunter reflect          # 手动触发自循环 reflect
python -m meme_hunter web --port 8080  # 启动 Web App
```

## 自循环机制

```
┌─────────────────────────────┐
↓                             │
generate ──→ Qwen 出梗 ──→ 梗图墙
↑                             │
│                             ↓
注入 hint               「戳到我了」
│                             │
│                         soul.md +1
│                             │
│                        每 5 次 reflect
│                             │
└─── profile/keywords 更新 ←──┘
```

## 环境变量

| 变量 | 必填 | 说明 |
|---|---|---|
| `DASHSCOPE_API_KEY` | ★ | Wan2.7 + Qwen 共用，一个 Key 搞定 |
| `QWEN_MODEL` | 否 | 默认 `qwen-plus`，可改 `qwen-max` |
| `DEEPSEEK_API_KEY` | 否 | 备选 LLM |
| `OPENAI_API_KEY` | 否 | 备选 LLM |

## 项目结构

```
MM-wan2.7-skill/
├── SKILL.md               # Claude Code / OpenClaw 双兼容
├── README.md
├── pyproject.toml
├── meme_hunter/
│   ├── __main__.py         # CLI 入口（generate/quiz/serve/web/reflect）
│   ├── webapp.py           # FastAPI Web App（公开 Demo 用）
│   ├── config.py           # 环境变量加载
│   ├── sources/            # 多源热榜采集（vvhan + DailyHotApi + 兜底）
│   ├── llm.py              # 6 种 LLM 适配（Qwen 优先）
│   ├── prompt_builder.py   # 热点 → 虾总梗点 → 出图 prompt
│   ├── wanxiang.py         # Wan2.7 客户端（真实 API + mock 降级）
│   ├── compose.py          # Pillow 烧字幕合成
│   ├── gallery.py          # 建筑极简风梗图墙 HTML
│   ├── quiz.py             # 8 题虾总笑点测试
│   ├── soul.py             # soul.md 读写 + reflect 自循环
│   └── server.py           # 本地 HTTP 服务器（点赞用）
└── output/                 # 产出物
```

## 比赛信息

参赛：**万相皆可 Skill**（WaytoAGI × 通义万相）

| 维度 | 命中 |
|---|---|
| 创意 30% | 「新闻 → 虾总扮演角色 → 梗图」全自动流水线 |
| 技术 30% | Wan2.7 文生图 + Qwen 文案 + 自循环 reflect |
| 完成度 20% | CLI + Skill + Web App，一键复现 |
| 传播 20% | 梗图自带传播属性 + 一键拷贝 |

## License

MIT
