from __future__ import annotations

import argparse
import os
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib import error, request

from activity_rules_runtime import active_rule_ids, has_rule, load_rules

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "data" / "processed" / "reports" / "recovery"
LOG_DIR = PROJECT_ROOT / "data" / "processed" / "logs"


def _http_ok(url: str, timeout: int = 4) -> bool:
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (error.URLError, TimeoutError, OSError):
        return False


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


def _start_api_detached(python_exe: Path) -> tuple[bool, str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"api_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    try:
        log_handle = log_path.open("a", encoding="utf-8")
        subprocess.Popen(
            [str(python_exe), "scripts\\start_api.py"],
            cwd=PROJECT_ROOT,
            stdout=log_handle,
            stderr=log_handle,
            creationflags=creation_flags,
        )
        return True, str(log_path)
    except Exception as exc:  # noqa: BLE001
        return False, f"failed to start api: {exc}"


def _run_step(name: str, cmd: list[str]) -> dict[str, str | int]:
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")
    return {
        "name": name,
        "code": result.returncode,
        "stdout": (result.stdout or "").strip()[:2000],
        "stderr": (result.stderr or "").strip()[:2000],
        "status": "PASS" if result.returncode == 0 else "FAIL",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quick recovery flow for YingYue")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--run-smoke", action="store_true")
    return parser.parse_args()


def _is_step_ok(step: dict[str, str | int], healthy_after: bool) -> bool:
    status = str(step.get("status", "FAIL"))
    name = str(step.get("name", ""))

    if status in {"PASS", "WARN"}:
        return True

    if name == "api_health_before" and healthy_after:
        return True

    return False


def _append_rule_actions(
    actions: list[dict[str, str | int]],
    rules_payload: dict[str, object],
    python_exe: Path,
    base_url: str,
) -> None:
    rule_ids = active_rule_ids(rules_payload)
    actions.append(
        {
            "name": "active_rules",
            "status": "PASS",
            "code": 0,
            "stdout": ",".join(rule_ids) if rule_ids else "none",
        }
    )

    if has_rule(rules_payload, "svc-001"):
        actions.append(
            _run_step(
                "rule_monitor_tick",
                [str(python_exe), "scripts\\monitor_tick.py", "--base-url", base_url],
            )
        )


def main() -> int:
    args = parse_args()
    python_exe = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        print("[FAIL] .venv python not found")
        return 1

    rules_payload = load_rules()
    rule_ids = active_rule_ids(rules_payload)

    actions: list[dict[str, str | int]] = []
    api_url = f"{args.base_url}/health"

    healthy_before = _http_ok(api_url)
    actions.append({"name": "api_health_before", "status": "PASS" if healthy_before else "FAIL", "code": 0 if healthy_before else 1})

    if not healthy_before:
        if _port_in_use(args.host, args.port):
            actions.append({"name": "api_port_check", "status": "WARN", "code": 0, "stdout": "port in use; skip start"})
        else:
            started, detail = _start_api_detached(python_exe)
            actions.append({"name": "api_start", "status": "PASS" if started else "FAIL", "code": 0 if started else 1, "stdout": detail})

        for _ in range(10):
            if _http_ok(api_url):
                break
            time.sleep(2)

    healthy_after = _http_ok(api_url)
    actions.append({"name": "api_health_after", "status": "PASS" if healthy_after else "FAIL", "code": 0 if healthy_after else 1})

    actions.append(_run_step("run_mvp", [str(python_exe), "scripts\\run_mvp.py"]))
    actions.append(_run_step("generate_daily_report", [str(python_exe), "scripts\\generate_daily_report.py"]))

    if args.run_smoke:
        actions.append(_run_step("smoke_test", [str(python_exe), "tests\\test_pipeline_smoke.py"]))

    _append_rule_actions(actions, rules_payload, python_exe, args.base_url)

    overall = "PASS" if all(_is_step_ok(step, healthy_after) for step in actions) else "FAIL"

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = REPORT_DIR / f"quick_recovery_{stamp}.md"

    lines = [
        "# YingYue Quick Recovery",
        "",
        f"- Timestamp: {datetime.now().isoformat(timespec='seconds')}",
        f"- Overall: {overall}",
        f"- Active Rules: {', '.join(rule_ids) if rule_ids else 'none'}",
        "",
        "## Steps",
    ]
    for step in actions:
        lines.append(f"- [{step.get('status', 'FAIL')}] {step.get('name')} (code={step.get('code', -1)})")
        if step.get("stdout"):
            lines.append(f"  - stdout: {step['stdout']}")
        if step.get("stderr"):
            lines.append(f"  - stderr: {step['stderr']}")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"recovery report written: {out_path}")
    print(f"overall={overall}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
