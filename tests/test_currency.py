import pytest
from datetime import date
from packages.currency.engine import CurrencyEngine

def test_currency_convert_identical():
    """Test identical currency conversion"""
    val = CurrencyEngine.convert(1000.0, 'TZS', 'TZS', None, date(2023, 1, 1), "Source")
    assert val.original_value == 1000.0
    assert val.normalized_value == 1000.0
    assert val.fx_rate == 1.0

def test_currency_convert_different():
    """Test currency conversion"""
    val = CurrencyEngine.convert(100.0, 'USD', 'TZS', 2500.0, date(2023, 1, 1), "CB")
    assert val.original_value == 100.0
    assert val.normalized_value == 250000.0
    assert val.fx_rate == 2500.0

def test_currency_unsupported():
    """Test unsupported currency"""
    with pytest.raises(ValueError):
        CurrencyEngine.convert(100.0, 'ABC', 'TZS', 1.0, date.today(), "Source")
        
def test_currency_none_value():
    """Test None value"""
    assert CurrencyEngine.convert(None, 'USD', 'TZS', 2500.0, date.today(), "CB") is None
