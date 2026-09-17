# UI Redesign: Final Review Planning

This document maps out the exact architectural changes required for the core routes to align with the new design system.

## 1. Home Route (`/`)
**Current:** Generic dashboard with widget cards.
**New Architecture:**
- **Split View:** Toggle between "Executive Briefing" and "Market Terminal".
- **Briefing Mode:** Editorial layout. A daily generated market commentary (text-heavy), highlighting top movers inline, and macro trends in a clean, non-boxed layout.
- **Terminal Mode:** High-density data grid showing index performance, live tickers, and a dense heatmap of sector performance.

## 2. Company Route (`/company/[ticker]`)
**Current:** Tabbed interface with isolated data points in cards.
**New Architecture:**
- **Header:** Integrated inline metrics for price, market cap, and primary ratio. No enclosing cards.
- **Left Column (Context):** Editorial summary of the company, recent news, and qualitative analysis.
- **Right Column (Data):** Dense, vertically scrollable financial tables (Income Statement, Balance Sheet, Cash Flow) using tabular figures.
- **Interaction:** Clicking a line item opens a Side Panel showing historical trends and formula breakdowns for that specific metric.

## 3. Portfolio Route (`/portfolio`)
**Current:** List of holdings with basic P&L cards.
**New Architecture:**
- **Top Section:** Seamless integration of portfolio aggregate metrics (Total Value, Alpha, Beta) using large typography, separated by vertical dividers, not cards.
- **Main Section:** A master-detail table. Rows represent holdings. Expanding a row reveals inline charts and contribution to overall portfolio risk/return, without navigating away.
