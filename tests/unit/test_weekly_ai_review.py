from pathlib import Path
import sys

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
