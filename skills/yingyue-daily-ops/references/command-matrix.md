# Yingyue Command Matrix

## Setup
- `python -m venv .venv`
- `.venv\\Scripts\\activate`
- `pip install -r requirements.txt`

## Daily Pipeline
- `python scripts\\run_mvp.py`
- `python scripts\\generate_daily_report.py`

## API
- `python scripts\\start_api.py`
- `curl http://127.0.0.1:8000/health`

## Health and Recovery
- `python scripts\\health_check.py --run-smoke`
- `python scripts\\status_report.py`
- `python scripts\\quick_recovery.py --run-smoke`

