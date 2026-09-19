"""TZS cost of equity with hand-checked Decimal arithmetic."""
from decimal import Decimal as D

from packages.analysis.cost_of_equity import cost_of_equity, cost_of_equity_grid

INPUTS = {
    "risk_free": {"value": D("0.106924")},       # 10Y TZS bond, weighted average yield
    "default_spread": {"value": D("0.0383")},    # Tanzania sovereign default spread
    "mature_erp": {"value": D("0.0423")},
    "country_risk_premium": {"value": D("0.0583")},
}
METHOD = {"subtract_default_spread": True, "crp_scaling": "beta"}


def beta(b):
    return {"available": True, "beta": b, "method": "test"}


def test_beta_scaled_country_risk():
    # (0.106924 - 0.0383) + 1.0 x (0.0423 + 0.0583) = 0.068624 + 0.1006 = 0.169224
    assert cost_of_equity(INPUTS, beta(D("1.0")), METHOD)["value"] == D("0.169224")
    # beta 0.8: 0.068624 + 0.8 x 0.1006 = 0.068624 + 0.08048 = 0.149104
    assert cost_of_equity(INPUTS, beta(D("0.8")), METHOD)["value"] == D("0.149104")


def test_additive_country_risk_and_no_spread_subtraction():
    # additive: 0.068624 + 0.8 x 0.0423 + 0.0583 = 0.068624 + 0.03384 + 0.0583 = 0.160764
    r = cost_of_equity(INPUTS, beta(D("0.8")), METHOD | {"crp_scaling": "additive"})
    assert r["value"] == D("0.160764")
    # no spread subtraction: 0.106924 + 1.0 x 0.1006 = 0.207524
    r = cost_of_equity(INPUTS, beta(D("1.0")), {"subtract_default_spread": False, "crp_scaling": "beta"})
    assert r["value"] == D("0.207524")
    assert "default spread" not in r["formula"]


def test_float_beta_is_converted_exactly():
    # A float 0.8 from config must act as Decimal('0.8'), not 0.8000000000000000444...
    assert cost_of_equity(INPUTS, beta(0.8), METHOD)["value"] == D("0.149104")


def test_blocked_beta_passes_its_status_through():
    r = cost_of_equity(INPUTS, {"available": False, "reason": "no licensed prices", "status": "BLOCKED"}, METHOD)
    assert r["available"] is False and r["status"] == "BLOCKED" and "no licensed prices" in r["reason"]


def test_missing_input_is_named():
    r = cost_of_equity({k: v for k, v in INPUTS.items() if k != "country_risk_premium"}, beta(1), METHOD)
    assert r["available"] is False and "country_risk_premium" in r["reason"]


def test_sensitivity_grid():
    g = cost_of_equity_grid(INPUTS, METHOD, [0.6, 1.2])
    # 0.068624 + 0.6 x 0.1006 = 0.128984; 0.068624 + 1.2 x 0.1006 = 0.189344
    assert [r["cost_of_equity"] for r in g["rows"]] == [D("0.128984"), D("0.189344")]
