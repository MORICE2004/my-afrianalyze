"""Line-item analysis: value, YoY change, CAGR and common-size share."""
from __future__ import annotations

from decimal import Decimal

from packages.analysis.common import Computed, Result, Unavailable


def yoy_change(current: float | None, prior: float | None) -> Result:
    if current is None or prior is None:
        return Unavailable("Prior or current year value not available")
    if prior == 0:
        return Unavailable("Prior year value is zero")
    return Computed((current - prior) / abs(prior), "(current - prior) / |prior|",
                    {"current": current, "prior": prior})


def cagr(first: float | None, last: float | None, years: int) -> Result:
    if first is None or last is None:
        return Unavailable("Start or end value not available")
    if years <= 0:
        return Unavailable("Need at least two fiscal years")
    if first <= 0 or last <= 0:
        return Unavailable("CAGR is undefined when the start or end value is zero or negative")
    return Computed((last / first) ** (Decimal(1) / Decimal(years)) - 1, "(last / first)^(1 / years) - 1",
                    {"first": first, "last": last, "years": years})


def common_size(value: float | None, base: float | None, base_label: str) -> Result:
    if value is None or base is None:
        return Unavailable(f"Value or {base_label} not available")
    if base == 0:
        return Unavailable(f"{base_label} is zero")
    return Computed(value / base, f"value / {base_label}", {"value": value, base_label: base})


def analyse_series(series: dict[int, float], base_series: dict[int, float] | None,
                   base_label: str, history: dict[int, float] | None = None) -> dict:
    """series maps fiscal year to value for the years shown. `history` may hold
    earlier years (e.g. a prior-year comparative) used only for the first YoY."""
    history = history or series
    years = sorted(series)
    rows = []
    for year in years:
        rows.append({
            "fiscal_year": year,
            "value": series[year],
            "yoy": yoy_change(series[year], history.get(year - 1)).to_dict(),
            "common_size": (common_size(series[year], base_series.get(year), base_label).to_dict()
                            if base_series is not None else None),
        })
    if len(years) >= 2:
        period = cagr(series[years[0]], series[years[-1]], years[-1] - years[0]).to_dict()
    else:
        period = Unavailable("Need at least two fiscal years").to_dict()
    return {"rows": rows, "cagr": period,
            "first_year": years[0] if years else None, "last_year": years[-1] if years else None}
