"""本地小服务器 - 服务梗图墙 + 接收点赞

启动后访问 http://127.0.0.1:7788/index.html
点「戳到我了」会 POST /api/like，写入 soul.md
"""
from __future__ import annotations
import json
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from . import config, soul
from .quiz import QUIZ


class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(config.OUTPUT_DIR), **kwargs)

    def log_message(self, fmt, *args):
        # 静默冗余日志
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def do_GET(self):
        if self.path == "/api/soul-status":
            data = soul.load()
            self._json(200, {
                "has_profile": bool(data.get("profile")),
                "iterations": data.get("iterations", 0),
                "liked_count": len(data.get("liked", [])),
                "summary": data.get("summary", ""),
            })
            return
        if self.path == "/api/quiz":
            questions = [
                {"q": q["q"], "options": [t for t, _ in q["options"]]}
                for q in QUIZ
            ]
            self._json(200, {"questions": questions})
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/like":
            length = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                count = soul.add_liked(data)
                self._json(200, {"ok": True, "liked_count": count})
                print(f"  [like] +1 ({count} 条已记入) - {data.get('top','')}/{data.get('bottom','')}")
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
            return
        if self.path == "/api/quiz":
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                answers = payload.get("answers", [])  # list of choice index 0-based
                profile: dict[str, float] = {}
                for q, choice in zip(QUIZ, answers):
                    if 0 <= choice < len(q["options"]):
                        _, dim = q["options"][choice]
                        profile[dim] = profile.get(dim, 0) + 1
                mx = max(profile.values()) if profile else 1
                profile = {k: round(v * 10 / mx, 1) for k, v in profile.items()}
                soul.update_profile(profile)
                self._json(200, {"ok": True, "profile": profile})
                print(f"  [quiz] 完成，profile: {profile}")
            except Exception as e:
                self._json(500, {"ok": False, "error": str(e)})
            return
        self.send_error(404)

    def _json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(port: int = 7788, open_browser: bool = True):
    addr = ("127.0.0.1", port)
    httpd = HTTPServer(addr, _Handler)
    url = f"http://127.0.0.1:{port}/index.html"
    print("=" * 50)
    print(f"  虾评爆点 · 梗图墙服务器")
    print(f"  打开浏览器: {url}")
    print(f"  Ctrl+C 退出")
    print("=" * 50)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  服务器已停止")
