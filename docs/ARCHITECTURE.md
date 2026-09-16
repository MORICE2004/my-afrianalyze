# Architecture

## Overview
My AfriAnalyze is a production-oriented African equity research platform designed to act as a digital equity-research team. It combines official public-company filings, stock-exchange data, regulatory disclosures, and market-price data with specialized AI research agents and deterministic financial calculations.

## Core Stack
- **Frontend:** Next.js + TypeScript (Vercel compatible)
- **Backend:** Python + FastAPI (Docker and DigitalOcean compatible)
- **AI Orchestration:** LangGraph (Stateful orchestration)
- **Structured Models:** Pydantic
- **Database:** PostgreSQL (Supabase where applicable)
- **Analytical Engine:** Python + pandas/numpy + DuckDB
- **Document Processing:** Docling
- **Web Research:** Firecrawl (isolated as an external service)
- **Object Storage:** S3-compatible storage
- **Authentication:** Supabase Auth

## Monorepo Structure
```text
my-afrianalyze/
├── apps/
│   ├── web/ (Next.js frontend)
│   └── api/ (FastAPI backend)
├── agents/ (LangGraph actors)
│   ├── company_researcher/
│   ├── financial_statement/
│   ├── accounting/
│   ├── market/
│   ├── macro/
│   ├── sector/
│   ├── valuation/
│   ├── risk/
│   ├── scenario/
│   ├── auditor/
│   └── research_director/
├── packages/ (Deterministic modules)
│   ├── financial_engine/
│   ├── valuation_engine/
│   ├── accounting/
│   ├── market_data/
│   ├── currency/
│   ├── document_parser/
│   └── schemas/
├── connectors/ (Exchange integrations)
│   ├── dse/
│   ├── nse_kenya/
│   ├── use/
│   ├── rse/
│   ├── ngx/
│   ├── gse/
│   ├── brvm/
│   └── jse/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── normalized/
│   └── evidence/
├── models/
│   ├── banks/
│   ├── insurance/
│   └── ...
├── tests/
└── docs/
```

## Source of Truth Hierarchy
1. Official stock exchange
2. Official company filing / investor relations
3. Regulatory authority
4. Central bank / official statistics authority
5. Audited financial statements
6. Official company presentations
7. Reputable market-data source
8. Reputable news source
9. General web sources

*Note: Search engines and LLMs are discovery mechanisms, not sources of truth. All metrics must be traced to a verifiable source.*

## Agent Pipeline
1. **Company Researcher:** Researches business model, ownership, etc.
2. **Financial Statement Agent:** Interprets financial statements and extracts metrics.
3. **Accounting Agent:** Verifies accounting consistency, reconciles statements.
4. **Market Agent:** Gathers and analyzes market data (price, volume, beta).
5. **Macro Agent:** Analyzes macro variables (inflation, rates).
6. **Sector Agent:** Analyzes sector KPIs.
7. **Valuation Agent:** Interprets output of deterministic valuation models.
8. **Scenario Agent:** Analyzes Bear/Base/Bull scenarios.
9. **Risk Agent:** Identifies multi-dimensional risks.
10. **Auditor Agent:** Adversarially challenges the thesis, checks for unsourced numbers and mathematical errors.
11. **Research Director:** Consolidates all verified outputs into a final report.

## State Management
Research runs are explicitly state-managed (DISCOVERING -> COLLECTING -> PROCESSING -> EXTRACTING -> VALIDATING -> ANALYZING -> VALUING -> AUDITING -> REPORTING -> COMPLETE). Failure states (e.g., INSUFFICIENT DATA) block further execution.
