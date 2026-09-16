import pytest
from datetime import date, timedelta
from packages.market_data.beta import BetaEngine, ReturnPoint, adjust_beta_blume

def test_adjust_beta_blume():
    """Test Blume adjustment"""
    assert adjust_beta_blume(1.5) == pytest.approx(1.333333333)

def test_beta_engine_perfect_correlation():
    """Test beta calculation with perfectly correlated returns"""
    engine = BetaEngine()
    start_date = date(2023, 1, 1)
    
    # 30 observations to avoid warnings
    stock_returns = []
    bench_returns = []
    
    for i in range(30):
        d = start_date + timedelta(days=i)
        stock_returns.append(ReturnPoint(date=d, stock_return=0.01 + (i*0.001)))
        bench_returns.append(ReturnPoint(date=d, benchmark_return=0.01 + (i*0.001)))
        
    result = engine.calculate_beta(stock_returns, bench_returns)
    assert result.raw_beta == pytest.approx(1.0)
    assert result.r_squared == pytest.approx(1.0)
    assert len(result.warnings) == 0

def test_beta_insufficient_data():
    """Test beta calculation with insufficient data"""
    engine = BetaEngine()
    stock_returns = [ReturnPoint(date=date(2023, 1, 1), stock_return=0.01)]
    bench_returns = [ReturnPoint(date=date(2023, 1, 1), benchmark_return=0.01)]
    
    result = engine.calculate_beta(stock_returns, bench_returns)
    assert result.raw_beta == 1.0
    assert "Fewer than 30 observations used" in result.warnings[0]
    assert "Insufficient data to calculate beta" in result.warnings[-1]

def test_beta_empty_data():
    """Test beta with empty data"""
    engine = BetaEngine()
    result = engine.calculate_beta([], [])
    assert result.raw_beta == 1.0
