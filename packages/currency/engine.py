from dataclasses import dataclass
from typing import Optional, ClassVar, List
from datetime import date

@dataclass
class CurrencyValue:
    original_value: float
    original_currency: str
    normalized_value: Optional[float]
    normalized_currency: Optional[str]
    fx_rate: Optional[float]
    fx_source: Optional[str]
    fx_date: Optional[date]

class CurrencyEngine:
    supported_currencies: ClassVar[List[str]] = ['TZS', 'KES', 'UGX', 'RWF', 'GHS', 'NGN', 'ZAR', 'XOF', 'XAF', 'USD', 'EUR', 'GBP']
    
    @classmethod
    def convert(cls, value: Optional[float], from_currency: str, to_currency: str, fx_rate: Optional[float], fx_date: Optional[date], fx_source: Optional[str]) -> Optional[CurrencyValue]:
        """
        Convert a value from one currency to another using the provided fx_rate.
        Never overwrites the original local-currency value.
        """
        if value is None:
            return None
            
        if from_currency not in cls.supported_currencies:
            raise ValueError(f"Unsupported from_currency: {from_currency}")
            
        if to_currency not in cls.supported_currencies:
            raise ValueError(f"Unsupported to_currency: {to_currency}")
            
        if from_currency == to_currency:
            return CurrencyValue(
                original_value=value,
                original_currency=from_currency,
                normalized_value=value,
                normalized_currency=to_currency,
                fx_rate=1.0,
                fx_source="Identical Currency",
                fx_date=fx_date
            )
            
        if fx_rate is None:
            return CurrencyValue(
                original_value=value,
                original_currency=from_currency,
                normalized_value=None,
                normalized_currency=to_currency,
                fx_rate=None,
                fx_source=None,
                fx_date=None
            )
            
        normalized_value = value * fx_rate
        
        return CurrencyValue(
            original_value=value,
            original_currency=from_currency,
            normalized_value=normalized_value,
            normalized_currency=to_currency,
            fx_rate=fx_rate,
            fx_source=fx_source,
            fx_date=fx_date
        )

    @classmethod
    def get_exchange_rate(cls, from_currency: str, to_currency: str, target_date: Optional[date] = None) -> Optional[float]:
        """
        Seamlessly fetch exchange rates, with specific support for TZS to KES tracking
        to allow portfolios to standardize to a base currency.
        """
        if from_currency not in cls.supported_currencies or to_currency not in cls.supported_currencies:
            raise ValueError("Unsupported currency.")
        
        if from_currency == to_currency:
            return 1.0

        # Simulation for tracking exchange rates (including KES, UGX)
        rates = {
            ("TZS", "KES"): 0.051,
            ("KES", "TZS"): 19.61,
            ("TZS", "UGX"): 1.45,
            ("UGX", "TZS"): 0.69,
            ("USD", "KES"): 135.0,
            ("USD", "TZS"): 2650.0,
            ("USD", "UGX"): 3800.0,
        }
        
        return rates.get((from_currency, to_currency))

    @classmethod
    def convert_seamless(cls, value: float, from_currency: str, to_currency: str, target_date: Optional[date] = None) -> Optional[CurrencyValue]:
        """
        Auto-fetches the correct rate to allow standardization.
        """
        rate = cls.get_exchange_rate(from_currency, to_currency, target_date)
        return cls.convert(value, from_currency, to_currency, rate, target_date, "Internal Engine")
