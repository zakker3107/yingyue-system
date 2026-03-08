from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from status_report import collect_status

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MONITOR_DIR = PROJECT_ROOT / "data" / "processed" / "reports" / "monitoring"



def _line_for(snapshot: dict) -> str:
    timestamp = snapshot["timestamp"]
    overall = snapshot["overall"]

    fail_count = sum(1 for c in snapshot["checks"] if c["status"] == "FAIL")
    warn_count = sum(1 for c in snapshot["checks"] if c["status"] == "WARN")

    return f"| {timestamp} | {overall} | {fail_count} | {warn_count} | {snapshot['base_url']} |"



def _ensure_daily_md(path: Path) -> None:
    if path.exists():
        return
    lines = [
        "# D1 Monitoring Summary (30-min ticks)",
        "",
        "| timestamp | overall | fail_count | warn_count | base_url |",
        "|---|---|---|---|---|",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")



def write_tick(snapshot: dict, daily_md: Path, daily_jsonl: Path) -> None:
    MONITOR_DIR.mkdir(parents=True, exist_ok=True)

    _ensure_daily_md(daily_md)
    with daily_md.open("a", encoding="utf-8") as f:
        f.write(_line_for(snapshot) + "\n")

    with daily_jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append one monitoring tick")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--date", default=datetime.now().date().isoformat())
    return parser.parse_args()



def main() -> int:
    args = parse_args()
    snapshot = collect_status(args.base_url)

    daily_md = MONITOR_DIR / f"d1_monitor_{args.date}.md"
    daily_jsonl = MONITOR_DIR / f"d1_monitor_{args.date}.jsonl"
    write_tick(snapshot, daily_md, daily_jsonl)

    print(f"monitor tick written: {daily_md}")
    print(f"overall={snapshot['overall']}")
    return 0 if snapshot["overall"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
