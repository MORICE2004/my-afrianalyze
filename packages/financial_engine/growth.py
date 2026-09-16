import math
from typing import List, Optional

def calculate_yoy_growth(values: List[float]) -> List[Optional[float]]:
    """
    Calculate Year-over-Year (YoY) growth for a list of sequential values.
    Returns a list of the same length, where the first element is None,
    and subsequent elements represent the growth from the previous value.
    """
    if not values:
        return []
    
    growth_rates: List[Optional[float]] = [None]
    for i in range(1, len(values)):
        current = values[i]
        previous = values[i-1]
        
        if previous is None or previous == 0:
            growth_rates.append(None)
        elif current is None:
            growth_rates.append(None)
        else:
            growth = (current - previous) / abs(previous)
            growth_rates.append(growth)
            
    return growth_rates

def calculate_cagr(start_value: Optional[float], end_value: Optional[float], years: Optional[int]) -> Optional[float]:
    """
    Calculate Compound Annual Growth Rate (CAGR).
    CAGR = (End Value / Start Value)^(1 / Years) - 1
    """
    if start_value is None or end_value is None or years is None or years <= 0:
        return None
    if start_value <= 0:
        # CAGR is mathematically undefined or problematic for negative/zero start values
        return None
        
    return (end_value / start_value) ** (1 / years) - 1

def calculate_moving_average(values: List[float], window: int) -> List[Optional[float]]:
    """
    Calculate a simple moving average over a specified window.
    Returns a list of the same length, where elements before the window size is met are None.
    """
    if not values or window <= 0:
        return [None] * len(values) if values else []
        
    moving_averages: List[Optional[float]] = []
    
    for i in range(len(values)):
        if i < window - 1:
            moving_averages.append(None)
        else:
            window_slice = values[i - window + 1:i + 1]
            if any(v is None for v in window_slice):
                moving_averages.append(None)
            else:
                moving_averages.append(sum(window_slice) / window)
                
    return moving_averages
