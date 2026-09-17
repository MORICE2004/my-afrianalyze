import numpy as np
import pandas as pd
from typing import Dict, Union

def calculate_var(returns: pd.Series, confidence_level: float = 0.95, method: str = 'historical') -> float:
    """Calculate Value at Risk (VaR)."""
    if method == 'historical':
        return np.percentile(returns.dropna(), 100 * (1 - confidence_level))
    elif method == 'parametric':
        mu = returns.mean()
        sigma = returns.std()
        from scipy.stats import norm
        return norm.ppf(1 - confidence_level, mu, sigma)
    else:
        raise ValueError(f"Unknown VaR method: {method}")

def calculate_cvar(returns: pd.Series, confidence_level: float = 0.95, method: str = 'historical') -> float:
    """Calculate Conditional Value at Risk (CVaR)."""
    var = calculate_var(returns, confidence_level, method)
    if method == 'historical':
        return returns[returns <= var].mean()
    else:
        # Simplified parametric CVaR
        mu = returns.mean()
        sigma = returns.std()
        from scipy.stats import norm
        return mu - sigma * norm.pdf(norm.ppf(1 - confidence_level)) / (1 - confidence_level)

def calculate_concentration(weights: Dict[str, float]) -> Dict[str, float]:
    """Calculate Herfindahl-Hirschman Index (HHI) for portfolio concentration."""
    hhi = sum(w**2 for w in weights.values())
    return {'hhi': hhi, 'top_holding': max(weights.values())}
