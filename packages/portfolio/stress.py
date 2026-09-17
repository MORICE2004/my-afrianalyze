import pandas as pd
from typing import Dict, Any, Optional

def stress_test_portfolio(weights: Dict[str, float], betas: Dict[str, float], duration: Optional[Dict[str, float]] = None, equity_shock: float = -0.20, rate_shock: float = 0.02) -> Dict[str, Any]:
    """
    Simulate portfolio performance under stress scenarios.
    
    Args:
        weights: Portfolio weights
        betas: Equity beta for each asset
        duration: Interest rate duration for each asset (if fixed income)
        equity_shock: Simulated market decline (e.g., -20%)
        rate_shock: Simulated interest rate increase (e.g., +2%)
        
    Returns:
        Dictionary of stress impacts
    """
    equity_impact = sum(weights.get(t, 0) * betas.get(t, 1.0) * equity_shock for t in weights)
    
    rate_impact = 0.0
    if duration:
        rate_impact = sum(weights.get(t, 0) * -duration.get(t, 0.0) * rate_shock for t in weights)
        
    total_impact = equity_impact + rate_impact
    
    return {
        'equity_shock_impact': equity_impact,
        'rate_shock_impact': rate_impact,
        'total_stress_impact': total_impact
    }
