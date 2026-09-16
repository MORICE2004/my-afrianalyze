import pytest
from pytest import approx
from packages.valuation_engine.residual_income import RIInputs, calculate_residual_income

def test_residual_income():
    """Test standard residual income model calculation."""
    inputs = RIInputs(
        current_book_value=1000.0,
        forecast_roe=[0.15],
        cost_of_equity=0.12,
        terminal_growth_rate=0.03,
        payout_ratio=1.0
    )
    
    result = calculate_residual_income(inputs)
    assert result.pv_residual_income == approx(26.7857, rel=1e-3)
    assert result.pv_terminal_ri == approx(306.547, rel=1e-3)

def test_value_destroying_roe():
    """Test RI when ROE is less than Cost of Equity."""
    inputs = RIInputs(
        current_book_value=1000.0,
        forecast_roe=[0.10],
        cost_of_equity=0.12,
        terminal_growth_rate=0.03,
        payout_ratio=0.5
    )
    
    result = calculate_residual_income(inputs)
    assert result.pv_residual_income < 0
    assert result.fair_value < 1000.0
