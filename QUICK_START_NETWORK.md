# 系統網路訪問指南

此指南說明如何以不同方式運行 YingYue 系統，以支果不同的訪問需求。

## 三種運行方式

### 1️⃣ 仅本地訪問 (Default)
**命令**: 雙擊 `start_api.bat`

```
API 訪問地址: http://127.0.0.1:8000
```

**適用場景**:
- 開發和測試
- 單機運行
- 無需外部訪問

---

### 2️⃣ 本地網路訪問 (推薦用於家網/辦公室網路)
**命令**: 雙擊 `start_api_network.bat`

```
本地訪問: http://127.0.0.1:8000
網路訪問: http://YOUR_PC_IP:8000  (如 http://192.168.1.100:8000)
```

**適用場景**:
- 同一個WiFi / LAN 上的其他設備訪問
- 家裡或辦公室使用
- 無需暴露到網際網路

**查詢您的 PC IP**:
```powershell
ipconfig
# 尋找 "IPv4 地址" 行，通常是 192.168.x.x
```

**在其他設備上訪問**:
```
於手機、平板、其他電腦上訪問:
http://192.168.1.YOUR_PC_NUMBER:8000
```

---

### 3️⃣ 網際網路訪問 (使用 ngrok 隧道)
**命令**: 雙擊 `start_api_with_tunnel.bat`

```
本地訪問: http://127.0.0.1:8000
網路訪問: http://192.168.1.100:8000
公開訪問: https://1234567890ab-1234.ngrok.io  (每次啟動都不同)
```

**適用場景**:
- 從世界任何地方訪問
- 分享 API 給朋友/團隊
- 測試遠端集成
- 無需購買域名或服務器

**前置要求**:
1. 安裝 ngrok (使用 npm):
   ```powershell
   npm install -g ngrok
   ```
   或下載: https://ngrok.com/download

2. 創建免費帳號: https://dashboard.ngrok.com

3. 配置 authtoken:
   ```powershell
   ngrok authconfig --authtoken YOUR_TOKEN
   ```

**ngrok 優勢**:
- ✅ 無需配置防火牆
- ✅ 無需購買域名
- ✅ 直接暴露本地 API
- ✅ HTTPS 加密傳輸
- ⚠️ 免費版每次啟動 URL 會變化

---

## MCP 開發者模式整合 (OpenAI)

### 📡 MCP 伺服器設定

**MCP 伺服器 URL 選項**：

#### 選項 1：本地開發（推薦）
```
基礎 URL: http://127.0.0.1:8000
```

**設定步驟**：
1. 先運行你的 API：`run_mvp.bat` 或 `start_api.bat`
2. 在 OpenAI 開發者模式中輸入：
   ```
   http://127.0.0.1:8000
   ```
3. 點擊「連接」或「Test Connection」

#### 選項 2：本地網路訪問
```
基礎 URL: http://YOUR_PC_IP:8000
例如: http://192.168.1.100:8000
```

**查詢你的 IP**：
```powershell
ipconfig
# 找到 IPv4 地址
```

#### 選項 3：網際網路訪問（ngrok）
```
基礎 URL: https://YOUR_NGROK_URL
例如: https://1234567890ab-1234.ngrok.io
```

**設定步驟**：
1. 安裝 ngrok：`npm install -g ngrok`
2. 運行隧道：`start_api_with_tunnel.bat`
3. 複製顯示的 ngrok URL
4. 在 OpenAI 開發者模式中輸入該 URL

---

### ✅ 連接測試

確認 MCP 伺服器連接正常：

```bash
# 測試基礎健康檢查
GET http://127.0.0.1:8000/health

# 預期回應
{"status": "ok", "timestamp": "..."}
```

### 🔌 可用 API 端點

OpenAI 開發者模式可調用以下端點：

```
GET  /health              # 系統健康檢查
GET  /news               # 最新新聞
GET  /philosophy/search  # 哲學查詢
GET  /trends            # 趨勢分析
GET  /network/events    # 網路事件
```

### 🛠️ 疑難排解

**連接失敗？**
- ✅ 確保 API 已啟動（看到 "Uvicorn 運行中" 訊息）
- ✅ 檢查防火牆是否允許 8000 埠
- ✅ 本地網路模式：確認 IP 無誤
- ✅ ngrok 模式：每次啟動 URL 會不同，需要更新

**超時？**
- 試試增加超時時間設定
- 確保網路連接穩定

**"Unsafe Connect" 錯誤？**

OpenAI 開發者模式需要 HTTPS，本地 HTTP 無法連接。解決方案：

#### 方案 1：使用 ngrok（推薦）✅
ngrok 自動提供 HTTPS 加密：
```powershell
# 1. 安裝 ngrok
npm install -g ngrok

# 2. 設定 authtoken（從 https://dashboard.ngrok.com 獲取）
ngrok authconfig --authtoken YOUR_TOKEN

# 3. 運行隧道
start_api_with_tunnel.bat

# 4. 複製顯示的 https://... URL
# 5. 在 OpenAI 填入該 URL
```

**優勢**：
- ✅ 自動 HTTPS
- ✅ 無需本地設定
- ✅ OpenAI 完全相容

#### 方案 2：本地 HTTPS 代理（進階）
使用 mitmproxy 或 Caddy 建立本地反向代理：
```powershell
# 安裝 Caddy
choco install caddy

# 建立 Caddyfile
"@echo off
127.0.0.1:8443 {
    reverse_proxy http://127.0.0.1:8000
    tls internal
}
" > Caddyfile

# 運行 Caddy
caddy run

# 在 OpenAI 填入：https://127.0.0.1:8443
```

#### 方案 3：告知 OpenAI 允許不安全連接
某些 OpenAI 客戶端設定允許 HTTP 本地開發：
- 檢查 OpenAI 設定是否有「Allow insecure connections」選項
- 部分 API 客戶端有環保式參數

**建議的最快方式**：
👉 **使用 ngrok（方案 1）** - 5 分鐘內完成，完全相容

---
GET /trends/summary

# 日常觀察
GET /observations/daily/latest
GET /observations/weekly/latest

# 思想連結
GET /thought-links/latest

# 代理輸出
GET /agents/latest

# 網路事件
GET /events/network?limit=20
GET /events/network/summary
```

---

## 快速測試

### 使用 curl 測試
```powershell
# 本地
curl http://127.0.0.1:8000/health

# 網路
curl http://192.168.1.100:8000/health

# ngrok
curl https://YOUR_NGROK_URL/health
```

### 使用瀏覽器測試
直接在瀏覽器中訪問（返回 JSON）：
```
http://127.0.0.1:8000/news/latest?limit=5
http://192.168.1.100:8000/trends/summary
https://YOUR_NGROK_URL/philosophy/search?q=ethics
```

---

## 配置環境變數

如果需要自訂設定，可以設定環境變數：

```powershell
# 設定 host 為網路訪問
$env:YINGYUE_API_HOST = "0.0.0.0"

# 設定自訂 port
$env:YINGYUE_API_PORT = "8080"

# 然後運行
python scripts\start_api.py
```

---

## 安全建議

### 🔒 本地網路使用
- 本地網路訪問相對安全
- 確保連接到可信的 WiFi
- API 目前無身份驗證

### ⚠️ 網際網路使用 (ngrok)
- **不要洩露您的 ngrok URL**
- **不要共享 ngrok authtoken**
- ngrok 免費版每月限 20,000 連接
- 考慮為 API 添加身份驗證層
- 不要 24/7 運行，除非升級付費版

### 🛡️ 生產環境建議
- 添加 API 密鑰驗證
- 使用 HTTPS 安全通信
- 限制 CORS 來源
- 監控日誌和錯誤
- 定期備份數據

---

## 故障排除

### 問題: 無法從其他設備訪問 API

**檢查清單**:
1. 確認兩個設備在同一個 WiFi
2. 檢查防火牆設置（允許 8000 port）
   ```powershell
   netsh advfirewall firewall show rule name=all | findstr 8000
   ```
3. 確認 API 正在運行
4. 使用正確的 IP 地址（運行 `ipconfig` 查看）

### 問題: ngrok 連接失敗

**檢查清單**:
1. 檢查 ngrok authtoken 配置
   ```powershell
   ngrok authconfig --authtoken YOUR_TOKEN
   ```
2. 檢查網際網路連接
3. 確認 ngrok 已安裝
   ```powershell
   ngrok --version
   ```

### 問題: 端口 8000 已被占用

**解決**:
```powershell
# 查找佔用 8000 的程序
netstat -ano | findstr :8000

# 終止程序 (PID 12345 為例)
taskkill /PID 12345 /F

# 或使用不同的 port
$env:YINGYUE_API_PORT = "8080"
python scripts\start_api.py
```

---

## 進階配置

### 持久化 ngrok URL (付費版)
```bash
ngrok http --domain=myapp.ngrok.io 8000
```

### 自訂域名 (付費版)
在 ngrok 儀表板添加自訂域名

### Docker 運行
```bash
docker run -p 8000:8000 yingyue-system
# 或使用 ngrok 暴露
docker run -p 8000:8000 --env YINGYUE_API_HOST=0.0.0.0 yingyue-system
```

---

## 相關文件

- [NETWORK_DEPLOYMENT.md](NETWORK_DEPLOYMENT.md) - 詳細的網路部署指南
- [LOCAL_DEPLOYMENT.md](LOCAL_DEPLOYMENT.md) - 本地部署選項
- [README.md](README.md) - 系統概述
