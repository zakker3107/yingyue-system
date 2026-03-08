# 上線首日值班檢查表（每 30 分鐘）

適用範圍：`yingyue-system` 上線後第 1 天（D1）  
輪巡頻率：每 30 分鐘一次

## 0. 值班資訊
- 日期：`____-__-__`
- 值班人：`________`
- 備援人：`________`
- 服務版本/Commit：`________`

## 1. 每 30 分鐘輪巡（固定檢查）
- [ ] `GET /health` 正常（HTTP 200，回應時間無明顯飆升）
- [ ] `GET /news/latest?limit=10` 正常（有資料、欄位完整）
- [ ] `GET /philosophy/search?q=ethics` 正常（可查詢、結果合理）
- [ ] `GET /trends/summary` 正常（可回應、內容非空）
- [ ] 應用錯誤率（5xx/timeout）無異常上升
- [ ] 延遲（P95）無異常上升
- [ ] CPU/RAM/磁碟空間正常（特別確認 `data\` 未暴增）
- [ ] 日誌可追蹤（錯誤含堆疊、可定位 request）

## 2. 每 2 小時檢查（資料與產出）
- [ ] pipeline 可正常執行：`python scripts\run_mvp.py`
- [ ] 產生報表：`python scripts\generate_daily_report.py`（可選）
- [ ] `data\processed\reports` 有當日檔案
- [ ] 報表日期正確、筆數合理、無大量空值
- [ ] CSV 可開啟且欄位完整

## 3. 開站前與首日必做（只做一次）
- [ ] `data\curated\yingyue.db` 建立備份快照
- [ ] 回滾步驟已演練（可在數分鐘內切回上一版）
- [ ] 停寫入或降級模式流程已確認（可快速止血）
- [ ] 通報群組與升級鏈路已確認（誰判斷、誰執行、誰通知）

## 4. 異常判定與處置（簡版 Runbook）
### A. API 健康檢查失敗（/health 非 200）
1. 立刻重試 2 次（間隔 1 分鐘）
2. 若持續失敗：啟動 API
   - `python scripts\start_api.py`
3. 仍失敗：通知備援並準備回滾

### B. 錯誤率或延遲異常上升
1. 先確認是否為上游資料波動或單一端點異常
2. 暫停非必要排程，保留核心讀取路徑
3. 10 分鐘內未恢復：啟動回滾流程

### C. 報表未產生或資料品質異常
1. 手動補跑：`python scripts\run_mvp.py`
2. 再執行：`python scripts\generate_daily_report.py`
3. 仍異常：標註影響範圍，通知相關人員

## 5. 時段輪巡記錄（D1）
| 時間 | /health | 核心端點 | 錯誤率/延遲 | 資源 | 報表/資料品質 | 處置紀錄 | 值班人 |
|---|---|---|---|---|---|---|---|
| 09:00 |  |  |  |  |  |  |  |
| 09:30 |  |  |  |  |  |  |  |
| 10:00 |  |  |  |  |  |  |  |
| 10:30 |  |  |  |  |  |  |  |
| 11:00 |  |  |  |  |  |  |  |
| 11:30 |  |  |  |  |  |  |  |
| 12:00 |  |  |  |  |  |  |  |
| 12:30 |  |  |  |  |  |  |  |
| 13:00 |  |  |  |  |  |  |  |
| 13:30 |  |  |  |  |  |  |  |
| 14:00 |  |  |  |  |  |  |  |
| 14:30 |  |  |  |  |  |  |  |
| 15:00 |  |  |  |  |  |  |  |
| 15:30 |  |  |  |  |  |  |  |
| 16:00 |  |  |  |  |  |  |  |
| 16:30 |  |  |  |  |  |  |  |
| 17:00 |  |  |  |  |  |  |  |
| 17:30 |  |  |  |  |  |  |  |
| 18:00 |  |  |  |  |  |  |  |

## 6. 快速命令（依 AGENTS.md）
```powershell
.venv\Scripts\activate
python scripts\run_mvp.py
python scripts\generate_daily_report.py
python scripts\start_api.py
python tests\test_pipeline_smoke.py
```
