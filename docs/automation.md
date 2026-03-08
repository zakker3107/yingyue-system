# 自動化執行

## 本機排程（Windows 工作排程器）

每日 08:00 執行：

```powershell
schtasks /Create /SC DAILY /TN "YingYueMVP" /TR "powershell -File C:\Users\User\OneDrive\文件\Visual Studio 18\yingyue-system\pipelines\scheduling\daily_job.ps1" /ST 08:00
```

## 手動執行

```powershell
python scripts\run_mvp.py
python scripts\generate_daily_report.py
python scripts\start_api.py
```

## 報告檔案
- `data/processed/reports/daily_report_YYYY-MM-DD.md`
- `data/processed/reports/daily_report_YYYY-MM-DD_news.csv`
