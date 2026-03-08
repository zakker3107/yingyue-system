# 影月系統 MVP

影月系統（YingYue System）是一個 AI 觀察系統，聚焦三條主線：
- 世界趨勢與新聞整理
- 科技發展與訊號分析
- 社會情緒與思想連結

## 核心能力

目前提供五個核心能力（由三層 Agent 架構實現）：
- **Scout Agent**：世界新聞與科技資訊收集（RSS + fallback）
- **Analyst Agent**：科技趨勢分析（主題占比 + 技術訊號） + 社會情緒觀察（新聞語意訊號）
- **Synthesizer Agent**：每日/週觀察生成 + 個人思想筆記（哲學框架反思） + 知識圖譜連結（趨勢/哲學/筆記）

## 快速開始

### 1) 第一次設置：系統/環境優化
```powershell
cd "C:\Users\User\OneDrive\文件\Visual Studio 18\yingyue-system"
python scripts\optimize_environment.py --dev
```
或直接雙擊：`optimize_system.bat`

### 2) 執行 MVP 管線（Scout → Analyst → Synthesizer）
```powershell
python scripts\run_mvp.py
```
或使用 VS Code 任務：`Ctrl+Shift+P` → `Run MVP`
或雙擊：`run_mvp.bat`

### 3) 啟動 API 服務

有三種方式啟動 API，具體取決於您的訪問需求：

**🔹 仅本地訪問 (開發用):**
```powershell
python scripts\start_api.py
# 訪問: http://127.0.0.1:8000
```
或雙擊：`start_api.bat`

**🔹 本地網路訪問 (家裡/辦公室):**
```powershell
# 自動綁定到 0.0.0.0，允許同 WiFi 設備訪問
python scripts\start_api.py
```
或雙擊：`start_api_network.bat`
- 本地: `http://127.0.0.1:8000`
- 網路: `http://YOUR_PC_IP:8000` (如 `http://192.168.1.100:8000`)

**🔹 網際網路訪問 (ngrok 隧道):**
```bash
# 需先安裝: npm install -g ngrok
./start_api_with_tunnel.bat
# 公開 URL: https://xxx.ngrok.io
```
或雙擊：`start_api_with_tunnel.bat`

詳見 [QUICK_START_NETWORK.md](QUICK_START_NETWORK.md)

### 4) 部署選項

#### 🌐 雲端部署 (Railway - 推薦給公開項目)
```bash
# 推送到 GitHub，Railway 自動部署
git add .
git commit -m "Ready for deployment"
git push
```
詳見 [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)

#### 🏠 本地部署 (推薦給個人使用)
**完全本地運行**：
```bash
run_mvp.bat          # 運行完整管線
start_api.bat        # 啟動 API 服務
```
詳見 [LOCAL_DEPLOYMENT.md](LOCAL_DEPLOYMENT.md)

#### 🌍 本地 + 網路連通 (推薦給家辦公室共享)
**本地服務 + 網路訪問**：
- 同 WiFi 設備訪問：`start_api_network.bat`
- 從任何地方訪問 (ngrok)：`start_api_with_tunnel.bat`

詳見 [QUICK_START_NETWORK.md](QUICK_START_NETWORK.md) 和 [NETWORK_DEPLOYMENT.md](NETWORK_DEPLOYMENT.md)

其他選項請參考 [ALTERNATIVE_DEPLOYMENT.md](ALTERNATIVE_DEPLOYMENT.md)

---

## 使用方式對比

| 場景 | 方式 | 命令 |
|-----|------|------|
| 快速執行 | 批處理腳本 | `run_mvp.bat` |
| IDE 集成 | VS Code 任務 | `Ctrl+Shift+P` → `Run MVP` |
| 手動控制 | 直接調用 | `python scripts\run_mvp.py` |
| 自動執行 | 排程任務 | `install_daily_task.bat` |
| API 查詢 | HTTP 請求 | `curl http://127.0.0.1:8000/health` |

---

## 重要文檔

- **[AGENTS.md](AGENTS.md)**：詳細的 Agent 工作流程、API 端點、配置說明
- **[docs/automation.md](docs/automation.md)**：自動化排程與系統集成細節

---

## 環境設置

### 初次執行
1. 激活虛擬環境：`.venv\Scripts\activate`
2. 安裝依賴：`pip install -r requirements.txt`
3. 安裝開發依賴：`pip install -r requirements-dev.txt`

### 或一鍵優化
```powershell
python scripts\optimize_environment.py --dev
```

---

## 可用命令速查

### 主要腳本
```powershell
# 一鍵管線（完整流程）
python scripts\run_mvp.py

# 單獨生成報告
python scripts\generate_daily_report.py

# 啟動 API
python scripts\start_api.py

# 環境優化與檢查
python scripts\optimize_environment.py --dev
```

### 批處理腳本（推薦用於快速執行）
```powershell
run_mvp.bat              # 運行 MVP 管線
start_api.bat            # 啟動 API 服務器
run_tests.bat            # 運行測試
optimize_system.bat      # 環境優化 + 執行 MVP
install_daily_task.bat   # 安裝每日排程
remove_daily_task.bat    # 移除每日排程
```

### 數據輸出位置
```
data/processed/reports/
├── daily_report_YYYY-MM-DD.md              # 每日觀察
├── daily_report_YYYY-MM-DD_news.csv        # 新聞表格
├── weekly_observation_YYYY-Www.md          # 每週觀察
└── thought_links_YYYY-MM-DD.md             # 思想連結
```

---

## API 端點（Scout/Analyst/Synthesizer 輸出）

### 健康檢查
```bash
GET /health
# Response: {"status": "ok"}
```

### Scout Agent 輸出
```bash
GET /news/latest?limit=10
# Response: [{title, source, topic, published_at, summary, link, signals}, ...]
```

### Analyst Agent 輸出
```bash
GET /trends/summary
# Response: {general: 41.51, ai: 45.28, chip: 1.89, policy: 3.77, security: 1.89, economy: 5.66}
```

### Synthesizer Agent 輸出
```bash
GET /observations/daily/latest
# Response: {date, markdown_content, ...}

GET /observations/weekly/latest
# Response: {week, markdown_content, ...}

GET /thought-links/latest
# Response: {date, markdown_content, ...}
```

### Agent 執行結果
```bash
GET /agents/latest
# Response: {scout: {...}, analyst: {...}, synthesizer: {...}}
```

### 搜索功能
```bash
GET /philosophy/search?q=ethics
# Response: [{content, link_count, related_trends}, ...]
```

---

## 專案架構

```
yingyue-system/
├── agents/                    # Agent 實現（Scout, Analyst, Synthesizer）
├── apps/                      # 應用層（API, Worker）
├── core/                      # 領域驅動設計核心
│   ├── domain/               # 業務邏輯
│   ├── orchestrator/         # 流程編排
│   └── ports/                # 接口定義
├── config/                    # 配置文件
│   ├── sources.json          # RSS 源定義
│   └── philosophy_seed.json  # 哲學框架
├── data/                      # 數據目錄
│   ├── raw/                  # 原始數據
│   ├── curated/              # 數據庫 (yingyue.db)
│   └── processed/            # 輸出報告
├── docs/                      # 文檔
├── infrastructure/            # 基礎設施代碼
├── modules/                   # 功能模塊
├── pipelines/                 # 數據管道
│   ├── orchestrator.py       # 主流程編排
│   ├── reporting/            # 報告生成
│   └── scheduling/           # 自動排程
├── scripts/                   # 執行腳本
├── services/                  # 服務層
│   ├── api/                  # HTTP API
│   └── core/                 # 核心服務
├── tests/                     # 測試
├── vendor/                    # 依賴庫
├── .venv/                     # 虛擬環境
├── .vscode/                   # VS Code 配置
├── AGENTS.md                  # Agent 工作流程指南
├── README.md                  # 本文件
└── requirements.txt           # 依賴列表
```

---

## 常見問題

**Q：MVP 是什麼意思？**  
A：最小可行產品（Minimum Viable Product），包含 Scout、Analyst、Synthesizer 三層基本能力

**Q：如何修改自動排程時間？**  
A：編輯 `install_daily_task.bat`，改變 `-Time "08:30"` 參數

**Q：報告生成失敗怎麼辦？**  
A：檢查 `data/curated/yingyue.db` 是否存在，或執行 `python scripts\optimize_environment.py --full` 重建

**Q：如何添加新聞源？**  
A：編輯 `config/sources.json`，按格式添加新的 RSS URL

---

## 後續計劃

- [ ] Web UI 儀表板
- [ ] 高級知識圖譜視覺化
- [ ] 更精細的情緒分析
- [ ] 多語言支持
- [ ] 雲部署支持

---

## 許可證

MIT License



## 一鍵健康檢查（新增）
- 雙擊 `health_check.bat`
- 或手動執行：`.venv\Scripts\python.exe scripts\health_check.py --run-smoke`

檢查內容包含：
- Windows 版本與 Python/pip 版本
- 磁碟空間
- 每日報告/CSV/agent 輸出是否存在
- 最近報告輸出檔案
- smoke test 結果
