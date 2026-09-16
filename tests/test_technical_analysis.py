import pytest
import pandas as pd
import numpy as np
from packages.technical_analysis.engine import TechnicalAnalysisEngine

@pytest.fixture
def sample_data():
    dates = pd.date_range('2023-01-01', periods=250)
    # create a trending data series
    close = np.linspace(100, 200, 250) + np.random.normal(0, 5, 250)
    df = pd.DataFrame({
        'date': dates,
        'open': close - 1,
        'high': close + 2,
        'low': close - 2,
        'close': close,
        'volume': np.random.randint(1000, 5000, 250)
    })
    return df

@pytest.fixture
def sparse_data():
    dates = pd.date_range('2023-01-01', periods=10)
    df = pd.DataFrame({
        'date': dates,
        'open': [10]*10,
        'high': [10]*10,
        'low': [10]*10,
        'close': [10]*10,
        'volume': [0]*10
    })
    return df

def test_data_quality_valid(sample_data):
    engine = TechnicalAnalysisEngine(sample_data)
    report = engine.check_data_quality()
    assert report.is_valid is True
    assert report.status == "OK"

def test_data_quality_sparse(sparse_data):
    engine = TechnicalAnalysisEngine(sparse_data)
    report = engine.check_data_quality(min_periods=20)
    assert report.is_valid is False
    assert report.status == "INSUFFICIENT_DATA"

def test_liquidity_liquid(sample_data):
    engine = TechnicalAnalysisEngine(sample_data)
    profile = engine.assess_liquidity()
    assert profile.is_illiquid is False
    assert profile.average_daily_volume > 1000

def test_liquidity_illiquid(sparse_data):
    engine = TechnicalAnalysisEngine(sparse_data)
    profile = engine.assess_liquidity(period=10)
    assert profile.is_illiquid is True
    assert profile.zero_volume_frequency == 1.0

def test_indicators(sample_data):
    engine = TechnicalAnalysisEngine(sample_data)
    
    sma = engine.calculate_sma(50)
    assert sma.status == "OK"
    assert sma.value > 0
    
    rsi = engine.calculate_rsi(14)
    assert rsi.status == "OK"
    assert 0 <= rsi.value <= 100
    
    macd = engine.calculate_macd()
    assert macd.status == "OK"
    assert macd.macd is not None
    
    bb = engine.calculate_bollinger_bands(20)
    assert bb.status == "OK"
    assert bb.upper > bb.lower

def test_regime(sample_data):
    engine = TechnicalAnalysisEngine(sample_data)
    regime = engine.determine_regime()
    
    # since data is trending up (100 to 200), SMA50 > SMA200 eventually
    assert regime.trend in ["Bullish", "Bearish"]
    assert "trend" in regime.explanation
