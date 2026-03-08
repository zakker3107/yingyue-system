# Agents 工作流程指南

## 系統概述

YingYue System 採用三層 Agent 架構，每層负责不同的观察维度：

```
Scout Agent (data collection)
    ↓
Analyst Agent (signal analysis) 
    ↓
Synthesizer Agent (insight generation)
```

## Agent 详解

### 1) Scout Agent
**职责**：收集与初步分类
- 從 RSS 來源抓取最新新聞
- 從備用來源補充缺失信息
- 對新聞進行初步標籤與分類
- 提取關鍵詞與情感信號

**輸出物件**：
```python
{
    "title": "News Title",
    "source": "BBC World",
    "topic": "technology|world|business",
    "published_at": "2026-03-06T12:00:00Z",
    "summary": "Brief summary",
    "link": "https://...",
    "signals": ["ai", "policy", "security"]  # 檢測到的趨勢訊號
}
```

**執行**：由 `pipelines/orchestrator.py` 在主管道中自動調用

---

### 2) Analyst Agent
**职责**：信号分析与趋势识别
- 分析新聞中的科技信號
- 識別社會情緒變化
- 連結相關趨勢與主題
- 生成初步洞見

**分析維度**：
- `general`: 通用綜合趨勢
- `ai`: 人工智能與機器學習
- `chip`: 芯片與硬件技術
- `policy`: 政策與監管
- `security`: 網絡安全與隱私
- `economy`: 經濟與市場動向

**輸出物件**：
```python
{
    "trend_summary": {
        "general": 41.51,  # 百分比占比
        "ai": 45.28,
        "chip": 1.89,
        "policy": 3.77,
        "security": 1.89,
        "economy": 5.66
    },
    "signals": [
        {
            "signal": "ai-advancement",
            "confidence": 0.85,
            "mentions": 123,
            "recent_items": [...]
        }
    ]
}
```

**執行**：由 `services/core/trends/analyzer.py` 自動執行

---

### 3) Synthesizer Agent
**职责**：洞见生成与知识组织
- 综合多源信息
- 生成每日/週觀察報告
- 構建思想與趨勢的連結
- 提供決策支援

**產出物件**：
1. **每日觀察**：`daily_report_YYYY-MM-DD.md`
   - 新聞摘要（按主題分類）
   - 趨勢熱力圖
   - 社會情緒評估

2. **週觀察**：`weekly_observation_YYYY-Www.md`
   - 週度趨勢總結
   - 信號變化分析
   - 跨域連結洞見

3. **思想連結**：`thought_links_YYYY-MM-DD.md`
   - 新聞與個人思想筆記的連結
   - 哲學框架反思
   - 知識圖譜更新

**執行**：由 `pipelines/reporting/daily_report.py` 自動執行

---

## 執行方式

### 方式 1: 一鍵 MVP 管線
運行所有 Agent，從收集到報告生成：
```powershell
python scripts\run_mvp.py
```

或使用 VS Code 任務：`Ctrl+Shift+P` → `Run MVP`

### 方式 2: 分段執行
```powershell
# 只執行 Scout + Analyst
python scripts\run_mvp.py

# 只生成報告（需要已有數據）
python scripts\generate_daily_report.py
```

### 方式 3: API 查詢
啟動 API 服務器：
```powershell
python scripts\start_api.py
```

查詢已生成的 Agent 結果：
```bash
GET /agents/latest              # 最新 Agent 執行結果
GET /news/latest?limit=10       # Scout 輸出
GET /trends/summary             # Analyst 輸出
GET /observations/daily/latest  # Synthesizer 輸出（日）
GET /observations/weekly/latest # Synthesizer 輸出（週）
GET /thought-links/latest       # Synthesizer 輸出（思想連結）
```

### 方式 4: 自動排程
設置每日自動執行：
```powershell
# 安裝排程（每日 08:30）
.\install_daily_task.bat

# 移除排程
.\remove_daily_task.bat
```

或使用 VS Code 任務：
- `Install Daily Task`
- `Remove Daily Task`

---

## 環境變量與配置

### 主要配置文件
- `config/sources.json`: RSS 來源定義
- `config/philosophy_seed.json`: 哲學框架與思想種子
- `services/core/settings.py`: 系統全局設置

### 數據庫
- `data/curated/yingyue.db`: SQLite 主數據庫
  - `news_items`: Scout 輸出
  - `trend_snapshots`: Analyst 輸出
  - `daily_observations`: Synthesizer 輸出（日）
  - `weekly_observations`: Synthesizer 輸出（週）
  - `thought_links`: 思想連結
  - `philosophy`: 哲學筆記

---

## 常見工作流程

### 01. 首次設置
```powershell
# 1. 優化環境（安裝依賴、檢查系統）
python scripts\optimize_environment.py --dev

# 2. 運行 MVP 管線（初始化數據）
python scripts\run_mvp.py

# 3. 啟動 API （測試是否正常）
python scripts\start_api.py
```

### 02. 日常觀察流程
```powershell
# 每天早上自動執行（如已安裝排程）
# 或手動執行
.\run_mvp.bat

# 查看報告
notepad data\processed\reports\daily_report_2026-03-06.md
```

### 03. 開發與調試
```powershell
# 運行測試
python tests\test_pipeline_smoke.py

# 優化環境（包含 lint、type check）
python scripts\optimize_environment.py --dev

# 查看 API 日誌
python scripts\start_api.py  # 在終端中實時查看
```

### 04. 定期維護
```powershell
# 清理臨時文件，重建數據庫
python scripts\optimize_environment.py --full

# 備份重要數據
# (手動複製 data/curated/yingyue.db 到安全位置)
```

---

## 輸出文件結構

```
data/processed/reports/
├── daily_report_2026-03-06.md           # 每日觀察（Synthesizer）
├── daily_report_2026-03-06_news.csv     # 新聞表格（Scout）
├── weekly_observation_2026-W10.md       # 週度總結（Synthesizer）
├── thought_links_2026-03-06.md          # 思想連結（Synthesizer）
└── ...
```

---

## 故障排除

### Agent 執行失敗
1. 檢查日誌：`pipelines/orchestrator.py` 中的錯誤信息
2. 驗證數據：檢查 `data/raw/` 中是否有新聞數據
3. 重建環境：`python scripts\optimize_environment.py --full`

### API 無回應
1. 確認 `data/curated/yingyue.db` 存在
2. 檢查端口 8000 是否被佔用
3. 查看 API 啟動日誌中的錯誤

### 排程未執行
1. 檢查任務計劃程序：`taskschd.msc`
2. 查找 `YingYue-Daily-MVP` 任務
3. 檢查該任務的「上次執行結果」

---

## 貢獻指南

新增或修改 Agent 時：
1. 繼承 `agents/base.py` 中的 `BaseAgent`
2. 實現 `run(context)` 方法
3. 在 `pipelines/orchestrator.py` 中註冊
4. 編寫單元測試
5. 更新本文檔

---

## 相關文件

- [README.md](README.md) - 項目概述與快速開始
- [AGENTS.md](AGENTS.md) - 本文件，Agent 工作流程詳解
- [docs/automation.md](docs/automation.md) - 自動化排程詳細配置