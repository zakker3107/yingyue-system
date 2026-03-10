# 系統穩定可用清單

更新日期：2026-03-10

本文件整理 2026-03-10 在本機環境完成的穩定性檢查結果，作為目前 `yingyue-system` 的維運參考。

## 一、整體結論

- 系統整體狀態：PASS
- 本機 API：正常
- 健康檢查：正常
- Smoke Test：PASS
- 每日報表輸出：正常
- Activity Rules 輸出：正常
- 背景啟動工具鏈：腳本完整

## 二、已完成驗證

### 1. 健康檢查與 Smoke Test

已執行：

```powershell
.\.venv\Scripts\python.exe scripts\health_check.py --run-smoke
```

確認結果：

- Windows、Python、pip 基本環境可讀取
- Firebase 狀態為 `READY_ADC`
- 今日報表輸出項目皆為 `OK`
- `Smoke Test: PASS`

### 2. API 狀態檢查

已執行：

```powershell
.\.venv\Scripts\python.exe scripts\api_status.py
```

確認結果：

- API 正在執行
- `/health` 回應 `200 OK`
- 目前狀態為 `Managed: NO, Running: YES`

說明：

- 目前 API 是正常運作中的進程
- 這個進程不是由目前的 managed background runtime metadata 啟動，所以不會顯示為 managed

### 3. 狀態報告產出

已執行：

```powershell
.\.venv\Scripts\python.exe scripts\status_report.py
```

確認結果：

- 成功產出狀態報告
- 報告路徑：`data\processed\reports\status_report.md`
- `overall=PASS`

### 4. 每日報表與衍生輸出

健康檢查已確認下列今日輸出存在且正常：

- `daily_report`
- `news_csv`
- `agent_json`
- `thought_links`

近期輸出亦已確認存在：

- `daily_report_2026-03-10.md`
- `agent_pipeline_2026-03-10.json`
- `strategic_report_2026-W11.md`

### 5. Activity Rules

已確認：

- `data\processed\reports\activity_rules_latest.json` 存在
- rule count = 2
- high priority rules = 1
- `svc-001`
- `content-001`

## 三、背景啟動工具鏈狀態

已檢查以下腳本鏈路：

- `start_api_background.bat`
- `start_api_network_background.bat`
- `stop_api.bat`
- `scripts\launch_api_background.py`
- `scripts\stop_api_background.py`
- `scripts\api_status.py`
- `scripts\api_background_runtime.py`

確認結果：

- bat 檔能正確呼叫對應 Python 腳本
- Python 腳本具備 PID/runtime 紀錄邏輯
- Python 腳本具備 port readiness 檢查
- Python 腳本具備停止 managed background process 的處理
- Python 腳本具備 stale runtime metadata 清理能力

目前觀察：

- `data\processed\runtime\api_background.json` 當下不存在
- 代表目前運行中的 API 並非透過這套 managed background metadata 啟動
- 這不影響 API 正常服務，但會影響 background manager 的追蹤顯示

## 四、每日排程狀態

已檢查：

- `install_daily_task.bat`
- `remove_daily_task.bat`
- `pipelines\scheduling\install_daily_task.ps1`

確認結果：

- 每日排程安裝腳本存在且邏輯完整
- 預設註冊的工作名稱為 `YingYue-Daily-Ops`
- 預設時間為每日 `08:30`

目前限制：

- 當前 session 無足夠權限直接讀取 Windows Scheduled Task 詳細狀態
- 因此本次僅能確認安裝腳本與任務名稱正確，無法在此 session 中直接確認系統排程是否已註冊成功

## 五、目前可穩定使用功能清單

- 本機 API 啟動與健康檢查
- MVP 主流程執行
- 每日報表生成
- 狀態報告生成
- Activity Rules 輸出
- 背景 API 啟動腳本
- 背景 API 停止腳本
- API 狀態查詢腳本
- 每日排程安裝與移除腳本

## 六、建議後續維運檢查

如需進一步收斂為正式維運流程，建議下次優先補查：

- 以系統管理員權限確認 `YingYue-Daily-Ops` 是否已成功註冊
- 確認目前 API 是否要統一改由 managed background mode 啟動
- 定期檢查 `data\processed\logs` 中的 API stderr log 是否持續乾淨
