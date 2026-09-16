# My AfriAnalyze

My AfriAnalyze is a production-oriented African equity research platform. It acts as a digital equity-research team, combining official public-company filings, stock-exchange data, regulatory disclosures, and market-price data with specialized AI research agents and deterministic financial calculations.

The platform explicitly prioritizes:
- **Calculation correctness**
- **Source traceability**
- **Reproducibility**
- **Data completeness**
- **Uncertainty measurement**
- **Explicit assumptions**

It is NOT a generic chatbot and does not invent financial figures.

## Initial Market Focus
- **Exchange:** Dar es Salaam Stock Exchange (DSE)
- **Flagship Company:** NMB Bank Plc

## Documentation
- [Architecture](docs/ARCHITECTURE.md)
- [Data Model & Evidence](docs/DATA_MODEL.md)
- [Development & Build Order](docs/DEVELOPMENT.md)
- [Open-Source Audit](docs/OPEN_SOURCE_AUDIT.md)

## Monorepo Setup
- `apps/web`: Next.js frontend
- `apps/api`: FastAPI backend
- `agents/`: LangGraph orchestration actors
- `packages/`: Deterministic calculations and core schemas
- `connectors/`: Exchange adapters (e.g., DSE)
- `models/`: Sector-specific analytical models (e.g., banks)
