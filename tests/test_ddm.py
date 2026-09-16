import pytest
from pytest import approx
from packages.valuation_engine.ddm import DDMInputs, calculate_ddm

def test_single_stage_ddm():
    """Test single stage DDM calculation."""
    inputs = DDMInputs(
        current_dps=10.0,
        stage1_growth_rates=[],
        terminal_growth_rate=0.05,
        cost_of_equity=0.12
    )
    result = calculate_ddm(inputs)
    assert result.fair_value == approx(150.0)
    assert result.stage1_pv == 0.0

def test_multi_stage_ddm():
    """Test multi stage DDM calculations with explicit growth."""
    inputs = DDMInputs(
        current_dps=10.0,
        stage1_growth_rates=[0.10, 0.10],
        stage2_growth_rate=0.08,
        stage2_years=2,
        terminal_growth_rate=0.05,
        cost_of_equity=0.12
    )
    
    result = calculate_ddm(inputs)
    assert result.fair_value > 0

def test_ddm_warnings():
    """Test warning when cost of equity <= g."""
    inputs = DDMInputs(
        current_dps=10.0,
        stage1_growth_rates=[],
        terminal_growth_rate=0.12,
        cost_of_equity=0.10
    )
    with pytest.raises(ValueError):
        calculate_ddm(inputs)
