"""Bank valuation methods on hand-made inputs (TZS millions; shares of 1,000,000 so per-share = millions)."""
from decimal import Decimal as D

import pytest

from packages.analysis.bank_valuation import ddm, justified_pb, project, residual_income

Q = D("0.000001")
STRUCT = {"year": 2025, "book_value": D("100"), "shares": D("1000000"), "loans": D("1000"),
          "earning_assets": D("1200"), "gross_loans": D("1050"), "earning_assets_to_loans": D("1.2"),
          "gross_to_net_loans": D("1.05"), "non_interest_to_nii": D("0.5"), "effective_tax_rate": D("0.3")}
ROWS = [  # two projection years
    {"t": 1, "year": 2026, "net_income": D("15"), "opening_book_value": D("100"), "dps": D("5")},
    {"t": 2, "year": 2027, "net_income": D("16.5"), "opening_book_value": D("110"), "dps": D("6")},
]


def test_projection_one_year_by_hand():
    drivers = {"loan_growth": D("0.1"), "nim": D("0.1"), "cost_of_risk": D("0.01"),
               "cost_to_income": D("0.4"), "payout": D("0.5")}
    r = project(STRUCT, drivers, 1)[0]
    # loans 1000 -> 1100; earning assets 1100 x 1.2 = 1320; gross 1100 x 1.05 = 1155
    assert (r["loans"], r["earning_assets"]) == (D("1100.0"), D("1320.00"))
    # NII = 0.1 x (1200 + 1320) / 2 = 126; income = 126 x 1.5 = 189; costs = 0.4 x 189 = 75.6
    assert r["net_interest_income"] == D("126") and r["total_operating_income"] == D("189")
    assert r["operating_expenses"] == D("75.6")
    # impairment = 0.01 x (1050 + 1155) / 2 = 11.025; PBT = 189 - 75.6 - 11.025 = 102.375
    assert r["impairment"] == D("11.025") and r["profit_before_tax"] == D("102.375")
    # NI = 102.375 x 0.7 = 71.6625; dividend = 35.83125; closing BV = 100 + 71.6625 - 35.83125 = 135.83125
    assert r["net_income"] == D("71.6625") and r["dividends"] == D("35.83125")
    assert r["closing_book_value"] == D("135.83125")


def test_residual_income_by_hand():
    # CoE 10%, g 5%. RI1 = 15 - 10 = 5 -> PV 4.545455; RI2 = 16.5 - 11 = 5.5 -> PV 4.545455.
    # Terminal RI = 5.5 x 1.05 = 5.775; TV = 5.775 / 0.05 = 115.5; PV = 115.5 / 1.21 = 95.454545.
    # Equity = 100 + 4.545455 + 4.545455 + 95.454545 = 204.545455 (per share, as shares = 1m).
    r = residual_income(STRUCT, ROWS, D("0.10"), D("0.05"))
    assert r["pv_residual_income"].quantize(Q) == D("9.090909")
    assert r["pv_terminal"].quantize(Q) == D("95.454545")
    assert r["per_share"].quantize(Q) == D("204.545455")


def test_justified_pb_by_hand():
    # (0.15 - 0.05) / (0.10 - 0.05) = 2.0 x BVPS 100 = 200
    r = justified_pb(STRUCT, D("0.15"), D("0.10"), D("0.05"))
    assert r["pb"] == D("2") and r["per_share"] == D("200")


def test_ddm_by_hand():
    # PV = 5 / 1.1 + 6 / 1.21 = 4.545455 + 4.958678 = 9.504132
    # TV = 6 x 1.05 / 0.05 = 126; PV = 126 / 1.21 = 104.132231; total 113.636364
    r = ddm(ROWS, D("0.10"), D("0.05"))
    assert r["pv_dividends"].quantize(Q) == D("9.504132")
    assert r["per_share"].quantize(Q) == D("113.636364")


@pytest.mark.parametrize("fn", [lambda c, g: residual_income(STRUCT, ROWS, c, g),
                                lambda c, g: justified_pb(STRUCT, D("0.15"), c, g),
                                lambda c, g: ddm(ROWS, c, g)])
def test_growth_at_or_above_cost_of_equity_is_refused(fn):
    for coe in (D("0.05"), D("0.04")):
        r = fn(coe, D("0.05"))
        assert r["available"] is False and "must exceed terminal growth" in r["reason"]
