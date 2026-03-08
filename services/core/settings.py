from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "curated" / "yingyue.db"
SOURCES_CONFIG = ROOT / "config" / "sources.json"
PHILOSOPHY_SEED = ROOT / "config" / "philosophy_seed.json"
RAW_NEWS_PATH = ROOT / "data" / "raw" / "news_items.json"
REPORT_DIR = ROOT / "data" / "processed" / "reports"
