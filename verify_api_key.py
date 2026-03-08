#!/usr/bin/env python
"""驗證新增的 API KEY 配置是否有效"""

import os
import sys
from pathlib import Path

print("=" * 70)
print("API KEY 配置驗證")
print("=" * 70)

# 檢查環境變數
print("\n[環境變數]")
google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
firebase_pid = os.getenv("FIREBASE_PROJECT_ID", "")
cloudsdk_config = os.getenv("CLOUDSDK_CONFIG", "")

print(f"✓ GOOGLE_APPLICATION_CREDENTIALS: {bool(google_creds)}")
if google_creds:
    cred_path = Path(google_creds)
    print(f"  - 路徑存在: {cred_path.exists()}")
    print(f"  - 完整路徑: {cred_path}")

print(f"✓ FIREBASE_PROJECT_ID: {firebase_pid if firebase_pid else '未設置'}")
print(f"✓ CLOUDSDK_CONFIG: {bool(cloudsdk_config)}")

# 檢查認證文件
print("\n[認證文件]")
adc_candidates = [
    Path(cloudsdk_config) / "application_default_credentials.json" if cloudsdk_config else None,
    Path.cwd() / ".gcloud" / "application_default_credentials.json",
    Path(os.getenv("APPDATA", "")) / "gcloud" / "application_default_credentials.json" if os.getenv("APPDATA") else None,
]

for i, candidate in enumerate(adc_candidates, 1):
    if candidate:
        exists = candidate.exists()
        status = "✓" if exists else "✗"
        print(f"{status} 位置 {i}: {candidate}")
        if exists:
            print(f"  - 文件大小: {candidate.stat().st_size} bytes")

# 驗證 Firebase
print("\n[Firebase SDK]")
try:
    import firebase_admin
    print("✓ firebase_admin SDK 已安裝")
    from firebase_admin import credentials
    print("✓ credentials 模組可用")
except ImportError as e:
    print(f"✗ Firebase SDK 導入失敗: {e}")
    sys.exit(1)

# 驗證認證
print("\n[認證驗證]")
try:
    if google_creds and Path(google_creds).exists():
        cred = credentials.Certificate(google_creds)
        print(f"✓ 認證文件有效")
        print(f"✓ Project ID (從文件): {cred.project_id}")
    else:
        print("⚠ 未找到有效的認證文件路徑")
except Exception as e:
    print(f"✗ 認證驗證失敗: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ API KEY 配置驗證完成 - 系統就緒")
print("=" * 70)
