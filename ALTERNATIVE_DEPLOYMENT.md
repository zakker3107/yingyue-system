# 替代部署選項

由於個人 Microsoft 帳號無法直接登入 Azure，以下是其他部署選項：

## 選項 1: Azure 學生/開發者帳號
1. 前往 https://azure.microsoft.com/en-us/free/students/
2. 使用學校 email 註冊學生帳號
3. 或使用 https://azure.microsoft.com/en-us/free/ 註冊免費開發者帳號

## 選項 2: 使用 Docker + 其他平台

### 建立 Dockerfile
```dockerfile
FROM python:3.14-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt requirements-dev.txt ./

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# 複製應用程式
COPY . .

# 建立資料目錄
RUN mkdir -p data/curated data/processed/reports

# 初始化資料庫
RUN python scripts/optimize_environment.py --init-db --skip-smoke

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["python", "-m", "uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 建立 docker-compose.yml
```yaml
version: '3.8'

services:
  yingyue-system:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
```

### 部署到：
- **Railway**: https://railway.app (免費層級可用)
- **Render**: https://render.com (免費 PostgreSQL + Web Service)
- **Fly.io**: https://fly.io (Docker 原生)

## 選項 3: 使用 GitHub Pages (前端靜態版本)
如果只需要展示功能，可以建立簡化的前端版本部署到 GitHub Pages。

## 選項 4: 本地部署 + 反向代理
使用 Nginx 或 Caddy 作為反向代理，提供 HTTPS 和負載平衡。

您想要使用哪個選項？我可以幫您設定對應的配置。