# African Market Capability Matrix

## Matrix Assessment

| Exchange | Country | Company Discovery | Price Data (EOD) | Corporate Actions | Status |
|---|---|---|---|---|---|
| DSE | Tanzania | LIVE_VERIFIED | LIVE_VERIFIED | LIVE_PARTIAL | LIVE_PARTIAL |
| NSE | Kenya | LIVE_VERIFIED | LIVE_VERIFIED | LIVE_VERIFIED | LIVE_VERIFIED |
| USE | Uganda | LIVE_PARTIAL | LIVE_PARTIAL | BLOCKED | LIVE_PARTIAL |

### DSE (Dar es Salaam Stock Exchange)
- **Company Discovery**: Verified via exchange published listings.
- **Price Data**: Regular scraping/API access is robust, though liquidity limitations cause staleness.
- **Corporate Actions**: Partial - dividend announcements require manual intervention and doc parsing.

### NSE (Nairobi Securities Exchange)
- **Company Discovery**: High transparency, fully verified.
- **Price Data**: High volume market, pricing data is continuous and reliable.
- **Corporate Actions**: Consistent reporting format makes parsing fully automated.

### USE (Uganda Securities Exchange)
- **Company Discovery**: Partially verified due to lower reporting frequency.
- **Price Data**: High frequency of non-trading days causes challenges with time series continuity.
- **Corporate Actions**: Currently BLOCKED due to unstructured reporting formats.
