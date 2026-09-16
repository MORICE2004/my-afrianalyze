import pytest
from packages.financial_engine.forecast import ForecastAssumption
from packages.financial_engine.scenario import ScenarioEngine

def test_scenario_consistency():
    """Test scenario validation warnings."""
    bear = {'loan_growth': ForecastAssumption(metric_name="LG", value=0.15, source="", rationale="")}
    base = {'loan_growth': ForecastAssumption(metric_name="LG", value=0.10, source="", rationale="")}
    bull = {'loan_growth': ForecastAssumption(metric_name="LG", value=0.05, source="", rationale="")}
    
    scenario_set = ScenarioEngine.create_scenario_set(bear, base, bull)
    warnings = ScenarioEngine.validate_scenario_consistency(scenario_set)
    
    assert len(warnings) > 0
    assert "bear (0.15) should be <= base (0.1)" in warnings[0]

def test_1d_sensitivity_table():
    """Test 1D sensitivity table generation."""
    base_assumptions = {
        'wacc': ForecastAssumption(metric_name="WACC", value=0.10, source="", rationale="")
    }
    
    def mock_valuation(assumptions):
        return 1.0 / assumptions['wacc'].value
        
    result = ScenarioEngine.generate_sensitivity_table(
        base_assumptions, 
        variable_name='wacc', 
        variable_range=[0.08, 0.10, 0.12], 
        valuation_func=mock_valuation
    )
    
    assert result['type'] == '1D'
    assert len(result['results']) == 3
    assert result['results'][1]['fair_value'] == 10.0

def test_2d_sensitivity_table():
    """Test 2D sensitivity table generation."""
    base_assumptions = {
        'wacc': ForecastAssumption(metric_name="WACC", value=0.10, source="", rationale=""),
        'terminal_growth': ForecastAssumption(metric_name="TG", value=0.03, source="", rationale="")
    }
    
    def mock_valuation(assumptions):
        w = assumptions['wacc'].value
        g = assumptions['terminal_growth'].value
        return 1.0 / (w - g)
        
    result = ScenarioEngine.generate_sensitivity_table(
        base_assumptions, 
        variable_name='wacc', 
        variable_range=[0.08, 0.10], 
        second_variable='terminal_growth',
        second_range=[0.02, 0.04],
        valuation_func=mock_valuation
    )
    
    assert result['type'] == '2D'
    assert len(result['matrix']) == 2
    assert len(result['matrix'][0]) == 2
