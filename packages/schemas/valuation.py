from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from uuid import UUID
from decimal import Decimal
from .research import DataQualityScore

class ValuationAssumptions(BaseModel):
    risk_free_rate: float = Field(description="Risk-free rate")
    risk_free_rate_source: str = Field(description="Source of risk-free rate")
    risk_free_rate_methodology: str = Field(description="Methodology for risk-free rate")
    equity_risk_premium: float = Field(description="Equity risk premium")
    equity_risk_premium_source: str = Field(description="Source of ERP")
    equity_risk_premium_methodology: str = Field(description="Methodology for ERP")
    beta: float = Field(description="Levered beta")
    beta_source: str = Field(description="Source of beta")
    beta_methodology: str = Field(description="Methodology for beta")
    cost_of_equity: float = Field(description="Calculated cost of equity")
    cost_of_equity_source: str = Field(description="Source of COE")
    cost_of_equity_methodology: str = Field(description="Methodology for COE")
    wacc: float = Field(description="Weighted average cost of capital")
    wacc_source: str = Field(description="Source of WACC")
    wacc_methodology: str = Field(description="Methodology for WACC")
    terminal_growth_rate: float = Field(description="Terminal growth rate")
    terminal_growth_rate_source: str = Field(description="Source of terminal growth rate")
    terminal_growth_rate_methodology: str = Field(description="Methodology for terminal growth rate")
    forecast_years: int = Field(description="Number of explicitly forecasted years")
    forecast_years_source: str = Field(description="Source of forecast years")
    forecast_years_methodology: str = Field(description="Methodology for forecast years")
    tax_rate: float = Field(description="Effective tax rate assumed")
    tax_rate_source: str = Field(description="Source of tax rate")
    tax_rate_methodology: str = Field(description="Methodology for tax rate")

class ScenarioAssumptions(BaseModel):
    scenario_name: Literal['BEAR', 'BASE', 'BULL'] = Field(description="Scenario identifier")
    revenue_growth: Optional[float] = Field(None, description="Assumed revenue growth rate")
    margin: Optional[float] = Field(None, description="Assumed operating margin")
    tax_rate: Optional[float] = Field(None, description="Assumed tax rate")
    capex_ratio: Optional[float] = Field(None, description="Assumed capex-to-revenue ratio")
    wacc: Optional[float] = Field(None, description="Assumed WACC")
    terminal_growth: Optional[float] = Field(None, description="Assumed terminal growth rate")
    loan_growth: Optional[float] = Field(None, description="Assumed loan growth rate (for banks)")
    nim: Optional[float] = Field(None, description="Assumed net interest margin (for banks)")
    credit_losses: Optional[float] = Field(None, description="Assumed provision for credit losses (for banks)")
    description: str = Field(description="Qualitative description of the scenario rationale")

class ValuationResult(BaseModel):
    model_name: str = Field(description="Name of the valuation model used (e.g., 'DCF', 'DDM')")
    fair_value: Decimal = Field(description="Estimated fair value per share")
    currency: str = Field(description="Currency of the fair value")
    current_price: Decimal = Field(description="Current market price")
    upside_downside_pct: float = Field(description="Percentage upside or downside")
    assumptions_used: ValuationAssumptions = Field(description="Assumptions used in this valuation")
    methodology_description: str = Field(description="Description of the methodology applied")
    warnings: List[str] = Field(default_factory=list, description="Any warnings or caveats")

class ScenarioResult(BaseModel):
    bear: ValuationResult = Field(description="Bear case valuation result")
    base: ValuationResult = Field(description="Base case valuation result")
    bull: ValuationResult = Field(description="Bull case valuation result")

class FinalRecommendation(BaseModel):
    recommendation: Literal['BUY', 'HOLD', 'SELL'] = Field(description="Final rating")
    current_price: Decimal = Field(description="Current market price")
    estimated_fair_value: Decimal = Field(description="Estimated base case fair value")
    valuation_range_low: Decimal = Field(description="Low end of valuation range (bear)")
    valuation_range_high: Decimal = Field(description="High end of valuation range (bull)")
    expected_upside_downside: float = Field(description="Expected upside/downside percentage")
    major_assumptions: List[str] = Field(description="List of major assumptions")
    major_risks: List[str] = Field(description="List of major risks")
    data_quality: DataQualityScore = Field(description="Data quality score")
    model_uncertainty: str = Field(description="Discussion of model uncertainty")
    evidence_ids: List[UUID] = Field(description="List of key evidence IDs used")
