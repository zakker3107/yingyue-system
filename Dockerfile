FROM python:3.14-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt requirements-dev.txt ./

# 安裝 Python 依賴
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# 複製應用程式
COPY . .

# 建立資料目錄
RUN mkdir -p data/curated data/processed/reports data/raw data/embeddings

# 設定環境變數
ENV PYTHONPATH=/app
ENV DATABASE_URL=/app/data/curated/yingyue.db

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.connect(('localhost', int('${PORT:-8000}')))" || exit 1

# 啟動命令
CMD ["sh", "-c", "python -m uvicorn services.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]