from typing import List, Optional
from pydantic import BaseModel, Field

class DDMInputs(BaseModel):
    current_dps: float = Field(description="Current Dividend Per Share (DPS)")
    stage1_growth_rates: List[float] = Field(description="Explicit year-by-year growth rates for high-growth phase")
    stage2_growth_rate: Optional[float] = Field(None, description="Transitional growth rate")
    stage2_years: int = Field(0, description="Number of years for stage 2")
    terminal_growth_rate: float = Field(description="Terminal growth rate")
    cost_of_equity: float = Field(description="Cost of Equity (CoE)")
    current_eps: Optional[float] = Field(None, description="Current Earnings Per Share (optional, for payout check)")

class DDMResult(BaseModel):
    stage1_pv: float = Field(description="Present value of Stage 1 dividends")
    stage2_pv: float = Field(description="Present value of Stage 2 dividends")
    terminal_pv: float = Field(description="Present value of terminal value")
    fair_value: float = Field(description="Total fair value per share")
    methodology_note: str = Field(description="Detailed methodology note")
    warnings: List[str] = Field(description="Warnings for the valuation")

def calculate_ddm(inputs: DDMInputs) -> DDMResult:
    """
    Calculates multi-stage Dividend Discount Model (DDM) valuation.
    
    Financial Methodology:
    Stage 1: Discount each year's dividend at CoE
    Stage 2: If stage2 exists, continue growing dividends at stage2_growth
    Terminal: Gordon Growth TV = D_terminal * (1+g) / (CoE - g)
    """
    warnings = []
    
    if inputs.cost_of_equity <= inputs.terminal_growth_rate:
        raise ValueError("Cost of Equity must be strictly greater than terminal growth rate.")
        
    if inputs.current_eps is not None and inputs.current_eps > 0:
        payout = inputs.current_dps / inputs.current_eps
        if payout > 1.0:
            warnings.append("Current payout ratio is > 100%, which may be unsustainably high.")
            
    stage1_pv = 0.0
    current_dps = inputs.current_dps
    t = 1
    
    for g in inputs.stage1_growth_rates:
        current_dps *= (1 + g)
        stage1_pv += current_dps / ((1 + inputs.cost_of_equity) ** t)
        t += 1
        
    stage2_pv = 0.0
    if inputs.stage2_growth_rate is not None and inputs.stage2_years > 0:
        for _ in range(inputs.stage2_years):
            current_dps *= (1 + inputs.stage2_growth_rate)
            stage2_pv += current_dps / ((1 + inputs.cost_of_equity) ** t)
            t += 1
            
    # Terminal Value calculation
    # Next year's dividend for terminal phase
    d_terminal = current_dps * (1 + inputs.terminal_growth_rate)
    terminal_value = d_terminal / (inputs.cost_of_equity - inputs.terminal_growth_rate)
    
    terminal_pv = terminal_value / ((1 + inputs.cost_of_equity) ** (t - 1))
    
    fair_value = stage1_pv + stage2_pv + terminal_pv
    
    if fair_value > 0 and (terminal_pv / fair_value) > 0.80:
        warnings.append("Terminal value dominates the valuation (>80% of Fair Value).")
        
    methodology_note = (
        "Multi-stage Dividend Discount Model. "
        f"Stage 1 spans {len(inputs.stage1_growth_rates)} years. "
        f"Stage 2 spans {inputs.stage2_years} years. "
        f"Terminal value calculated using Gordon Growth with {inputs.terminal_growth_rate:.2%} growth "
        f"and discounted at Cost of Equity ({inputs.cost_of_equity:.2%})."
    )
    
    return DDMResult(
        stage1_pv=stage1_pv,
        stage2_pv=stage2_pv,
        terminal_pv=terminal_pv,
        fair_value=fair_value,
        methodology_note=methodology_note,
        warnings=warnings
    )
