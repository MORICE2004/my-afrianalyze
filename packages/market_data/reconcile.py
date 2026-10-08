"""Compare one day's close from two providers and record the result.

Rule (PRODUCT_CONTEXT addendum, launch directive items 51 and 53): when two sources disagree by more than the
tolerance, the day is CONFLICTING_SOURCE. The values are never averaged and the "better-looking" one is never
picked; the stored close stays the one the primary provider published, and the conflict is recorded with both
values, both providers' codes, the currency and the time of the check.

The comparison is exact Decimal arithmetic; difference_pct is relative to provider A (the primary).
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from packages.database.models import PriceReconciliation

MATCH = "MATCH"
CONFLICTING_SOURCE = "CONFLICTING_SOURCE"
CURRENCY_MISMATCH = "CURRENCY_MISMATCH"


def compare(instrument_id: str, trade_date: date, *, provider_a: str, symbol_a: str, close_a: Decimal,
            currency_a: str, provider_b: str, symbol_b: str, close_b: Decimal, currency_b: str,
            tolerance_pct: Decimal) -> dict:
    """The comparison as a plain record. A currency difference is its own status: the closes are not comparable."""
    if currency_a != currency_b:
        status = CURRENCY_MISMATCH
        diff = pct = Decimal(0)
    else:
        diff = close_b - close_a
        pct = diff / close_a if close_a else Decimal(0)
        status = MATCH if abs(pct) <= tolerance_pct else CONFLICTING_SOURCE
    return {"instrument_id": instrument_id, "trade_date": trade_date, "currency": currency_a,
            "provider_a": provider_a, "symbol_a": symbol_a, "close_a": close_a,
            "provider_b": provider_b, "symbol_b": symbol_b, "close_b": close_b,
            "difference": diff, "difference_pct": pct, "tolerance_pct": tolerance_pct, "status": status}


def record(session: Session, result: dict, checked_at: datetime | None = None) -> PriceReconciliation:
    row = PriceReconciliation(**result, checked_at=checked_at or datetime.now(timezone.utc))
    session.add(row)
    return row


def latest_for(session: Session, instrument_id: str) -> PriceReconciliation | None:
    return (session.query(PriceReconciliation).filter_by(instrument_id=instrument_id)
            .order_by(PriceReconciliation.checked_at.desc()).first())
