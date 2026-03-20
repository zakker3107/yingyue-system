from pathlib import Path
import sys
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import generate_weekly_ai_review as weekly_review


def test_clean_text_strips_control_characters():
    assert weekly_review._clean_text('A\x00B\nC') == 'AB C'


def test_analyze_conversation_sanitizes_title_and_message_text():
    raw = {
        'title': 'Bad\x00Title',
        'create_time': 1773043200,
        'mapping': {
            '1': {
                'message': {
                    'author': {'role': 'user'},
                    'content': {'parts': ['Need\x00 review']},
                    'metadata': {},
                }
            },
            '2': {
                'message': {
                    'author': {'role': 'assistant'},
                    'content': {'parts': ['Done\x00 now']},
                    'metadata': {},
                }
            },
        },
    }

    record = weekly_review._analyze_conversation(raw)

    assert record is not None
    assert record.title == 'BadTitle'
    assert record.user_chars == len('Need review')
    assert record.assistant_chars == len('Done now')


def test_resolve_export_path_picks_newest_export_dir(tmp_path, monkeypatch):
    export_root = tmp_path / "imports"
    older = export_root / "chat_export_20260301"
    newer = export_root / "chat_export_20260307"
    older.mkdir(parents=True)
    newer.mkdir(parents=True)
    (older / "conversations-000.json").write_text("[]", encoding="utf-8")
    (newer / "conversations-000.json").write_text("[]", encoding="utf-8")

    older_ts = datetime(2026, 3, 1, 8, 0).timestamp()
    newer_ts = datetime(2026, 3, 7, 8, 0).timestamp()
    older.touch()
    newer.touch()
    (older / "conversations-000.json").touch()
    (newer / "conversations-000.json").touch()
    import os
    os.utime(older, (older_ts, older_ts))
    os.utime(newer, (newer_ts, newer_ts))

    monkeypatch.setattr(weekly_review, "DEFAULT_EXPORT_ROOT", export_root)

    resolved = weekly_review._resolve_export_path("")

    assert resolved == newer
