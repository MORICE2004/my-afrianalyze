"""Deterministic fixed-rate bond mathematics in exact Decimal.

Street convention: coupon dates are counted back from maturity in steps of 12/frequency months; the first
period is fractional, w = days(settlement -> next coupon) / days(previous coupon -> next coupon);

  dirty price = sum_k (C/f) / (1 + y/f)^(w + k)  +  100 / (1 + y/f)^(w + N - 1)
  accrued     = (C/f) x (1 - w)          clean = dirty - accrued
  Macaulay duration = sum_k t_k PV_k / dirty, with t_k = (w + k) / f   (years)
  modified duration = Macaulay / (1 + y/f)
  convexity   = sum_k CF_k (w+k)(w+k+1) / (1 + y/f)^(w+k+2) / (dirty x f^2)

Prices are per 100 of face value. Which frequency and settlement lag a market uses is checked against the
issuer's own published prices (tests/v1/test_bonds.py), not assumed.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, getcontext

getcontext().prec = 28
HUNDRED = Decimal(100)


def _add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    year, month = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):
        try:
            return date(year, month, day)
        except ValueError:
            continue
    raise ValueError(d)


def schedule(settlement: date, maturity: date, frequency: int) -> tuple[date, list[date]]:
    """(previous coupon date, remaining coupon dates up to and including maturity)."""
    if settlement >= maturity:
        raise ValueError("Settlement is on or after maturity")
    step = 12 // frequency
    dates, k = [], 0
    while True:
        d = _add_months(maturity, -step * k)
        if d <= settlement:
            return d, sorted(dates)
        dates.append(d)
        k += 1


def analyse(coupon: Decimal, ytm: Decimal, settlement: date, maturity: date, frequency: int = 2) -> dict:
    """coupon and ytm as decimals (0.095 for 9.5%)."""
    prev, coupons = schedule(settlement, maturity, frequency)
    f = Decimal(frequency)
    c = coupon * HUNDRED / f
    v = 1 + ytm / f
    w = Decimal((coupons[0] - settlement).days) / Decimal((coupons[0] - prev).days)
    dirty = mac = conv = Decimal(0)
    for k, _ in enumerate(coupons):
        cf = c + (HUNDRED if k == len(coupons) - 1 else 0)
        e = w + k
        pv = cf / v ** e
        dirty += pv
        mac += (e / f) * pv
        conv += cf * e * (e + 1) / v ** (e + 2)
    accrued = c * (1 - w)
    macaulay = mac / dirty
    return {"clean_price": dirty - accrued, "dirty_price": dirty, "accrued_interest": accrued,
            "macaulay_duration": macaulay, "modified_duration": macaulay / v,
            "convexity": conv / (dirty * f * f), "coupons_remaining": len(coupons),
            "next_coupon": coupons[0].isoformat(), "frequency": frequency}


def price_change(modified_duration: Decimal, convexity: Decimal, dy: Decimal) -> Decimal:
    """Approximate % price change for a yield change dy: -D_mod x dy + 0.5 x convexity x dy^2."""
    return -modified_duration * dy + convexity * dy * dy / 2
