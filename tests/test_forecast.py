import pytest
from pytest import approx
from packages.financial_engine.forecast import ForecastAssumption, ForecastLine, ForecastResult, GeneralForecaster

def test_forecast_revenue():
    """Test forecasting revenue with constant growth rate."""
    historical = {"FY1": 1000.0}
    growth = ForecastAssumption(metric_name="Revenue Growth", value=0.10, source="Analyst", rationale="Target")
    
    result = GeneralForecaster.forecast_revenue(historical, growth, 5)
    
    assert result.metric_name == "Revenue"
    assert "FY2" in result.forecast_values
    
    expected = [1100.0, 1210.0, 1331.0, 1464.1, 1610.51]
    
    keys = sorted(result.forecast_values.keys())
    for i, key in enumerate(keys):
        assert result.forecast_values[key] == approx(expected[i], rel=1e-5)
    
    assert result.assumptions_used[0] == growth

def test_forecast_with_margin():
    """Test forecasting a metric based on a margin of another forecast."""
    historical = {"FY1": 1000.0}
    growth = ForecastAssumption(metric_name="Revenue Growth", value=0.10, source="Analyst", rationale="Target")
    revenue_line = GeneralForecaster.forecast_revenue(historical, growth, 5)
    
    margin = ForecastAssumption(metric_name="Operating Margin", value=0.20, source="Analyst", rationale="Target")
    result = GeneralForecaster.forecast_with_margin(revenue_line, margin, "Operating Income")
    
    assert result.metric_name == "Operating Income"
    keys = sorted(result.forecast_values.keys())
    assert result.forecast_values[keys[0]] == approx(1100.0 * 0.20)
    assert result.forecast_values[keys[-1]] == approx(1610.51 * 0.20, rel=1e-5)
    assert result.assumptions_used[0] == margin
