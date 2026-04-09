"""建筑极简风梗图墙 HTML 生成"""
from __future__ import annotations
from pathlib import Path
from typing import List
from datetime import datetime

from . import config
from .prompt_builder import MemeIdea


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>虾评爆点 · 虾总今日上线</title>
<style>
:root {
  --black:#1a1a1a; --dark:#2d2d2d; --gray-700:#555; --gray-500:#888;
  --gray-100:#e8e8e8; --white:#fafafa; --warm:#c8a882; --warm-bg:#f5f0eb;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: "Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;
  background: var(--white); color: var(--dark); line-height: 1.7;
  padding: 80px 24px 120px;
}
.container { max-width: 1100px; margin: 0 auto; }
header { margin-bottom: 80px; }
.tag {
  font-size: 0.72rem; letter-spacing: 0.35em; color: var(--warm);
  text-transform: uppercase; margin-bottom: 24px;
}
h1 {
  font-family: "Noto Serif SC", Georgia, serif;
  font-size: clamp(2rem, 5vw, 3.6rem); font-weight: 600;
  letter-spacing: 0.02em; color: var(--black); margin-bottom: 16px;
}
.subtitle { color: var(--gray-700); font-size: 1rem; }
.subtitle .sep { margin: 0 12px; color: var(--gray-100); }
.grid {
  display: grid; gap: 48px;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  margin-top: 48px;
}
.card {
  border: 1px solid var(--gray-100); background: #fff;
  padding: 0 0 24px 0; transition: all 0.5s cubic-bezier(0.22,1,0.36,1);
  position: relative; overflow: hidden;
}
.card::before {
  content:""; position:absolute; top:0; left:0; width:0; height:2px;
  background: var(--warm); transition: width 0.5s ease;
}
.card:hover { transform: translateY(-4px); border-color: var(--warm); }
.card:hover::before { width: 100%; }
.card img { width:100%; display:block; }
.meta { padding: 24px 24px 0; }
.source {
  font-size: 0.7rem; letter-spacing: 0.2em; color: var(--warm);
  text-transform: uppercase; margin-bottom: 8px;
}
.title {
  font-family: "Noto Serif SC", Georgia, serif;
  font-size: 1rem; color: var(--black); margin-bottom: 12px; font-weight: 500;
}
.point {
  font-size: 0.85rem; color: var(--gray-700); font-style: italic;
  border-left: 2px solid #e8d5c0; padding-left: 12px;
}
.link {
  display:inline-block; margin-top: 16px; font-size: 0.75rem;
  color: var(--gray-500); text-decoration: none; letter-spacing: 0.1em;
}
.link:hover { color: var(--warm); }
.like-btn {
  display:inline-block; margin-top: 16px; margin-left: 12px;
  padding: 6px 14px; border: 1px solid var(--gray-100);
  background: #fff; color: var(--gray-700); font-size: 0.75rem;
  letter-spacing: 0.1em; cursor: pointer;
  transition: all 0.3s ease; font-family: inherit;
}
.like-btn:hover { border-color: var(--warm); color: var(--warm); }
.like-btn.liked {
  background: var(--black); color: var(--warm); border-color: var(--black);
  cursor: default;
}
.tip {
  text-align:center; color: var(--gray-500); font-size: 0.78rem;
  margin: 32px 0 0; letter-spacing: 0.1em;
}
/* 首次笑点测试 modal */
.modal-mask {
  position: fixed; inset: 0; background: rgba(26,26,26,0.85);
  backdrop-filter: blur(8px); z-index: 100;
  display: none; align-items: center; justify-content: center;
}
.modal-mask.active { display: flex; }
.modal {
  background: #fff; width: 92%; max-width: 640px; max-height: 88vh;
  overflow-y: auto; padding: 56px 48px;
  border-top: 3px solid var(--warm); position: relative;
}
.modal .modal-tag {
  font-size: 0.72rem; letter-spacing: 0.35em; color: var(--warm);
  text-transform: uppercase; margin-bottom: 16px;
}
.modal h2 {
  font-family: "Noto Serif SC", Georgia, serif;
  font-size: 1.8rem; color: var(--black); margin-bottom: 8px;
}
.modal .modal-sub { color: var(--gray-700); font-size: 0.9rem; margin-bottom: 32px; }
.modal .progress {
  font-size: 0.7rem; letter-spacing: 0.2em; color: var(--warm);
  margin-bottom: 12px;
}
.modal .question {
  font-size: 1.05rem; color: var(--black); margin-bottom: 24px; line-height: 1.6;
}
.modal .options { display: flex; flex-direction: column; gap: 12px; }
.modal .option {
  border: 1px solid var(--gray-100); padding: 16px 20px;
  cursor: pointer; transition: all 0.3s ease;
  font-size: 0.95rem; color: var(--dark); background: #fff;
  text-align: left; font-family: inherit;
}
.modal .option:hover {
  border-color: var(--warm); transform: translateX(4px);
}
.modal .option.selected {
  background: var(--black); color: var(--warm); border-color: var(--black);
}
.modal .skip {
  position: absolute; top: 24px; right: 32px;
  background: none; border: none; color: var(--gray-500);
  font-size: 0.78rem; letter-spacing: 0.1em; cursor: pointer;
}
.modal .skip:hover { color: var(--warm); }
.modal .result h3 {
  font-family: "Noto Serif SC", serif; font-size: 1.4rem;
  margin-bottom: 16px; color: var(--black);
}
.modal .dim-row {
  display: flex; align-items: center; gap: 12px;
  font-size: 0.9rem; padding: 6px 0;
}
.modal .dim-row .name { width: 110px; color: var(--gray-700); }
.modal .dim-row .bar { flex: 1; height: 6px; background: var(--gray-100); }
.modal .dim-row .bar > span { display:block; height:100%; background: var(--warm); }
.modal .dim-row .val { width: 32px; text-align: right; color: var(--warm); font-weight: 600; }
.modal .done-btn {
  margin-top: 24px; padding: 14px 32px; background: var(--black);
  color: var(--white); border: none; cursor: pointer;
  font-size: 0.85rem; letter-spacing: 0.2em; font-family: inherit;
}
.modal .done-btn:hover { background: var(--warm); color: var(--black); }
footer {
  margin-top: 120px; padding-top: 48px; border-top: 1px solid var(--gray-100);
  text-align: center; color: var(--gray-500); font-size: 0.8rem;
  letter-spacing: 0.15em;
}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="tag">01 / LOBSTER HOT TAKE</div>
    <h1>虾评爆点 · 虾总今日上线</h1>
    <div class="subtitle">
      <span>__DATE__</span><span class="sep">/</span>
      <span>__COUNT__ 张梗图</span><span class="sep">/</span>
      <span>POWERED BY WAN 2.7</span>
    </div>
  </header>

  <div class="grid">
    __CARDS__
  </div>

  <p class="tip">点「戳到我了」按钮 → 偏好记入 soul.md → 下一轮虾总越来越懂你</p>

  <footer>虾评爆点 · 虾总出品 · POWERED BY WAN 2.7 + QWEN · CLAUDE CODE × OPENCLAW SKILL</footer>
</div>

<!-- 首次访问笑点测试 -->
<div class="modal-mask" id="quizMask">
  <div class="modal" id="quizModal">
    <button class="skip" onclick="skipQuiz()">跳过 ×</button>
    <div class="modal-tag">00 / FIRST TIME</div>
    <h2>虾总笑点测试</h2>
    <p class="modal-sub">8 道题，30 秒，让虾总搞清楚你的笑点在哪 — 后续梗图会自动按你的画像生成。</p>
    <div id="quizBody"></div>
  </div>
</div>
__LIKE_JS__
</body>
</html>
"""

CARD_TEMPLATE = """
<article class="card"
         data-title="__TITLE__"
         data-top="__TOP__"
         data-bottom="__BOTTOM__"
         data-point="__POINT__"
         data-source="__SOURCE__">
  <img src="__IMG__" alt="__TITLE__">
  <div class="meta">
    <div class="source">__SOURCE__ · __HOT__</div>
    <div class="title">__TITLE__</div>
    <div class="point">__POINT__</div>
    <a class="link" href="__URL__" target="_blank">查看原文 →</a>
    <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;">
      <button class="like-btn" onclick="like(this)">戳到我了 +1</button>
      <button class="like-btn" onclick="copyText(this)">复制文案</button>
      <button class="like-btn" onclick="downloadImg(this)">下载图片</button>
    </div>
  </div>
</article>
"""

LIKE_JS = """
<script>
// ========== 一键拷贝文案 ==========
async function copyText(btn) {
  const card = btn.closest('.card');
  const source = card.dataset.source;
  const title = card.dataset.title;
  const top = card.dataset.top;
  const bottom = card.dataset.bottom;
  const point = card.dataset.point;
  const url = card.querySelector('.link')?.href || '';
  const text = `${top}\\n${bottom}\\n\\n${point}\\n\\n来源：${source}「${title}」\\n原文：${url}\\n\\n@虾评爆点 · Lobster Hot Take`;
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = '已复制 ✓';
    setTimeout(() => btn.textContent = '复制文案', 2000);
  } catch(e) {
    prompt('手动复制：', text);
  }
}

// ========== 下载图片 ==========
function downloadImg(btn) {
  const card = btn.closest('.card');
  const img = card.querySelector('img');
  if (!img) return;
  const a = document.createElement('a');
  a.href = img.src;
  a.download = (card.dataset.title || 'meme').slice(0,30) + '.png';
  a.click();
  btn.textContent = '已下载 ✓';
  setTimeout(() => btn.textContent = '下载图片', 2000);
}

// ========== 点赞 ==========
async function like(btn) {
  if (btn.classList.contains('liked')) return;
  const card = btn.closest('.card');
  const payload = {
    title: card.dataset.title,
    top: card.dataset.top,
    bottom: card.dataset.bottom,
    meme_point: card.dataset.point,
    source: card.dataset.source,
  };
  try {
    const r = await fetch('/api/like', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const data = await r.json();
    btn.textContent = '已记入笑点画像 ✓ (' + data.liked_count + ')';
    btn.classList.add('liked');
  } catch(e) {
    btn.textContent = '请用 serve 模式启动';
  }
}

// ========== 首次笑点测试 ==========
let _quiz = null;
let _answers = [];
let _step = 0;

async function checkFirstTime() {
  try {
    const r = await fetch('/api/soul-status');
    const s = await r.json();
    if (!s.has_profile) {
      const qr = await fetch('/api/quiz');
      _quiz = (await qr.json()).questions;
      _answers = new Array(_quiz.length).fill(-1);
      _step = 0;
      document.getElementById('quizMask').classList.add('active');
      renderQuiz();
    }
  } catch(e) { /* 静态打开就不弹 */ }
}

function renderQuiz() {
  const q = _quiz[_step];
  const body = document.getElementById('quizBody');
  body.innerHTML = `
    <div class="progress">${_step + 1} / ${_quiz.length}</div>
    <div class="question">${q.q}</div>
    <div class="options">
      ${q.options.map((t, i) =>
        `<button class="option" onclick="pick(${i})">${t}</button>`
      ).join('')}
    </div>
  `;
}

function pick(i) {
  _answers[_step] = i;
  if (_step < _quiz.length - 1) {
    _step++;
    renderQuiz();
  } else {
    submitQuiz();
  }
}

async function submitQuiz() {
  document.getElementById('quizBody').innerHTML = '<p style="color:#888">虾总正在分析你的笑点...</p>';
  try {
    const r = await fetch('/api/quiz', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({answers: _answers}),
    });
    const data = await r.json();
    showResult(data.profile);
  } catch(e) {
    document.getElementById('quizBody').innerHTML = '<p style="color:#c8a882">提交失败：' + e + '</p>';
  }
}

const DIM_LABELS = {
  dark: '黑色幽默', workplace: '职场吐槽', technical: '技术自嘲',
  absurd: '无厘头', pun: '谐音文字', contrast: '反差萌',
  cold: '冷幽默', self_deprecating: '自嘲'
};

function showResult(profile) {
  const sorted = Object.entries(profile).sort((a,b) => b[1] - a[1]);
  const rows = sorted.map(([k, v]) => `
    <div class="dim-row">
      <span class="name">${DIM_LABELS[k] || k}</span>
      <div class="bar"><span style="width:${v*10}%"></span></div>
      <span class="val">${v}</span>
    </div>
  `).join('');
  document.getElementById('quizBody').innerHTML = `
    <div class="result">
      <h3>你的笑点画像</h3>
      ${rows}
      <p style="margin-top:24px; color:#888; font-size:0.85rem;">
        画像已写入 soul.md。下次跑梗图时虾总会按你的偏好出梗。
      </p>
      <button class="done-btn" onclick="closeQuiz()">开始看梗图 →</button>
    </div>
  `;
}

function skipQuiz() { closeQuiz(); }
function closeQuiz() { document.getElementById('quizMask').classList.remove('active'); }

document.addEventListener('DOMContentLoaded', checkFirstTime);
</script>
"""


def render(ideas: List[MemeIdea], meme_paths: List[Path], out_path: Path | None = None) -> Path:
    cards = []
    for idea, p in zip(ideas, meme_paths):
        rel = str(Path("memes") / p.name).replace("\\", "/")
        card = (CARD_TEMPLATE
                .replace("__IMG__", rel)
                .replace("__TITLE__", _esc(idea.source_item.title))
                .replace("__SOURCE__", _esc(idea.source_item.source))
                .replace("__HOT__", _esc(idea.source_item.hot or ""))
                .replace("__POINT__", _esc(idea.meme_point))
                .replace("__URL__", _esc(idea.source_item.url))
                .replace("__TOP__", _esc(idea.top_text))
                .replace("__BOTTOM__", _esc(idea.bottom_text)))
        cards.append(card)
    html = (HTML_TEMPLATE
            .replace("__DATE__", datetime.now().strftime("%Y-%m-%d %H:%M"))
            .replace("__COUNT__", str(len(ideas)))
            .replace("__CARDS__", "\n".join(cards))
            .replace("__LIKE_JS__", LIKE_JS))
    out_path = out_path or (config.OUTPUT_DIR / "index.html")
    out_path.write_text(html, encoding="utf-8")
    return out_path


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
