# Phase 8 Mock Audit

This document identifies all mocked, stubbed, or fabricated components across the My AfriAnalyze architecture.

## 1. DSE Connector (connectors/dse/connector.py)
**Status: MOCKED**
- `get_company_profile("NMB")`: Sends a request to Firecrawl, but completely ignores the `scraped_markdown` response and returns a hardcoded `Company` Pydantic model for NMB Bank Plc.
- `get_price_history("NMB")`: Sends a request to Firecrawl, ignores the response, and returns a single fabricated `PricePoint` array with a hardcoded close price of `3520.00`.
- All other methods (`get_filings`, `get_announcements`, etc.) raise `NotImplementedError`.

## 2. LLM Provider (agents/llm_provider.py / orchestrator executions)
**Status: STUBBED / MOCKED**
- The agents (like `AuditorAgent`, `TechnicalAnalysisAgent`) are instantiated, but their `execute()` methods are typically overridden or stubbed to return immediate, hardcoded results without sending real API calls to Anthropic or OpenAI. This is done to keep test speeds below 1 second. 
- Real parsing of unstructured financial data into structured formats is currently mocked.

## 3. UI Frontend Integration (apps/web)
**Status: MOCKED DATA**
- The frontend Next.js app renders the correct structural components (FinancialMetrics, AgentFindings, TechnicalChart, Timeline), but is fed synthetic JSON mock data instead of polling the FastAPI backend dynamically.

## 4. Real Market Data and Document Ingestion
**Status: NON-EXISTENT**
- No real PDFs are being ingested or hashed via Docling.
- No real historical time series data (years of NMB trading) is being fed into the Technical Analysis engine (it uses synthetic arrays in `test_technical_analysis.py`).

## Acceptable vs. Unacceptable Mocks
**Acceptable:**
- Test fixtures in `tests/*` supplying synthetic data to verify mathematical purity (e.g., testing that SMA50 is correctly calculated from `[10, 20, 30]`).

**Unacceptable for Production (Must be replaced for real Phase 8/9 validation):**
- The DSE connector hardcoding NMB data.
- The lack of real PDF ingestion.
- The lack of live, multi-year market data streams.
