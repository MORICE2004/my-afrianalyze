import pytest
from packages.financial_engine.growth import (
    calculate_yoy_growth, calculate_cagr, calculate_moving_average
)

def test_calculate_yoy_growth():
    """Test YoY growth calculation"""
    values = [100, 110, 121, 96.8]
    growth = calculate_yoy_growth(values)
    assert growth[0] is None
    assert growth[1] == pytest.approx(0.1)
    assert growth[2] == pytest.approx(0.1)
    assert growth[3] == pytest.approx(-0.2)
    
    assert calculate_yoy_growth([]) == []
    assert calculate_yoy_growth([100, None, 110]) == [None, None, None]

def test_calculate_cagr():
    """Test CAGR calculation"""
    assert calculate_cagr(100, 121, 2) == pytest.approx(0.1)
    assert calculate_cagr(100, 100, 5) == 0.0
    assert calculate_cagr(None, 121, 2) is None
    assert calculate_cagr(100, 121, 0) is None
    assert calculate_cagr(-100, 121, 2) is None

def test_calculate_moving_average():
    """Test Moving Average"""
    values = [10, 20, 30, 40]
    ma = calculate_moving_average(values, 2)
    assert ma == [None, 15.0, 25.0, 35.0]
    
    ma3 = calculate_moving_average(values, 3)
    assert ma3 == [None, None, 20.0, 30.0]
    
    assert calculate_moving_average([], 2) == []
    assert calculate_moving_average([10], 2) == [None]
