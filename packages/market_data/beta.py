"""
Beta Calculation Engine for My AfriAnalyze.
"""
from typing import List, Literal, Optional
from pydantic import BaseModel
from datetime import date
import numpy as np

class ReturnPoint(BaseModel):
    date: date
    stock_return: Optional[float] = None
    benchmark_return: Optional[float] = None

class BetaResult(BaseModel):
    raw_beta: float
    adjusted_beta: float
    r_squared: float
    covariance: float
    benchmark_variance: float
    observations_used: int
    total_observations_provided: int
    warnings: List[str]
    methodology_note: str

def adjust_beta_blume(raw_beta: float) -> float:
    """
    Blume adjustment: adjusted_beta = (2/3) * raw_beta + (1/3) * 1.0
    
    This adjustment is used because empirical evidence shows that over time, 
    a security's beta tends to revert toward the market mean of 1.0. 
    In African markets with sporadic liquidity, this helps dampen extreme beta estimates 
    driven by data noise rather than true systematic risk.
    """
    return (2.0 / 3.0) * raw_beta + (1.0 / 3.0) * 1.0

class BetaEngine:
    """
    Deterministic beta calculation engine.
    FORMULA: beta = Cov(stock_return, benchmark_return) / Var(benchmark_return)
    """
    
    def calculate_beta(self, stock_returns: List[ReturnPoint], benchmark_returns: List[ReturnPoint], frequency: Literal['daily', 'weekly', 'monthly'] = 'weekly') -> BetaResult:
        """
        Calculates beta by aligning stock and benchmark returns by date.
        """
        # Align by date
        # Create dictionary for benchmark returns
        bench_map = {r.date: r.benchmark_return for r in benchmark_returns if r.benchmark_return is not None}
        
        aligned_stock = []
        aligned_bench = []
        
        total_provided = max(len(stock_returns), len(benchmark_returns))
        
        for sr in stock_returns:
            if sr.stock_return is not None and sr.date in bench_map:
                aligned_stock.append(sr.stock_return)
                aligned_bench.append(bench_map[sr.date])
                
        obs_used = len(aligned_stock)
        warnings = []
        
        if obs_used < 30:
            warnings.append(f"Fewer than 30 observations used ({obs_used}). Beta estimate may not be statistically significant.")
            
        if total_provided > 0 and (total_provided - obs_used) / total_provided > 0.2:
            warnings.append(f"More than 20% of data is missing or could not be aligned. Quality of beta is severely degraded.")
            
        if obs_used < 2:
            # Cannot calculate covariance/variance
            return BetaResult(
                raw_beta=1.0,
                adjusted_beta=1.0,
                r_squared=0.0,
                covariance=0.0,
                benchmark_variance=0.0,
                observations_used=obs_used,
                total_observations_provided=total_provided,
                warnings=warnings + ["Insufficient data to calculate beta. Defaulting to 1.0."],
                methodology_note="Beta set to 1.0 due to lack of aligned historical returns."
            )
            
        # Calculate covariance and variance
        cov_matrix = np.cov(aligned_stock, aligned_bench)
        cov = cov_matrix[0, 1]
        var_bench = cov_matrix[1, 1]
        
        if var_bench == 0 or np.isnan(var_bench):
            warnings.append("Benchmark variance is zero or NaN. Cannot calculate beta properly. Defaulting to 1.0.")
            raw_beta = 1.0
            r_squared = 0.0
        else:
            raw_beta = float(cov / var_bench)
            # R-squared = (Cov(x,y) / (Std(x)*Std(y)))^2
            var_stock = cov_matrix[0, 0]
            if var_stock == 0:
                r_squared = 0.0
            else:
                correlation = cov / (np.sqrt(var_stock) * np.sqrt(var_bench))
                r_squared = float(correlation ** 2)
                
        if r_squared < 0.05 and obs_used >= 30:
            warnings.append(f"R-squared is very low ({r_squared:.4f}). The beta may be meaningless as the stock's movements are poorly explained by the benchmark.")
            
        adj_beta = adjust_beta_blume(raw_beta)
        
        methodology = (
            f"Beta calculated using {obs_used} {frequency} observations. "
            f"Formula: Covariance(stock, benchmark) / Variance(benchmark). "
            f"Blume adjustment applied to raw beta ({raw_beta:.4f}) to yield {adj_beta:.4f}."
        )
        
        return BetaResult(
            raw_beta=raw_beta,
            adjusted_beta=adj_beta,
            r_squared=r_squared,
            covariance=float(cov),
            benchmark_variance=float(var_bench),
            observations_used=obs_used,
            total_observations_provided=total_provided,
            warnings=warnings,
            methodology_note=methodology
        )
