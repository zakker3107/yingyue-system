from __future__ import annotations

import csv
import io
import json
import os
import signal
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / "data" / "processed" / "runtime"
LOG_DIR = PROJECT_ROOT / "data" / "processed" / "logs"
PID_FILE = RUNTIME_DIR / "api_background.json"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_runtime_dirs() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_runtime() -> dict[str, object] | None:
    if not PID_FILE.exists():
        return None
    try:
        return json.loads(PID_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_runtime(payload: dict[str, object]) -> None:
    ensure_runtime_dirs()
    PID_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def remove_runtime() -> None:
    try:
        PID_FILE.unlink()
    except FileNotFoundError:
        pass


def is_port_open(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
        output = (result.stdout or "").strip()
        if output and not output.startswith("INFO:"):
            rows = list(csv.reader(io.StringIO(output)))
            if rows and len(rows[0]) >= 2 and rows[0][1] == str(pid):
                return True

        # Some Windows sessions cannot inspect tasklist details for detached
        # background processes. Fall back to Get-Process before declaring it dead.
        fallback = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue; if ($p) {{ 'RUNNING' }}",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
        return (fallback.stdout or "").strip() == "RUNNING"
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def get_process_command_line(pid: int) -> str:
    if pid <= 0:
        return ""
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "$p = Get-CimInstance Win32_Process -Filter \"ProcessId = %d\"; "
                "if ($p) { $p.CommandLine }"
            )
            % pid,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    return (result.stdout or "").strip()


def looks_like_project_api_process(pid: int) -> bool:
    cmdline = get_process_command_line(pid).lower()
    if not cmdline:
        return False
    project_marker = str(PROJECT_ROOT).lower()
    return project_marker in cmdline and "start_api" in cmdline


def get_runtime_status() -> dict[str, object]:
    runtime = load_runtime()
    if not runtime:
        return {
            "managed": False,
            "running": is_port_open(),
            "message": "No managed background API process metadata found.",
        }

    pid = int(runtime.get("pid", 0) or 0)
    host = str(runtime.get("host", DEFAULT_HOST))
    port = int(runtime.get("port", DEFAULT_PORT) or DEFAULT_PORT)
    pid_running = is_pid_running(pid)
    is_project_process = looks_like_project_api_process(pid) if pid_running else False
    port_open = is_port_open(host=host, port=port)

    if not pid_running or not is_project_process:
        return {
            "managed": True,
            "running": port_open,
            "stale": True,
            "pid": pid,
            "host": host,
            "port": port,
            "runtime": runtime,
            "message": "Managed background metadata is stale.",
        }

    return {
        "managed": True,
        "running": True,
        "stale": False,
        "pid": pid,
        "host": host,
        "port": port,
        "runtime": runtime,
        "message": "Managed background API process is running.",
    }


def cleanup_stale_runtime() -> None:
    status = get_runtime_status()
    if status.get("stale"):
        remove_runtime()


def terminate_pid(pid: int, timeout: float = 8.0) -> bool:
    if pid <= 0 or not is_pid_running(pid):
        return True

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        os.kill(pid, signal.SIGTERM)

    deadline = time.time() + timeout
    while time.time() < deadline:
        if not is_pid_running(pid):
            return True
        time.sleep(0.2)
    return not is_pid_running(pid)

