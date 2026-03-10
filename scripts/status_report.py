from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error, request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "data" / "processed" / "reports"
DB_PATH = PROJECT_ROOT / "data" / "curated" / "yingyue.db"


@dataclass
class CheckResult:
    name: str
    status: str
    details: str
    latency_ms: int | None = None


def _http_json(url: str, timeout: int = 6) -> tuple[int, Any, int, str]:
    start = time.perf_counter()
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            elapsed = int((time.perf_counter() - start) * 1000)
            payload = json.loads(body) if body else None
            return resp.status, payload, elapsed, ""
    except error.HTTPError as exc:
        elapsed = int((time.perf_counter() - start) * 1000)
        return exc.code, None, elapsed, f"HTTPError: {exc}"
    except Exception as exc:  # noqa: BLE001
        elapsed = int((time.perf_counter() - start) * 1000)
        return 0, None, elapsed, str(exc)


def _today_files(today: str) -> list[Path]:
    return [
        REPORT_DIR / f"daily_report_{today}.md",
        REPORT_DIR / f"daily_report_{today}_news.csv",
        REPORT_DIR / f"agent_pipeline_{today}.json",
    ]


def collect_status(base_url: str) -> dict[str, Any]:
    now = datetime.now()
    today = now.date().isoformat()

    checks: list[CheckResult] = []

    venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    checks.append(
        CheckResult(
            name="venv",
            status="PASS" if venv_python.exists() else "FAIL",
            details=str(venv_python),
        )
    )

    if DB_PATH.exists():
        db_info = (
            f"size={DB_PATH.stat().st_size} bytes, "
            f"mtime={datetime.fromtimestamp(DB_PATH.stat().st_mtime).isoformat(timespec='seconds')}"
        )
        checks.append(CheckResult(name="database", status="PASS", details=db_info))
    else:
        checks.append(CheckResult(name="database", status="FAIL", details=f"missing: {DB_PATH}"))

    for file_path in _today_files(today):
        if file_path.exists():
            checks.append(CheckResult(name=f"artifact:{file_path.name}", status="PASS", details="present"))
        else:
            checks.append(CheckResult(name=f"artifact:{file_path.name}", status="WARN", details="not generated yet"))

    api_endpoints = [
        ("health", "/health"),
        ("news_latest", "/news/latest?limit=10"),
        ("philosophy_search", "/philosophy/search?q=ethics"),
        ("trends_summary", "/trends/summary"),
    ]

    api_reachable = True
    for name, path in api_endpoints:
        status_code, payload, elapsed, err = _http_json(f"{base_url}{path}")
        if status_code == 200:
            payload_kind = type(payload).__name__
            details = f"status=200, payload={payload_kind}"
            checks.append(CheckResult(name=f"api:{name}", status="PASS", details=details, latency_ms=elapsed))
            continue

        api_reachable = False
        message = err or f"status={status_code}"
        checks.append(CheckResult(name=f"api:{name}", status="WARN", details=message, latency_ms=elapsed))

    statuses = [item.status for item in checks]
    overall = "FAIL" if "FAIL" in statuses else "WARN" if "WARN" in statuses else "PASS"

    return {
        "timestamp": now.isoformat(timespec="seconds"),
        "base_url": base_url,
        "overall": overall,
        "api_reachable": api_reachable,
        "checks": [
            {
                "name": item.name,
                "status": item.status,
                "details": item.details,
                "latency_ms": item.latency_ms,
            }
            for item in checks
        ],
    }


def write_markdown(snapshot: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# YingYue Status Report",
        "",
        f"- Timestamp: {snapshot['timestamp']}",
        f"- Base URL: {snapshot['base_url']}",
        f"- Overall: {snapshot['overall']}",
        "",
        "## Checks",
    ]

    for item in snapshot["checks"]:
        latency = f" | latency={item['latency_ms']}ms" if item["latency_ms"] is not None else ""
        lines.append(f"- [{item['status']}] {item['name']}: {item['details']}{latency}")

    lines.extend(["", "## Next Action"])
    if snapshot["overall"] == "PASS":
        lines.append("- System is healthy. Continue 30-minute monitoring.")
    elif snapshot["overall"] == "WARN":
        lines.append("- System is partially healthy. Check missing artifacts and re-run pipeline if needed.")
    else:
        lines.append("- System has critical failures. Trigger quick recovery and review API/service logs.")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def dated_markdown_path(base_output_path: Path, timestamp_text: str) -> Path:
    stamp = datetime.fromisoformat(timestamp_text).strftime("%Y-%m-%d")
    return base_output_path.parent / f"status_report_{stamp}.md"


def write_outputs(snapshot: dict[str, Any], output_path: Path, json_output_path: Path | None = None) -> None:
    write_markdown(snapshot, output_path)
    write_markdown(snapshot, dated_markdown_path(output_path, snapshot["timestamp"]))

    if json_output_path is not None:
        json_output_path.parent.mkdir(parents=True, exist_ok=True)
        json_output_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one-shot status report")
    parser.add_argument("--base-url", default=os.getenv("YINGYUE_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument(
        "--output",
        default=str(REPORT_DIR / "status_report.md"),
        help="Markdown output path",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Optional JSON output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot = collect_status(args.base_url)

    output_path = Path(args.output)
    json_output_path = Path(args.json_output) if args.json_output else None
    write_outputs(snapshot, output_path, json_output_path)

    print(f"status report written: {output_path}")
    print(f"overall={snapshot['overall']}")
    return 0 if snapshot["overall"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
