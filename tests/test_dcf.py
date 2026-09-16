import pytest
from pytest import approx
from packages.valuation_engine.dcf import DCFInputs, calculate_dcf

def test_dcf_valuation():
    """Test standard DCF valuation."""
    fcfs = {
        "Y1": 100.0,
        "Y2": 110.0,
        "Y3": 121.0,
        "Y4": 133.0,
        "Y5": 146.0
    }
    inputs = DCFInputs(
        free_cash_flows=fcfs,
        wacc=0.10,
        terminal_growth_rate=0.03,
        forecast_years=5,
        terminal_value_method="gordon_growth"
    )
    
    result = calculate_dcf(inputs, net_debt=500.0, shares_outstanding=100)
    
    assert sum(result.pv_fcfs.values()) == approx(454.225, rel=1e-3)
    assert result.terminal_value == approx(2148.285, rel=1e-3)
    assert result.pv_terminal_value == approx(1333.91, rel=1e-3)
    assert result.enterprise_value == approx(1788.135, rel=1e-3)
    assert result.fair_value_per_share == approx(12.88, rel=1e-3)

def test_dcf_warnings_and_errors():
    """Test wacc <= g triggers error."""
    fcfs = {"Y1": 100.0}
    inputs = DCFInputs(
        free_cash_flows=fcfs,
        wacc=0.10,
        terminal_growth_rate=0.10,
        forecast_years=1,
        terminal_value_method="gordon_growth"
    )
    
    with pytest.raises(ValueError):
        calculate_dcf(inputs, 0, 10)
        
    inputs.wacc = 0.08
    with pytest.raises(ValueError):
        calculate_dcf(inputs, 0, 10)

def test_dcf_exit_multiple():
    """Test exit multiple method."""
    fcfs = {"Y1": 100.0}
    inputs = DCFInputs(
        free_cash_flows=fcfs,
        wacc=0.10,
        terminal_growth_rate=0.0,
        forecast_years=1,
        terminal_value_method="exit_multiple",
        exit_multiple=10.0,
        terminal_year_ebitda=150.0
    )
    
    result = calculate_dcf(inputs, net_debt=0.0, shares_outstanding=10)
    assert result.terminal_value == 1500.0
    assert result.pv_terminal_value == approx(1500.0 / 1.1)
