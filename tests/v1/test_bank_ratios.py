"""Bank ratios on a small hand-made bank. Every expected value is worked out in the comments."""
from decimal import Decimal as D

import pytest

from packages.analysis.bank_ratios import add_derived, compute_ratios, earning_assets
from packages.analysis.line_items import cagr, common_size, yoy_change


@pytest.fixture()
def facts():
    f = {
        "net_interest_income": {2025: D("110")},
        "loans_advances_net": {2024: D("800"), 2025: D("1000")},
        "placements_banks": {2024: D("50"), 2025: D("50")},
        "inv_securities_amortised_cost": {2024: D("100"), 2025: D("100")},
        "inv_securities_fvoci": {2024: D("50"), 2025: D("50")},
        "total_operating_expenses": {2025: D("-60")},
        "total_operating_income": {2025: D("130")},  # stated after impairment, as NMB does
        "total_impairment": {2025: D("-20")},
        "impairment_loans": {2025: D("-18")},
        "gross_loans": {2024: D("850"), 2025: D("1050")},
        "stage3_gross_loans": {2025: D("42")},
        "ecl_loans": {2025: D("-50")},
        "deposits_customers": {2025: D("1250")},
        "profit_attributable_owners": {2025: D("45")},
        "equity_owners": {2024: D("200"), 2025: D("250")},
        "profit_for_year": {2025: D("46")},
        "total_assets": {2024: D("1400"), 2025: D("1600")},
        "total_regulatory_capital": {2025: D("300")},
        "total_rwa": {2025: D("1200")},
        "dps": {2025: D("50")},
        "eps": {2025: D("150")},
    }
    add_derived(f)
    return f


def value(r: dict, code: str) -> D:
    assert r[code]["available"], r[code]
    assert isinstance(r[code]["value"], D), "ratios must stay Decimal"
    return r[code]["value"]


def test_operating_income_before_impairment_adds_the_charge_back(facts):
    # 130 stated after a charge of -20, so 150 before it.
    assert facts["operating_income_pre_impairment"][2025] == D("150")


def test_earning_assets_exclude_cash_and_treat_missing_fvpl_as_nil(facts):
    # 1000 + 50 + 100 + 50 = 1200 (no FVPL line reported).
    assert earning_assets(facts, 2025) == D("1200")


def test_ratios_match_hand_calculation(facts):
    r = compute_ratios(facts, 2025)
    # NIM: 110 / average earning assets ((1000 + 1200) / 2 = 1100) = 0.1
    assert value(r, "nim") == D("0.1")
    # Cost-to-income: 60 / 150 = 0.4
    assert value(r, "cost_to_income") == D("0.4")
    # Cost of risk: 18 / average gross loans ((850 + 1050) / 2 = 950) = 0.0189473...
    assert value(r, "cost_of_risk").quantize(D("0.000001")) == D("0.018947")
    # NPL: 42 / 1050 = 0.04
    assert value(r, "npl_ratio") == D("0.04")
    # Coverage: 50 / 42 = 1.190476...
    assert value(r, "coverage").quantize(D("0.000001")) == D("1.190476")
    # Loan-to-deposit: 1000 / 1250 = 0.8
    assert value(r, "loan_to_deposit") == D("0.8")
    # ROE: 45 / ((200 + 250) / 2 = 225) = 0.2
    assert value(r, "roe") == D("0.2")
    # ROA: 46 / ((1400 + 1600) / 2 = 1500) = 0.030666...
    assert value(r, "roa").quantize(D("0.000001")) == D("0.030667")
    # CAR: 300 / 1200 = 0.25
    assert value(r, "car") == D("0.25")
    # Payout: 50 / 150 = 0.333...
    assert value(r, "dividend_payout").quantize(D("0.0001")) == D("0.3333")


def test_ratio_needing_an_opening_balance_says_what_is_missing(facts):
    del facts["gross_loans"][2024]
    r = compute_ratios(facts, 2025)["cost_of_risk"]
    assert r["available"] is False
    assert "average_gross_loans" in r["reason"]
    assert "value" not in r


def test_zero_denominator_is_not_a_number(facts):
    facts["deposits_customers"][2025] = D("0")
    r = compute_ratios(facts, 2025)["loan_to_deposit"]
    assert r == {"available": False, "reason": "Denominator is zero", "status": "INSUFFICIENT_DATA"}


def test_line_item_helpers():
    # YoY: (120 - 100) / 100 = 0.2; a negative prior uses its size.
    assert yoy_change(D("120"), D("100")).value == D("0.2")
    assert yoy_change(D("-120"), D("-100")).value == D("-0.2")
    # CAGR over 2 years from 100 to 121: sqrt(1.21) - 1 = 0.1
    assert cagr(D("100"), D("121"), 2).value.quantize(D("0.000001")) == D("0.100000")
    # Common size: 25 / 200 = 0.125
    assert common_size(D("25"), D("200"), "total assets").value == D("0.125")
