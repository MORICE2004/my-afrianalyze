import math
from typing import List, Tuple
from decimal import Decimal, ROUND_HALF_UP

class FundAnalyzer:
    """Calculates deterministic metrics for Mutual Funds and ETFs."""
    
    @staticmethod
    def calculate_total_return(start_nav: Decimal, end_nav: Decimal, distributions: Decimal = Decimal('0.0')) -> Decimal:
        """Calculate total return including distributions."""
        if start_nav <= 0:
            raise ValueError("Start NAV must be greater than zero.")
        total_return = (end_nav - start_nav + distributions) / start_nav
        return total_return.quantize(Decimal('0.000000'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_annualized_return(start_nav: Decimal, end_nav: Decimal, years: Decimal) -> Decimal:
        """Calculate annualized return (CAGR)."""
        if start_nav <= 0 or years <= 0:
            raise ValueError("Start NAV and years must be positive.")
        
        cagr = (end_nav / start_nav) ** (Decimal('1.0') / years) - Decimal('1.0')
        return cagr.quantize(Decimal('0.000000'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_volatility(returns: List[Decimal], annualization_factor: Decimal = Decimal('252')) -> Decimal:
        """Calculate annualized volatility from a list of returns."""
        if len(returns) < 2:
            return Decimal('0.0')
            
        mean_return = sum(returns) / Decimal(len(returns))
        variance = sum((r - mean_return) ** 2 for r in returns) / Decimal(len(returns) - 1)
        
        # Convert variance to float for math.sqrt, then back to Decimal
        volatility = Decimal(str(math.sqrt(float(variance)))) * Decimal(str(math.sqrt(float(annualization_factor))))
        return volatility.quantize(Decimal('0.000000'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_max_drawdown(nav_history: List[Decimal]) -> Decimal:
        """Calculate Maximum Drawdown."""
        if not nav_history:
            return Decimal('0.0')
            
        max_drawdown = Decimal('0.0')
        peak = nav_history[0]
        
        for nav in nav_history:
            if nav > peak:
                peak = nav
            drawdown = (peak - nav) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                
        return max_drawdown.quantize(Decimal('0.000000'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_sharpe_ratio(annualized_return: Decimal, risk_free_rate: Decimal, annualized_volatility: Decimal) -> Decimal:
        """Calculate Sharpe Ratio."""
        if annualized_volatility == 0:
            return Decimal('0.0')
            
        sharpe = (annualized_return - risk_free_rate) / annualized_volatility
        return sharpe.quantize(Decimal('0.0000'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_sortino_ratio(returns: List[Decimal], risk_free_rate: Decimal, annualization_factor: Decimal = Decimal('252')) -> Decimal:
        """Calculate Sortino Ratio using downside deviation."""
        if len(returns) < 2:
            return Decimal('0.0')
            
        period_rf = risk_free_rate / annualization_factor
        downside_returns = [r - period_rf for r in returns if r < period_rf]
        
        if not downside_returns:
            return Decimal('0.0') # Or infinity, but 0 is safer fallback
            
        downside_variance = sum(r ** 2 for r in downside_returns) / Decimal(len(returns))
        downside_deviation = Decimal(str(math.sqrt(float(downside_variance)))) * Decimal(str(math.sqrt(float(annualization_factor))))
        
        if downside_deviation == 0:
            return Decimal('0.0')
            
        annualized_return = sum(returns) / Decimal(len(returns)) * annualization_factor
        
        sortino = (annualized_return - risk_free_rate) / downside_deviation
        return sortino.quantize(Decimal('0.0000'), rounding=ROUND_HALF_UP)

    @classmethod
    def analyze_fund_performance(cls, nav_history: List[Decimal], risk_free_rate: Decimal = Decimal('0.05')) -> dict | str:
        """
        Analyze fund performance returning a dictionary of metrics, 
        or 'BLOCKED' if historical NAV observations are insufficient.
        """
        if len(nav_history) < 2:
            return "BLOCKED"
            
        returns = [(nav_history[i] - nav_history[i-1]) / nav_history[i-1] for i in range(1, len(nav_history))]
        
        start_nav = nav_history[0]
        end_nav = nav_history[-1]
        
        # Approximate years assuming daily observations
        years = Decimal(len(nav_history)) / Decimal('252')
        if years == 0:
            return "BLOCKED"
            
        total_ret = cls.calculate_total_return(start_nav, end_nav)
        ann_ret = cls.calculate_annualized_return(start_nav, end_nav, years)
        vol = cls.calculate_volatility(returns)
        max_dd = cls.calculate_max_drawdown(nav_history)
        
        sharpe = cls.calculate_sharpe_ratio(ann_ret, risk_free_rate, vol) if vol > 0 else Decimal('0.0')
        sortino = cls.calculate_sortino_ratio(returns, risk_free_rate)
        
        return {
            "total_return": total_ret,
            "annualized_return": ann_ret,
            "volatility": vol,
            "max_drawdown": max_dd,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino
        }
