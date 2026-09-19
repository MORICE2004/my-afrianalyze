from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

ZERO = Decimal(0)
MILLION = Decimal(1_000_000)


def to_dec(x: Any) -> Decimal | None:
    """Exact conversion to Decimal. Floats (config values, numpy outputs) go through
    their shortest repr so 0.05 becomes Decimal('0.05'), not a binary expansion."""
    if x is None:
        return None
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


# Data status words (CLAUDE.md rule 1).
VERIFIED = "VERIFIED"
PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
BLOCKED = "BLOCKED"
STALE = "STALE"
CONFLICTING_SOURCE = "CONFLICTING_SOURCE"


@dataclass(frozen=True)
class Unavailable:
    """A value that could not be computed, and why."""

    reason: str
    status: str = INSUFFICIENT_DATA

    def to_dict(self) -> dict[str, Any]:
        return {"available": False, "reason": self.reason, "status": self.status}


@dataclass(frozen=True)
class Computed:
    value: Decimal
    formula: str
    inputs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"available": True, "value": self.value, "formula": self.formula, "inputs": self.inputs}


Result = Computed | Unavailable


def safe_div(num: Decimal | None, den: Decimal | None, formula: str, inputs: dict[str, Any]) -> Result:
    if num is None or den is None:
        missing = [k for k, v in inputs.items() if v is None]
        return Unavailable(f"Missing input: {', '.join(missing) or 'unknown'}")
    if den == 0:
        return Unavailable("Denominator is zero")
    return Computed(num / den, formula, inputs)
