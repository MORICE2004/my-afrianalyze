"""The industry beta: the basis the owner chose for the valuation on 2026-09-20.

A DSE bank does not trade every day, so a beta regressed on its own price is pulled toward zero and
swings with the measurement interval. On the real data NMB comes out at 0.02 daily and 0.79 monthly
from the same ten years, which is not one answer. The valuation therefore uses the average beta of
comparable listed banks, and keeps the local regressions on the page as a cross-check.
"""
from __future__ import annotations

from decimal import Decimal as D

import pytest

from packages.analysis import beta as bm
from packages.database.models import ReferenceInput
from packages.database.session import SessionLocal

RULE = {"thin_trading_threshold": 0.1,
        "min_observations": {"industry": 20, "monthly": 36, "weekly": 104, "dimson": 250},
        "order_thin": ["industry", "monthly", "weekly", "dimson"],
        "order_liquid": ["industry", "monthly", "weekly"],
        "blume_adjust": True}


def test_the_industry_beta_is_used_as_published():
    est = bm.industry(0.604, 104, "Damodaran, Banks (Regional)")
    assert est["available"] and est["beta"] == 0.604 and est["observations"] == 104


def test_nothing_is_invented_when_the_industry_beta_is_missing():
    est = bm.industry(None, None, None)
    assert est["available"] is False and "Run pipelines.macro" in est["reason"]


def test_blume_is_not_applied_to_an_average_of_many_banks():
    """Blume shrinks a noisy single-stock regression toward 1. An average is already shrunk."""
    estimates = {"industry": bm.industry(0.604, 104, "src")}
    zero = {"available": True, "value": 0.36}
    chosen = bm.select_beta(estimates, zero, RULE)
    assert chosen["method"] == "industry"
    assert chosen["beta"] == 0.604, "the published average must not be shrunk a second time"
    assert "No Blume adjustment" in chosen["reason"]


def test_blume_still_applies_to_a_regression():
    estimates = {"industry": bm.industry(None, None, None),
                 "monthly": {"available": True, "beta": 0.786, "observations": 120, "r_squared": 0.27}}
    chosen = bm.select_beta(estimates, {"available": True, "value": 0.36}, RULE)
    assert chosen["method"] == "monthly"
    assert chosen["beta"] == pytest.approx((2 / 3) * 0.786 + 1 / 3)


def test_the_industry_beta_works_without_any_price_history():
    """A bank with no loaded prices still gets a beta, because this one does not need them."""
    estimates = {"industry": bm.industry(0.604, 104, "src")}
    unknown = {"available": False, "reason": "No index trading days"}
    chosen = bm.select_beta(estimates, unknown, RULE)
    assert chosen["available"] and chosen["method"] == "industry" and chosen["beta"] == 0.604


def test_without_prices_and_without_an_industry_beta_nothing_is_selected():
    chosen = bm.select_beta({"industry": bm.industry(None, None, None)},
                            {"available": False, "reason": "No index trading days"}, RULE)
    assert chosen["available"] is False


def test_the_relevered_figure_is_offered_only_as_a_cross_check():
    """Deposits are not gearing, so relevering a bank is shown but never used."""
    est = bm.industry(0.604, 104, "src", industry_de=5.4013, industry_tax=0.1530,
                      target_de=4.67, target_tax=0.30)
    cross = est["relevered_cross_check"]
    assert est["beta"] == 0.604, "the valuation input stays the published levered beta"
    assert 0.3 < cross["beta"] < 1.0
    assert "not used" in cross["note"]


def test_the_stored_industry_beta_is_sourced_and_believable():
    with SessionLocal() as s:
        row = s.get(ReferenceInput, "EM_BANK_INDUSTRY_BETA")
        firms = s.get(ReferenceInput, "EM_BANK_INDUSTRY_FIRMS")
    if row is None:
        pytest.skip("run pipelines.macro to load the industry beta")
    assert D("0.1") < row.value < D("3"), "an industry beta outside this range is not usable"
    assert firms.value >= 20, "too few firms to call it an average"
    assert row.source_url and row.sha256 and row.as_of, "the figure must carry where it came from"
    assert "Damodaran" in row.source_name and "banks" in row.label.lower()
