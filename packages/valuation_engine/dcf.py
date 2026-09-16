from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field

class DCFInputs(BaseModel):
    free_cash_flows: Dict[str, float] = Field(description="Period to Free Cash Flow mapping")
    wacc: float = Field(description="Weighted Average Cost of Capital")
    terminal_growth_rate: float = Field(description="Terminal growth rate")
    forecast_years: int = Field(description="Number of forecasted years")
    terminal_value_method: Literal['gordon_growth', 'exit_multiple'] = Field('gordon_growth', description="Method for terminal value")
    exit_multiple: Optional[float] = Field(None, description="EV/EBITDA multiple for exit method")
    terminal_year_ebitda: Optional[float] = Field(None, description="EBITDA in the terminal year for exit method")

class DCFResult(BaseModel):
    pv_fcfs: Dict[str, float] = Field(description="Present value of each FCF by period")
    terminal_value: float = Field(description="Terminal value")
    pv_terminal_value: float = Field(description="Present value of terminal value")
    enterprise_value: float = Field(description="Enterprise value")
    equity_value: float = Field(description="Equity value")
    fair_value_per_share: float = Field(description="Fair value per share")
    net_debt: float = Field(description="Net debt")
    shares_outstanding: int = Field(description="Shares outstanding")
    methodology_note: str = Field(description="Detailed methodology note")
    warnings: List[str] = Field(description="Warnings for the valuation")

def calculate_dcf(inputs: DCFInputs, net_debt: float, shares_outstanding: int) -> DCFResult:
    """
    Calculates Discounted Cash Flow Valuation.
    
    Financial Methodology:
    a) Discount each FCF: PV = FCF / (1 + WACC)^t
    b) Terminal value (Gordon Growth): TV = FCF_terminal * (1 + g) / (WACC - g)
       or Terminal value (Exit Multiple): TV = EBITDA_terminal * Exit Multiple
    c) PV of terminal value: PV_TV = TV / (1 + WACC)^n
    d) Enterprise Value = Sum(PV_FCFs) + PV_TV
    e) Equity Value = EV - Net Debt
    f) Fair Value Per Share = Equity Value / Shares Outstanding
    """
    warnings = []
    
    if inputs.wacc <= inputs.terminal_growth_rate and inputs.terminal_value_method == 'gordon_growth':
        raise ValueError("WACC must be strictly greater than terminal growth rate for Gordon Growth model.")
    
    pv_fcfs = {}
    sum_pv_fcfs = 0.0
    all_negative = True
    
    # Sort periods assuming they are year labels or comparable sequential strings
    sorted_periods = sorted(inputs.free_cash_flows.keys())
    for t, period in enumerate(sorted_periods, start=1):
        fcf = inputs.free_cash_flows[period]
        if fcf > 0:
            all_negative = False
            
        discount_factor = (1 + inputs.wacc) ** t
        pv = fcf / discount_factor
        pv_fcfs[period] = pv
        sum_pv_fcfs += pv
        
    if all_negative:
        warnings.append("All projected Free Cash Flows are negative.")
        
    terminal_value = 0.0
    if inputs.terminal_value_method == 'gordon_growth':
        last_fcf = inputs.free_cash_flows[sorted_periods[-1]] if sorted_periods else 0.0
        terminal_value = last_fcf * (1 + inputs.terminal_growth_rate) / (inputs.wacc - inputs.terminal_growth_rate)
    elif inputs.terminal_value_method == 'exit_multiple':
        if inputs.exit_multiple is None or inputs.terminal_year_ebitda is None:
            raise ValueError("Exit multiple and terminal year EBITDA must be provided for exit_multiple method.")
        terminal_value = inputs.terminal_year_ebitda * inputs.exit_multiple
        
    n = inputs.forecast_years
    pv_terminal_value = terminal_value / ((1 + inputs.wacc) ** n)
    
    enterprise_value = sum_pv_fcfs + pv_terminal_value
    equity_value = enterprise_value - net_debt
    
    fair_value_per_share = 0.0
    if shares_outstanding > 0:
        fair_value_per_share = equity_value / shares_outstanding
        
    if enterprise_value > 0 and (pv_terminal_value / enterprise_value) > 0.75:
        warnings.append("Heavy reliance on terminal value (>75% of Enterprise Value).")
        
    methodology_note = (
        "Discounted Cash Flow (DCF) Valuation. "
        f"Forecasted {n} years of cash flows discounted at WACC ({inputs.wacc:.2%}). "
        f"Terminal value calculated using {inputs.terminal_value_method.replace('_', ' ')}. "
        "Enterprise Value is the sum of PV of FCFs and PV of Terminal Value. "
        "Equity Value is Enterprise Value less Net Debt."
    )
    
    return DCFResult(
        pv_fcfs=pv_fcfs,
        terminal_value=terminal_value,
        pv_terminal_value=pv_terminal_value,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        fair_value_per_share=fair_value_per_share,
        net_debt=net_debt,
        shares_outstanding=shares_outstanding,
        methodology_note=methodology_note,
        warnings=warnings
    )
