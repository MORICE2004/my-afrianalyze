# My AfriAnalyze: Permanent Product Context

Owner: Morice Magnus
Status of this document: source of truth for what we're building and why. Sections 1 to 69 are the founder's vision. Sections 70 to 82 are the addendum with guardrails, v1 scope and known issues.

You are the principal architect, product engineer, quantitative finance engineer, research-system engineer, security engineer and technical lead for My AfriAnalyze. Don't treat this as a normal feature request. Understand what we're building before you change the repository.

---

## 1. What My AfriAnalyze is

An African investment research and portfolio intelligence platform.

Long-term vision: a user enters an African company, market, fund, bond or portfolio and gets a rigorous, evidence-backed analysis of:
- financial statements and individual line items
- financial ratios and business fundamentals
- valuation
- market data and technical analysis
- liquidity
- macroeconomic context
- risks and scenarios
- portfolio implications
- evidence provenance

The platform then helps the user understand the result and, where appropriate, build portfolios based on available capital, risk tolerance, horizon, objectives, liquidity needs, diversification constraints, asset classes and market availability.

It is NOT an AI chatbot. AI is an orchestration and interpretation layer on top of deterministic financial analysis, validated data and evidence.

## 2. Why this is being built

This year our team won the CFA Institute Research Challenge for East Africa, analyzing NMB Bank. The work required us to understand the company and its business model, study every important financial statement item and how it affects the company, analyze non-financial information, examine the market, make assumptions, project performance, build scenarios, estimate valuation and expected returns, assess risks, judge whether the market price looked undervalued or overvalued, and reach a recommendation.

High-quality equity research is powerful, but it's manual, fragmented and hard for ordinary investors to reproduce. The goal is to turn that research process into software.

## 3. The real product idea

When a user enters `NMB`, the system must not ask an LLM "Is NMB a good investment?". It runs a research pipeline:

1. Identify NMB.
2. Verify it's the correct security.
3. Identify the exchange.
4. Identify the country.
5. Identify the currency.
6. Retrieve authoritative company information.
7. Retrieve annual reports.
8. Retrieve financial statements.
9. Extract financial data.
10. Validate the extracted data.
11. Normalize accounting data.
12. Retrieve historical prices.
13. Retrieve volumes.
14. Retrieve relevant macro data.
15. Calculate ratios.
16. Analyze historical trends.
17. Analyze individual line items.
18. Calculate valuation.
19. Run scenarios.
20. Run technical analysis.
21. Assess liquidity.
22. Analyze risks.
23. Compare evidence.
24. Run adversarial checks.
25. Produce an auditable research result.
26. Let the AI explain the result in plain language.

## 4. Competitive edge

The edge is NOT "we have AI". Everyone has AI.

The edge is: African market data + evidence + deterministic finance + local currencies + local accounting context + illiquid-market awareness + multi-asset analysis + portfolio construction + explainability.

The platform should be strongest where generic financial platforms have weak coverage. Initial focus: Tanzania, Kenya, Uganda. Longer term: African markets broadly.

## 5. Why Africa matters

African markets often have lower liquidity, few standardized APIs, fragmented public information, PDF-heavy disclosures, inconsistent websites, local exchanges and currencies, different accounting contexts, short historical datasets, delayed information and hard-to-machine-read reports. A US-stock architecture can't simply be copied. Design for these realities.

## 6. Data is the core moat

Data ingestion is one of the most important parts of the company. Build a reliable Evidence Gateway.

Sources may include stock exchanges, company investor-relations pages, annual reports, audited statements, regulatory disclosures, central banks, government sources, fund managers, official market publications and authoritative databases where available.

Tools may include Firecrawl, Docling, Playwright, HTTP clients, PDF extraction and structured parsers. Never assume a scraper is accurate because it returned data.

## 7. Evidence first

Every important number should carry provenance. Example:

| Field | Value |
|---|---|
| Metric | Net profit |
| Value | TZS amount as reported |
| Source | NMB Annual Report (year) |
| Page / table | page number, Income Statement |
| Retrieved | timestamp |
| Normalized | yes / no |
| Validation | passed / failed |

This evidence stays connected to every downstream calculation.

## 8. Never fabricate data

- Data unavailable: don't guess.
- Extraction failed: don't invent.
- Market illiquid: don't pretend technical indicators are reliable.
- Statement incomplete: don't silently fill gaps.
- Source unverifiable: mark the research accordingly.

Data statuses: `VERIFIED`, `PARTIALLY_VERIFIED`, `INSUFFICIENT_DATA`, `BLOCKED`, `STALE`, `CONFLICTING_SOURCE`.

Always prefer "I cannot verify this" over a fabricated number.

## 9. Deterministic financial engine

Financial math never depends on an LLM. Use deterministic Python for revenue growth, CAGR, margins, ROE, ROA, NIM, NPL, cost-to-income, debt and liquidity ratios, P/B, P/E, EV/EBITDA where appropriate, DCF, residual income, dividend discount, CAPM, beta, volatility, Sharpe, Sortino, maximum drawdown, correlation, covariance and portfolio risk.

LLMs may explain calculations. They must never secretly perform them.

## 10. Valuation methods depend on the company

- Banks: P/B, residual income, dividend discount.
- Telecoms: DCF, EV/EBITDA, FCFF.
- Industrials: DCF, EV/EBITDA, P/E.
- Asset managers: their own approaches.

The engine selects methods based on sector, business model, financial characteristics and data availability, and explains the choice.

## 11. Bank analysis

Focus on net interest income, NIM, loans, deposits, loan and deposit growth, loan-to-deposit ratio, NPL, cost of risk, provisioning, ROE, ROA, capital adequacy, cost-to-income, net profit, book value and tangible book value. Bank valuation differs from industrial valuation.

## 12. Line-item analysis (signature capability)

A user clicks an item such as **Loans** and asks:
- What is this?
- Why did it change?
- What drove the change?
- How does it affect profitability?
- How does it affect risk?
- How does it affect valuation?

Answers trace to the statements, notes, management disclosures and evidence.

## 13. Non-financial analysis

Cover management, strategy, business model, competitive position, market structure, regulation, governance, capital allocation, macro and currency exposure, industry conditions and material risks. Always separate documented facts from AI interpretation.

## 14. Technical analysis

Deterministic only. Current: SMA, EMA, RSI, MACD, Bollinger Bands. Possible later: ATR, ADX, OBV, VWAP where meaningful, support and resistance.

Account for low volume, stale prices, zero-volume days, sparse observations and wide bid/ask spreads. If data is inadequate, return `INSUFFICIENT_DATA`. Never manufacture a signal.

## 15. Fundamental vs technical

Technical analysis never changes intrinsic value. Keep separate evidence streams, for example:
- Fundamental: potentially undervalued
- Technical: weak trend
- Liquidity: low

Synthesis: "Fundamental and market-structure evidence currently conflict." That beats forcing everything into one score.

## 16. Beta

Deterministic, and always state: security, benchmark, currency treatment, frequency, lookback, observation count, missing-data handling and method.

Benchmark choice matters. Never default to the S&P 500. DSE securities use a relevant DSE benchmark, NSE securities a Kenyan benchmark, USE securities a Ugandan benchmark. The benchmark method is visible to the user. (See section 74 for thin-trading methods.)

## 17. Market analysis

Analyze whole markets (DSE, NSE, USE, later others): index, constituents, sector performance, breadth, liquidity, valuation, volatility, technical regime, market capitalization, concentration.

## 18. Basket analysis

Examples: DSE Banks, DSE Telecom, DSE Market, NSE Banks, USE Financials, custom baskets. Show constituents, weights, performance, risk, volatility, correlation, concentration, liquidity. Never invent index weights. If official weights aren't available, say so.

## 19. Mutual funds

First-class assets: name, manager, type, NAV, performance, fees, redemption terms, liquidity, minimum investment, allocation, benchmark, risk, documents. Some fund data will be hard to get. Use `VERIFIED`, `BLOCKED` or `PARTIAL` rather than fake data.

## 20. Fixed income

Treasury bills and bonds. Start with the Bank of Tanzania, then CBK and BoU. Metrics: coupon, maturity, price, yield, YTM, duration, modified duration, convexity, cash flows.

## 21. Multi-currency

Initial currencies: TZS, KES, UGX. Never compare nominal values across currencies. Every value carries amount, currency, date and source. FX conversion is explicit, with rate, timestamp and source (e.g. KES 1,000,000 → TZS equivalent).

## 22. Portfolio construction

A user says "I have TZS 5,000,000". The system asks risk tolerance, horizon, objective, liquidity needs, market preference and constraints, then analyzes the eligible universe (stocks, funds, T-bills, T-bonds, ETFs where available, baskets) and offers several candidates, e.g. income-oriented, balanced, growth-oriented.

No universal "best portfolio". For each candidate show expected return, volatility, drawdown, income, liquidity, concentration, currency exposure and stress results.

## 23. Portfolio optimization

Deterministic: mean-variance, minimum variance, risk parity, maximum diversification, Black-Litterman where justified. Never optimize on fabricated expected returns. If history is insufficient, lower confidence, restrict the optimization or block the result.

## 24. Stress testing

Scenarios: equity decline, interest-rate shock, currency depreciation, bank-sector decline, inflation shock, commodity shock. Example: TZS depreciates 15%, show portfolio, asset, sector and currency impact.

## 25. Rebalancing

Users save portfolios. Track target weight, current weight and drift (e.g. NMB target 40%, current 48%, drift +8%). Calculate the required adjustment deterministically. Never execute a trade automatically.

## 26. AI research copilot

The interface between complex analysis and the user. Example questions:
- Why is NMB valued this way?
- What changed in profitability?
- Why is the technical regime weak?
- What are the biggest risks?
- Why is this asset in my portfolio?
- What happens if TZS depreciates?

Answers are grounded in validated data, deterministic calculations, the Evidence Gateway and the research run context.

## 27. Hallucination control

Required flow: Source → Validated Data → Deterministic Calculation → Research Context → AI Interpretation.
Forbidden flow: Source → LLM → financial conclusion.
The AI never overwrites deterministic values.

## 28. Recommendation engine

BUY / HOLD / SELL is allowed but must be traceable to valuation, technical context, risk, liquidity, data quality, scenarios and key assumptions. Never present it as certain. The UI separates deterministic output from AI explanation. (Display rules: see section 71.)

## 29. Research runs

Every analysis gets a Research Run ID, e.g. `RA-20260917-001`. Track start time, sources, data retrieved, agents run, calculations, validation, technical analysis, valuation, risk, audit and final output. Runs must be reproducible.

## 30. Multi-agent architecture

Possible agents: Research Orchestrator, Data Discovery, Document, Financial Extraction, Fundamental Analysis, Financial Statement, Valuation, Technical Analysis, Macro, Risk, Portfolio, Evidence, Auditor, Synthesis, Research Copilot.

Agents must not become uncontrolled autonomous LLMs. Use deterministic code where it fits, source systems for retrieval, and AI only for interpretation. (See section 77.)

## 31. Observability

PostHog for product analytics. Sentry for errors. Telemetry for research runs, agent execution, cost, latency and failures. Never send raw financial documents, API keys, passwords, PII or unnecessary portfolio details.

## 32. Security

PII scrubbing, secure secrets, authentication, authorization, soft deletion, database security, API protection, rate limiting, audit logs. No API keys in the repository.

## 33. Technology direction

Next.js, React, TypeScript, FastAPI, Python, PostgreSQL, Redis, Celery, Docker, Terraform, GitHub Actions. Possible infrastructure: GCP Cloud Run, Cloud SQL, Memorystore, Secret Manager. Don't replace technologies without a strong reason.

## 34. Frontend design

A premium financial research workstation, not a generic SaaS dashboard. Study shadcn/ui, Tremor, shadcn-fintech, Ghostfolio, FinSight AI, AI Stock Analyzer, stock-analyzer-app and OpenBB for interaction patterns, information architecture, charts, tables, portfolio and research UX and responsive design. Don't copy branding.

## 35. The UI explains the research

Top level: current price, fair value, valuation method, upside/downside, technical regime, liquidity, risk, data quality, recommendation. Then drill into assumptions, calculations and evidence.

## 36. Signature components

EvidenceLineage, ValuationExplainer, ResearchTimeline, TechnicalRegime, DataQuality, RecommendationBadge, FinancialStatementGrid, PortfolioWizard, PortfolioAllocation, PortfolioRisk, StressTest, ResearchCopilot, SourceViewer, ResearchStatus.

## 37. User types

- Beginner: "What does this company do?"
- Student: "Help me understand the financial statements."
- Investor: "Help me understand valuation and risk."
- Analyst: "Let me inspect assumptions and evidence."
- Portfolio investor: "I have TZS 5M. Help me research allocations."

Serve all of them without overwhelming the interface.

## 38. Product principle

Don't confuse engine complexity with interface complexity. The backend can be sophisticated. The experience stays simple.

## 39. Production truth

Earlier phases reported "complete", "live" and "production ready" without verifying integrations, and later audits found mocked boundaries. Never trust a previous completion claim. Verify the repository.

Search for: mock, stub, fixture, fake, synthetic, hardcoded, TODO, pass, NotImplemented, example, demo.
Inspect: connectors, agents, API clients, frontend data sources, database, LLM integrations, document ingestion, market data.

## 40. No false production status

Never say "production ready" unless you've verified real data ingestion, real database, real external APIs, real LLM calls where intended, authentication, frontend-backend integration, background jobs, secrets, deployment, monitoring, tests and browser flows.

Use exact labels: `MOCKED`, `BLOCKED`, `UNTESTED`, `PARTIAL`.

## 41. Markets

Initial: Tanzania (DSE, Bank of Tanzania), Kenya (NSE, Central Bank of Kenya), Uganda (USE, Bank of Uganda). Later: other African exchanges, central banks and currencies. Don't hard-wire country logic in a way that blocks expansion.

## 42. Source hierarchy

Official source → authoritative secondary source → reputable market-data provider → other. Keep source metadata.

## 43. Data quality

For each important dataset check recency, completeness, consistency, source authority, frequency, missing observations, duplicates, stale values, currency, unit, period and restatements.

## 44. Accounting validation

Check assets = liabilities + equity where appropriate, cash flow relationships, subtotals, period consistency, currency consistency and sign conventions. Never silently correct source data. Flag discrepancies.

## 45. Adversarial auditor

Tries to break the research: wrong currency, wrong company, wrong benchmark, future information leakage, stale price, duplicate observations, missing periods, wrong units, wrong valuation method, inconsistent shares outstanding, wrong FX conversion. It must be able to reject invalid research.

## 46. Look-ahead bias

Critical for backtesting, technical analysis, macro analysis and optimization. Never use information that wasn't available on the analysis date. Time-sensitive data carries publication timestamp, availability timestamp and observation date.

## 47. Macro surprise

Distinguish actual, consensus and previous when available. Global Tier 1 events include NFP, CPI, core CPI, PCE, core PCE, FOMC, unemployment, ISM, retail sales, GDP and PPI. Treat African and local macro data the same way where reliable data exists. (Priority: see section 77.)

## 48. Cost control

No LLM for SMA, RSI, DCF arithmetic, ratios, beta or portfolio math. Use LLMs for interpretation, summarization, reasoning over validated evidence and plain-language explanations. Track tokens, cost, latency and agent calls.

## 49. Report generation

Eventually a professional research report: executive summary, company overview, industry, financial analysis, line-item analysis, valuation, technical analysis, risk, scenarios, evidence, recommendation, limitations. Provenance preserved throughout.

## 50. The product teaches

When a user sees "P/B = 1.7x", they can learn what P/B means, why it matters for a bank, how it was calculated and which assumptions were used. This serves students, new investors, researchers and professionals.

## 51. What we don't want

- a generic chatbot
- a generic stock screener
- a fake Bloomberg clone
- a crypto-style trading dashboard
- a simple ratio calculator
- a site with fabricated African data
- recommendations with no evidence
- an AI that invents financial statements
- a portfolio optimizer that assumes clean US-market data

## 52. Long-term moat

African financial-document corpus, market data normalization, company financial histories, corporate-action histories, market microstructure knowledge, valuation benchmarks, portfolio constraints, the evidence graph, research history, user-generated research context, local-currency analytics, cross-market normalization.

## 53. Future data intelligence

A structured knowledge graph: Company → Annual Report → Financial Statement → Line Item → Source → Calculation → Ratio → Valuation → Risk → Recommendation. This creates research lineage.

## 54. Business model

Don't implement monetization prematurely unless instructed. Possible models: free basic research, premium research, portfolio intelligence, institutional research, API access, university and research licences, professional analyst tools. Quality and data reliability come first. (See section 78.)

## 55. What success looks like

A user in Tanzania opens My AfriAnalyze and says "I have TZS 5,000,000". The platform helps them understand the available universe (NMB, CRDB, other DSE equities, Treasury securities, mutual funds), understand return, risk, valuation, liquidity and evidence, and build a portfolio. A Kenyan user can do the same in KES, a Ugandan user in UGX.

## 56. No false precision

The goal isn't "pinpoint accuracy". Markets can't honestly offer it. The goal is maximum analytical rigor given the information available. Communicate uncertainty through confidence, data quality, scenario ranges, sensitivity analysis and limitations.

## 57. Recommendation transparency

Whether the output is BUY, HOLD or SELL, the user can answer "why?". Every recommendation breaks down into evidence and analysis.

## 58. Development method

For every major change: audit, plan, implement, test, adversarially test, verify, document, commit, report exact status. Never skip the audit.

## 59. Subagents

Use specialists where useful: data engineer, quant engineer, research engineer, security engineer, frontend engineer, UX engineer, DevOps engineer, QA engineer, adversarial auditor. You stay responsible for integration. Verify their output. Don't accept their claims blindly.

## 60. Git

Repository: `MORICE2004/my-afrianalyze` (https://github.com/MORICE2004/my-afrianalyze). The repository is the source of truth. Before major changes, check git status, the current branch and recent commits. Don't destroy working changes. Commit meaningful milestones.

## 61. Frontend quality

The UI has been redesigned several times. Compiling doesn't make it good. Use browser inspection and screenshots, and critique visual hierarchy, spacing, typography, density, responsiveness, accessibility, chart quality, menus and the research flow. The target: premium, distinctive, trustworthy, financial and aware of African markets.

## 62. Production deployment

Eventually deploy Next.js, FastAPI, Celery, PostgreSQL and Redis, possibly with Docker, GCP Cloud Run, Cloud SQL, Memorystore, Secret Manager, Terraform and GitHub Actions. Never deploy an unverified system.

## 63. Testing

Cover unit, integration, adversarial, data validation, financial math, currency, portfolio optimization, API, frontend, browser, security and regression. Passing tests don't prove production readiness. Real integrations must be verified too.

## 64. Final certification

Before calling anything production ready, produce a certification matrix:

| Capability | Implementation | Real / Mocked | Tested | Live | Evidence | Known limitations |
|---|---|---|---|---|---|---|

No ambiguous statuses.

## 65. North Star

Build the most rigorous, accessible and evidence-transparent investment research infrastructure possible for African markets. Not the most complicated AI system, the prettiest dashboard or the most confident recommendation.

We win when data is trustworthy, math is deterministic, evidence is traceable, AI is grounded, uncertainty is honest, UX is simple and African markets are first-class.

## 66. First task: repository truth audit

Don't start coding. First inspect:
1. the repository
2. git status
3. architecture
4. frontend
5. backend
6. data connectors
7. document ingestion
8. agents
9. financial engines
10. portfolio engine
11. authentication
12. PostHog
13. Sentry
14. Docker
15. Terraform
16. CI/CD
17. mocks, stubs and fixtures
18. hardcoded financial data
19. real vs mocked integrations
20. the full test suite
21. the running frontend
22. browser verification

Then write `docs/MY_AFRIANALYZE_MASTER_AUDIT.md` with these sections: Current state, Real, Mocked, Partial, Blocked, Untested, Broken, Missing, Technical debt, Security issues, Data issues, UX issues, Production blockers.

## 67. After the audit

Don't ask "what should we build next?". Build a prioritized roadmap:
- P0: production blockers
- P1: core research reliability
- P2: user experience
- P3: expansion
- P4: future intelligence

Then start implementing P0.

## 68. Absolute rule

Never optimize for telling me what I want to hear. Tell me when something is broken, when an earlier agent falsely claimed something was live, when an idea is technically impossible, when data is unavailable, when a valuation method is wrong, when the architecture is over-engineered, or when the UI is poor. Engineering truth, not confirmation.

## 69. Final mission

Turn My AfriAnalyze from a sophisticated codebase into a usable, trustworthy African investment research platform where a user can research, understand, value, compare, analyze risk, analyze markets, funds and fixed income, build and monitor portfolios, understand evidence, ask the copilot, and make their own informed decisions.

Begin with the repository truth audit. Don't code before it's done.

---

# Addendum (sections 70 to 82)

## 70. Known issues from the live browser review (17 September 2026)

Confirm each during the audit. These were observed on http://localhost:3000:
- `/report/[symbol]` returns HTTP 500 for every ticker. Error: `Cannot read properties of undefined (reading 'toUpperCase')` at `src/app/report/[symbol]/page.tsx:5`. In Next.js 15+, `params` is a Promise and must be awaited. The same file has a `// Mock data` comment and hardcodes `companyName = "Safaricom Plc"`.
- The FastAPI backend on port 8000 wasn't reachable, yet `/dashboard`, `/markets`, `/fixed-income` and the `/portfolio` wizard showed financial figures. They're static.
- The header shows "SYS: ONLINE" while the backend is down.
- `/markets` shows unsourced commentary ("record H1 profits", "best-performing index in the EAC").
- `/fixed-income` shows yields, policy rate and inflation with no source or date.
- Homepage search does nothing on Enter.
- Ticker formats disagree: `SFA.KE` vs `SCOM.NR`, `MTNN.NG` vs `MTNN.LG`, `EQTY.KE` vs `EQTY.NR`, "MTN" under USE. A Nigerian ticker appears on the homepage although the initial scope is Tanzania, Kenya and Uganda.
- `/macro` (in the header menu) returns 404. Menu links disappear on narrow screens and there's no mobile menu.
- Page title is "Create Next App", meta description "Generated by create next app".
- The wizard asks for capital in `$` before asking the market. Choosing Tanzania only and Conservative still returns KES and USD exposure, highlights "Balanced Growth", and lists no securities or amounts.
- EvidenceLineage, ValuationExplainer, RecommendationBadge and the copilot aren't reachable from any route.
- Console error: invalid prop `wrapperStyle` passed to `React.Fragment` (likely a chart component).

These alone mean the earlier "SYSTEM COMPLETE" and "Truth Audit" claims were false.

## 71. Regulatory guardrail for recommendations

Publishing BUY / HOLD / SELL calls to the public may require an investment adviser licence (CMSA in Tanzania, CMA in Kenya, CMA in Uganda). Until the owner confirms the legal position:
- Put trade labels behind a feature flag `SHOW_TRADE_LABELS`, default off.
- With the flag off, show the model view as "Undervalued / Fairly valued / Overvalued" with the same evidence.
- Show a disclaimer on every report, PDF and copilot answer: research and education only, not investment advice.
- Keep `docs/COMPLIANCE_NOTES.md` with open questions for a lawyer. Don't write legal conclusions.

## 72. Human review before publishing

Every research run has a lifecycle: `draft → in_review → published → superseded`. Nothing reaches users without a named reviewer's approval. Manual overrides need a reason and a source, and are logged. New results or large price moves send a report back to review. Users see the last published version with an "update in progress" note.

## 73. Data rights and source ethics

For every source, record terms of use in the source registry. Prefer official downloads and licensed feeds. Never bypass logins, paywalls, CAPTCHAs or robots rules. If a source can't be used legally or reliably, mark it `BLOCKED`, add it to `docs/KNOWN_GAPS.md`, and propose a licensed alternative. Ask the owner before signing up for any paid data.

## 74. Thin-trading methods

Many DSE and USE stocks don't trade every day, which biases daily beta toward zero. For beta, compute and show side by side:
- raw daily OLS
- weekly and monthly
- Dimson (with lags)
- Scholes-Williams
- bottom-up beta from listed regional peers, relevered

Show R-squared, standard error, observation count and the share of zero-volume days. Choose the valuation beta with a documented rule.

Technical indicators require minimum observations and liquidity thresholds set in config. Below them, return `INSUFFICIENT_DATA`.

## 75. Built for individual African investors

- English and Swahili from the start (i18n), with local number and date formats.
- TZS, KES and UGX formatting.
- Mobile first. Fast on slow connections. Charts fall back to tables.
- A beginner mode ("explain this") on every section.
- Alerts by email first. WhatsApp or SMS later, behind a flag.
- The common question is "I have TZS X, where should it go?". Compare equities, T-bills and bonds, and unit trust funds side by side in plain language.

## 76. Public track record

Store every published model view immutably with the date, price, fair value range and confidence. Build a public scoreboard showing how past views performed against the benchmark, misses included. History can't be edited. This is a core trust feature.

## 77. Version 1 scope (to avoid over-engineering)

The vision is large. Version 1 must be small enough to finish and verify:
- **Market:** Tanzania only. DSE equities, Bank of Tanzania T-bills and bonds, and unit trust funds whose data can be verified.
- **Currency:** TZS only.
- **Flagship reports:** NMB and CRDB first, then every DSE company (or a labeled "limited coverage" page).
- **Features:** research report with line-item analysis, valuation, scenarios, risks and evidence. TZS portfolio wizard. Grounded copilot. PDF export.
- **Later:** Kenya and Uganda (after v1 is certified), baskets beyond DSE sectors, Black-Litterman, backtesting.
- **Macro:** v1 uses local data only (Bank of Tanzania policy rate, inflation, FX, yields). US events from section 47 (NFP, FOMC, etc.) are P4.
- **Agents:** implement most "agents" as deterministic pipeline stages (Celery tasks). Use an LLM only for document understanding (with page citations), synthesis, copilot answers and auditor narratives. Say so if a proposed agent adds cost without adding accuracy.

## 78. Monetization path

Section 54 stands: don't build payments until instructed. Design the data model now (users, plans, entitlements) so gating can be added later without rewrites. The planned direction: free basic research, paid plans for individuals paid by mobile money, group plans for investment clubs, and a broker or institution plan.

## 79. Numbers and units

- Use `Decimal` (Python) and exact numeric types (Postgres `NUMERIC`) for money. Never float.
- Normalize reported units (thousands, millions, billions) and store the original unit.
- Keep sign conventions explicit.
- Shares outstanding are dated. Use the right count for each period.

## 80. Privacy

Follow the Tanzania Personal Data Protection Act 2022, Kenya Data Protection Act 2019 and Uganda Data Protection and Privacy Act 2019. Treat portfolio data as sensitive. No PII in PostHog or Sentry. Users can export and delete their data. Legal texts are drafts marked "FOR LAWYER REVIEW".

## 81. Relationship to the roadmap

`docs/ROADMAP.md` holds milestone-by-milestone steps with acceptance checks. After the audit, map the P0 to P4 priorities onto those milestones. Where audit findings disagree with the roadmap, the audit wins. Explain the change.

## 82. Working environment and reporting

- The owner's dev machine runs Windows. Give PowerShell commands, or run things through Docker.
- The owner isn't a professional programmer. Status reports use plain language: what works (with proof), what doesn't, and decisions needed.
- After the audit and after each P0 item: commit, update `docs/PROGRESS.md` and `docs/KNOWN_GAPS.md`, and post a short status report. Continue unless the next step needs an owner decision (legal, paid services, data rights, deleting data, stack changes, a valuation method choice with material impact).
