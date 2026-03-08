# YingYue Deployment and Operations (No VS Registration)

This guide is the shortest path to run and operate `yingyue-system` without Visual Studio deployment features.

## 1. Environment Setup

```powershell
cd "C:\Users\User\OneDrive\文件\Visual Studio 18\yingyue-system"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 2. Local Bring-up

Start API:

```powershell
.\.venv\Scripts\activate
python scripts\start_api.py
```

Run MVP pipeline in another terminal:

```powershell
.\.venv\Scripts\activate
python scripts\run_mvp.py
python scripts\generate_daily_report.py
```

## 3. Health and Monitoring

Generate one-shot status report:

```powershell
health_report.bat
```

Output:
- `data\processed\reports\status_report.md`

Append one 30-min monitoring tick:

```powershell
run_monitor_tick.bat
```

Output:
- `data\processed\reports\monitoring\d1_monitor_YYYY-MM-DD.md`
- `data\processed\reports\monitoring\d1_monitor_YYYY-MM-DD.jsonl`

## 4. Quick Recovery (Stop-the-bleed)

Run quick recovery workflow:

```powershell
recover_quick.bat
```

What it does:
- Checks `/health`
- Starts API if needed and port is free
- Re-runs MVP pipeline
- Regenerates daily report
- Runs smoke test
- Writes a recovery report under `data\processed\reports\recovery`

## 5. Validation Checklist

Required endpoints:
- `GET /health`
- `GET /news/latest?limit=10`
- `GET /philosophy/search?q=ethics`
- `GET /trends/summary`

Required outputs:
- `data\processed\reports\daily_report_YYYY-MM-DD.md`
- `data\processed\reports\daily_report_YYYY-MM-DD_news.csv`

## 6. Cloud Deployment Note

If cloud runtime is already configured (Railway/Azure/other), continue deploying from your existing cloud path.
Do not block release on VS registration.

Use this repo's operational scripts for runtime checks regardless of IDE status.
