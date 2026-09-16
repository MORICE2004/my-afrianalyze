import pytest
from datetime import date
from packages.market_data.returns import (
    simple_return, log_return, annualize_return, annualize_volatility, calculate_sharpe_ratio
)
from packages.market_data.engine import MarketDataEngine, PricePoint

def test_returns():
    """Test simple and log returns"""
    assert simple_return(110, 100) == 0.1
    assert simple_return(110, 0) is None
    
    assert log_return(110, 100) == pytest.approx(0.095310179)
    assert log_return(110, -100) is None

def test_annualize():
    """Test annualization"""
    assert annualize_return(0.01, 12) == pytest.approx(0.12682503)
    assert annualize_volatility(0.05, 12) == pytest.approx(0.17320508)
    assert calculate_sharpe_ratio(0.12, 0.05, 0.15) == pytest.approx(0.46666666)
    assert calculate_sharpe_ratio(0.12, 0.05, 0.0) is None

def test_market_data_engine():
    """Test Market Data Engine for quality issues"""
    engine = MarketDataEngine()
    
    prices = [
        PricePoint(date=date(2023, 1, 1), price=100, volume=1000),
        PricePoint(date=date(2023, 1, 2), price=100, volume=0),
        PricePoint(date=date(2023, 1, 3), price=100, volume=500),
        PricePoint(date=date(2023, 1, 4), price=100, volume=500),
        PricePoint(date=date(2023, 1, 5), price=110, volume=500),
        PricePoint(date=date(2023, 1, 12), price=110, volume=500),
    ]
    
    returns = engine.calculate_returns(prices)
    assert len(returns) == 5
    assert returns[0].stock_return == 0.0  # 100 -> 100
    
    quality = engine.detect_data_quality_issues(prices)
    assert quality.zero_volume_days == 1
    assert quality.stale_price_periods == 1  # 4 consecutive 100s triggers stale detection
    assert quality.missing_days > 0  # Gap between Jan 5 and Jan 12
