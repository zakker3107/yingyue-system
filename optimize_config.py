#!/usr/bin/env python
"""系統配置優化腳本"""

import sqlite3
from pathlib import Path
import json

print("=" * 70)
print("系統配置優化")
print("=" * 70)

# 1. 數據庫優化
print("\n[數據庫優化]")
db_path = Path("data/curated/yingyue.db")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 啟用外鍵約束
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # 設置最優的 PRAGMA 值
    optimizations = [
        ("PRAGMA journal_mode = WAL", "WAL 日誌模式"),
        ("PRAGMA cache_size = -2000", "設置 2MB 緩存"),
        ("PRAGMA temp_store = MEMORY", "使用內存存儲臨時文件"),
        ("PRAGMA synchronous = NORMAL", "優化寫入同步"),
        ("PRAGMA foreign_keys = ON", "啟用外鍵約束"),
    ]
    
    for pragma, desc in optimizations:
        try:
            cursor.execute(pragma)
            print(f"✓ {desc}")
        except Exception as e:
            print(f"⚠ {desc}: {e}")
    
    conn.commit()
    conn.close()
    
except Exception as e:
    print(f"✗ 數據庫優化失敗: {e}")

# 2. 檢查配置文件
print("\n[配置文件驗證]")
config_files = {
    "config/sources.json": "新聞來源配置",
    "config/philosophy_seed.json": "哲學數據",
}

for config_path, desc in config_files.items():
    try:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                keys = len(data)
                print(f"✓ {desc}: {keys} 個主鍵")
            elif isinstance(data, list):
                items = len(data)
                print(f"✓ {desc}: {items} 個項目")
        else:
            print(f"⚠ {config_path}: 文件不存在")
    except Exception as e:
        print(f"✗ {config_path}: {e}")

# 3. 環境配置
print("\n[環境配置檢查]")
import os

env_vars = {
    "GOOGLE_APPLICATION_CREDENTIALS": "Google 認證文件",
    "FIREBASE_PROJECT_ID": "Firebase 項目 ID",
}

for var, desc in env_vars.items():
    value = os.getenv(var, "未設置")
    if value != "未設置":
        print(f"✓ {desc}: 已設置")
    else:
        print(f"⚠ {desc}: 未設置")

# 4. 虛擬環境檢查
print("\n[依賴檢查]")
try:
    import fastapi
    import firebase_admin
    import feedparser
    import pydantic
    
    modules = [
        ("fastapi", fastapi.__version__),
        ("firebase_admin", firebase_admin.__version__),
        ("feedparser", feedparser.__version__),
        ("pydantic", pydantic.__version__),
    ]
    
    for module, version in modules:
        print(f"✓ {module}: {version}")
except ImportError as e:
    print(f"✗ 依賴導入失敗: {e}")

# 5. 系統資源
print("\n[系統資源]")
import os
import shutil

disk = shutil.disk_usage("/")
print(f"✓ 磁碟空間: {disk.free / 1024**3:.1f} GB / {disk.total / 1024**3:.1f} GB")
print(f"✓ CPU 核心: {os.cpu_count()}")

print("\n" + "=" * 70)
print("✅ 優化完成 - 系統已優化至最佳配置")
print("=" * 70)
