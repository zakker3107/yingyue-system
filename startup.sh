#!/bin/bash

# Azure App Service 啟動腳本

echo "Starting YingYue System..."

# 確保在正確目錄
cd /home/site/wwwroot

# 激活虛擬環境
source venv/bin/activate

# 設定環境變數
export PYTHONPATH=/home/site/wwwroot
export DATABASE_URL=/home/site/wwwroot/data/curated/yingyue.db

# 確保資料目錄存在
mkdir -p data/curated
mkdir -p data/processed/reports

# 啟動應用
python -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000