# Development & Build Order

## Build Order

### Phase 1: Foundations (MVP Preparation)
- Repository audit (Completed)
- Architecture & Data Model (Completed)
- Financial schemas & Evidence model
- DSE connector contract
- NMB ingestion setup

### Phase 2: Engine Construction
- Financial statement parser
- Validation engine
- Ratio engine
- Market-data engine
- Beta engine

### Phase 3: Financial Modeling
- Bank analytical model
- Forecast engine
- Valuation engine
- Scenario engine

### Phase 4: AI & Orchestration
- Agent orchestration (LangGraph)
- Research agents
- Auditor
- Research Director

### Phase 5: User Interface
- Web UI
- Company dashboard
- Source viewer
- Valuation interface
- Research report

### Phase 6: Quality Assurance
- Testing (Unit, Integration, Financial Reconciliation)
- Adversarial QA
- Performance & Security

### Phase 7: Expansion
- Additional exchange adapters (NSE Kenya, USE, RSE, NGX, GSE, BRVM, JSE)

## Definition of Done for MVP
A user must be able to:
1. Open My AfriAnalyze and search NMB.
2. The system automatically discovers relevant public documents.
3. Downloads and processes the annual report (using Docling).
4. Extracts financial statements and runs deterministic validation.
5. Calculates key financial ratios and market information.
6. Calculates beta using a documented methodology, explicitly noting liquidity.
7. Analyzes NMB using a bank-specific analytical model.
8. Creates Base/Bear/Bull forecast scenarios.
9. Values the company deterministically.
10. Identifies risks.
11. The Auditor attempts to break the analysis and flags unsourced claims.
12. The Research Director produces a structured report.
13. **Every material financial number has verifiable evidence.**
14. The system clearly reports missing or uncertain information.
15. The result is reproducible from the stored research run.

## Development Style
- Write maintainable, production-oriented code.
- Avoid giant files. Separate domain logic, data access, AI logic, scraping, financial calculations, API, and UI.
- Use type hints and Pydantic models.
- Financial formulas must be deterministic and independently testable without LLMs.
- Never invent data. Label unavailable data explicitly.
