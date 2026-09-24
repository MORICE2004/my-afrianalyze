# African Research Data Source Capability Matrix

This matrix documents the verification, access method, licensing status, and operational reliability of all primary data sources for Tanzania, Kenya, Uganda, and Global macroeconomic indicators.

| Source ID | Institution | Country | Asset Class | Status | Licensing | Extraction Pipeline | Known Limitations |
|---|---|---|---|---|---|---|---|
| `dse_equities` | Dar es Salaam Stock Exchange | Tanzania | Equities | PARTIALLY_WORKING | PUBLIC_REGULATORY | Firecrawl + DOM Parser | Layout variability across updates. |
| `nse_equities` | Nairobi Securities Exchange | Kenya | Equities | PARTIALLY_WORKING | LICENSE_REVIEW_REQUIRED | HTTP + BeautifulSoup | Cloudflare protection on quotes. |
| `use_equities` | Uganda Securities Exchange | Uganda | Equities | PARTIALLY_WORKING | PUBLIC_REGULATORY | HTTP + BeautifulSoup | Low trading volume / stale sessions. |
| `bot_fixed_income` | Bank of Tanzania | Tanzania | Fixed Income | WORKING | OFFICIAL_CENTRAL_BANK | Docling + Camelot dual consensus | Merged table headers in auction PDFs. |
| `cbk_fixed_income` | Central Bank of Kenya | Kenya | Fixed Income | WORKING | OFFICIAL_CENTRAL_BANK | BeautifulSoup + PDF Parser | Variable bulletin publication times. |
| `bou_fixed_income` | Bank of Uganda | Uganda | Fixed Income | WORKING | OFFICIAL_CENTRAL_BANK | BeautifulSoup + Docling | Download URL shifts during site updates. |
| `cmsa_funds` | CMSA Tanzania | Tanzania | Mutual Funds / CIS | WORKING | OFFICIAL_REGULATOR | HTTP + BeautifulSoup | Provides entity licensing, not daily NAVs. |
| `world_bank_macro` | World Bank API | Global/Africa | Macroeconomics | WORKING | OPEN_DATA_CC_BY_4 | REST JSON API | Annual reporting lag (1-2 years). |
| `imf_ifs` | International Monetary Fund | Global/Africa | Macro / FX | WORKING | OPEN_DATA_PUBLIC | REST JSON API | Periodic API rate limits. |

## Licensing & Commercial Display Policy
In accordance with Directive §14, financial data sourced directly from exchange websites for public consumption must respect commercial rights:
- Central Bank regulatory circulars (BoT, CBK, BoU) and statistical agency releases (NBS, KNBS, UBOS) are public government records.
- DSE, NSE, and USE end-of-day market feeds are subject to exchange redistribution policies. AfriEdge treats web-derived market feeds as delayed research inputs under `LICENSE_REVIEW_REQUIRED` until direct vendor API agreements (e.g. DSE direct data feed or NSE market data license) are executed.
