from decimal import Decimal, ROUND_HALF_UP

class TreasuryBillCalculator:
    """Deterministic math for T-Bills."""
    
    @staticmethod
    def calculate_price(face_value: Decimal, discount_rate: Decimal, days_to_maturity: int, year_basis: int = 364) -> Decimal:
        """Calculate T-Bill price based on discount rate."""
        discount = face_value * discount_rate * (Decimal(days_to_maturity) / Decimal(year_basis))
        price = face_value - discount
        return price.quantize(Decimal('0.0000'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_yield(face_value: Decimal, price: Decimal, days_to_maturity: int, year_basis: int = 364) -> Decimal:
        """Calculate annualized yield from price."""
        if price <= 0:
            raise ValueError("Price must be greater than zero.")
        yield_rate = ((face_value - price) / price) * (Decimal(year_basis) / Decimal(days_to_maturity))
        return yield_rate.quantize(Decimal('0.000000'), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_discount_rate(face_value: Decimal, price: Decimal, days_to_maturity: int, year_basis: int = 364) -> Decimal:
        """Calculate discount rate from price."""
        if face_value <= 0:
            raise ValueError("Face value must be greater than zero.")
        discount = ((face_value - price) / face_value) * (Decimal(year_basis) / Decimal(days_to_maturity))
        return discount.quantize(Decimal('0.000000'), rounding=ROUND_HALF_UP)
