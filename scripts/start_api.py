from __future__ import annotations

import gzip
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "apps" / "frontend"
STATION_PAGE = PROJECT_ROOT / "apps" / "api" / "network_station.html"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.api import main as api


class YingYueHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: object, status: int = 200, compress: bool = True) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if compress and len(body) > 1024 and self.client_address[0] != "127.0.0.1":
            body = gzip.compress(body, compresslevel=6)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "max-age=60")
            self.send_header("Vary", "Accept-Encoding")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        else:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "max-age=60")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        self.wfile.write(body)

    def _send_html(self, content: str, status: int = 200) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, file_path: Path) -> bool:
        if not file_path.exists():
            return False
        self._send_html(file_path.read_text(encoding="utf-8"))
        return True

    def log_message(self, format, *args):
        try:
            status_code = int(args[1]) if len(args) > 1 else 0
            if status_code >= 300 or (len(args) > 0 and "/health" not in str(args[0])):
                super().log_message(format, *args)
        except (ValueError, TypeError, IndexError):
            super().log_message(format, *args)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path in {"/", "/station"}:
            if not STATION_PAGE.exists():
                self._send_json({"error": "network station page not found"}, status=404)
                return
            self._send_html(STATION_PAGE.read_text(encoding="utf-8"))
            return

        frontend_routes = {
            "/console": FRONTEND_ROOT / "dashboard" / "index.html",
            "/console/dashboard": FRONTEND_ROOT / "dashboard" / "index.html",
            "/console/tasks": FRONTEND_ROOT / "task_management" / "index.html",
            "/console/assistant": FRONTEND_ROOT / "ai_assistant" / "index.html",
            "/console/monitoring": FRONTEND_ROOT / "system_monitoring" / "index.html",
        }
        if parsed.path in frontend_routes:
            if not self._serve_file(frontend_routes[parsed.path]):
                self._send_json({"error": "frontend page not found"}, status=404)
            return

        if parsed.path == "/health":
            self._send_json(api.health())
            return
        if parsed.path == "/news/latest":
            try:
                limit = int(query.get("limit", ["10"])[0])
            except ValueError:
                self._send_json({"error": "limit must be an integer"}, status=400)
                return
            if limit <= 0 or limit > 100:
                self._send_json({"error": "limit must be between 1 and 100"}, status=400)
                return
            self._send_json(api.latest_news(limit=limit))
            return
        if parsed.path == "/philosophy/search":
            q = query.get("q", [""])[0]
            if len(q) < 2:
                self._send_json({"error": "q must be at least 2 chars"}, status=400)
                return
            self._send_json(api.search_philosophy(q=q))
            return
        if parsed.path == "/trends/summary":
            self._send_json(api.trends_summary())
            return
        if parsed.path == "/observations/daily/latest":
            payload = api.latest_daily_observation()
            self._send_json(payload, status=404 if "error" in payload else 200)
            return
        if parsed.path == "/observations/weekly/latest":
            payload = api.latest_weekly_observation()
            self._send_json(payload, status=404 if "error" in payload else 200)
            return
        if parsed.path == "/thought-links/latest":
            payload = api.latest_thought_links()
            self._send_json(payload, status=404 if "error" in payload else 200)
            return
        if parsed.path == "/agents/latest":
            payload = api.latest_agent_pipeline()
            self._send_json(payload, status=404 if "error" in payload else 200)
            return
        if parsed.path == "/events/network":
            try:
                event_type = query.get("type", [""])[0]
                status = query.get("status", ["active"])[0]
                limit = int(query.get("limit", ["20"])[0])
            except ValueError:
                self._send_json({"error": "limit must be an integer"}, status=400)
                return
            if limit <= 0 or limit > 100:
                self._send_json({"error": "limit must be between 1 and 100"}, status=400)
                return
            self._send_json(api.network_events(event_type=event_type, status=status, limit=limit))
            return
        if parsed.path == "/events/network/summary":
            self._send_json(api.network_event_summary())
            return
        if parsed.path.startswith("/events/network/type/"):
            event_type = parsed.path.replace("/events/network/type/", "").strip()
            if not event_type:
                self._send_json({"error": "event type required"}, status=400)
                return
            try:
                limit = int(query.get("limit", ["20"])[0])
            except ValueError:
                self._send_json({"error": "limit must be an integer"}, status=400)
                return
            self._send_json(api.network_events_by_type(event_type=event_type, limit=limit))
            return
        if parsed.path == "/station/summary":
            self._send_json(api.station_summary())
            return
        if parsed.path == "/tasks/overview":
            self._send_json(api.task_overview())
            return
        if parsed.path == "/assistant/context":
            self._send_json(api.assistant_context())
            return
        if parsed.path == "/monitor/snapshot":
            self._send_json(api.monitor_snapshot())
            return
        self._send_json({"error": "not found"}, status=404)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    api.startup()
    server = ThreadingHTTPServer((host, port), YingYueHandler)
    print(f"YingYue API running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    host = os.getenv("YINGYUE_API_HOST", "127.0.0.1")
    port = int(os.getenv("YINGYUE_API_PORT", "8000"))
    run_server(host=host, port=port)
