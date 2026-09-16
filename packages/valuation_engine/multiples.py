from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import math

class ComparableCompany(BaseModel):
    name: str
    ticker: str
    exchange: str
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    ev_sales: Optional[float] = None
    dividend_yield: Optional[float] = None
    roe: Optional[float] = None
    market_cap: Optional[float] = None
    data_quality_note: str

class MultiplesResult(BaseModel):
    metric_name: str
    peer_values: Dict[str, float]
    peer_mean: float
    peer_median: float
    target_fundamental: float
    implied_value_from_mean: float
    implied_value_from_median: float
    warnings: List[str]

def _calculate_stats_and_validate(metric_name: str, target_fundamental: float, peers: List[ComparableCompany], metric_getter) -> MultiplesResult:
    warnings = []
    
    peer_values = {}
    for p in peers:
        val = metric_getter(p)
        if val is not None:
            peer_values[p.ticker] = val
            
    if len(peer_values) < 3:
        warnings.append(f"Fewer than 3 peers available with valid {metric_name} data.")
        
    values_list = list(peer_values.values())
    
    if not values_list:
        return MultiplesResult(
            metric_name=metric_name,
            peer_values={},
            peer_mean=0.0,
            peer_median=0.0,
            target_fundamental=target_fundamental,
            implied_value_from_mean=0.0,
            implied_value_from_median=0.0,
            warnings=["No valid peer data available."]
        )
        
    peer_mean = sum(values_list) / len(values_list)
    sorted_vals = sorted(values_list)
    mid = len(sorted_vals) // 2
    if len(sorted_vals) % 2 == 0:
        peer_median = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0
    else:
        peer_median = sorted_vals[mid]
        
    if peer_mean > 0 and len(values_list) > 1:
        variance = sum((x - peer_mean) ** 2 for x in values_list) / (len(values_list) - 1)
        std_dev = math.sqrt(variance)
        if (std_dev / peer_mean) > 0.5:
            warnings.append(f"High dispersion among peer {metric_name} multiples (std/mean > 0.5). Peers might not be highly comparable.")
            
    implied_mean = peer_mean * target_fundamental
    implied_median = peer_median * target_fundamental
    
    return MultiplesResult(
        metric_name=metric_name,
        peer_values=peer_values,
        peer_mean=peer_mean,
        peer_median=peer_median,
        target_fundamental=target_fundamental,
        implied_value_from_mean=implied_mean,
        implied_value_from_median=implied_median,
        warnings=warnings
    )

def calculate_pe_valuation(target_eps: float, peers: List[ComparableCompany]) -> MultiplesResult:
    """
    Calculates comparable valuation using Price-to-Earnings (P/E) multiple.
    Implied Value = Peer Multiple * Target EPS
    """
    return _calculate_stats_and_validate("P/E", target_eps, peers, lambda p: p.pe_ratio)

def calculate_pb_valuation(target_bvps: float, peers: List[ComparableCompany]) -> MultiplesResult:
    """
    Calculates comparable valuation using Price-to-Book (P/B) multiple.
    Implied Value = Peer Multiple * Target BVPS
    """
    return _calculate_stats_and_validate("P/B", target_bvps, peers, lambda p: p.pb_ratio)

def calculate_ev_ebitda_valuation(target_ebitda: float, net_debt: float, shares: int, peers: List[ComparableCompany]) -> MultiplesResult:
    """
    Calculates comparable valuation using EV/EBITDA multiple.
    Implied Enterprise Value = Peer Multiple * Target EBITDA
    Implied Equity Value = Enterprise Value - Net Debt
    Implied Value Per Share = Equity Value / Shares
    """
    res = _calculate_stats_and_validate("EV/EBITDA", target_ebitda, peers, lambda p: p.ev_ebitda)
    
    if shares <= 0:
        res.warnings.append("Shares outstanding must be positive to calculate per-share value.")
        res.implied_value_from_mean = 0.0
        res.implied_value_from_median = 0.0
        return res
        
    ev_mean = res.implied_value_from_mean
    ev_median = res.implied_value_from_median
    
    eq_mean = ev_mean - net_debt
    eq_median = ev_median - net_debt
    
    res.implied_value_from_mean = eq_mean / shares
    res.implied_value_from_median = eq_median / shares
    
    return res
