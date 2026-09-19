"""Deterministic model view, optional trade label, and confidence level.

Rule (thresholds in config/recommendation.json, shown on the page):
  expected total return (ETR) = (target - price) / price + expected DPS / price
  ETR > cost of equity + buy_margin   -> Undervalued   (trade label BUY)
  ETR < cost of equity - sell_margin  -> Overvalued    (trade label SELL)
  otherwise                           -> Fairly valued (trade label HOLD)

Trade labels (BUY / HOLD / SELL) may need an investment adviser licence to
publish (PRODUCT_CONTEXT.md section 71). They are only returned when the
SHOW_TRADE_LABELS setting is on; it is off by default.
"""
from __future__ import annotations

from packages.analysis.common import BLOCKED, INSUFFICIENT_DATA, Unavailable, to_dec

VIEWS = {"up": ("Undervalued", "BUY"), "mid": ("Fairly valued", "HOLD"), "down": ("Overvalued", "SELL")}


def recommend(price: dict, valuation: dict, coe: dict, cfg: dict, show_trade_labels: bool) -> dict:
    if not price.get("available"):
        return Unavailable("No sourced share price: " + price.get("reason", ""),
                           price.get("status", BLOCKED)).to_dict()
    if not valuation.get("available"):
        return Unavailable("Valuation not available: " + valuation.get("reason", ""),
                           valuation.get("status", INSUFFICIENT_DATA)).to_dict()
    if not coe.get("available"):
        return Unavailable("Cost of equity not available: " + coe.get("reason", ""),
                           coe.get("status", INSUFFICIENT_DATA)).to_dict()
    p = to_dec(price["value"])
    upside = (to_dec(valuation["target_price_12m"]) - p) / p
    dy = to_dec(valuation["expected_dps_12m"]) / p
    etr = upside + dy
    coe_v = to_dec(coe["value"])
    buy_above = coe_v + to_dec(cfg["buy_margin"])
    sell_below = coe_v - to_dec(cfg["sell_margin"])
    band = "up" if etr > buy_above else "down" if etr < sell_below else "mid"
    view, label = VIEWS[band]
    out = {"available": True, "model_view": view, "expected_total_return": etr,
           "price_upside": upside, "dividend_yield": dy,
           "thresholds": {"above": buy_above, "below": sell_below,
                          "buy_margin": to_dec(cfg["buy_margin"]), "sell_margin": to_dec(cfg["sell_margin"])},
           "rule": "Undervalued if ETR > CoE + margin; Overvalued if ETR < CoE - margin; otherwise Fairly valued",
           "trade_labels_enabled": show_trade_labels}
    if show_trade_labels:
        out["trade_label"] = label
    return out


def confidence(completeness: float, open_conflicts: int, beta: dict, stale_inputs: list[str], cfg: dict) -> dict:
    """Score 0-100 from data completeness, open extraction conflicts, beta quality and freshness."""
    c = cfg["confidence"]
    score = 100.0
    notes = []
    missing_pct = (1 - completeness) * 100
    score -= missing_pct * c["penalty_per_missing_pct"]
    notes.append(f"Data completeness {completeness:.0%}: -{missing_pct * c['penalty_per_missing_pct']:.0f}")
    conflict_pen = min(open_conflicts * c["penalty_per_open_conflict"], c["max_conflict_penalty"])
    score -= conflict_pen
    notes.append(f"{open_conflicts} open extraction conflict(s): -{conflict_pen:.0f}")
    if not beta.get("available"):
        score -= c["penalty_beta_unavailable"]
        notes.append(f"Beta not measured: -{c['penalty_beta_unavailable']}")
    elif beta.get("r_squared") is not None and beta["r_squared"] < c["low_r_squared"]:
        score -= c["penalty_low_r_squared"]
        notes.append(f"Beta R-squared below {c['low_r_squared']}: -{c['penalty_low_r_squared']}")
    if stale_inputs:
        pen = min(len(stale_inputs) * c["penalty_per_stale_input"], c["max_stale_penalty"])
        score -= pen
        notes.append(f"Stale input(s) {', '.join(stale_inputs)}: -{pen:.0f}")
    score = max(0.0, min(100.0, score))
    level = "High" if score >= c["high_at"] else "Medium" if score >= c["medium_at"] else "Low"
    return {"score": score, "level": level, "notes": notes}
