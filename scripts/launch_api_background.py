from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_SCRIPT = PROJECT_ROOT / "scripts" / "start_api_local.py"
NETWORK_SCRIPT = PROJECT_ROOT / "scripts" / "start_api_network.py"
DETACHED_FLAGS = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "CREATE_NO_WINDOW", 0)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.api_background_runtime import LOG_DIR, cleanup_stale_runtime, ensure_runtime_dirs, is_port_open, save_runtime, utc_now_iso


def wait_for_port(host: str, port: int, timeout: float = 12.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_open(host=host, port=port, timeout=0.5):
            return True
        time.sleep(0.3)
    return False


def spawn_background_process(script: Path, stdout_path: Path, stderr_path: Path) -> int:
    with stdout_path.open("ab") as stdout_handle, stderr_path.open("ab") as stderr_handle:
        process = subprocess.Popen(
            [sys.executable, str(script)],
            cwd=str(PROJECT_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            creationflags=DETACHED_FLAGS if os.name == "nt" else 0,
            close_fds=False if os.name == "nt" else True,
        )
    return process.pid


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "local").strip().lower()
    if mode not in {"local", "network"}:
        print(f"[ERROR] Unsupported mode: {mode}")
        return 1

    cleanup_stale_runtime()
    host = "127.0.0.1"
    port = 8000
    if is_port_open(host=host, port=port):
        print(f"[OK] YingYue API already running on http://{host}:{port}")
        return 0

    script = LOCAL_SCRIPT if mode == "local" else NETWORK_SCRIPT
    if not script.exists():
        print(f"[ERROR] API script not found: {script}")
        return 1

    ensure_runtime_dirs()
    stdout_path = LOG_DIR / f"api_{mode}_stdout.log"
    stderr_path = LOG_DIR / f"api_{mode}_stderr.log"

    pid = spawn_background_process(script=script, stdout_path=stdout_path, stderr_path=stderr_path)

    payload = {
        "pid": pid,
        "mode": mode,
        "host": host,
        "port": port,
        "started_at": utc_now_iso(),
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "script": str(script),
    }
    save_runtime(payload)

    if not wait_for_port(host=host, port=port):
        print("[ERROR] API process started but did not become ready in time")
        print(f"[LOG] {stdout_path}")
        print(f"[LOG] {stderr_path}")
        return 1

    print(f"[OK] Started YingYue API in {mode} background mode")
    print(f"[PID] {pid}")
    print(f"[LOG] {stdout_path}")
    print(f"[LOG] {stderr_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())