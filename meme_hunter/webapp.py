"""虾评爆点 Web App（FastAPI）

公开 Demo 模式：用户自带 API Key，服务器不存储密钥。
所有 Key 通过请求头传递，仅在本次请求内使用。
"""
from __future__ import annotations
import json
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .sources import fetch_all_hotlists
from .prompt_builder import build_meme_idea, MemeIdea
from .wanxiang import generate as wan_generate
from .compose import compose_meme
from .gallery import render as render_gallery
from . import soul

app = FastAPI(title="虾评爆点 · Lobster Hot Take", version="0.1.0")

# 静态文件
app.mount("/output", StaticFiles(directory=str(config.OUTPUT_DIR)), name="output")

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ==================== 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index():
    return _landing_page()


@app.get("/gallery", response_class=HTMLResponse)
async def gallery():
    html_path = config.OUTPUT_DIR / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>还没有梗图，先点「开始生成」</h1>"


# ==================== API 路由 ====================

@app.post("/api/generate")
async def api_generate(request: Request):
    """接收用户 API Key，生成梗图

    请求体 JSON:
    {
        "dashscope_key": "sk-xxx",     // Wan2.7 + Qwen
        "llm_provider": "qwen",        // qwen/deepseek/minimax/glm/nano-banana
        "llm_key": "sk-xxx",           // LLM 专用 key（如不同于 dashscope）
        "count": 5
    }
    """
    body = await request.json()
    dash_key = body.get("dashscope_key", "")
    llm_provider = body.get("llm_provider", "qwen")
    llm_key = body.get("llm_key", "") or dash_key
    count = min(int(body.get("count", 5)), 10)

    if not dash_key:
        return JSONResponse({"ok": False, "error": "请填写 DashScope API Key（Wan2.7 必需）"}, 400)

    # 临时注入 key（仅本次请求有效）
    _orig_dash = config.DASHSCOPE_API_KEY
    _orig_deep = config.DEEPSEEK_API_KEY
    config.DASHSCOPE_API_KEY = dash_key

    if llm_provider == "deepseek":
        config.DEEPSEEK_API_KEY = llm_key

    try:
        items = fetch_all_hotlists(limit_per_source=10)
        from .prompt_builder import build_batch
        ideas = build_batch(items, max_count=count)
        if not ideas:
            return JSONResponse({"ok": False, "error": "文案生成失败，请检查 LLM Key"}, 500)

        meme_paths = []
        valid_ideas = []
        for idea in ideas:
            try:
                base = wan_generate(idea.image_prompt, size="1024*1024", n=1)[0]
                final = compose_meme(idea, base)
                meme_paths.append(final)
                valid_ideas.append(idea)
            except Exception as e:
                continue

        if not valid_ideas:
            return JSONResponse({"ok": False, "error": "Wan2.7 出图失败，请检查 DashScope Key"}, 500)

        out_html = render_gallery(valid_ideas, meme_paths)
        meta = [i.to_dict() for i in valid_ideas]

        meta_path = config.OUTPUT_DIR / "memes.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        return JSONResponse({
            "ok": True,
            "count": len(valid_ideas),
            "gallery_url": "/gallery",
            "memes": meta,
        })
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, 500)
    finally:
        config.DASHSCOPE_API_KEY = _orig_dash
        config.DEEPSEEK_API_KEY = _orig_deep


@app.get("/api/soul-status")
async def api_soul_status():
    data = soul.load()
    return {
        "has_profile": bool(data.get("profile")),
        "iterations": data.get("iterations", 0),
        "liked_count": len(data.get("liked", [])),
    }


@app.get("/api/quiz")
async def api_quiz():
    from .quiz import QUIZ
    questions = [{"q": q["q"], "options": [t for t, _ in q["options"]]} for q in QUIZ]
    return {"questions": questions}


@app.post("/api/quiz")
async def api_quiz_submit(request: Request):
    from .quiz import QUIZ
    body = await request.json()
    answers = body.get("answers", [])
    profile = {}
    for q, choice in zip(QUIZ, answers):
        if 0 <= choice < len(q["options"]):
            _, dim = q["options"][choice]
            profile[dim] = profile.get(dim, 0) + 1
    mx = max(profile.values()) if profile else 1
    profile = {k: round(v * 10 / mx, 1) for k, v in profile.items()}
    soul.update_profile(profile)
    return {"ok": True, "profile": profile}


@app.post("/api/like")
async def api_like(request: Request):
    body = await request.json()
    count = soul.add_liked(body)
    return {"ok": True, "liked_count": count}


# ==================== Landing Page ====================

def _landing_page() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>虾评爆点 · Lobster Hot Take</title>
<style>
:root {
  --black:#1a1a1a; --dark:#2d2d2d; --gray-700:#555; --gray-500:#888;
  --gray-100:#e8e8e8; --white:#fafafa; --warm:#c8a882; --warm-bg:#f5f0eb;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: "Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;
  background: var(--white); color: var(--dark); line-height: 1.7;
  display: flex; justify-content: center; padding: 80px 24px;
}
.container { max-width: 720px; width: 100%; }
.tag {
  font-size: 0.72rem; letter-spacing: 0.35em; color: var(--warm);
  text-transform: uppercase; margin-bottom: 24px;
}
h1 {
  font-family: "Noto Serif SC", Georgia, serif;
  font-size: clamp(2rem, 5vw, 3rem); font-weight: 600;
  letter-spacing: 0.02em; color: var(--black); margin-bottom: 12px;
}
.sub { color: var(--gray-700); font-size: 0.95rem; margin-bottom: 48px; }

/* Key 输入区 */
.section-label {
  font-size: 0.7rem; letter-spacing: 0.25em; color: var(--warm);
  text-transform: uppercase; margin-bottom: 12px; margin-top: 36px;
}
.key-group { margin-bottom: 24px; }
.key-group label {
  display: block; font-size: 0.85rem; color: var(--gray-700);
  margin-bottom: 6px; letter-spacing: 0.05em;
}
.key-group .hint {
  font-size: 0.75rem; color: var(--gray-500); margin-bottom: 8px;
}
.key-group input, .key-group select {
  width: 100%; padding: 14px 16px; border: 1px solid var(--gray-100);
  font-size: 0.9rem; font-family: inherit;
  transition: border-color 0.3s;
}
.key-group input:focus, .key-group select:focus {
  outline: none; border-color: var(--warm);
}
.key-group input::placeholder { color: #ccc; }

.divider {
  height: 1px; background: var(--gray-100); margin: 32px 0;
}

/* 数量选择 */
.count-row {
  display: flex; align-items: center; gap: 16px; margin-bottom: 32px;
}
.count-row label { font-size: 0.85rem; color: var(--gray-700); }
.count-row input {
  width: 80px; padding: 10px; border: 1px solid var(--gray-100);
  font-size: 0.9rem; text-align: center; font-family: inherit;
}

/* 生成按钮 */
.gen-btn {
  display: block; width: 100%; padding: 18px;
  background: var(--black); color: var(--white); border: none;
  font-size: 1rem; letter-spacing: 0.2em; cursor: pointer;
  font-family: inherit; transition: all 0.3s;
}
.gen-btn:hover { background: var(--warm); color: var(--black); }
.gen-btn:disabled {
  background: var(--gray-500); cursor: not-allowed; opacity: 0.6;
}

/* 进度 */
.progress-area {
  margin-top: 24px; padding: 24px; border: 1px solid var(--gray-100);
  display: none;
}
.progress-area .step {
  font-size: 0.85rem; color: var(--gray-700); padding: 4px 0;
}
.progress-area .step.active { color: var(--warm); font-weight: 600; }
.progress-area .step.done { color: var(--black); }
.progress-area .step.done::before { content: "[OK] "; color: var(--warm); }

.error-box {
  margin-top: 16px; padding: 16px; background: #fff5f5;
  border-left: 3px solid #e53e3e; color: #c53030; font-size: 0.85rem;
  display: none;
}

/* 源标注 */
.source-badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.source-badge {
  font-size: 0.7rem; letter-spacing: 0.1em; padding: 4px 12px;
  border: 1px solid var(--gray-100); color: var(--gray-500);
}

/* provider 说明 */
.provider-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
  margin-top: 8px;
}
.provider-card {
  padding: 10px; border: 1px solid var(--gray-100); text-align: center;
  font-size: 0.78rem; color: var(--gray-700); cursor: pointer;
  transition: all 0.3s;
}
.provider-card:hover, .provider-card.selected {
  border-color: var(--warm); color: var(--warm);
}
.provider-card .name { font-weight: 600; }
.provider-card .desc { font-size: 0.68rem; color: var(--gray-500); margin-top: 2px; }

footer {
  margin-top: 64px; padding-top: 32px; border-top: 1px solid var(--gray-100);
  text-align: center; color: var(--gray-500); font-size: 0.75rem;
  letter-spacing: 0.15em;
}
footer a { color: var(--warm); text-decoration: none; }
</style>
</head>
<body>
<div class="container">
  <div class="tag">LOBSTER HOT TAKE / SETUP</div>
  <h1>虾评爆点</h1>
  <p class="sub">
    让拟人龙虾「虾总」为你点评今日全网热点，自动生成可传播的梗图。<br>
    填入你的 API Key → 点击生成 → 获得建筑极简风梗图墙。
  </p>

  <div class="source-badges">
    <span class="source-badge">微博热搜</span>
    <span class="source-badge">知乎热榜</span>
    <span class="source-badge">IT之家</span>
    <span class="source-badge">抖音热点</span>
    <span class="source-badge">36氪</span>
    <span class="source-badge">百度热搜</span>
    <span class="source-badge">B站热门</span>
  </div>

  <div class="divider"></div>

  <!-- Wan2.7 Key (必填) -->
  <div class="section-label">01 / WAN 2.7 IMAGE KEY (REQUIRED)</div>
  <div class="key-group">
    <label>DashScope API Key</label>
    <div class="hint">
      同时驱动 Wan2.7 文生图 + Qwen 文案。
      <a href="https://bailian.console.aliyun.com/" target="_blank" style="color:var(--warm)">去申请 →</a>
      格式：sk-xxx（非 sk-sp-xxx）
    </div>
    <input type="password" id="dashKey" placeholder="sk-xxxxxxxxxxxxxxxx" autocomplete="off">
  </div>

  <div class="divider"></div>

  <!-- LLM Provider 选择 -->
  <div class="section-label">02 / LLM PROVIDER (OPTIONAL)</div>
  <p style="font-size:0.82rem;color:var(--gray-700);margin-bottom:12px;">
    默认使用 Qwen（与 Wan2.7 共用同一个 Key）。如需其他模型生成文案，选择并填入对应 Key：
  </p>
  <div class="provider-grid">
    <div class="provider-card selected" onclick="selectProvider(this,'qwen')">
      <div class="name">Qwen</div>
      <div class="desc">共用 DashScope Key</div>
    </div>
    <div class="provider-card" onclick="selectProvider(this,'deepseek')">
      <div class="name">DeepSeek</div>
      <div class="desc">中文梗王</div>
    </div>
    <div class="provider-card" onclick="selectProvider(this,'minimax')">
      <div class="name">MiniMax</div>
      <div class="desc">abab-7</div>
    </div>
    <div class="provider-card" onclick="selectProvider(this,'glm')">
      <div class="name">GLM 5.1</div>
      <div class="desc">智谱 ChatGLM</div>
    </div>
    <div class="provider-card" onclick="selectProvider(this,'nano-banana')">
      <div class="name">Nano Banana 2</div>
      <div class="desc">阶跃星辰</div>
    </div>
    <div class="provider-card" onclick="selectProvider(this,'openai')">
      <div class="name">OpenAI</div>
      <div class="desc">GPT-4o</div>
    </div>
  </div>
  <div class="key-group" id="llmKeyGroup" style="display:none;margin-top:16px;">
    <label id="llmKeyLabel">LLM API Key</label>
    <input type="password" id="llmKey" placeholder="sk-xxxxxxxxxxxxxxxx" autocomplete="off">
  </div>

  <div class="divider"></div>

  <!-- 生成参数 -->
  <div class="section-label">03 / GENERATE</div>
  <div class="count-row">
    <label>梗图数量</label>
    <input type="number" id="count" value="5" min="1" max="10">
  </div>

  <button class="gen-btn" id="genBtn" onclick="generate()">
    让虾总开工 →
  </button>

  <div class="progress-area" id="progressArea">
    <div class="step" id="s1">抓取全网热榜...</div>
    <div class="step" id="s2">Qwen 改编梗点...</div>
    <div class="step" id="s3">Wan2.7 生成虾总底图...</div>
    <div class="step" id="s4">烧字幕合成梗图...</div>
    <div class="step" id="s5">渲染建筑极简梗图墙...</div>
  </div>

  <div class="error-box" id="errorBox"></div>

  <footer>
    虾评爆点 · MEME HUNTER · POWERED BY WAN 2.7 + QWEN
    <br>
    <a href="https://github.com/nieao/MM-wan2.7-skill" target="_blank">GitHub</a>
    · CLAUDE CODE × OPENCLAW SKILL
  </footer>
</div>

<script>
let provider = 'qwen';

function selectProvider(el, p) {
  document.querySelectorAll('.provider-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  provider = p;
  const llmGroup = document.getElementById('llmKeyGroup');
  if (p === 'qwen') {
    llmGroup.style.display = 'none';
  } else {
    llmGroup.style.display = 'block';
    document.getElementById('llmKeyLabel').textContent =
      {deepseek:'DeepSeek',minimax:'MiniMax',glm:'GLM 5.1','nano-banana':'Nano Banana 2',openai:'OpenAI'}[p] + ' API Key';
  }
}

async function generate() {
  const dashKey = document.getElementById('dashKey').value.trim();
  if (!dashKey) { alert('请填写 DashScope API Key'); return; }

  const btn = document.getElementById('genBtn');
  const prog = document.getElementById('progressArea');
  const errBox = document.getElementById('errorBox');
  btn.disabled = true;
  btn.textContent = '虾总正在努力出工...';
  prog.style.display = 'block';
  errBox.style.display = 'none';

  // 模拟进度
  const steps = ['s1','s2','s3','s4','s5'];
  let si = 0;
  const timer = setInterval(() => {
    if (si > 0) document.getElementById(steps[si-1]).classList.replace('active','done');
    if (si < steps.length) document.getElementById(steps[si]).classList.add('active');
    si++;
    if (si > steps.length) clearInterval(timer);
  }, 3000);

  try {
    const r = await fetch('/api/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        dashscope_key: dashKey,
        llm_provider: provider,
        llm_key: document.getElementById('llmKey')?.value?.trim() || '',
        count: parseInt(document.getElementById('count').value) || 5,
      }),
    });
    clearInterval(timer);
    steps.forEach(s => {
      document.getElementById(s).classList.remove('active');
      document.getElementById(s).classList.add('done');
    });
    const data = await r.json();
    if (data.ok) {
      btn.textContent = '完成！跳转到梗图墙 →';
      btn.disabled = false;
      btn.onclick = () => window.location.href = '/gallery';
    } else {
      errBox.textContent = data.error;
      errBox.style.display = 'block';
      btn.textContent = '重试 →';
      btn.disabled = false;
      btn.onclick = generate;
    }
  } catch(e) {
    clearInterval(timer);
    errBox.textContent = '网络错误: ' + e;
    errBox.style.display = 'block';
    btn.textContent = '重试 →';
    btn.disabled = false;
    btn.onclick = generate;
  }
}

// 记住 key 到 localStorage
document.getElementById('dashKey').value = localStorage.getItem('mm_dash_key') || '';
document.getElementById('dashKey').addEventListener('change', e => localStorage.setItem('mm_dash_key', e.target.value));
</script>
</body>
</html>"""
