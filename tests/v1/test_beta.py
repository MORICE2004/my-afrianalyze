"""Beta methods (section 74). Hand-checkable regressions plus a thin-trading case where the
plain daily beta is biased and the Dimson and Scholes-Williams corrections recover the true value."""
from datetime import date, timedelta

import numpy as np
import pytest

from packages.analysis import beta as B

RULE = {
    "thin_trading_threshold": 0.1,
    "min_observations": {"raw_daily": 250, "weekly": 104, "monthly": 36, "dimson": 250,
                         "scholes_williams": 250, "bottom_up": 3},
    "order_thin": ["dimson", "scholes_williams", "weekly", "monthly", "bottom_up"],
    "order_liquid": ["weekly", "monthly", "raw_daily", "bottom_up"],
    "blume_adjust": True,
}


def test_ols_matches_hand_calculation():
    # x = 1..5, y = 2,1,4,3,5 (in %). Sxy = 8, Sxx = 10, so slope = 0.8.
    # Fitted 1.4, 2.2, 3.0, 3.8, 4.6; residuals .6, -1.2, 1, -.8, .4; SSR = 3.6.
    # s^2 = 3.6 / 3 = 1.2; SE = sqrt(1.2 / 10) = 0.34641; R^2 = 64 / (10 * 10) = 0.64.
    x = np.array([1, 2, 3, 4, 5]) / 100
    y = np.array([2, 1, 4, 3, 5]) / 100
    r = B.ols(y, x)
    assert r.beta == pytest.approx(0.8)
    assert r.std_error == pytest.approx(0.34641, abs=1e-5)
    assert r.r_squared == pytest.approx(0.64)
    assert r.observations == 5


def test_ols_refuses_too_little_or_flat_data():
    assert isinstance(B.ols(np.array([0.1, 0.2]), np.array([0.1, 0.3])), B.Unavailable)
    flat = B.ols(np.array([0.1, 0.2, 0.3]), np.array([0.01, 0.01, 0.01]))
    assert isinstance(flat, B.Unavailable) and "zero variance" in flat.reason


def _market(n: int = 400, seed: int = 7) -> tuple[list[date], np.ndarray]:
    rng = np.random.default_rng(seed)
    days, d = [], date(2024, 1, 1)
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days, rng.normal(0.0005, 0.01, n)


def _prices(days: list[date], returns: np.ndarray, start: float = 1000.0) -> dict[date, float]:
    px, level = {}, start
    for d, r in zip(days, returns):
        level *= 1 + r
        px[d] = level
    return px


def test_liquid_stock_daily_beta_is_exact():
    days, rm = _market()
    index = _prices(days, rm)
    stock = _prices(days, 1.2 * rm)  # moves exactly 1.2x the index every day
    r = B.raw_daily(stock, index)
    assert r["beta"] == pytest.approx(1.2, abs=1e-9)
    assert r["r_squared"] == pytest.approx(1.0)


def test_stock_that_reacts_a_day_late_needs_dimson():
    # True beta 1.0, but half the reaction comes a day late: r_s(t) = 0.5 r_m(t) + 0.5 r_m(t-1).
    days, rm = _market()
    index = _prices(days, rm)
    rs = 0.5 * rm + 0.5 * np.concatenate([[0.0], rm[:-1]])
    stock = _prices(days, rs)
    raw = B.raw_daily(stock, index)["beta"]
    dim = B.dimson(stock, index, lags=1)
    sw = B.scholes_williams(stock, index)
    assert raw == pytest.approx(0.5, abs=0.1)          # biased toward zero
    assert dim["beta"] == pytest.approx(1.0, abs=1e-6)  # 0.5 lag + 0.5 same day + 0 lead
    assert dim["slopes"] == pytest.approx([0.5, 0.5, 0.0], abs=1e-6)
    assert sw["beta"] == pytest.approx(1.0, abs=0.1)    # (b-1 + b0 + b+1) / (1 + 2 rho), rho near 0


def test_carried_forward_prices_count_as_zero_volume_days():
    days, rm = _market(n=10)
    volumes = {d: (1000 if i % 2 == 0 else 0) for i, d in enumerate(days)}
    volumes[days[1]] = None  # missing volume counts as no trade
    z = B.zero_volume_share(volumes, days)
    assert z["zero_volume_days"] == 5 and z["value"] == pytest.approx(0.5)


def test_weekly_and_monthly_use_period_end_prices():
    days, rm = _market(n=260)
    index = _prices(days, rm)
    stock = _prices(days, 1.1 * rm)
    w, m = B.weekly(stock, index), B.monthly(stock, index)
    assert w["observations"] == len({d.isocalendar()[:2] for d in days}) - 1
    assert m["observations"] == len({(d.year, d.month) for d in days}) - 1
    # Compounding over a period makes the fit near, not exactly, 1.1.
    assert w["beta"] == pytest.approx(1.1, abs=0.02)


def test_bottom_up_hamada_matches_hand_calculation():
    # Peer A: 1.1 / (1 + 0.7 * 0.5) = 0.814815; peer B: 0.9 / (1 + 0.7 * 0.2) = 0.789474.
    # Mean unlevered 0.802144; relevered at D/E 0.4, tax 30%: 0.802144 * 1.28 = 1.026745.
    peers = [{"name": "A", "levered_beta": 1.1, "debt_to_equity": 0.5, "tax_rate": 0.3},
             {"name": "B", "levered_beta": 0.9, "debt_to_equity": 0.2, "tax_rate": 0.3}]
    r = B.bottom_up(peers, 0.4, 0.3)
    assert r["unlevered_beta"] == pytest.approx(0.802144, abs=1e-6)
    assert r["beta"] == pytest.approx(1.026745, abs=1e-6)
    assert B.bottom_up([], 0.4, 0.3)["available"] is False


def test_blume_adjustment():
    # 2/3 x 1.3 + 1/3 = 1.2
    assert B.blume(1.3) == pytest.approx(1.2)


def test_selection_rule_thin_market_prefers_dimson_and_applies_blume():
    est = {"dimson": {"available": True, "beta": 1.3, "observations": 300},
           "weekly": {"available": True, "beta": 0.9, "observations": 150}}
    s = B.select_beta(est, {"available": True, "value": 0.4}, RULE)
    assert s["method"] == "dimson"
    assert s["raw_beta"] == 1.3 and s["beta"] == pytest.approx(1.2)
    assert "above the 10% threshold" in s["reason"]


def test_selection_rule_skips_methods_without_enough_observations():
    est = {"weekly": {"available": True, "beta": 0.9, "observations": 50},
           "monthly": {"available": True, "beta": 1.0, "observations": 40}}
    s = B.select_beta(est, {"available": True, "value": 0.05}, RULE)
    assert s["method"] == "monthly"
    assert s["skipped"] == ["weekly: 50 observations < 104"]


def test_selection_rule_gives_up_honestly():
    s = B.select_beta({}, {"available": True, "value": 0.5}, RULE)
    assert s["available"] is False and "No beta method met its requirements" in s["reason"]
    s = B.select_beta({}, {"available": False, "reason": "no prices"}, RULE)
    assert s["available"] is False and "no prices" in s["reason"]
