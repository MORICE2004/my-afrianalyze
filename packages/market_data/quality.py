"""Checks on a stored price or index series before it is used in a calculation.

A ROUND TRIP is a level that jumps by more than `move` from the day before and comes back within
`within` sessions to within `back` of where it started. A real market can fall 12% in a day; it does not
fall 68% and recover in three sessions while nothing else happens. The DSE's published index series has
such days (the DSEI read 1,365 on 2026-08-24 and 26 between 4,255 and 4,385, the week NMB's 1:10 split took
effect), so every daily return that touches them would be noise of the size of the whole series.

The days found are excluded from returns and charts, and the report lists them; the stored rows are never
changed or deleted (the source published them, and that record is kept).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

MOVE = Decimal("0.10")      # a one-session move larger than this starts a candidate
BACK = Decimal("0.05")      # ... which is a round trip if the level returns within this of the start
WITHIN = 5                  # ... in at most this many sessions


def round_trips(series: dict[date, Decimal], move: Decimal = MOVE, back: Decimal = BACK,
                within: int = WITHIN) -> list[date]:
    """Days whose level is part of a round trip. Sorted; empty when the series is clean."""
    days = sorted(series)
    flagged: set[date] = set()
    i = 1
    while i < len(days):
        start = series[days[i - 1]]
        level = series[days[i]]
        if start and abs(level / start - 1) > move:
            for k in range(i + 1, min(i + 1 + within, len(days))):
                if abs(series[days[k]] / start - 1) <= back:
                    flagged.update(days[i:k])      # every day away from the start, not the day it came back
                    i = k
                    break
        i += 1
    return sorted(flagged)
