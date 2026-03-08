from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        check=check,
    )


def print_system_profile() -> None:
    disk = shutil.disk_usage(PROJECT_ROOT)
    free_gb = disk.free / (1024**3)
    total_gb = disk.total / (1024**3)
    print("[System] Platform:", platform.platform())
    print("[System] Python:", sys.version.replace("\n", " "))
    print("[System] CPU Cores:", platform.machine(), "/", (os.cpu_count() or 1))
    print(f"[System] Disk Free: {free_gb:.1f} GB / {total_gb:.1f} GB")


def ensure_venv() -> None:
    if VENV_PYTHON.exists():
        print("[Setup] .venv already exists")
        return

    print("[Setup] Creating .venv")
    run([sys.executable, "-m", "venv", ".venv"])


def install_dependencies(include_dev: bool) -> None:
    print("[Setup] Upgrading pip/setuptools/wheel")
    run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

    print("[Setup] Installing requirements.txt")
    run([str(VENV_PYTHON), "-m", "pip", "install", "-r", "requirements.txt"])

    if include_dev:
        print("[Setup] Installing requirements-dev.txt")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-r", "requirements-dev.txt"])


def run_smoke_test() -> None:
    print("[Check] Running smoke test")
    run([str(VENV_PYTHON), "tests\\test_pipeline_smoke.py"])


def init_database() -> None:
    print("[Setup] Initializing database")
    # 確保資料目錄存在
    data_dir = PROJECT_ROOT / "data" / "curated"
    data_dir.mkdir(parents=True, exist_ok=True)

    # 運行 MVP 管道來初始化資料庫
    run([str(VENV_PYTHON), "scripts\\run_mvp.py"])


def run_mvp_pipeline() -> None:
    print("[Run] Running MVP pipeline")
    run([str(VENV_PYTHON), "scripts\\run_mvp.py"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optimize local environment for yingyue-system")
    parser.add_argument("--skip-install", action="store_true", help="Skip dependency installation")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--run-mvp", action="store_true", help="Run MVP pipeline after optimization")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip smoke test")
    parser.add_argument("--init-db", action="store_true", help="Initialize database")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print_system_profile()
    ensure_venv()

    if not args.skip_install:
        install_dependencies(include_dev=args.dev)
    else:
        print("[Setup] Skipping dependency install")

    if args.init_db:
        init_database()

    if not args.skip_smoke:
        run_smoke_test()
    else:
        print("[Check] Skipping smoke test")

    if args.run_mvp:
        run_mvp_pipeline()

    print("[Done] Environment optimization complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
