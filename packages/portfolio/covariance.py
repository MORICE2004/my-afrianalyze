import numpy as np
import pandas as pd
from typing import Optional

def calculate_covariance_matrix(returns: pd.DataFrame, method: str = 'historical', min_periods: int = 30) -> pd.DataFrame:
    """
    Calculate covariance matrix of asset returns.
    
    Args:
        returns: DataFrame of asset returns (rows are dates, columns are tickers)
        method: 'historical' or 'ledoit_wolf'
        min_periods: Minimum number of observations required per pair
        
    Returns:
        Covariance matrix as a DataFrame
    """
    if method == 'historical':
        return returns.cov(min_periods=min_periods)
    elif method == 'ledoit_wolf':
        try:
            from sklearn.covariance import LedoitWolf
            clean_returns = returns.dropna()
            lw = LedoitWolf()
            cov_matrix = lw.fit(clean_returns).covariance_
            return pd.DataFrame(cov_matrix, index=returns.columns, columns=returns.columns)
        except ImportError:
            raise ImportError("scikit-learn is required for Ledoit-Wolf shrinkage")
    else:
        raise ValueError(f"Unknown covariance method: {method}")
