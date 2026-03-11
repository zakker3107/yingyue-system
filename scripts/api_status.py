from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.api_background_runtime import get_runtime_status


def fetch_health() -> tuple[bool, str]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body)
            return True, f"{response.status} {json.dumps(payload, ensure_ascii=False)}"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return False, str(exc)


def main() -> int:
    status = get_runtime_status()
    healthy, health_detail = fetch_health()

    print("[API Status]")
    print(f"- Managed: {'YES' if status.get('managed') else 'NO'}")
    print(f"- Running: {'YES' if status.get('running') else 'NO'}")
    print(f"- Health:  {'OK' if healthy else 'DOWN'}")
    if status.get("stale"):
        print("- State:   STALE")
    if status.get("pid"):
        print(f"- PID:     {status['pid']}")
    if status.get("runtime"):
        runtime = status["runtime"]
        print(f"- Mode:    {runtime.get('mode', 'unknown')}")
        print(f"- Bind:    {runtime.get('bind_host', runtime.get('host', 'unknown'))}:{runtime.get('port', 'unknown')}")
        print(f"- Probe:   http://{runtime.get('host', '127.0.0.1')}:{runtime.get('port', 'unknown')}")
        print(f"- Started: {runtime.get('started_at', 'unknown')}")
        print(f"- Stdout:  {runtime.get('stdout_log', '')}")
        print(f"- Stderr:  {runtime.get('stderr_log', '')}")
    print(f"- Note:    {status.get('message', '')}")
    print(f"- Detail:  {health_detail}")
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
