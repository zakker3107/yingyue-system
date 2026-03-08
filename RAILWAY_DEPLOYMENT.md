# Railway 部署指南

Railway 是一個現代化的雲端平台，支援 Docker 部署，非常適合個人開發者。

## 步驟 1: 註冊 Railway 帳號
1. 前往 https://railway.app
2. 使用 GitHub 或 email 註冊
3. 驗證 email

## 步驟 2: 安裝 Railway CLI (可選)
```bash
# 安裝 Railway CLI
npm install -g @railway/cli

# 登入
railway login
```

## 步驟 3: 部署應用程式

### 方法 1: 使用 Railway CLI
```bash
# 初始化專案
railway init

# 連結到現有專案或創建新專案
railway link

# 部署
railway up
```

### 方法 2: 使用 GitHub 整合 (推薦)
1. 在 Railway 儀表板中點擊 "New Project"
2. 選擇 "Deploy from GitHub repo"
3. 連接您的 GitHub 帳號
4. 選擇 yingyue-system 倉庫
5. Railway 會自動檢測 Dockerfile 並部署

## 步驟 4: 設定環境變數
在 Railway 專案設定中添加：
- `PYTHONPATH=/app`
- `DATABASE_URL=/app/data/curated/yingyue.db`

## 步驟 5: 資料庫初始化
Railway 會自動運行 Dockerfile 中的初始化命令。

## 步驟 6: 設定域名 (可選)
Railway 提供免費的 `*.up.railway.app` 域名，您也可以連接自訂域名。

## 監控和日誌
- 在 Railway 儀表板查看應用程式狀態
- 查看即時日誌
- 監控資源使用情況

## 免費層級限制
- 512 MB RAM
- 1 GB 儲存空間
- 每月 100 小時運行時間

如果需要更多資源，可以升級到付費計劃。

## 疑難排解
- 檢查 Railway 日誌中的錯誤訊息
- 確保 Dockerfile 中的所有依賴都正確安裝
- 確認網路端口設定正確 (Railway 會自動設定 $PORT 環境變數)