# Godot 웹 빌드를 테일스케일로 서빙 — 아이폰 사파리 접속용 정적 서버(정확 MIME·0.0.0.0, 읽기전용)
"""build_web/ 디렉토리(godot 웹 export 산출)를 0.0.0.0:PORT로 서빙한다. .wasm/.pck MIME를 바로잡는다.
스레드 끈 export라 COOP/COEP 헤더 없이도 동작. 사용: python godot/serve_web.py [PORT]
아이폰: http://<테일스케일IP>:PORT/
"""
import http.server
import os
import socketserver
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8771
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_web")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".wasm": "application/wasm",
        ".pck": "application/octet-stream",
        ".js": "text/javascript",
        ".html": "text/html",
    }

    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    if not os.path.isdir(ROOT):
        raise SystemExit(f"{ROOT} 없음 — 먼저 웹 export 하세요(godot --export-release Web).")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"Godot 웹 서버 → http://0.0.0.0:{PORT}/  [테일스케일 IP로 아이폰 접속]")
        httpd.serve_forever()
