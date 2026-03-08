---
name: yingyue-daily-ops
description: Run and troubleshoot the yingyue-system daily workflow (MVP pipeline, report generation, health checks, API smoke checks, and quick recovery). Use when requests mention run_mvp, daily reports, API health, monitor ticks, or recovery in the yingyue-system workspace.
---

# Yingyue Daily Ops

## Overview
Use deterministic project scripts to execute daily operations for `yingyue-system` with minimal ad-hoc commands.

## Workflow Decision Tree
1. If the task is daily content processing, run `scripts\\run_mvp.py` first.
2. If the task asks for report output, run `scripts\\generate_daily_report.py` and verify files under `data\\processed\\reports`.
3. If the task asks for API readiness, run `scripts\\start_api.py` and validate `/health`.
4. If the task asks for stability checks, run `scripts\\health_check.py --run-smoke` and `scripts\\status_report.py`.
5. If health checks fail, run `scripts\\quick_recovery.py --run-smoke`.

## Required Execution Rules
- Work inside `yingyue-system`.
- Activate `.venv\\Scripts\\activate` before Python scripts.
- Prefer scripts in `scripts\\` over manual command sequences.
- After code edits, run at least `python tests\\test_pipeline_smoke.py`.

## Quick Commands
- Full daily run: `powershell -ExecutionPolicy Bypass -File skills\\yingyue-daily-ops\\scripts\\run_daily_ops.ps1`
- Health-only run: `powershell -ExecutionPolicy Bypass -File skills\\yingyue-daily-ops\\scripts\\run_daily_ops.ps1 -HealthOnly`

## References
- Command matrix: `references/command-matrix.md`

