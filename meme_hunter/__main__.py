"""虾评爆点 · 主入口

用法：
    python -m meme_hunter              # 默认：抓热点 → 出梗图 → 写 index.html
    python -m meme_hunter generate     # 同上
    python -m meme_hunter quiz         # 跑笑点测试，写入 soul.md
    python -m meme_hunter serve        # 启动本地服务器，可点赞影响后续生成
    python -m meme_hunter reflect      # 手动触发自循环 reflect
"""
from __future__ import annotations
import argparse
import json
import sys

from . import config
from .sources import fetch_all_hotlists
from .prompt_builder import build_batch
from .wanxiang import generate as wan_generate
from .compose import compose_meme
from .gallery import render


def cmd_generate(args):
    print("=" * 50)
    print("  虾评爆点 · LOBSTER HOT TAKE")
    print("  主角：虾总（一只拟人龙虾）")
    print("=" * 50)

    print("\n[1/4] 抓取全网热榜...")
    items = fetch_all_hotlists(limit_per_source=args.per_source)
    print(f"  共抓到 {len(items)} 条热点")

    print(f"\n[2/4] LLM 改编为梗图方案 (top {args.count})...")
    if args.qwen_model:
        config.QWEN_MODEL = args.qwen_model
        print(f"  [info] Qwen 模型已覆盖为: {args.qwen_model}")
    ideas = build_batch(items, max_count=args.count)
    if not ideas:
        print("  [error] 没有任何梗图方案")
        sys.exit(1)

    print(f"\n[3/4] 调用 Wan2.7 生成底图...")
    meme_paths = []
    valid_ideas = []
    for i, idea in enumerate(ideas, 1):
        print(f"  [{i}/{len(ideas)}] 出图：{idea.top_text} / {idea.bottom_text}")
        try:
            base = wan_generate(idea.image_prompt, size=args.size, n=1)[0]
            final = compose_meme(idea, base)
            meme_paths.append(final)
            valid_ideas.append(idea)
        except Exception as e:
            print(f"    [skip] {e}")

    print(f"\n[4/4] 渲染建筑极简梗图墙...")
    out_html = render(valid_ideas, meme_paths)

    meta_path = config.OUTPUT_DIR / "memes.json"
    meta_path.write_text(
        json.dumps([i.to_dict() for i in valid_ideas], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 50)
    print(f"  完成！共 {len(meme_paths)} 张梗图")
    print(f"  浏览：{out_html}")
    print(f"  下一步：python -m meme_hunter serve  → 启动可点赞模式")
    print("=" * 50)


def cmd_quiz(args):
    from . import quiz
    quiz.run()


def cmd_serve(args):
    from . import server
    server.serve(port=args.port, open_browser=not args.no_browser)


def cmd_reflect(args):
    from . import soul
    soul.reflect_and_update()


def cmd_web(args):
    import uvicorn
    print("=" * 50)
    print(f"  虾评爆点 · Web App")
    print(f"  http://{args.host}:{args.port}")
    print("=" * 50)
    uvicorn.run("meme_hunter.webapp:app", host=args.host, port=args.port, reload=False)


def main():
    parser = argparse.ArgumentParser(description="虾评爆点 - 用 Wan2.7 + Qwen 让虾总点评今日热点")
    sub = parser.add_subparsers(dest="cmd")

    p_gen = sub.add_parser("generate", help="生成梗图（默认）")
    p_gen.add_argument("--count", type=int, default=5)
    p_gen.add_argument("--size", default="1024*1024")
    p_gen.add_argument("--per-source", type=int, default=10)
    p_gen.add_argument("--qwen-model", default=None)
    p_gen.set_defaults(func=cmd_generate)

    p_quiz = sub.add_parser("quiz", help="跑笑点测试，写入 soul.md")
    p_quiz.set_defaults(func=cmd_quiz)

    p_serve = sub.add_parser("serve", help="启动本地服务器（可点赞）")
    p_serve.add_argument("--port", type=int, default=7788)
    p_serve.add_argument("--no-browser", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    p_reflect = sub.add_parser("reflect", help="手动触发自循环 reflect")
    p_reflect.set_defaults(func=cmd_reflect)

    p_web = sub.add_parser("web", help="启动 Web App（FastAPI，用户自带 Key）")
    p_web.add_argument("--port", type=int, default=8080)
    p_web.add_argument("--host", default="0.0.0.0")
    p_web.set_defaults(func=cmd_web)

    # 兼容老调用：python -m meme_hunter --count 3
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--size", default="1024*1024")
    parser.add_argument("--per-source", type=int, default=10)
    parser.add_argument("--qwen-model", default=None)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        cmd_generate(args)


if __name__ == "__main__":
    main()
