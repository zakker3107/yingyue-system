from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import api_background_runtime


def test_get_runtime_status_treats_unknown_ownership_as_running_when_port_is_open(monkeypatch):
    runtime = {"pid": 1234, "host": "127.0.0.1", "port": 8000}

    monkeypatch.setattr(api_background_runtime, "load_runtime", lambda: runtime)
    monkeypatch.setattr(api_background_runtime, "is_pid_running", lambda pid: True)
    monkeypatch.setattr(api_background_runtime, "looks_like_project_api_process", lambda pid: None)
    monkeypatch.setattr(api_background_runtime, "is_port_open", lambda host, port: True)

    status = api_background_runtime.get_runtime_status()

    assert status["managed"] is True
    assert status["running"] is True
    assert status["stale"] is False
    assert status["ownership_unverified"] is True


def test_get_runtime_status_marks_unknown_ownership_as_stale_when_port_is_closed(monkeypatch):
    runtime = {"pid": 1234, "host": "127.0.0.1", "port": 8000}

    monkeypatch.setattr(api_background_runtime, "load_runtime", lambda: runtime)
    monkeypatch.setattr(api_background_runtime, "is_pid_running", lambda pid: True)
    monkeypatch.setattr(api_background_runtime, "looks_like_project_api_process", lambda pid: None)
    monkeypatch.setattr(api_background_runtime, "is_port_open", lambda host, port: False)

    status = api_background_runtime.get_runtime_status()

    assert status["managed"] is True
    assert status["running"] is False
    assert status["stale"] is True
    assert status["ownership_unverified"] is True
