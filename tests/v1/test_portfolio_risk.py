"""Portfolio analysis: optimisers against their two-asset closed forms, stress arithmetic by hand, and the
INSUFFICIENT_DATA paths. Synthetic weekly prices built in the tests."""
from __future__ import annotations

import json
import math
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path

import numpy as np
import pytest

from packages.analysis import portfolio_risk as pr

CFG = json.loads(Path("config/portfolio.json").read_text(encoding="utf-8"))
START = date(2024, 1, 5)          # a Friday


def _series(prices, volume=D(1000)):
    return [(START + timedelta(weeks=i), D(str(p)), volume) for i, p in enumerate(prices)]


def _wavy(n, base, amp, period, phase=0.0, drift=0.0):
    return [round(base * (1 + drift * i) * (1 + amp * math.sin(2 * math.pi * i / period + phase)), 2) for i in range(n)]


A = _wavy(120, 1000, 0.08, 9)
B = _wavy(120, 3000, 0.03, 13, phase=1.0)
HOLD = [{"security_id": "DSE:AAA", "quantity": D(100), "sector": "Banking", "currency": "TZS"},
        {"security_id": "DSE:BBB", "quantity": D(50), "sector": "Telecom", "currency": "TZS"}]
HIST = {"DSE:AAA": _series(A), "DSE:BBB": _series(B)}


def _run(**kw):
    return pr.analyse(HOLD, HIST, CFG, today=START + timedelta(weeks=120), **kw)


def test_value_weights_and_concentration_by_hand():
    out = _run()
    va, vb = D(100) * D(str(A[-1])), D(50) * D(str(B[-1]))
    assert out["market_value"] == va + vb
    assert out["weights"]["DSE:AAA"] == va / (va + vb)
    hhi = (va / (va + vb)) ** 2 + (vb / (va + vb)) ** 2
    assert out["concentration"]["herfindahl"] == hhi
    assert out["currency_exposure"] == {"TZS": D(1)}


def test_volatility_matches_numpy_on_the_same_weekly_values():
    out = _run()
    win_a, win_b = np.array(A[-(CFG["history_weeks"] + 1):]), np.array(B[-(CFG["history_weeks"] + 1):])
    value = 100 * win_a + 50 * win_b
    rets = value[1:] / value[:-1] - 1
    assert abs(float(out["risk"]["annualised_volatility"]) - np.std(rets, ddof=1) * math.sqrt(52)) < 1e-6
    peak = np.maximum.accumulate(value)
    assert abs(float(out["risk"]["max_drawdown"]) - (value / peak - 1).min()) < 1e-6


def test_optimisers_match_the_two_asset_closed_forms():
    out = _run()["optimisation"]
    ra = np.array(A[-(CFG["history_weeks"] + 1):]); rb = np.array(B[-(CFG["history_weeks"] + 1):])
    xa, xb = ra[1:] / ra[:-1] - 1, rb[1:] / rb[:-1] - 1
    s1, s2, rho = np.std(xa, ddof=1), np.std(xb, ddof=1), np.corrcoef(xa, xb)[0, 1]
    w1 = (s2 ** 2 - rho * s1 * s2) / (s1 ** 2 + s2 ** 2 - 2 * rho * s1 * s2)
    w1 = min(max(w1, 0.0), 1.0)
    assert abs(float(out["minimum_variance"]["weights"]["DSE:AAA"]) - w1) < 1e-5
    rp1 = (1 / s1) / (1 / s1 + 1 / s2)                 # two assets: risk parity is inverse volatility
    assert abs(float(out["risk_parity"]["weights"]["DSE:AAA"]) - rp1) < 1e-5
    assert out["minimum_variance"]["volatility"] <= out["current"]["volatility"]
    assert out["mean_variance"]["status"] == "INSUFFICIENT_DATA" and "expected returns" in out["mean_variance"]["reason"]


def _stress(out, sid):
    return next(s for s in out["stress_tests"] if s["name"] == next(x["name"] for x in CFG["stress_scenarios"] if x["id"] == sid))


def test_stress_arithmetic_by_hand():
    out = _run(inflation={"value": D("0.043"), "as_of": "2026-08", "source": "NBS"})
    total = out["market_value"]
    assert _stress(out, "equity_minus_20")["portfolio_effect"] == total * D("-0.2")
    banks = _stress(out, "banks_minus_30")
    assert banks["by_sector"] == {"Banking": D(100) * D(str(A[-1])) * D("-0.3"), "Telecom": D(0)}
    fx = _stress(out, "tzs_minus_20")
    assert abs(fx["portfolio_effect_pct"] - (D(1) / D("1.2") - 1)) < D("1e-20") and fx["measured_in"] == "USD"
    infl = _stress(out, "inflation_latest")
    assert abs(infl["portfolio_effect_pct"] - (D(1) / D("1.043") - 1)) < D("1e-20")
    for sid in ("rates_plus_200bp", "commodity_minus_30"):
        assert _stress(out, sid)["status"] == "INSUFFICIENT_DATA"


def test_the_historical_stress_finds_a_planted_crash():
    crash = list(A)
    for i in range(60, 73):
        crash[i] = round(crash[59] * (1 - 0.03 * (i - 59)), 2)      # 13 weeks down to 61% of the start
    out = pr.analyse(HOLD[:1], {"DSE:AAA": _series(crash)}, CFG, today=START + timedelta(weeks=120))
    worst = _stress(out, "worst_13_weeks")
    # Independent brute force over every 13-week window (the planted fall may not be the worst on its own:
    # starting a week earlier, at a peak of the wave, can fall further).
    expected, at = min((crash[i + 13] / crash[i] - 1, i) for i in range(len(crash) - 13))
    assert abs(float(worst["portfolio_effect_pct"]) - expected) < 1e-9
    assert expected <= crash[72] / crash[59] - 1
    assert str(START + timedelta(weeks=at)) in worst["how"]


def test_drift_and_whole_share_trades():
    out = _run(target_weights={"DSE:AAA": D("0.5"), "DSE:BBB": D("0.5")})
    rows = {r["security_id"]: r for r in out["drift"]["rows"]}
    total, pa = out["market_value"], D(str(A[-1]))
    expect = ((D("0.5") * total - D(100) * pa) / pa).to_integral_value(rounding="ROUND_DOWN")
    assert rows["DSE:AAA"]["trade_shares"] == expect
    assert "board lots" in out["drift"]["note"]


def test_too_little_common_history_is_insufficient_data():
    out = pr.analyse(HOLD, {"DSE:AAA": _series(A[:30]), "DSE:BBB": _series(B[:30])}, CFG)
    assert out["risk"]["status"] == "INSUFFICIENT_DATA" and out["optimisation"]["status"] == "INSUFFICIENT_DATA"
    assert out["stress_tests"][0]["available"]           # shocks on today's values still work


@pytest.mark.parametrize("holdings, history, status", [
    ([], {}, "NO_DATA"),
    ([HOLD[0]], {}, "INSUFFICIENT_DATA"),
])
def test_empty_and_unpriced_portfolios(holdings, history, status):
    assert pr.analyse(holdings, history, CFG)["status"] == status


def test_an_unpriced_holding_is_named_and_left_out():
    out = pr.analyse(HOLD, {"DSE:AAA": _series(A)}, CFG)
    assert out["status"] == "PARTIAL" and out["unpriced_holdings"] == ["DSE:BBB"]
    assert out["optimisation"]["status"] == "INSUFFICIENT_DATA"
