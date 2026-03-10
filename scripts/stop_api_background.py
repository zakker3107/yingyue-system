from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.api_background_runtime import get_runtime_status, remove_runtime, terminate_pid


def main() -> int:
    status = get_runtime_status()
    pid = int(status.get("pid", 0) or 0)

    if status.get("managed") and status.get("running") and not status.get("stale"):
        if terminate_pid(pid):
            remove_runtime()
            print(f"[DONE] Stopped managed YingYue API process PID={pid}")
            return 0
        print(f"[ERROR] Failed to stop managed YingYue API process PID={pid}")
        return 1

    if status.get("managed") and status.get("stale"):
        remove_runtime()
        print("[DONE] Removed stale YingYue API background metadata")
        return 0

    if status.get("running"):
        print("[WARN] Port 8000 is active, but it is not tracked as a managed YingYue background process.")
        print("[WARN] Stop it manually if that service should be terminated.")
        return 1

    print("[DONE] No managed YingYue API background process found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
