# Live Data Architecture for My AfriAnalyze

## DSE Market Data Implementation
OpenBB does not natively cover the Dar es Salaam Stock Exchange (DSE) comprehensively without a custom backend. African markets often suffer from illiquidity, sparse data, non-trading days, and stale prices.

To address this, we have designed a custom `BaseMarketDataProvider` abstraction.
The specific implementation for DSE (`DSEMarketProvider`) resides in `connectors/dse/market_provider.py`. It is responsible for fetching real historical prices from the DSE website (or a legitimate proxy API that aggregates DSE data).

This allows us to maintain the strict requirement of determinism, accurate decimal calculations, and explicit handling of African market characteristics while decoupling the domain logic from I/O constraints.
