from __future__ import annotations

import argparse
import importlib.util
import json
import locale
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from activity_rules_runtime import active_rule_ids, load_rules
from task_scheduler_runtime import get_task_snapshot

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
REPORT_DIR = PROJECT_ROOT / "data" / "processed" / "reports"
TASK_NAME = os.getenv("YINGYUE_TASK_NAME", "YingYue-Daily-Ops")
SUBPROCESS_ENCODING = locale.getpreferredencoding(False) or "utf-8"


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def to_console_text(value: object) -> str:
    text = str(value)
    encoding = sys.stdout.encoding or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


def print_line(title: str, value: str) -> None:
    print(to_console_text(f"- {title}: {value}"))


def get_windows_version() -> str:
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            product_name = winreg.QueryValueEx(key, "ProductName")[0]
            display_version = winreg.QueryValueEx(key, "DisplayVersion")[0]
            current_build = winreg.QueryValueEx(key, "CurrentBuild")[0]
            ubr = winreg.QueryValueEx(key, "UBR")[0]
        return f"{product_name} {display_version} (Build {current_build}.{ubr})"
    except Exception:
        return platform.platform()


def get_pip_version() -> str:
    try:
        from importlib.metadata import version

        return version("pip")
    except Exception:
        return "unknown"


def run_subprocess(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        encoding=SUBPROCESS_ENCODING,
        errors="replace",
    )


def get_firebase_status() -> str:
    sdk_installed = importlib.util.find_spec("firebase_admin") is not None
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    cloudsdk_config = os.getenv("CLOUDSDK_CONFIG", "").strip()
    adc_candidates = [
        Path(cloudsdk_config) / "application_default_credentials.json" if cloudsdk_config else None,
        PROJECT_ROOT / "tools" / "gcloud-config" / "application_default_credentials.json",
        PROJECT_ROOT / ".gcloud" / "application_default_credentials.json",
        Path(os.getenv("APPDATA", "")) / "gcloud" / "application_default_credentials.json" if os.getenv("APPDATA") else None,
    ]
    has_adc = any(path and path.exists() for path in adc_candidates)
    if not sdk_installed and not cred_path and not project_id and not has_adc:
        return "NOT_CONFIGURED"
    if not sdk_installed:
        return "SDK_MISSING (install firebase-admin)"
    cred_exists = Path(cred_path).exists() if cred_path else False
    if cred_exists:
        return "READY_BASIC"
    if has_adc:
        return "READY_ADC"
    if cred_path and not cred_exists:
        return f"CREDENTIALS_NOT_FOUND ({cred_path})"
    return "CREDENTIALS_MISSING (set GOOGLE_APPLICATION_CREDENTIALS or run gcloud auth application-default login)"


def get_report_status(today: str) -> dict[str, str]:
    expected = {
        "daily_report": REPORT_DIR / f"daily_report_{today}.md",
        "news_csv": REPORT_DIR / f"daily_report_{today}_news.csv",
        "agent_json": REPORT_DIR / f"agent_pipeline_{today}.json",
        "thought_links": REPORT_DIR / f"thought_links_{today}.md",
    }
    status: dict[str, str] = {}
    for key, path in expected.items():
        status[key] = "OK" if path.exists() else "MISSING"
    return status


def get_recent_outputs(limit: int = 5) -> list[str]:
    if not REPORT_DIR.exists():
        return []
    files = sorted(REPORT_DIR.glob("*"), key=lambda path: path.stat().st_mtime, reverse=True)
    return [f"{path.name} ({datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')})" for path in files[:limit]]


def get_activity_rules_status() -> dict[str, object]:
    payload = load_rules()
    rule_ids = active_rule_ids(payload)
    high_count = 0
    for item in payload.get("rules", []):
        if isinstance(item, dict) and str(item.get("severity", "")).lower() == "high":
            high_count += 1
    return {
        "exists": bool(payload.get("exists", False)),
        "path": str(payload.get("path", "")),
        "rule_count": len(rule_ids),
        "high_count": high_count,
        "rule_ids": rule_ids,
    }


def run_smoke_test() -> str:
    if not VENV_PYTHON.exists():
        return "SKIPPED (.venv missing)"
    result = subprocess.run(
        [str(VENV_PYTHON), "tests\\test_pipeline_smoke.py"],
        cwd=PROJECT_ROOT,
        text=True,
    )
    return "PASS" if result.returncode == 0 else f"FAIL (exit={result.returncode})"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Health check for yingyue-system and host")
    parser.add_argument("--run-smoke", action="store_true", help="Run smoke test")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    return parser.parse_args()


def main() -> int:
    configure_stdout()
    args = parse_args()
    disk = shutil.disk_usage(PROJECT_ROOT)
    now = datetime.now().strftime("%Y-%m-%d")
    report_status = get_report_status(now)
    task_snapshot = get_task_snapshot(TASK_NAME)
    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "windows": get_windows_version(),
        "python": sys.version.split()[0],
        "venv_python": str(VENV_PYTHON),
        "venv_exists": VENV_PYTHON.exists(),
        "pip": get_pip_version(),
        "cpu_cores": os.cpu_count() or 1,
        "disk_free_gb": round(disk.free / (1024**3), 1),
        "disk_total_gb": round(disk.total / (1024**3), 1),
        "task_status": str(task_snapshot.get("summary", "")),
        "task_details": task_snapshot,
        "firebase": get_firebase_status(),
        "reports_today": report_status,
        "recent_outputs": get_recent_outputs(),
        "activity_rules": get_activity_rules_status(),
    }
    if args.run_smoke:
        summary["smoke_test"] = run_smoke_test()
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    print(to_console_text("[YingYue Health Check]"))
    print_line("Time", summary["timestamp"])
    print_line("Windows", summary["windows"])
    print_line("Python", summary["python"])
    print_line("pip", summary["pip"])
    print_line("CPU Cores", str(summary["cpu_cores"]))
    print_line("Disk Free", f"{summary['disk_free_gb']} GB / {summary['disk_total_gb']} GB")
    print_line("Task", summary["task_status"])
    print_line("Task Verify", str(task_snapshot.get("verify_command", "")))
    print_line("Firebase", summary["firebase"])
    print(to_console_text("- Reports Today:"))
    for key, value in summary["reports_today"].items():
        print(to_console_text(f"  - {key}: {value}"))
    rules = summary["activity_rules"]
    print(to_console_text("- Activity Rules:"))
    print(to_console_text(f"  - path: {rules['path']}"))
    print(to_console_text(f"  - exists: {rules['exists']}"))
    print(to_console_text(f"  - rule_count: {rules['rule_count']} (high={rules['high_count']})"))
    print(to_console_text(f"  - rule_ids: {', '.join(rules['rule_ids']) if rules['rule_ids'] else 'none'}"))
    if args.run_smoke:
        print_line("Smoke Test", summary["smoke_test"])
    print(to_console_text("- Recent Outputs:"))
    for line in summary["recent_outputs"]:
        print(to_console_text(f"  - {line}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
