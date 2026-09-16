import pytest
from models.banks.valuation import (
    residual_income_valuation, dividend_discount_model,
    pb_relative_valuation, pe_relative_valuation
)

def test_residual_income_valuation():
    """Test residual income valuation (Gordon Growth)"""
    res = residual_income_valuation(100.0, 0.20, 0.15, 0.05)
    # BV + (ROE - CoE)*BV / (CoE - g)
    # 100 + (0.2 - 0.15)*100 / (0.15 - 0.05) = 100 + 5 / 0.10 = 150
    assert res['fair_value'] == pytest.approx(150.0)

def test_residual_income_valuation_edge():
    """Test edge case for residual income valuation"""
    res = residual_income_valuation(100.0, 0.20, 0.05, 0.10)
    assert res['fair_value'] == 0.0
    assert len(res['warnings']) > 0

def test_dividend_discount_model():
    """Test DDM model"""
    # dps = 10. g=[0.1, 0.1], terminal_g=0.05, coe=0.15
    res = dividend_discount_model(10.0, [0.1, 0.1], 0.05, 0.15)
    assert res['fair_value'] > 0
    
def test_ddm_edge():
    res = dividend_discount_model(10.0, [0.1, 0.1], 0.15, 0.15)
    assert res['fair_value'] == 0.0

def test_justified_pb():
    """Test justified PB"""
    assert pb_relative_valuation(0.20, 0.15, 0.05) == pytest.approx(1.5)
    assert pb_relative_valuation(0.20, 0.05, 0.10) == 0.0

def test_justified_pe():
    """Test justified PE"""
    assert pe_relative_valuation(0.20, 0.50, 0.15, 0.05) == pytest.approx(5.0)
