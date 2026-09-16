from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class ForecastAssumption(BaseModel):
    metric_name: str = Field(description="Name of the metric being assumed")
    value: float = Field(description="The numeric value of the assumption")
    source: str = Field(description="Where did this assumption come from")
    rationale: str = Field(description="Rationale for this assumption")
    is_user_overridden: bool = Field(default=False, description="True if manually overridden by user")

class ForecastLine(BaseModel):
    metric_name: str = Field(description="Name of the metric being forecasted")
    historical_values: Dict[str, float] = Field(description="Historical values mapped by period")
    forecast_values: Dict[str, float] = Field(description="Forecast values mapped by period")
    growth_rates: Dict[str, Optional[float]] = Field(description="Growth rates mapped by period")
    assumptions_used: List[ForecastAssumption] = Field(description="Assumptions used to calculate this line")

class ForecastResult(BaseModel):
    company_id: str = Field(description="Target company identifier")
    forecast_years: int = Field(description="Number of years forecasted")
    base_year: str = Field(description="The base year from which the forecast starts")
    lines: List[ForecastLine] = Field(description="The individual forecast lines")
    all_assumptions: List[ForecastAssumption] = Field(description="All assumptions used in the forecast")
    warnings: List[str] = Field(default_factory=list, description="Warnings or issues during forecasting")

class GeneralForecaster:
    """General forecasting engine for standard corporate financials."""
    
    @staticmethod
    def _generate_future_keys(base_year: str, years: int) -> List[str]:
        # Simple heuristic to increment years in strings like 'FY2022' -> 'FY2023'
        import re
        keys = []
        match = re.search(r'(\d+)', base_year)
        if match:
            year_num = int(match.group(1))
            prefix = base_year[:match.start()]
            suffix = base_year[match.end():]
            for i in range(1, years + 1):
                keys.append(f"{prefix}{year_num + i}{suffix}")
        else:
            for i in range(1, years + 1):
                keys.append(f"T+{i}")
        return keys

    @staticmethod
    def forecast_revenue(historical_revenues: Dict[str, float], growth_assumption: ForecastAssumption, years: int) -> ForecastLine:
        """Forecasts revenue based on a constant growth assumption."""
        sorted_keys = sorted(historical_revenues.keys())
        base_year = sorted_keys[-1] if sorted_keys else "FY0"
        base_value = historical_revenues[base_year] if sorted_keys else 0.0
        
        future_keys = GeneralForecaster._generate_future_keys(base_year, years)
        forecast_values = {}
        growth_rates = {}
        
        current_val = base_value
        for key in future_keys:
            current_val *= (1.0 + growth_assumption.value)
            forecast_values[key] = current_val
            growth_rates[key] = growth_assumption.value
            
        return ForecastLine(
            metric_name="Revenue",
            historical_values=historical_revenues,
            forecast_values=forecast_values,
            growth_rates=growth_rates,
            assumptions_used=[growth_assumption]
        )

    @staticmethod
    def forecast_with_margin(revenue_forecast: ForecastLine, margin_assumption: ForecastAssumption, metric_name: str = "Operating Income") -> ForecastLine:
        """Forecasts a metric as a fixed margin of revenue (e.g., EBIT, Net Income)."""
        forecast_values = {}
        for key, rev in revenue_forecast.forecast_values.items():
            forecast_values[key] = rev * margin_assumption.value
            
        return ForecastLine(
            metric_name=metric_name,
            historical_values={}, # Cannot compute historicals without historical margins/revenue
            forecast_values=forecast_values,
            growth_rates={},
            assumptions_used=[margin_assumption]
        )

    @staticmethod
    def forecast_from_ratio(base_forecast: ForecastLine, ratio_assumption: ForecastAssumption, metric_name: str) -> ForecastLine:
        """Forecasts a metric as a fixed ratio of a base forecast (e.g., Capex as % of Revenue)."""
        forecast_values = {}
        for key, base_val in base_forecast.forecast_values.items():
            forecast_values[key] = base_val * ratio_assumption.value
            
        return ForecastLine(
            metric_name=metric_name,
            historical_values={}, 
            forecast_values=forecast_values,
            growth_rates={},
            assumptions_used=[ratio_assumption]
        )
