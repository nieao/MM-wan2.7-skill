"""配置加载"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", ROOT / "output"))
RAW_DIR = OUTPUT_DIR / "raw"
MEME_DIR = OUTPUT_DIR / "memes"

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
WANXIANG_MODEL = os.getenv("WANXIANG_MODEL", "wan2.2-t2i-flash")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")

# DashScope 地域 → Base URL 映射（OpenAI 兼容模式）
_DASHSCOPE_BASE_URLS = {
    "beijing": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "singapore": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "us": "https://dashscope-us.aliyuncs.com/compatible-mode/v1",
}
DASHSCOPE_REGION = os.getenv("DASHSCOPE_REGION", "beijing").lower()
DASHSCOPE_BASE_URL = _DASHSCOPE_BASE_URLS.get(DASHSCOPE_REGION, _DASHSCOPE_BASE_URLS["beijing"])

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 确保目录存在
for d in (OUTPUT_DIR, RAW_DIR, MEME_DIR):
    d.mkdir(parents=True, exist_ok=True)
