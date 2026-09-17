from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date
from pydantic import BaseModel
from decimal import Decimal

class Quote(BaseModel):
    symbol: str
    price: Decimal
    currency: str
    timestamp: date
    volume: Optional[int] = None
    
class HistoricalData(BaseModel):
    symbol: str
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

class BaseMarketDataProvider(ABC):
    """
    Abstract base class for all market data providers in My AfriAnalyze.
    Provides methods to retrieve real-time quotes and historical data.
    """
    
    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        """Fetch the latest available quote for a given symbol."""
        pass
        
    @abstractmethod
    def get_history(self, symbol: str, start_date: date, end_date: date) -> List[HistoricalData]:
        """Fetch historical price data for a given symbol within a date range."""
        pass

class MarketDataProvider(BaseMarketDataProvider):
    """
    Concrete implementation of Market Data Provider.
    Includes Redis caching for historical data.
    """
    
    def get_quote(self, symbol: str) -> Quote:
        # Dummy implementation
        return Quote(symbol=symbol, price=Decimal("10.0"), currency="KES", timestamp=date.today())

    def get_history(self, symbol: str, start_date: date, end_date: date) -> List[HistoricalData]:
        from packages.cache.manager import cache_manager
        import json
        
        cache_key = f"market_data_history:{symbol}:{start_date.isoformat()}:{end_date.isoformat()}"
        cached_data = cache_manager.get(cache_key)
        
        if cached_data:
            try:
                data = json.loads(cached_data)
                return [HistoricalData(**item) for item in data]
            except Exception:
                pass
                
        # Dummy implementation for getting history
        history = [
            HistoricalData(
                symbol=symbol,
                date=start_date,
                open=Decimal("10.0"),
                high=Decimal("10.5"),
                low=Decimal("9.5"),
                close=Decimal("10.0"),
                volume=1000
            )
        ]
        
        # Cache the results with a 12-hour TTL (43200 seconds)
        try:
            cache_data = json.dumps([item.model_dump(mode="json") for item in history])
            cache_manager.set(cache_key, cache_data, ttl=43200)
        except Exception:
            pass
            
        return history
