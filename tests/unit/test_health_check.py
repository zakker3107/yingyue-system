from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts import health_check


class Completed:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_get_task_status_from_schtasks_marks_limited_session_as_unverified(monkeypatch):
    monkeypatch.setattr(
        health_check,
        "run_subprocess",
        lambda cmd: Completed(stderr="ERROR: The system cannot find the path specified.", returncode=1),
    )

    status = health_check.get_task_status_from_schtasks()

    assert status == health_check.SESSION_LIMITED_TASK_STATUS


def test_get_task_status_falls_back_to_schtasks_when_powershell_access_is_denied(monkeypatch):
    calls = []

    def fake_run(cmd):
        calls.append(cmd)
        if cmd[0] == "powershell":
            return Completed(stdout="Unavailable: Access is denied", returncode=0)
        return Completed(stderr="ERROR: The system cannot find the path specified.", returncode=1)

    monkeypatch.setattr(health_check, "run_subprocess", fake_run)

    status = health_check.get_task_status()

    assert status == health_check.SESSION_LIMITED_TASK_STATUS
    assert any(cmd[0] == "schtasks" for cmd in calls)
