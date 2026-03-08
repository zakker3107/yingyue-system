#!/usr/bin/env python
"""診斷和優化數據庫配置"""

import sqlite3
from pathlib import Path

print("=" * 70)
print("數據庫優化診斷")
print("=" * 70)

db_path = Path("data/curated/yingyue.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 1. 檢查 PRAGMA 設置
print("\n[PRAGMA 設置]")
pragmas = {
    'journal_mode': '日誌模式',
    'cache_size': '緩存大小',
    'temp_store': '臨時存儲',
    'synchronous': '同步級別',
    'foreign_keys': '外鍵'
}

for pragma, desc in pragmas.items():
    try:
        cursor.execute(f'PRAGMA {pragma}')
        value = cursor.fetchone()[0]
        print(f"✓ {pragma}: {value} ({desc})")
    except Exception as e:
        print(f"✗ {pragma}: 錯誤 - {e}")

# 2. 檢查表的索引
print("\n[索引檢查]")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    try:
        cursor.execute(f'PRAGMA index_list({table})')
        indexes = cursor.fetchall()
        if indexes:
            print(f"✓ {table}: {len(indexes)} 個索引")
        else:
            print(f"⚠ {table}: 無索引 (考慮添加)")
    except Exception as e:
        print(f"✗ {table}: 錯誤 - {e}")

# 3. 數據庫大小
print("\n[數據庫狀態]")
db_size = db_path.stat().st_size
print(f"✓ 文件大小: {db_size / 1024:.1f} KB")

cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
occupied = cursor.fetchone()[0]
print(f"✓ 佔用空間: {occupied / 1024:.1f} KB")

# 4. 表記錄數統計
print("\n[表記錄數]")
for table in tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"✓ {table}: {count} 條")
    except:
        pass

# 5. 檢查未使用的空間
print("\n[空間優化建議]")
cursor.execute("PRAGMA freelist_count")
freelist = cursor.fetchone()[0]
if freelist > 0:
    print(f"⚠ 可回收空間: ~{freelist} 頁 ({freelist * 4096 / 1024:.1f} KB)")
    print("  建議: 執行 VACUUM 以回收空間")
else:
    print("✓ 無可回收空間")

conn.close()

print("\n" + "=" * 70)
print("✅ 診斷完成")
print("=" * 70)
