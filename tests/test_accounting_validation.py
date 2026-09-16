import pytest
from packages.accounting.validation import (
    validate_balance_sheet, validate_cash_flow, validate_equity_movement,
    validate_eps, validate_period_consistency, validate_currency_consistency
)

def test_validate_balance_sheet():
    """Test Balance Sheet validation"""
    # 1000 = 600 + 400
    res = validate_balance_sheet(1000, 600, 400)
    assert res.is_valid is True
    assert res.status == 'VALID'
    
    # Fail 1000 != 600 + 500
    res = validate_balance_sheet(1000, 600, 500)
    assert res.is_valid is False
    assert res.status == 'RECONCILIATION_FAILED'
    
    # Missing
    res = validate_balance_sheet(1000, None, 400)
    assert res.is_valid is False
    assert res.status == 'MISSING'

def test_validate_cash_flow():
    """Test Cash Flow validation"""
    res = validate_cash_flow(100, 50, -20, -10, 120)
    assert res.is_valid is True
    
    res = validate_cash_flow(100, 50, -20, -10, 130)
    assert res.is_valid is False

def test_validate_equity_movement():
    """Test Equity Movement"""
    # opening 100, ni 50, div 20, other 10, closing 140
    res = validate_equity_movement(100, 50, 20, 10, 140)
    assert res.is_valid is True

def test_validate_eps():
    """Test EPS validation"""
    res = validate_eps(500, 100, 5.0)
    assert res.is_valid is True
    
    res = validate_eps(500, 100, 5.1, tolerance=0.15)
    assert res.is_valid is True

def test_validate_period_consistency():
    """Test Period Consistency"""
    assert validate_period_consistency(["2020", "2021"]).is_valid is True
    assert validate_period_consistency(["2020", "2020"]).is_valid is False
    assert validate_period_consistency([]).is_valid is False

def test_validate_currency_consistency():
    """Test Currency Consistency"""
    assert validate_currency_consistency(["TZS", "TZS"]).is_valid is True
    assert validate_currency_consistency(["TZS", "USD"]).is_valid is False
