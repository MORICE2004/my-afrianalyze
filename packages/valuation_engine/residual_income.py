from typing import List
from pydantic import BaseModel, Field

class RIInputs(BaseModel):
    current_book_value: float = Field(description="Current Book Value per share")
    forecast_roe: List[float] = Field(description="Year-by-year ROE forecasts")
    cost_of_equity: float = Field(description="Cost of Equity (CoE)")
    terminal_growth_rate: float = Field(description="Terminal growth rate")
    payout_ratio: float = Field(description="Dividend payout ratio")

class RIResult(BaseModel):
    current_bv: float = Field(description="Current Book Value")
    pv_residual_income: float = Field(description="Present value of forecasted Residual Income")
    pv_terminal_ri: float = Field(description="Present value of Terminal Residual Income")
    fair_value: float = Field(description="Fair Value per share")
    methodology_note: str = Field(description="Detailed methodology note")
    warnings: List[str] = Field(description="Warnings for the valuation")

def calculate_residual_income(inputs: RIInputs) -> RIResult:
    """
    Calculates Residual Income valuation.
    
    Financial Methodology:
    RI_t = (ROE_t - CoE) * BV_{t-1}
    BV_t = BV_{t-1} + ROE_t * BV_{t-1} - Dividends_t
         (assuming Dividends_t = ROE_t * BV_{t-1} * payout_ratio)
    Terminal RI = RI_n * (1+g) / (CoE - g)
    Fair Value = BV_0 + PV(sum of RIs) + PV(Terminal RI)
    """
    warnings = []
    
    if inputs.cost_of_equity <= inputs.terminal_growth_rate:
        raise ValueError("Cost of Equity must be strictly greater than terminal growth rate.")
        
    current_bv = inputs.current_book_value
    pv_residual_income = 0.0
    
    bv_prev = current_bv
    last_ri = 0.0
    
    for t, roe in enumerate(inputs.forecast_roe, start=1):
        ri = (roe - inputs.cost_of_equity) * bv_prev
        pv_residual_income += ri / ((1 + inputs.cost_of_equity) ** t)
        
        earnings = roe * bv_prev
        dividends = earnings * inputs.payout_ratio
        bv_prev = bv_prev + earnings - dividends
        last_ri = ri
        
    n = len(inputs.forecast_roe)
    
    terminal_ri_val = last_ri * (1 + inputs.terminal_growth_rate) / (inputs.cost_of_equity - inputs.terminal_growth_rate)
    pv_terminal_ri = terminal_ri_val / ((1 + inputs.cost_of_equity) ** n)
    
    fair_value = current_bv + pv_residual_income + pv_terminal_ri
    
    if fair_value > 0 and (pv_terminal_ri / fair_value) > 0.80:
        warnings.append("Terminal residual income dominates the valuation (>80% of Fair Value).")
        
    methodology_note = (
        "Residual Income Model. "
        f"Forecasted {n} years of residual income based on projected ROEs and Cost of Equity ({inputs.cost_of_equity:.2%}). "
        f"Terminal value calculated using {inputs.terminal_growth_rate:.2%} growth rate. "
        "Fair Value is Current Book Value plus PV of forecasted RI and PV of Terminal RI."
    )
    
    return RIResult(
        current_bv=current_bv,
        pv_residual_income=pv_residual_income,
        pv_terminal_ri=pv_terminal_ri,
        fair_value=fair_value,
        methodology_note=methodology_note,
        warnings=warnings
    )
