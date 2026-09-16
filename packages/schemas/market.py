from pydantic import BaseModel, Field
from typing import Optional, List
import datetime
from decimal import Decimal

class PricePoint(BaseModel):
    ticker: str = Field(description="Stock ticker symbol")
    exchange: str = Field(description="Exchange code")
    date: datetime.date = Field(description="Trading date")
    open: Optional[Decimal] = Field(None, description="Opening price")
    high: Optional[Decimal] = Field(None, description="High price")
    low: Optional[Decimal] = Field(None, description="Low price")
    close: Decimal = Field(description="Closing price")
    volume: int = Field(description="Trading volume")
    adjusted_close: Optional[Decimal] = Field(None, description="Adjusted closing price")
    is_trading_day: bool = Field(description="Indicates if it was a valid trading day")
    is_suspended: bool = Field(description="Indicates if the stock was suspended")
    is_stale: bool = Field(description="Indicates if the price is carried over due to illiquidity")

class MarketSnapshot(BaseModel):
    ticker: str = Field(description="Stock ticker symbol")
    exchange: str = Field(description="Exchange code")
    current_price: Decimal = Field(description="Current market price")
    price_date: datetime.date = Field(description="Date of the current price")
    shares_outstanding: int = Field(description="Total shares outstanding")
    market_cap: Decimal = Field(description="Current market capitalization")
    avg_volume_30d: Optional[int] = Field(None, description="30-day average volume")
    avg_volume_90d: Optional[int] = Field(None, description="90-day average volume")
    fifty_two_week_high: Optional[Decimal] = Field(None, description="52-week high price")
    fifty_two_week_low: Optional[Decimal] = Field(None, description="52-week low price")

class BetaResult(BaseModel):
    beta: float = Field(description="Calculated beta")
    measurement_period_start: datetime.date = Field(description="Start of measurement period")
    measurement_period_end: datetime.date = Field(description="End of measurement period")
    frequency: str = Field(description="Frequency of returns (e.g., 'daily', 'weekly')")
    benchmark_ticker: str = Field(description="Ticker of benchmark index")
    benchmark_name: str = Field(description="Name of benchmark index")
    num_observations: int = Field(description="Number of valid observations used")
    missing_observations: int = Field(description="Number of missing observations handled")
    r_squared: float = Field(description="R-squared of the regression")
    methodology_note: str = Field(description="Note on methodology, particularly handling of stale prices")
    warnings: List[str] = Field(default_factory=list, description="Any warnings from the calculation")

class DividendRecord(BaseModel):
    ticker: str = Field(description="Stock ticker symbol")
    ex_date: Optional[datetime.date] = Field(None, description="Ex-dividend date")
    record_date: Optional[datetime.date] = Field(None, description="Record date")
    payment_date: Optional[datetime.date] = Field(None, description="Payment date")
    amount: Decimal = Field(description="Dividend amount")
    currency: str = Field(description="Currency of the dividend")

class CorporateAction(BaseModel):
    ticker: str = Field(description="Stock ticker symbol")
    date: datetime.date = Field(description="Date of the corporate action")
    action_type: str = Field(description="Type of action (e.g., 'SPLIT', 'RIGHTS_ISSUE')")
    description: str = Field(description="Description of the action")
    details: Optional[str] = Field(None, description="Further details or terms")
