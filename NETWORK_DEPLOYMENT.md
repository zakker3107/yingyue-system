# 本地部署 + 網際網路連通方案

此方案允許您在本地機器運行 YingYue 系統，並通過 ngrok 隧道安全地暴露到網際網路。

## 快速開始

### 步驟 1: 安裝 ngrok

#### 選項 A: 使用 npm (推薦)
```powershell
npm install -g ngrok
```

#### 選項 B: 直接下載
1. 前往 https://ngrok.com/download
2. 下載適合 Windows 的版本
3. 解壓到某個目錄（如 `C:\ngrok`）
4. 將該目錄添加到 PATH 環境變數

#### 驗證安裝
```powershell
ngrok --version
```

### 步驟 2: 創建 ngrok 帳號 (免費)
1. 前往 https://dashboard.ngrok.com
2. 使用 Google/GitHub/email 註冊
3. 複製您的 authtoken

### 步驟 3: 配置 ngrok authtoken
```powershell
ngrok authconfig --authtoken YOUR_AUTHTOKEN_HERE
```

### 步驟 4: 啟動 API + ngrok 隧道

#### 方式 1: 使用批次檔案 (最簡單)
雙擊 `start_api_with_tunnel.bat`

#### 方式 2: 手動啟動
```powershell
# 終端 1: 啟動 API
cd "c:\Users\User\OneDrive\文件\Visual Studio 18\yingyue-system"
.venv\Scripts\activate.bat
python scripts\start_api.py

# 終端 2: 啟動 ngrok 隧道
ngrok http 8000
```

## 訪問您的系統

### 本地訪問
```
http://127.0.0.1:8000
```

### 從開放網際網路訪問
ngrok 啟動時會顯示類似以下的 URL：
```
Forwarding   https://12345678-1234.ngrok.io -> http://127.0.0.1:8000
```

使用此 URL 從任何地方訪問您的 API：
```
https://12345678-1234.ngrok.io/health
https://12345678-1234.ngrok.io/news/latest?limit=10
https://12345678-1234.ngrok.io/philosophy/search?q=ethics
```

## API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/health` | GET | 健康檢查 |
| `/news/latest` | GET | 最新新聞 |
| `/philosophy/search` | GET | 哲學搜尋 |
| `/trends/summary` | GET | 趨勢摘要 |
| `/report` | GET | 日報告 |
| `/network-events` | GET | 網路事件 |
| `/agent-output` | GET | 代理輸出 |

### 示例調用

```bash
# 健康檢查
curl https://YOUR_NGROK_URL/health

# 獲取最新新聞
curl https://YOUR_NGROK_URL/news/latest?limit=5

# 搜尋哲學
curl https://YOUR_NGROK_URL/philosophy/search?q=ethics
```

## 注意事項

### 🔒 安全性

1. **ngrok authtoken**: 不要洩露您的 authtoken，這相當於您定時器的密碼。
2. **公開 URL**: ngrok 生成的 URL 每次重啟時會更改（免費版本）。
3. **認證**: 目前 API 没有身份驗證，建議：
   - 不要在公開互聯網上長期運行
   - 使用強密碼的防火牆
   - 為生產環境添加 API 密鑰驗證

### ⏱️ 限制

**ngrok 免費版限制**:
- 每月限制 20,000 連接
- 每個 TCP 連接 2 小時超時
- 共享 IP 地址

**升級到付費版**以獲得：
- 自訂域名
- 更多連接
- 更長的連接時限

### 💾 數據持久化

確保 `data/` 資料夾不會被意外刪除，因為數據庫和報告都存儲在這裡。

## 故障排除

### 問題 1: ngrok 找不到
**解決**: 確保已安裝 ngrok 並在 PATH 中
```powershell
where ngrok
```

### 問題 2: 端口 8000 已被占用
**解決**: 更改 API 端口
```powershell
# 編輯 scripts\start_api.py
# 將 uvicorn.run(..., port=8000) 改為 port=8001
```

### 問題 3: ngrok 認證失敗
**解決**: 重新配置 authtoken
```powershell
ngrok authconfig --authtoken YOUR_NEW_AUTHTOKEN
```

## 停止服務

1. 在 ngrok 終端按 `Ctrl+C`
2. 在 API 終端按 `Ctrl+C`

## 定期運行任務

要定期運行 MVP 管線（收集新聞、生成報告等），保持 API 運行並額外執行：

```powershell
# 終端 3: 定期運行管線
.venv\Scripts\activate.bat
python scripts\run_mvp.py
```

這會每小時或按計劃更新數據。

## 相關文件

- [LOCAL_DEPLOYMENT.md](LOCAL_DEPLOYMENT.md) - 本地部署選項
- [README.md](README.md) - 系統概述
- [AGENTS.md](AGENTS.md) - 代理工作流
