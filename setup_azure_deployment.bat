@echo off
REM Azure 持續部署設定腳本
REM 請先執行: az login

echo 設定 Azure 資源...

REM 設定變數
set RESOURCE_GROUP=yingyue-rg
set LOCATION=eastasia
set APP_NAME=yingyue-system
set PLAN_NAME=yingyue-plan

REM 創建資源組
echo 創建資源組 %RESOURCE_GROUP%...
az group create --name %RESOURCE_GROUP% --location %LOCATION%

REM 創建 App Service 計劃
echo 創建 App Service 計劃...
az appservice plan create --name %PLAN_NAME% --resource-group %RESOURCE_GROUP% --sku B1 --is-linux

REM 創建 Web App
echo 創建 Web App...
az webapp create --name %APP_NAME% --resource-group %RESOURCE_GROUP% --plan %PLAN_NAME% --runtime "PYTHON:3.14"

REM 設定應用設定
echo 設定應用設定...
az webapp config appsettings set --name %APP_NAME% --resource-group %RESOURCE_GROUP% --setting SCM_DO_BUILD_DURING_DEPLOYMENT=true

REM 顯示部署資訊
echo.
echo 部署完成！請複製以下資訊到 GitHub Secrets:
echo AZUREAPPSERVICE_PUBLISHPROFILE_%APP_NAME:u%=
az webapp deployment list-publishing-profiles --name %APP_NAME% --resource-group %RESOURCE_GROUP% --xml

echo.
echo 接下來：
echo 1. 在 GitHub 倉庫設定中添加 AZUREAPPSERVICE_PUBLISHPROFILE_YINGYUESYSTEM secret
echo 2. 推送程式碼到 main 分支觸發自動部署
echo 3. 應用將部署到: https://%APP_NAME%.azurewebsites.net