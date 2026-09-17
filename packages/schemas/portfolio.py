from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal

from .evidence import EvidenceRecord

class PortfolioPosition(BaseModel):
    """
    Represents a single deterministic position in a portfolio.
    """
    ticker: str
    shares: Decimal
    average_cost: Decimal
    current_price: Decimal
    weighting: Decimal
    unrealized_pnl: Decimal
    drift: Decimal
    evidence: List[EvidenceRecord] = Field(default_factory=list)

class SavedPortfolio(BaseModel):
    """
    Represents a saved user portfolio with deterministic calculations.
    """
    portfolio_id: str
    name: str
    total_value: Decimal
    positions: List[PortfolioPosition]
