# Data Model & Evidence

## Overview
Every extracted fact in My AfriAnalyze must support provenance. We do not allow any model-generated number into the financial database without verifiable source evidence.

## Evidence Schema
A fundamental structured model (Pydantic / PostgreSQL) that represents a single data point extracted from a source.

```sql
CREATE TABLE evidence (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    metric_id VARCHAR NOT NULL, -- e.g., 'net_profit'
    value NUMERIC,
    unit VARCHAR,
    currency VARCHAR,
    period_start DATE,
    period_end DATE,
    reporting_period VARCHAR, -- e.g., 'FY2025'
    statement_type VARCHAR, -- e.g., 'income_statement', 'balance_sheet'
    source_type VARCHAR, -- e.g., 'annual_report', 'exchange_announcement'
    source_name VARCHAR,
    source_url VARCHAR,
    document_id UUID,
    page_number INTEGER,
    table_reference VARCHAR,
    retrieved_at TIMESTAMP,
    extraction_method VARCHAR, -- e.g., 'docling_llm', 'manual'
    confidence NUMERIC,
    verification_status VARCHAR -- 'UNVERIFIED', 'VERIFIED', 'CONFLICTING'
);
```

## Financial Statement Schema
A standardized view of financial statements with a mapping layer for local/company-specific labels.

```python
class FinancialMetric(BaseModel):
    canonical_label: str
    original_label: str
    value: Decimal
    currency: str
    evidence_id: UUID

class IncomeStatement(BaseModel):
    revenue: FinancialMetric
    net_interest_income: Optional[FinancialMetric]
    operating_income: FinancialMetric
    ebit: FinancialMetric
    ebitda: FinancialMetric
    profit_before_tax: FinancialMetric
    profit_after_tax: FinancialMetric
    # ...
```

## Currency Engine Schema
Local currency must be a first-class citizen. Valuations and calculations store original and normalized values.

```python
class CurrencyValue(BaseModel):
    original_value: Decimal
    original_currency: str
    normalized_value: Decimal
    normalized_currency: str
    fx_rate: Decimal
    fx_source: str
    fx_date: date
```

## Market Data Schema
Tracks price history, explicitly modeling African market illiquidity.

```sql
CREATE TABLE market_data (
    ticker VARCHAR,
    exchange VARCHAR,
    price NUMERIC,
    date DATE,
    volume BIGINT,
    shares_outstanding BIGINT,
    market_capitalization NUMERIC,
    is_trading_day BOOLEAN,
    is_suspended BOOLEAN,
    stale_price BOOLEAN,
    corporate_actions JSONB
);
```
