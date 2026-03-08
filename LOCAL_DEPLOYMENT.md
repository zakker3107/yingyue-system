# 本地部署選項

如果您不註冊 Railway，可以繼續使用本地部署，以下是完整的本地運行方案：

## 選項 1: 本地開發環境 (推薦)

### 快速啟動
```bash
# 雙擊啟動
run_mvp.bat          # 運行完整管線
start_api.bat        # 啟動 API 服務
run_tests.bat        # 運行測試
```

### VS Code 任務啟動
1. 開啟 VS Code
2. `Ctrl+Shift+P` → 運行任務
3. 選擇：
   - `Workflow: Setup Environment` - 環境設定
   - `Workflow: Daily MVP Pipeline` - 完整管線
   - `Workflow: API Development` - API 開發模式

## 選項 2: 本地伺服器部署

### 使用批次檔案
```bash
# 啟動 API 服務
.\start_api.bat

# 或手動啟動
python scripts\start_api.py
```

### API 端點
- 本地訪問：`http://127.0.0.1:8000`
- 健康檢查：`GET /health`
- 新聞 API：`GET /news/latest?limit=10`
- 哲學搜尋：`GET /philosophy/search?q=ethics`
- 趨勢摘要：`GET /trends/summary`

## 選項 3: Docker 本地運行

### 建置和運行
```bash
# 建置映像
docker build -t yingyue-system .

# 運行容器
docker run -p 8000:8000 -v $(pwd)/data:/app/data yingyue-system
```

## 優點和限制

### ✅ 本地部署優點
- **完全控制**：您掌控所有資料和設定
- **無成本**：不需要付費雲端服務
- **快速迭代**：本地開發和測試更快
- **資料安全**：所有資料留在本地
- **離線工作**：不需要網路連接

### ⚠️ 本地部署限制
- **無法遠端訪問**：只能在本地機器訪問
- **需要保持電腦運行**：服務會在電腦關閉時停止
- **網路限制**：無法從外部網路訪問
- **資源限制**：受限於本地硬體
- **無法自動擴展**：無法處理大量並發請求

## 混合方案

### 保留本地開發 + 定期雲端同步
1. **本地開發和測試**
2. **定期將資料匯出到雲端儲存**
3. **使用免費的靜態網站託管展示結果**

### 資料同步選項
- **GitHub Pages**：免費靜態網站
- **Google Drive/Dropbox**：檔案同步
- **免費雲端儲存**：AWS S3 免費層級等

## 總結

**如果不註冊 Railway，您仍然可以完整使用 YingYue 系統的所有功能**，只是：
- 服務只能在本地運行
- 需要保持電腦開機
- 無法從外部網路訪問

這對於個人使用、學習和開發來說是完全足夠的！