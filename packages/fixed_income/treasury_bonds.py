from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple

class TreasuryBondCalculator:
    """Deterministic math for T-Bonds."""
    
    @staticmethod
    def calculate_price(face_value: Decimal, coupon_rate: Decimal, yield_to_maturity: Decimal, periods: int, frequency: int = 2) -> Decimal:
        """Calculate T-Bond price using DCF."""
        if yield_to_maturity <= 0 or frequency <= 0:
            raise ValueError("Invalid yield or frequency.")
            
        period_yield = yield_to_maturity / Decimal(frequency)
        period_coupon = (face_value * coupon_rate) / Decimal(frequency)
        
        price = Decimal('0.0')
        for t in range(1, periods + 1):
            price += period_coupon / ((1 + period_yield) ** t)
            
        price += face_value / ((1 + period_yield) ** periods)
        return price.quantize(Decimal('0.0000'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_macaulay_duration(face_value: Decimal, coupon_rate: Decimal, yield_to_maturity: Decimal, periods: int, frequency: int = 2) -> Decimal:
        """Calculate Macaulay Duration."""
        if yield_to_maturity <= 0 or frequency <= 0:
            raise ValueError("Invalid yield or frequency.")

        period_yield = yield_to_maturity / Decimal(frequency)
        period_coupon = (face_value * coupon_rate) / Decimal(frequency)
        
        weighted_time_sum = Decimal('0.0')
        price = Decimal('0.0')
        
        for t in range(1, periods + 1):
            cf = period_coupon
            if t == periods:
                cf += face_value
            
            pv_cf = cf / ((1 + period_yield) ** t)
            price += pv_cf
            weighted_time_sum += pv_cf * (Decimal(t) / Decimal(frequency))
            
        if price == 0:
            return Decimal('0.0')
            
        mac_duration = weighted_time_sum / price
        return mac_duration.quantize(Decimal('0.0000'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_modified_duration(macaulay_duration: Decimal, yield_to_maturity: Decimal, frequency: int = 2) -> Decimal:
        """Calculate Modified Duration."""
        period_yield = yield_to_maturity / Decimal(frequency)
        mod_duration = macaulay_duration / (1 + period_yield)
        return mod_duration.quantize(Decimal('0.0000'), rounding=ROUND_HALF_UP)
        
    @staticmethod
    def calculate_convexity(face_value: Decimal, coupon_rate: Decimal, yield_to_maturity: Decimal, periods: int, frequency: int = 2) -> Decimal:
        """Calculate Convexity."""
        period_yield = yield_to_maturity / Decimal(frequency)
        period_coupon = (face_value * coupon_rate) / Decimal(frequency)
        
        price = Decimal('0.0')
        convexity_sum = Decimal('0.0')
        
        for t in range(1, periods + 1):
            cf = period_coupon
            if t == periods:
                cf += face_value
            
            pv_cf = cf / ((1 + period_yield) ** t)
            price += pv_cf
            t_in_years = Decimal(t) / Decimal(frequency)
            
            convexity_sum += pv_cf * (t_in_years ** 2 + t_in_years / Decimal(frequency))
            
        if price == 0:
            return Decimal('0.0')
            
        convexity = convexity_sum / (price * (1 + period_yield) ** 2)
        return convexity.quantize(Decimal('0.0000'), rounding=ROUND_HALF_UP)
