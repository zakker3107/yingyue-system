# 影月系統程式架構設計

## 1) 系統架構

### 架構層次
- Ingestion Layer: 擷取世界新聞與外部資訊來源。
- Knowledge Layer: 管理思想筆記、哲學資料、知識關聯。
- Analysis Layer: 進行情緒觀察、趨勢分析、主題歸納。
- Agent Layer: 以可插拔 Agent 完成觀察、分析、綜合輸出。
- Orchestration Layer: 管線協調、排程、任務觸發。
- API Layer: 對外提供查詢與觀察結果輸出。
- Storage Layer: 關聯式資料庫 + 向量儲存（可擴充）。

### Agent 擴充策略
- `BaseAgent` 定義統一介面：`run(context) -> dict`。
- 目前預留三種 Agent：
  - `ScoutAgent`: 新聞偵測與蒐集。
  - `AnalystAgent`: 趨勢/情緒分析。
  - `SynthesizerAgent`: 思想連結與報告生成。
- 新增 Agent 時只需：
  - 實作 `BaseAgent`
  - 在 `core/orchestrator/pipeline.py` 接入工作流
  - 視需要增加 `core/ports/*` 與 `infrastructure/*` 適配

## 2) 資料夾結構

```text
yingyue-system/
  apps/
    api/
      routes.py
    worker/
      main.py

  agents/
    base.py
    scout_agent.py
    analyst_agent.py
    synthesizer_agent.py

  core/
    orchestrator/
      pipeline.py
      scheduler.py
    domain/
      models.py
      services.py
    ports/
      repositories.py
      llm.py

  modules/
    news/
      collectors/rss.py
      normalizers/base.py
    notes/
      parser.py
      linker.py
    graph/
      builder.py
      ranking.py
    analysis/
      sentiment.py
      trends.py
      topic_model.py
    reporting/
      daily.py
      weekly.py
      thought_links.py

  infrastructure/
    db/
      sqlite_repo.py
      postgres_repo.py
    vector/
      chroma_store.py
    llm/
      openai_client.py
    queue/
      task_bus.py

  config/
    prompts/
      README.md

  docs/
    architecture_design.md

  services/ ... (既有 MVP 相容層)
  pipelines/ ... (既有 MVP 相容層)
  scripts/ ... (既有 MVP 相容層)
```

## 3) Python / Node 版本建議

- 核心系統: Python 3.12
- API: FastAPI + Uvicorn（目前可先沿用現有 HTTP server）
- 若要前端儀表板: Node.js 22 LTS（僅前端/控制台）

## 落地原則
- 保留現有 MVP 路徑 (`services/`, `pipelines/`, `scripts/`) 以確保可運行。
- 新架構採並行增量遷移，先接 Agent 管線，再逐步替換舊模組。
