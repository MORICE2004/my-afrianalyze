# Phase 14 Architecture Audit: Portfolio Intelligence Expansion

## 1. Existing Capabilities (Reuse)
- **Financial & Market Data**: The existing packages/market_data/ and connectors/dse/ are robust for pulling equity prices. We can reuse the SourceRegistry and rate-limiting patterns for BoT (Bank of Tanzania) and CMSA.
- **Valuation & Tech Analysis**: packages/valuation/ and packages/technical_analysis/ are equity-centric. They can be reused for individual stock components of a portfolio.
- **Agent Orchestration**: gents/orchestrator.py handles sequential agent execution perfectly. We will branch this into a PortfolioOrchestrator using the same underlying LLMClient and PIIScrubber.
- **Currency Engine**: packages/currency/engine.py is fully capable of standardizing multi-currency assets into a unified base (e.g., TZS).

## 2. Missing Components (To Build)
- **Data Models**: Need to expand packages/schemas/ to include Asset, Fund, TreasuryBill, TreasuryBond, and PortfolioRequest.
- **Universe Discovery**: Need a new packages/asset_universe/ module to dynamically discover investable assets from the DSE, CMSA (funds), and Bank of Tanzania (fixed income).
- **Fixed Income Math**: A new packages/fixed_income/ module is required to calculate yields, discount rates, duration, and convexity for Tanzanian T-Bills and T-Bonds.
- **Portfolio Construction**: Need packages/portfolio_optimizer/ to execute deterministic math (Mean-Variance, Risk Parity, Capital-Aware constraints) using SciPy.
- **Backtesting & Stress Engine**: Need packages/backtesting/ to simulate historical drawdown and run covariance matrices.
- **New Agents**: AssetUniverseAgent, FundResearchAgent, FixedIncomeAgent, PortfolioConstructionAgent, PortfolioRiskAgent, PortfolioAuditor.

## 3. Structural Changes
- **Abstracting the Target**: The system currently assumes the research target is a 	icker and exchange. We must refactor the API entry point to accept a polymorphic ResearchTarget (could be Company, Fund, Market, or PortfolioRequest).
- **Data-Quality Gates**: The optimizer must enforce strict NaN handling and liquidity penalties (e.g., illiquid Tanzanian bonds cannot receive a 50% weight in a high-liquidity portfolio).
