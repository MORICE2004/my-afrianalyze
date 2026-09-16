"""
Return calculation utilities.
"""
from typing import Optional
import math

def simple_return(price_current: float, price_previous: float) -> Optional[float]:
    """
    Calculates simple return: (P_t - P_{t-1}) / P_{t-1}
    """
    if price_previous is None or price_current is None or price_previous == 0:
        return None
    return (price_current - price_previous) / price_previous

def log_return(price_current: float, price_previous: float) -> Optional[float]:
    """
    Calculates log return: ln(P_t / P_{t-1})
    """
    if price_previous is None or price_current is None or price_previous <= 0 or price_current <= 0:
        return None
    return math.log(price_current / price_previous)

def annualize_return(periodic_return: float, periods_per_year: float) -> float:
    """
    Annualizes a periodic return (assumes compounding).
    Formula: (1 + periodic_return) ^ periods_per_year - 1
    """
    return (1.0 + periodic_return) ** periods_per_year - 1.0

def annualize_volatility(periodic_volatility: float, periods_per_year: float) -> float:
    """
    Annualizes periodic volatility (standard deviation).
    Formula: periodic_volatility * sqrt(periods_per_year)
    """
    if periodic_volatility < 0 or periods_per_year < 0:
        return 0.0
    return periodic_volatility * math.sqrt(periods_per_year)

def calculate_sharpe_ratio(annualized_return: float, risk_free_rate: float, annualized_volatility: float) -> Optional[float]:
    """
    Calculates the Sharpe ratio.
    Formula: (annualized_return - risk_free_rate) / annualized_volatility
    """
    if annualized_volatility <= 0:
        return None
    return (annualized_return - risk_free_rate) / annualized_volatility
