"""
Market Data Engine for handling price history, corporate actions, data quality, and returns.
"""
from typing import List, Literal, Optional, Dict
from pydantic import BaseModel
from datetime import date, timedelta
import math

class PricePoint(BaseModel):
    date: date
    price: float
    volume: float = 0.0
    shares_outstanding: Optional[float] = None
    is_suspended: bool = False

class ReturnPoint(BaseModel):
    date: date
    stock_return: Optional[float] = None
    benchmark_return: Optional[float] = None

class MarketDataQuality(BaseModel):
    total_observations: int
    missing_days: int
    stale_price_periods: int
    zero_volume_days: int
    suspended_days: int
    coverage_ratio: float
    is_sufficient_for_beta: bool
    warnings: List[str]

class MarketDataEngine:
    """
    Engine to manage market data, calculate returns, and detect data quality issues
    common in illiquid African markets.
    """
    
    def __init__(self):
        self.prices: List[PricePoint] = []
        
    def calculate_returns(self, prices: List[PricePoint], method: Literal['simple', 'log'] = 'simple') -> List[ReturnPoint]:
        """
        Calculates returns given a list of price points.
        Assumes prices are sorted by date ascending.
        """
        if not prices:
            return []
            
        returns = []
        for i in range(1, len(prices)):
            prev = prices[i-1]
            curr = prices[i]
            
            ret = None
            if prev.price > 0 and curr.price >= 0:
                if method == 'simple':
                    from .returns import simple_return
                    ret = simple_return(curr.price, prev.price)
                elif method == 'log':
                    from .returns import log_return
                    ret = log_return(curr.price, prev.price)
            
            returns.append(ReturnPoint(
                date=curr.date,
                stock_return=ret,
                benchmark_return=None
            ))
            
        return returns

    def detect_data_quality_issues(self, prices: List[PricePoint]) -> MarketDataQuality:
        """
        Analyzes a price series to detect data quality issues such as stale prices,
        missing days, suspensions, and zero volume days.
        """
        if not prices:
            return MarketDataQuality(
                total_observations=0,
                missing_days=0,
                stale_price_periods=0,
                zero_volume_days=0,
                suspended_days=0,
                coverage_ratio=0.0,
                is_sufficient_for_beta=False,
                warnings=["Empty price series provided."]
            )
            
        # Sort prices by date
        sorted_prices = sorted(prices, key=lambda x: x.date)
        total_obs = len(sorted_prices)
        zero_volume = 0
        suspended = 0
        stale_periods = 0
        missing_days = 0
        
        consecutive_same_price = 0
        
        for i, p in enumerate(sorted_prices):
            if p.volume == 0:
                zero_volume += 1
            if p.is_suspended:
                suspended += 1
                
            if i > 0:
                prev = sorted_prices[i-1]
                gap = (p.date - prev.date).days
                if gap > 3:
                    missing_days += (gap - 3) 
                    
                if p.price == prev.price:
                    consecutive_same_price += 1
                    if consecutive_same_price == 3: 
                        stale_periods += 1
                else:
                    consecutive_same_price = 0
                    
        start_date = sorted_prices[0].date
        end_date = sorted_prices[-1].date
        
        coverage = self.get_trading_day_coverage(sorted_prices, start_date, end_date)
        
        warnings = []
        if total_obs < 30:
            warnings.append("Less than 30 observations available. Data is extremely sparse.")
        if zero_volume / total_obs > 0.2:
            warnings.append("Highly illiquid security: >20% of days have zero trading volume.")
        if stale_periods > (total_obs / 20):
            warnings.append("Frequent stale pricing periods detected. Price discovery may be poor.")
        if coverage < 0.8:
            warnings.append("Coverage ratio is below 80%. Many missing trading days.")
            
        is_sufficient = total_obs >= 52 and coverage >= 0.7
        
        return MarketDataQuality(
            total_observations=total_obs,
            missing_days=missing_days,
            stale_price_periods=stale_periods,
            zero_volume_days=zero_volume,
            suspended_days=suspended,
            coverage_ratio=coverage,
            is_sufficient_for_beta=is_sufficient,
            warnings=warnings
        )
        
    def get_trading_day_coverage(self, prices: List[PricePoint], start_date: date, end_date: date, expected_trading_days_per_week: int = 5) -> float:
        """
        Calculates the coverage ratio of the price data against expected trading days.
        """
        if start_date >= end_date:
            return 1.0 if len(prices) > 0 else 0.0
            
        total_days = (end_date - start_date).days + 1
        expected_trading_days = total_days * (expected_trading_days_per_week / 7.0)
        
        if expected_trading_days <= 0:
            return 0.0
            
        actual_days = len(prices)
        coverage = actual_days / expected_trading_days
        return min(coverage, 1.0)
