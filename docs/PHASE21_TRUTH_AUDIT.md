# Phase 21 Truth Audit

## Mock & Hardcoded Data Search Results
The entire codebase was scanned for references to MOCK, FAKE, FIXTURE, STUB, and HARDCODED.
The following files were flagged:

- gents/llm_provider.py (Classification: MOCKED/BLOCKED - LLM abstraction layer)
- scripts/run_phase18_acceptance.py (Classification: TEST_FIXTURE)
- docs/MOCK_AUDIT.md (Classification: HISTORICAL_RECORD)
- docs/PHASE13_PRODUCTION_AUDIT.md (Classification: HISTORICAL_RECORD)
- docs/PHASE8_VERIFICATION.md (Classification: HISTORICAL_RECORD)
- docs/PHASE9_AUDIT.md (Classification: HISTORICAL_RECORD)

## External Project Audit

1. **QuantLib**:
   - Purpose: Quantitative finance framework for derivatives and pricing.
   - License: Modified BSD License (compatible).
   - Recommendation: Use for complex derivatives and bond pricing, but overkill for simple equities.

2. **TA-Lib**:
   - Purpose: Technical analysis library for indicators like MACD, RSI.
   - License: BSD License.
   - Recommendation: Essential for market data technical overlays. Highly recommended.

3. **Docling**:
   - Purpose: Parsing PDFs and semi-structured documents.
   - License: MIT License.
   - Recommendation: Use for corporate action documents and annual reports parsing.

4. **Camelot**:
   - Purpose: PDF table extraction.
   - License: MIT License.
   - Recommendation: Use specifically for tabular financial statements in annual reports.

5. **OpenBB**:
   - Purpose: Open-source investment research platform.
   - License: AGPL (potentially problematic for proprietary integrations).
   - Recommendation: Exercise caution due to AGPL license. Prefer direct API integrations where possible.

6. **PyPortfolioOpt**:
   - Purpose: Portfolio optimization based on Modern Portfolio Theory.
   - License: MIT License.
   - Recommendation: Good for constructing optimal portfolios from African equities, though illiquidity requires constraints tuning.
