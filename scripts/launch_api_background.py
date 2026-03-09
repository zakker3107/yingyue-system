from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SCRIPT = PROJECT_ROOT / "scripts" / "start_api_local.py"
NETWORK_SCRIPT = PROJECT_ROOT / "scripts" / "start_api_network.py"
LOG_DIR = PROJECT_ROOT / "data" / "processed" / "logs"
DETACHED_FLAGS = subprocess.CREATE_NEW_PROCESS_GROUP


def _is_api_reachable(host: str = "127.0.0.1", port: int = 8000) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "local").strip().lower()
    if mode not in {"local", "network"}:
        print(f"[ERROR] Unsupported mode: {mode}")
        return 1

    if _is_api_reachable():
        print("[OK] YingYue API already running on http://127.0.0.1:8000")
        return 0

    script = LOCAL_SCRIPT if mode == "local" else NETWORK_SCRIPT
    if not script.exists():
        print(f"[ERROR] API script not found: {script}")
        return 1

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stdout_path = LOG_DIR / f"api_{mode}_stdout.log"
    stderr_path = LOG_DIR / f"api_{mode}_stderr.log"

    with stdout_path.open("ab") as stdout_handle, stderr_path.open("ab") as stderr_handle:
        subprocess.Popen(
            [sys.executable, str(script)],
            cwd=str(PROJECT_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            creationflags=DETACHED_FLAGS,
            env=os.environ.copy(),
        )

    print(f"[OK] Started YingYue API in {mode} mode")
    print(f"[LOG] {stdout_path}")
    print(f"[LOG] {stderr_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
