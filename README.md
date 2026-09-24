# AfriEdge Terminal

AfriEdge is a production-grade African investment research and portfolio intelligence platform. It acts as a digital equity-research workstation, combining official public-company filings, stock-exchange data, regulatory disclosures, central bank publications, and market-price data with specialized AI research agents and deterministic financial calculations.

The platform explicitly prioritizes:
- **Calculation correctness** — deterministic math, never AI-generated numbers
- **Source traceability** — every metric linked to its original document
- **Reproducibility** — identical inputs always produce identical outputs
- **Data completeness** — graceful degradation when sources are unavailable
- **Uncertainty measurement** — explicit confidence levels
- **Evidence provenance** — dual-extraction consensus from PDF filings

It is NOT a generic chatbot and does not invent financial figures.

## Market Coverage
| Exchange | Country | Currency |
|----------|---------|----------|
| Dar es Salaam Stock Exchange (DSE) | Tanzania | TZS |
| Nairobi Securities Exchange (NSE) | Kenya | KES |
| Uganda Securities Exchange (USE) | Uganda | UGX |

**Asset Classes:** Equities, ETFs, Mutual Funds/CIS, Treasury Bills, Treasury Bonds, Market/Index Baskets

## Quick Start

```bash
# Clone
git clone https://github.com/MORICE2004/my-afrianalyze.git
cd my-afrianalyze

# Frontend
cd apps/web && npm install && npm run dev

# Backend (requires Python 3.11+)
pip install -r requirements.txt
cp .env.example .env  # Edit with your credentials
uvicorn apps.api.main:app --reload

# Full stack (requires Docker)
docker-compose up --build
```

## Documentation
- [Architecture](docs/ARCHITECTURE.md)
- [Data Model & Evidence](docs/DATA_MODEL.md)
- [Development & Build Order](docs/DEVELOPMENT.md)
- [Brand System](apps/web/docs/BRAND_SYSTEM.md)
- [Design System](apps/web/docs/DESIGN_SYSTEM.md)
- [African Market Capability Matrix](docs/AFRICAN_MARKET_CAPABILITY_MATRIX.md)

## Monorepo Structure
```
├── apps/web/          # Next.js frontend (AfriEdge Terminal UI)
├── apps/api/          # FastAPI backend & Celery workers
├── agents/            # LangGraph orchestration actors
├── packages/          # Deterministic calculations & core schemas
│   ├── portfolio/     # Optimizer, risk, stress, rebalance
│   ├── valuation_engine/  # DCF, DDM, multiples, residual income
│   ├── fixed_income/  # Treasury bills & bonds math
│   ├── evidence_gateway/  # Dual-extraction consensus & lineage
│   └── technical_analysis/  # SMA, EMA, RSI, MACD, Bollinger
├── connectors/        # Exchange adapters (DSE, NSE, USE, BoT, CBK, BoU)
├── models/            # Sector-specific models (banks)
├── infra/             # Terraform (GCP) & Docker deployment
├── tests/             # Pytest suite
└── docs/              # Architecture & audit documentation
```

## License
Proprietary — © 2026 AfriEdge
