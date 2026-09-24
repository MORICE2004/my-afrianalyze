# AfriEdge Data Quality and Validation Policy

## 1. Principles of Financial Correctness
1. **Deterministic Calculation Integrity:** All mathematical routines (growth, margins, ROE, book value, DCF, duration, covariance, optimization) are computed via Python math and numerical libraries (`numpy`, `pandas`, `scipy`). No LLM is permitted to perform or modify financial arithmetic.
2. **Dual-Extraction Consensus:** Extracted tables from annual reports are processed through both `docling` and `camelot`. If numerical results diverge materially (>0.5% variance), an `EXTRACTION_CONFLICT` is raised and data is blocked from downstream valuation until manually reviewed.
3. **Immutability of Evidence:** Every metric extracted from public filings must retain:
   - Reporting Period (e.g. FY2024 Audited)
   - Unit & Currency (e.g. Millions TZS)
   - Source Document SHA-256 hash
   - Page and Table Coordinates
   - Extraction Confidence Score

## 2. Handling Missing and Stale Data
- If historical observations are fewer than required (e.g. <30 trading sessions for beta/volatility), the engine outputs `INSUFFICIENT_DATA`. It does not invent or extrapolate missing candles.
- If a security experiences zero-volume trading sessions, the engine marks the price point as `is_stale = True` rather than assuming market liquidity.
- Valuation models flag `ASSUMPTION_DEFICIT` if cost of equity inputs (risk-free rate, equity risk premium, country risk spread) cannot be grounded in central bank or regulatory benchmarks.
