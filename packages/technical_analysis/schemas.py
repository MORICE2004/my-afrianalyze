from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class DataQualityReport(BaseModel):
    is_valid: bool
    status: str
    missing_days: int
    zero_volume_days: int
    stale_price_days: int
    reason: Optional[str] = None

class LiquidityProfile(BaseModel):
    average_daily_volume: float
    zero_volume_frequency: float
    is_illiquid: bool
    status: str

class IndicatorResult(BaseModel):
    value: Optional[float]
    status: str  # "OK", "INSUFFICIENT_DATA"
    reason: Optional[str] = None

class MACDResult(BaseModel):
    macd: Optional[float]
    signal: Optional[float]
    histogram: Optional[float]
    status: str

class BollingerBandsResult(BaseModel):
    upper: Optional[float]
    middle: Optional[float]
    lower: Optional[float]
    status: str

class TechnicalRegime(BaseModel):
    trend: str  # Bullish, Bearish, Neutral
    momentum: str  # Bullish, Bearish, Neutral
    volatility: str  # High, Low, Normal
    explanation: Dict[str, str]
