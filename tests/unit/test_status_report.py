from pathlib import Path
import shutil
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import status_report


TMP_ROOT = PROJECT_ROOT / 'tests' / '_runtime_tmp' / 'status_report'


def test_collect_status_marks_api_downtime_as_warn(monkeypatch):
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT, ignore_errors=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(status_report, 'REPORT_DIR', TMP_ROOT)
    monkeypatch.setattr(status_report, 'DB_PATH', TMP_ROOT / 'yingyue.db')
    status_report.DB_PATH.write_text('db', encoding='utf-8')

    def fake_http_json(url: str, timeout: int = 6):
        return 0, None, 25, 'connection refused'

    monkeypatch.setattr(status_report, '_http_json', fake_http_json)

    snapshot = status_report.collect_status('http://127.0.0.1:8000')

    assert snapshot['overall'] == 'WARN'
    assert snapshot['api_reachable'] is False
    api_checks = [item for item in snapshot['checks'] if item['name'].startswith('api:')]
    assert api_checks
    assert all(item['status'] == 'WARN' for item in api_checks)
