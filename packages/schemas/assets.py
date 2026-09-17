from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field

class AssetType(str, Enum):
    COMPANY = "COMPANY"
    SECURITY = "SECURITY"
    FUND = "FUND"
    INDEX = "INDEX"
    BASKET = "BASKET"
    PORTFOLIO = "PORTFOLIO"

class SecuritySubType(str, Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    T_BILL = "T_BILL"
    T_BOND = "T_BOND"

class AssetBase(BaseModel):
    id: str = Field(..., description="Unique identifier for the asset")
    name: str = Field(..., description="Name of the asset")
    asset_type: AssetType = Field(..., description="High-level asset category")

class Company(AssetBase):
    asset_type: AssetType = AssetType.COMPANY
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None

class Security(AssetBase):
    asset_type: AssetType = AssetType.SECURITY
    sub_type: SecuritySubType
    ticker: str
    exchange: Optional[str] = None
    currency: str = "TZS"
    expires_at: Optional[str] = None
    status: str = "ACTIVE"

class Fund(AssetBase):
    asset_type: AssetType = AssetType.FUND
    manager: str
    nav: Optional[float] = None
    expense_ratio: Optional[float] = None
    expires_at: Optional[str] = None
    status: str = "ACTIVE"

class Index(AssetBase):
    asset_type: AssetType = AssetType.INDEX
    provider: str

class Basket(AssetBase):
    asset_type: AssetType = AssetType.BASKET
    components: List[str] = Field(default_factory=list, description="IDs of component assets")

class PortfolioItem(BaseModel):
    asset_id: str
    weight: float

class Portfolio(AssetBase):
    asset_type: AssetType = AssetType.PORTFOLIO
    holdings: List[PortfolioItem] = Field(default_factory=list)

class PortfolioRequest(BaseModel):
    portfolio_id: str
    target_date: Optional[str] = None
    rebalance: bool = False

InvestmentEntity = Union[Company, Security, Fund, Index, Basket, Portfolio]
