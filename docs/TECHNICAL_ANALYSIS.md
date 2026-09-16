# Technical Analysis Engine (Phase 8)

The Technical Analysis Engine is designed to calculate key technical indicators deterministically for African equities while taking into account market sparsity and data quality.

## Key Features

1. **Deterministic Calculations**:
   - Simple Moving Average (SMA)
   - Exponential Moving Average (EMA)
   - Relative Strength Index (RSI)
   - MACD (Moving Average Convergence Divergence)
   - Bollinger Bands

2. **Data Quality Checks**:
   African markets frequently feature days with zero trading volume or stale prices. 
   - `check_data_quality()`: Examines minimum periods, zero-volume days, and stale price patterns. Returns `INSUFFICIENT_DATA` rather than fabricated values.

3. **Liquidity Assessment**:
   - `assess_liquidity()`: Determines average daily volume and zero-volume frequency. Categorizes the stock into `LIQUID` or `ILLIQUID`.

4. **Regime Synthesis**:
   - `determine_regime()`: Automatically determines the technical regime (Trend, Momentum, Volatility) based on the calculated indicators and provides explicit, deterministic explanations for its conclusions (e.g., "SMA50 > SMA200 indicating an uptrend").

## Usage

```python
import pandas as pd
from packages.technical_analysis.engine import TechnicalAnalysisEngine

# Ensure dataframe has 'date', 'open', 'high', 'low', 'close', 'volume'
df = pd.read_csv("market_data.csv")
engine = TechnicalAnalysisEngine(df)

# Check quality
report = engine.check_data_quality()

if report.is_valid:
    regime = engine.determine_regime()
    print(regime.trend)
    print(regime.explanation['trend'])
```
