from __future__ import annotations

import csv
import json
import locale
import subprocess
from io import StringIO

SUBPROCESS_ENCODING = locale.getpreferredencoding(False) or "utf-8"
TASK_SUMMARY_KEYS = {
    "status",
    "last run time",
    "next run time",
    "last result",
    "taskname",
}


def run_subprocess(cmd: list[str], encoding: str = SUBPROCESS_ENCODING) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        encoding=encoding,
        errors="replace",
    )


def _task_help_command(task_name: str) -> str:
    return f"schtasks /Query /TN {task_name} /V /FO LIST"


def _empty_snapshot(task_name: str) -> dict[str, object]:
    return {
        "task_name": task_name,
        "available": False,
        "source": "unavailable",
        "state": "",
        "last_result": "",
        "last_run_time": "",
        "next_run_time": "",
        "summary": "",
        "message": "",
        "verify_command": _task_help_command(task_name),
    }


def _summarize(snapshot: dict[str, object]) -> str:
    if not snapshot.get("available"):
        message = str(snapshot.get("message", "")).strip()
        return message or "Unavailable"

    parts: list[str] = []
    for key, label in (
        ("state", ""),
        ("last_result", "LastResult="),
        ("next_run_time", "Next="),
        ("last_run_time", "LastRun="),
        ("source", "Source="),
    ):
        value = str(snapshot.get(key, "")).strip()
        if not value:
            continue
        parts.append(f"{label}{value}" if label else value)
    return " | ".join(parts) if parts else "Available"


def _from_powershell(task_name: str) -> dict[str, object]:
    ps_script = (
        "$ErrorActionPreference='Stop';"
        "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false);"
        "$OutputEncoding=[Console]::OutputEncoding;"
        f"$name='{task_name}';"
        "try {"
        "$task=Get-ScheduledTask -TaskName $name -TaskPath '\\';"
        "$info=Get-ScheduledTaskInfo -TaskName $name -TaskPath '\\';"
        "$last=if($info.LastRunTime -and $info.LastRunTime.Year -gt 1){$info.LastRunTime.ToString('s')}else{''};"
        "$next=if($info.NextRunTime -and $info.NextRunTime.Year -gt 1){$info.NextRunTime.ToString('s')}else{''};"
        "[pscustomobject]@{"
        "available=$true;"
        "source='powershell';"
        "task_name=$name;"
        "state=[string]$task.State;"
        "last_result=[string]$info.LastTaskResult;"
        "last_run_time=$last;"
        "next_run_time=$next;"
        "message=''"
        "} | ConvertTo-Json -Compress"
        "} catch {"
        "[pscustomobject]@{"
        "available=$false;"
        "source='powershell';"
        "task_name=$name;"
        "state='';"
        "last_result='';"
        "last_run_time='';"
        "next_run_time='';"
        "message=$_.Exception.Message"
        "} | ConvertTo-Json -Compress"
        "}"
    )
    result = run_subprocess(["powershell", "-NoProfile", "-Command", ps_script], encoding="utf-8")
    payload_text = ((result.stdout or "") + (result.stderr or "")).strip()
    snapshot = _empty_snapshot(task_name)
    snapshot["source"] = "powershell"
    if not payload_text:
        snapshot["message"] = "No output from PowerShell task query"
        snapshot["summary"] = _summarize(snapshot)
        return snapshot
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        snapshot["message"] = payload_text
        snapshot["summary"] = _summarize(snapshot)
        return snapshot
    snapshot.update(payload)
    snapshot["summary"] = _summarize(snapshot)
    return snapshot


def _parse_schtasks_csv(stdout: str) -> dict[str, str]:
    rows = list(csv.DictReader(StringIO(stdout)))
    if not rows:
        return {}
    row = rows[0]
    normalized = {str(key).strip().lower(): str(value).strip() for key, value in row.items() if key}
    return {key: value for key, value in normalized.items() if key in TASK_SUMMARY_KEYS and value}


def _from_schtasks(task_name: str) -> dict[str, object]:
    for candidate in (task_name, f"\\{task_name}"):
        result = run_subprocess(["schtasks", "/Query", "/TN", candidate, "/V", "/FO", "CSV"])
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        combined = f"{stdout}\n{stderr}".lower()
        snapshot = _empty_snapshot(task_name)
        snapshot["source"] = "schtasks"

        if "access is denied" in combined or "cannot find the path specified" in combined:
            snapshot["message"] = (
                "UNVERIFIED_FROM_CURRENT_SESSION "
                f"(Task Scheduler access is limited in this session; verify with: {_task_help_command(task_name)})"
            )
            snapshot["summary"] = _summarize(snapshot)
            return snapshot

        if result.returncode != 0 and not stdout:
            continue

        parsed = _parse_schtasks_csv(stdout)
        if parsed:
            snapshot.update(
                {
                    "available": True,
                    "state": parsed.get("status", ""),
                    "last_result": parsed.get("last result", ""),
                    "last_run_time": parsed.get("last run time", ""),
                    "next_run_time": parsed.get("next run time", ""),
                }
            )
            snapshot["summary"] = _summarize(snapshot)
            return snapshot

        if stdout:
            snapshot["message"] = stdout.splitlines()[0]
            snapshot["summary"] = _summarize(snapshot)
            return snapshot

    snapshot = _empty_snapshot(task_name)
    snapshot["source"] = "schtasks"
    snapshot["message"] = f"NOT_INSTALLED_OR_INVISIBLE (check with: {_task_help_command(task_name)})"
    snapshot["summary"] = _summarize(snapshot)
    return snapshot


def get_task_snapshot(task_name: str) -> dict[str, object]:
    powershell_snapshot = _from_powershell(task_name)
    if powershell_snapshot.get("available"):
        return powershell_snapshot

    schtasks_snapshot = _from_schtasks(task_name)
    if schtasks_snapshot.get("available"):
        return schtasks_snapshot
    if schtasks_snapshot.get("message"):
        return schtasks_snapshot
    return powershell_snapshot
