from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from task_scheduler_runtime import get_task_snapshot


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Windows Task Scheduler status for YingYue")
    parser.add_argument("--task-name", default="YingYue-Daily-Ops")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    return parser.parse_args()


def main() -> int:
    _configure_stdout()
    args = parse_args()
    payload = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        **get_task_snapshot(args.task_name),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload.get("available") else 1

    print("[YingYue Task Status]")
    print(f"- Task: {payload['task_name']}")
    print(f"- Available: {'YES' if payload.get('available') else 'NO'}")
    print(f"- Source: {payload.get('source', '')}")
    print(f"- Summary: {payload.get('summary', '')}")
    if payload.get("last_run_time"):
        print(f"- Last Run: {payload['last_run_time']}")
    if payload.get("next_run_time"):
        print(f"- Next Run: {payload['next_run_time']}")
    if payload.get("last_result"):
        print(f"- Last Result: {payload['last_result']}")
    if payload.get("message") and payload.get("message") != payload.get("summary"):
        print(f"- Message: {payload['message']}")
    print(f"- Verify: {payload['verify_command']}")
    return 0 if payload.get("available") else 1


if __name__ == "__main__":
    raise SystemExit(main())
