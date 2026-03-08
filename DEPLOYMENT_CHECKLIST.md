# 部署檢查清單

## ✅ 已完成
- [x] Dockerfile 配置
- [x] Railway 服務配置
- [x] Docker 忽略檔案
- [x] 部署文檔
- [x] 環境變數設定
- [x] 健康檢查配置
- [x] 資料持久化配置

## 🔍 最終檢查

### 1. 程式碼準備
- [ ] 所有程式碼已提交到 GitHub
- [ ] 主要分支為 `main`
- [ ] 所有測試通過

### 2. Railway 設定
- [ ] 註冊 Railway 帳號
- [ ] 連接 GitHub 倉庫
- [ ] 專案名稱設定為 `yingyue-system`

### 3. 環境變數 (在 Railway 儀表板設定)
```
PYTHONPATH=/app
DATABASE_URL=/app/data/curated/yingyue.db
```

### 4. 測試部署
- [ ] 應用程式成功部署
- [ ] 健康檢查通過
- [ ] API 端點可訪問：
  - GET /health
  - GET /news/latest?limit=10
  - GET /philosophy/search?q=ethics
  - GET /trends/summary

## 🚀 部署後任務

### 資料初始化
第一次部署後，資料庫會自動初始化。如果需要手動初始化：

```bash
# 在 Railway 儀表板中運行命令
python scripts/optimize_environment.py --init-db
```

### 監控
- 檢查 Railway 日誌
- 監控資源使用情況
- 設定提醒（可選）

### 備份
Railway 會自動處理資料持久化，但建議定期備份重要資料。

## ❓ 常見問題

**Q: 部署失敗怎麼辦？**
A: 檢查 Railway 日誌中的錯誤訊息，確認 Dockerfile 和依賴配置正確。

**Q: 應用程式無法啟動？**
A: 檢查環境變數設定，特別是 PORT 變數。

**Q: 資料遺失？**
A: Railway 的 volumes 會持久化資料，但重新部署可能會重置。

**Q: 如何更新應用程式？**
A: 推送到 GitHub main 分支，Railway 會自動重新部署。

## 📞 支援
如果遇到問題，請提供：
1. Railway 專案 ID
2. 錯誤訊息
3. 部署日誌片段