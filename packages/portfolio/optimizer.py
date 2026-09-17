import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from decimal import Decimal

def optimize_portfolio(
    returns: pd.DataFrame,
    cov_matrix: pd.DataFrame,
    method: str = 'mean_variance',
    target_return: Optional[float] = None,
    risk_free_rate: float = 0.0,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    capital: Decimal = Decimal('10000.00'),
    min_investment: Decimal = Decimal('100.00')
) -> Dict[str, float]:
    """
    Optimize portfolio weights using specified method.
    
    Args:
        returns: Historical returns
        cov_matrix: Covariance matrix
        method: 'equal_weight', 'minimum_variance', 'mean_variance', 'risk_parity'
        capital: Total capital available
        min_investment: Minimum absolute investment amount per asset
        
    Returns:
        Dictionary mapping tickers to optimal weights
    """
    tickers = cov_matrix.columns.tolist()
    n_assets = len(tickers)
    
    if method == 'equal_weight':
        weights = np.ones(n_assets) / n_assets
    elif method == 'minimum_variance':
        weights = _optimize_min_variance(cov_matrix, min_weight, max_weight)
    elif method == 'mean_variance':
        expected_returns = returns.mean()
        weights = _optimize_mean_variance(expected_returns, cov_matrix, target_return, min_weight, max_weight)
    elif method == 'risk_parity':
        weights = _optimize_risk_parity(cov_matrix)
    else:
        raise ValueError(f"Unknown optimization method: {method}")
        
    # Capital-Aware Construction: reject/adjust weights that violate minimum investment
    final_weights = _apply_capital_constraints(weights, tickers, capital, min_investment)
    
    return dict(zip(tickers, final_weights))

def _optimize_min_variance(cov_matrix: pd.DataFrame, min_w: float, max_w: float) -> np.ndarray:
    import scipy.optimize as sco
    n = len(cov_matrix)
    
    def objective(w):
        return w.T @ cov_matrix.values @ w
        
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((min_w, max_w) for _ in range(n))
    initial_guess = np.ones(n) / n
    
    result = sco.minimize(objective, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    return result.x

def _optimize_mean_variance(returns: pd.Series, cov_matrix: pd.DataFrame, target_return: Optional[float], min_w: float, max_w: float) -> np.ndarray:
    import scipy.optimize as sco
    n = len(cov_matrix)
    
    def objective(w):
        return w.T @ cov_matrix.values @ w
        
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    if target_return is not None:
        constraints.append({'type': 'eq', 'fun': lambda x: np.sum(x * returns.values) - target_return})
        
    bounds = tuple((min_w, max_w) for _ in range(n))
    initial_guess = np.ones(n) / n
    
    result = sco.minimize(objective, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    return result.x

def _optimize_risk_parity(cov_matrix: pd.DataFrame) -> np.ndarray:
    import scipy.optimize as sco
    n = len(cov_matrix)
    
    def objective(w):
        port_variance = w.T @ cov_matrix.values @ w
        marginal_risk = cov_matrix.values @ w
        risk_contribs = w * marginal_risk
        target_risk = port_variance / n
        return np.sum((risk_contribs - target_risk)**2)
        
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0.0, 1.0) for _ in range(n))
    initial_guess = np.ones(n) / n
    
    result = sco.minimize(objective, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    return result.x

def _apply_capital_constraints(weights: np.ndarray, tickers: List[str], capital: Decimal, min_investment: Decimal) -> np.ndarray:
    """Ensure allocations meet minimum investment thresholds."""
    adjusted_weights = weights.copy()
    capital_float = float(capital)
    min_inv_float = float(min_investment)
    
    for i in range(len(adjusted_weights)):
        allocation = adjusted_weights[i] * capital_float
        if allocation > 0 and allocation < min_inv_float:
            adjusted_weights[i] = 0.0
            
    # Re-normalize
    weight_sum = np.sum(adjusted_weights)
    if weight_sum == 0:
        raise ValueError("Capital constraints rejected all assets.")
    return adjusted_weights / weight_sum
