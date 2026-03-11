from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import launch_api_background


def test_resolve_hosts_uses_network_bind_with_local_probe():
    bind_host, probe_host = launch_api_background.resolve_hosts("network")

    assert bind_host == "0.0.0.0"
    assert probe_host == "127.0.0.1"


def test_main_fails_when_port_is_taken_by_unmanaged_process(monkeypatch, capsys):
    monkeypatch.setattr(launch_api_background, "cleanup_stale_runtime", lambda: None)
    monkeypatch.setattr(launch_api_background, "get_runtime_status", lambda: {"managed": False, "running": False, "stale": False})
    monkeypatch.setattr(launch_api_background, "is_port_open", lambda host, port: True)
    monkeypatch.setattr(launch_api_background.sys, "argv", ["launch_api_background.py", "local"])

    exit_code = launch_api_background.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "unmanaged process" in output


def test_main_removes_runtime_when_process_never_becomes_ready(monkeypatch, capsys):
    saved_payloads = []
    removed = []

    monkeypatch.setattr(launch_api_background, "cleanup_stale_runtime", lambda: None)
    monkeypatch.setattr(launch_api_background, "get_runtime_status", lambda: {"managed": False, "running": False, "stale": False})
    monkeypatch.setattr(launch_api_background, "is_port_open", lambda host, port: False)
    monkeypatch.setattr(launch_api_background, "ensure_runtime_dirs", lambda: None)
    monkeypatch.setattr(launch_api_background, "spawn_background_process", lambda script, stdout_path, stderr_path: 4321)
    monkeypatch.setattr(launch_api_background, "save_runtime", lambda payload: saved_payloads.append(payload))
    monkeypatch.setattr(launch_api_background, "remove_runtime", lambda: removed.append(True))
    monkeypatch.setattr(launch_api_background, "wait_for_port", lambda host, port: False)
    monkeypatch.setattr(launch_api_background, "LOCAL_SCRIPT", PROJECT_ROOT / "scripts" / "start_api_local.py")
    monkeypatch.setattr(launch_api_background, "LOG_DIR", PROJECT_ROOT / "data" / "processed" / "logs")
    monkeypatch.setattr(launch_api_background.sys, "argv", ["launch_api_background.py", "local"])

    exit_code = launch_api_background.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert removed == [True]
    assert saved_payloads[0]["bind_host"] == "127.0.0.1"
    assert saved_payloads[0]["stdout_log"].endswith("api_local_stdout.log")
    assert saved_payloads[0]["stderr_log"].endswith("api_local_stderr.log")
    assert "did not become ready in time" in output
