"""Share splits: adjusting prices so a split is not mistaken for a crash.

The DSE publishes prices exactly as they traded. When NMB split 1:10 on 2026-08-24 the close went from
TZS 17,700 to TZS 1,850, which is not a 90% loss. Measuring returns on the raw series would give every
beta method a fabricated one-day collapse, and comparing today's price with an earnings figure from
before the split would be comparing two different things.

So two adjustments, both explicit and both traceable to `config/corporate_actions.json`:

* `adjust_prices` divides every close before the effective date by the split ratio, putting the whole
  series on today's basis (the usual "adjusted close"). Volumes are not touched here; the zero-volume
  share used by the beta rule only asks whether a share traded, which a split does not change.
* `per_share_factor` says how many of today's shares one share of a past year has become, so a
  per-share figure from that year's accounts can be put on today's basis.

Nothing is applied without an action that carries its source.
"""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from packages.core.config import REPO_ROOT

CONFIG = REPO_ROOT / "config" / "corporate_actions.json"


def load_actions(security_id: str, path: Path | None = None) -> list[dict]:
    """The splits recorded for one security, oldest first. Each one must cite its evidence."""
    cfg = json.loads((path or CONFIG).read_text(encoding="utf-8"))
    out = []
    for a in cfg.get("actions", []):
        if a.get("security_id") != security_id or a.get("kind") != "share_split":
            continue
        if not a.get("evidence"):
            raise ValueError(f"Corporate action for {security_id} on {a.get('effective_date')} cites no source")
        out.append(a)
    return sorted(out, key=lambda a: a["effective_date"])


def _ratio(action: dict) -> Decimal:
    return Decimal(str(action["ratio_new_for_old"]))


def adjust_prices(prices: dict[date, Decimal], actions: list[dict]) -> dict[date, Decimal]:
    """Put a price series on today's share basis, so returns across a split are real returns."""
    if not actions:
        return dict(prices)
    out = {}
    for day, close in prices.items():
        factor = Decimal(1)
        for a in actions:
            if day < date.fromisoformat(a["effective_date"]):
                factor *= _ratio(a)
        out[day] = close / factor
    return out


def per_share_factor(actions: list[dict], as_of: date) -> Decimal:
    """How many of today's shares one share held on `as_of` has become."""
    factor = Decimal(1)
    for a in actions:
        if as_of < date.fromisoformat(a["effective_date"]):
            factor *= _ratio(a)
    return factor


def describe(actions: list[dict], as_of: date | None = None) -> list[str]:
    """Plain sentences for the report, so the adjustment is visible rather than silent."""
    lines = []
    for a in actions:
        if as_of is not None and as_of < date.fromisoformat(a["effective_date"]):
            continue
        lines.append(f"{a['ratio_new_for_old']}-for-1 share split effective {a['effective_date']}: "
                     f"prices before that date are divided by {a['ratio_new_for_old']} so that returns are "
                     f"comparable, and per-share figures from earlier years are restated on the same basis.")
    return lines
