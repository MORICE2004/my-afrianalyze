"""
Portfolio Rebalancing Engine

Provides deterministic calculations for portfolio drift and rebalancing requirements.
"""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel

class EvidenceRecord(BaseModel):
    """Traces financial figures to their source."""
    source_id: str
    document_ref: str
    page_num: Optional[int] = None
    extraction_date: str

class Asset(BaseModel):
    """Represents a portfolio asset."""
    ticker: str
    target_weight: Decimal
    current_weight: Decimal
    current_price: Decimal
    current_shares: int
    price_evidence: EvidenceRecord

class SavedPortfolio(BaseModel):
    """Represents a user's saved portfolio."""
    name: str
    total_value: Decimal
    assets: List[Asset]
    drift_threshold: Decimal = Decimal("0.05")  # Default 5% drift threshold

class RebalanceAlert(BaseModel):
    """Recommendation to buy or sell an asset to restore target weights."""
    ticker: str
    action: str  # "BUY" or "SELL"
    shares_to_trade: int
    estimated_value: Decimal
    target_weight: Decimal
    current_weight: Decimal

def check_drift_and_rebalance(portfolio: SavedPortfolio) -> List[RebalanceAlert]:
    """
    Compares a SavedPortfolio's target weights to its current market weights.
    If the drift exceeds the drift_threshold, it generates a RebalanceAlert.
    
    Financial Methodology:
    1. Drift = |Target Weight - Current Weight|
    2. If Drift > Threshold, Target Value = Total Portfolio Value * Target Weight
    3. Current Value = Current Shares * Current Price
    4. Value Difference = Target Value - Current Value
    5. Shares to Trade = Floor(|Value Difference| / Current Price)
    
    Returns:
        List[RebalanceAlert]: Recommended trades to restore target weights.
    """
    alerts = []
    for asset in portfolio.assets:
        drift = abs(asset.target_weight - asset.current_weight)
        if drift > portfolio.drift_threshold:
            target_value = portfolio.total_value * asset.target_weight
            current_value = Decimal(asset.current_shares) * asset.current_price
            value_diff = target_value - current_value
            
            # Cannot trade if value diff is less than one share price
            if abs(value_diff) < asset.current_price:
                continue
                
            shares_to_trade = int(abs(value_diff) / asset.current_price)
            if shares_to_trade > 0:
                alerts.append(
                    RebalanceAlert(
                        ticker=asset.ticker,
                        action="BUY" if value_diff > 0 else "SELL",
                        shares_to_trade=shares_to_trade,
                        estimated_value=Decimal(shares_to_trade) * asset.current_price,
                        target_weight=asset.target_weight,
                        current_weight=asset.current_weight
                    )
                )
    return alerts
