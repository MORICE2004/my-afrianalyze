# My AfriAnalyze Observability

This document outlines the tracking for cost, tracing, and deterministic validation execution across our agent runs.

## 1. Run & Execution Tracking
- **TelemetryManager (`agents/telemetry.py`)**: 
  - Every agent execution is wrapped with `start_agent_run` and `end_agent_run`.
  - Captures start/end times, execution duration, and success/fail statuses.
  - Automatically correlates agent runs to an overarching `run_id`.

## 2. Cost Tracking
- **Token Estimation (`agents/llm_provider.py`)**:
  - Intercepts every LLM prompt to compute estimated token limits and dollar costs based on `provider` and `model_name`.
  - Costs are synced into the Run Metrics via the `TelemetryManager`.

## 3. Scrubbing Sensitive Contexts
- Prompts, raw financial data, and credentials are **never** logged to external systems or persisted in plain text to general traces. Only aggregate token limits and structural metadata (like the list of technical indicators processed) are captured.
