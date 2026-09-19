"""Model view rule, the SHOW_TRADE_LABELS switch, and the confidence score."""
from decimal import Decimal as D

import pytest

from packages.analysis.recommendation import confidence, recommend

CFG = {"buy_margin": 0.02, "sell_margin": 0.02,
       "confidence": {"penalty_per_missing_pct": 0.8, "penalty_per_open_conflict": 3, "max_conflict_penalty": 30,
                      "penalty_beta_unavailable": 40, "low_r_squared": 0.05, "penalty_low_r_squared": 15,
                      "high_at": 75, "medium_at": 50, "penalty_per_stale_input": 5, "max_stale_penalty": 15}}
PRICE = {"available": True, "value": D("1000")}
COE = {"available": True, "value": D("0.169224")}  # thresholds: above 0.189224, below 0.149224


def val(target, dps="50"):
    return {"available": True, "target_price_12m": D(target), "expected_dps_12m": D(dps)}


@pytest.mark.parametrize("target,view,label", [
    ("1150", "Undervalued", "BUY"),     # ETR = 0.15 + 0.05 = 0.20 > 0.189224
    ("1100", "Fairly valued", "HOLD"),  # ETR = 0.10 + 0.05 = 0.15, inside the band
    ("1050", "Overvalued", "SELL"),     # ETR = 0.05 + 0.05 = 0.10 < 0.149224
])
def test_model_view_bands(target, view, label):
    r = recommend(PRICE, val(target), COE, CFG, show_trade_labels=False)
    assert r["model_view"] == view
    assert "trade_label" not in r and r["trade_labels_enabled"] is False
    assert r["thresholds"]["above"] == D("0.189224") and r["thresholds"]["below"] == D("0.149224")
    on = recommend(PRICE, val(target), COE, CFG, show_trade_labels=True)
    assert on["trade_label"] == label and on["model_view"] == view


def test_expected_total_return_is_exact():
    r = recommend(PRICE, val("1150"), COE, CFG, False)
    assert (r["price_upside"], r["dividend_yield"], r["expected_total_return"]) == (D("0.15"), D("0.05"), D("0.20"))


def test_no_price_means_no_view_and_the_status_says_blocked():
    r = recommend({"available": False, "reason": "No licensed DSE prices", "status": "BLOCKED"},
                  val("1150"), COE, CFG, True)
    assert r == {"available": False, "reason": "No sourced share price: No licensed DSE prices", "status": "BLOCKED"}


def test_missing_valuation_or_coe_is_not_a_view():
    r = recommend(PRICE, {"available": False, "reason": "no beta", "status": "BLOCKED"}, COE, CFG, False)
    assert r["available"] is False and r["status"] == "BLOCKED"
    r = recommend(PRICE, val("1150"), {"available": False, "reason": "missing CRP"}, CFG, False)
    assert r["available"] is False and r["status"] == "INSUFFICIENT_DATA"


def test_confidence_score():
    # 100 - 0 (complete) - 0 (no conflicts) - 40 (no beta) - 15 (3 stale inputs x 5) = 45 -> Low
    c = confidence(1.0, 0, {"available": False}, ["A", "B", "C"], CFG)
    assert (c["score"], c["level"]) == (45.0, "Low")
    # 90% complete: -8; 2 conflicts: -6; beta with R^2 0.5: 0 -> 86 -> High
    c = confidence(0.9, 2, {"available": True, "r_squared": 0.5}, [], CFG)
    assert c["score"] == pytest.approx(86.0) and c["level"] == "High"
    # Penalties are capped: 20 conflicts cost 30, not 60; 9 stale inputs cost 15, not 45.
    c = confidence(1.0, 20, {"available": True, "r_squared": 0.01}, list("ABCDEFGHI"), CFG)
    assert c["score"] == pytest.approx(100 - 30 - 15 - 15)
