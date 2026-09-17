import pytest
from decimal import Decimal
from packages.fixed_income.treasury_bills import TreasuryBillCalculator
from packages.fixed_income.treasury_bonds import TreasuryBondCalculator

def test_tbill_price():
    price = TreasuryBillCalculator.calculate_price(
        face_value=Decimal('100.00'),
        discount_rate=Decimal('0.05'),
        days_to_maturity=182,
        year_basis=364
    )
    assert price == Decimal('97.5000')

def test_tbill_yield():
    yield_rate = TreasuryBillCalculator.calculate_yield(
        face_value=Decimal('100.00'),
        price=Decimal('97.50'),
        days_to_maturity=182,
        year_basis=364
    )
    # (2.50 / 97.50) * 2 = 0.051282
    assert yield_rate == Decimal('0.051282')

def test_tbond_price():
    price = TreasuryBondCalculator.calculate_price(
        face_value=Decimal('100.00'),
        coupon_rate=Decimal('0.10'),
        yield_to_maturity=Decimal('0.10'),
        periods=20,
        frequency=2
    )
    # Should be par when coupon == ytm
    assert price == Decimal('100.0000')

def test_tbond_macaulay_duration():
    mac_dur = TreasuryBondCalculator.calculate_macaulay_duration(
        face_value=Decimal('100.00'),
        coupon_rate=Decimal('0.10'),
        yield_to_maturity=Decimal('0.10'),
        periods=2,
        frequency=1
    )
    # CF1 = 10, CF2 = 110
    # PV1 = 10 / 1.1 = 9.0909
    # PV2 = 110 / 1.21 = 90.9091
    # Weight1 = 1 * 9.0909 = 9.0909
    # Weight2 = 2 * 90.9091 = 181.8182
    # Sum = 190.9091 / 100 = 1.9091
    assert mac_dur == Decimal('1.9091')
