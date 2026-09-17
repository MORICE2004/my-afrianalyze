import pandas as pd
import numpy as np
from typing import Dict, List, Callable, Optional
from decimal import Decimal

class BacktestEngine:
    def __init__(self, prices: pd.DataFrame, initial_capital: Decimal, transaction_cost_bps: float = 10.0):
        self.prices = prices.sort_index()
        self.initial_capital = float(initial_capital)
        self.transaction_cost_pct = transaction_cost_bps / 10000.0
        
    def run(self, rebalance_dates: List[pd.Timestamp], strategy_func: Callable) -> pd.DataFrame:
        """
        Run backtest preventing look-ahead bias.
        
        Args:
            rebalance_dates: Dates when portfolio is rebalanced
            strategy_func: Function that takes (current_date, historical_prices) and returns target weights
            
        Returns:
            DataFrame of portfolio value and returns over time
        """
        portfolio_value = self.initial_capital
        # Track shares instead of weights to naturally drift with prices
        current_shares = {ticker: 0.0 for ticker in self.prices.columns}
        cash = portfolio_value
        
        history = []
        
        for date in self.prices.index:
            current_prices = self.prices.loc[date]
            
            # Calculate current portfolio value based on previous shares and current prices
            holdings_value = sum(current_shares[t] * current_prices[t] for t in current_shares if not pd.isna(current_prices[t]))
            portfolio_value = cash + holdings_value
            
            if date in rebalance_dates:
                # Provide only historical data up to current date (no look-ahead)
                historical_data = self.prices.loc[:date]
                
                target_weights = strategy_func(date, historical_data)
                
                # Calculate target values
                target_values = {t: w * portfolio_value for t, w in target_weights.items()}
                
                # Calculate current values
                current_values = {t: current_shares[t] * current_prices[t] for t in current_shares if not pd.isna(current_prices[t])}
                
                # Calculate turnover value
                trade_values = {t: target_values.get(t, 0.0) - current_values.get(t, 0.0) for t in set(target_values) | set(current_values)}
                turnover = sum(abs(v) for v in trade_values.values()) / 2.0
                transaction_costs = turnover * self.transaction_cost_pct
                
                # Rebalance
                portfolio_value -= transaction_costs
                # Recalculate target values post-costs
                target_values = {t: w * portfolio_value for t, w in target_weights.items()}
                
                # Update shares and cash
                current_shares = {t: target_values.get(t, 0.0) / current_prices[t] if current_prices.get(t, 0.0) != 0 else 0.0 for t in self.prices.columns}
                holdings_value = sum(current_shares[t] * current_prices[t] for t in current_shares if not pd.isna(current_prices[t]))
                cash = portfolio_value - holdings_value
                
            history.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'cash': cash
            })
            
        df_history = pd.DataFrame(history).set_index('date')
        df_history['return'] = df_history['portfolio_value'].pct_change()
        return df_history
