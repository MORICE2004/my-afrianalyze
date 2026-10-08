"""Round-trip detection on index series (packages/market_data/quality.py) and its use in the beta."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal as D

from packages.market_data.quality import round_trips


def _series(levels):
    start = date(2026, 8, 17)
    return {start + timedelta(days=i): D(str(v)) for i, v in enumerate(levels)}


def test_the_dsei_split_week_is_a_round_trip():
    # The DSE's published DSEI around NMB's split: 4,254.75, then 1,365.54 and 1,380.68, then 4,385.06.
    s = _series([4238.03, 4255.50, 4254.75, 1365.54, 1380.68, 4385.06, 4444.48])
    days = sorted(s)
    assert round_trips(s) == [days[3], days[4]]


def test_a_real_fall_that_stays_down_is_not_a_round_trip():
    s = _series([1000, 1010, 880, 870, 860, 865, 870, 880])      # -13% and no recovery
    assert round_trips(s) == []


def test_small_moves_are_never_flagged():
    s = _series([1000, 1040, 990, 1050, 995, 1020])
    assert round_trips(s) == []
