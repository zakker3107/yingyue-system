# Azure 持續部署設定指南

## 步驟 1: 登入 Azure
```bash
az login
```

## 步驟 2: 執行 Azure 資源設定
```bash
.\setup_azure_deployment.bat
```

這會：
- 創建資源組 `yingyue-rg`
- 創建 App Service 計劃
- 創建 Web App `yingyue-system`
- 顯示發佈設定檔

## 步驟 3: 設定 GitHub Secrets
1. 複製 `setup_azure_deployment.bat` 輸出的發佈設定檔
2. 前往 GitHub 倉庫 → Settings → Secrets and variables → Actions
3. 添加新 secret：
   - Name: `AZUREAPPSERVICE_PUBLISHPROFILE_YINGYUESYSTEM`
   - Value: 從步驟 2 複製的 XML 內容

## 步驟 4: 推送程式碼
```bash
git add .
git commit -m "Add Azure deployment configuration"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## 步驟 5: 監控部署
- 前往 GitHub Actions 標籤頁查看部署狀態
- 應用將部署到: `https://yingyue-system.azurewebsites.net`

## API 端點
部署後可用端點：
- `GET /health` - 健康檢查
- `GET /news/latest?limit=10` - 最新新聞
- `GET /philosophy/search?q=ethics` - 哲學搜尋
- `GET /trends/summary` - 趨勢摘要

## 疑難排解
- 如果部署失敗，檢查 GitHub Actions 日誌
- 確保所有檔案都包含在 git 中
- 檢查 Azure App Service 日誌：`az webapp log tail --name yingyue-system --resource-group yingyue-rg`