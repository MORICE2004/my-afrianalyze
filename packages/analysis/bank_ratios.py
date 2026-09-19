"""Bank ratios computed from extracted statement lines.

Averages use the opening and closing balance of the year. A ratio that needs an
opening balance is unavailable for a year whose prior-year balance was not
extracted.
"""
from __future__ import annotations

from decimal import Decimal

from packages.analysis.common import ZERO, Computed, Result, Unavailable, safe_div

Facts = dict[str, dict[int, Decimal]]  # item_code -> {fiscal_year: value}


def get(facts: Facts, item: str, year: int) -> Decimal | None:
    return facts.get(item, {}).get(year)


def average(facts: Facts, item: str, year: int) -> Decimal | None:
    close, opening = get(facts, item, year), get(facts, item, year - 1)
    if close is None or opening is None:
        return None
    return (close + opening) / 2


def earning_assets(facts: Facts, year: int) -> Decimal | None:
    """Net loans to customers + placements with banks + investment securities at
    amortised cost and FVOCI (+ FVPL where reported). Cash and balances with the
    Bank of Tanzania are excluded because statutory reserves do not earn interest."""
    parts = [
        get(facts, "loans_advances_net", year),
        get(facts, "placements_banks", year),
        get(facts, "inv_securities_amortised_cost", year),
        get(facts, "inv_securities_fvoci", year),
    ]
    if any(p is None for p in parts):
        return None
    # A year with no FVPL line reported holds none; that is a reported nil, not a gap.
    return sum(parts, ZERO) + (get(facts, "inv_securities_fvpl", year) or ZERO)  # type: ignore[arg-type]


def _abs(v: Decimal | None) -> Decimal | None:
    return None if v is None else abs(v)


def add_derived(facts: Facts) -> dict[str, dict]:
    """Add derived lines in place and return how each was derived.

    operating_income_pre_impairment: NMB's 'total operating income' is stated after
    impairment charges, so the charge is added back for cost-to-income.
    """
    derived: dict[str, dict] = {}
    toi, imp = facts.get("total_operating_income", {}), facts.get("total_impairment", {})
    pre = {y: toi[y] - imp[y] for y in toi if y in imp}
    if pre:
        facts["operating_income_pre_impairment"] = pre
        derived["operating_income_pre_impairment"] = {
            "label": "Operating income before impairment",
            "formula": "total operating income - total impairment charge (charge is negative)"}
    return derived


def compute_ratios(facts: Facts, year: int) -> dict[str, dict]:
    def g(item: str) -> Decimal | None:
        return get(facts, item, year)

    ea_close, ea_open = earning_assets(facts, year), earning_assets(facts, year - 1)
    avg_ea = None if ea_close is None or ea_open is None else (ea_close + ea_open) / 2
    avg_gross = average(facts, "gross_loans", year)
    avg_equity = average(facts, "equity_owners", year)
    avg_assets = average(facts, "total_assets", year)

    out: dict[str, Result] = {
        "nim": safe_div(g("net_interest_income"), avg_ea,
                        "net interest income / average earning assets",
                        {"net_interest_income": g("net_interest_income"), "average_earning_assets": avg_ea}),
        "cost_to_income": safe_div(_abs(g("total_operating_expenses")), g("operating_income_pre_impairment"),
                                   "total operating expenses / operating income before impairment",
                                   {"total_operating_expenses": g("total_operating_expenses"),
                                    "operating_income_pre_impairment": g("operating_income_pre_impairment")}),
        "cost_of_risk": safe_div(_abs(g("impairment_loans")), avg_gross,
                                 "loan impairment charge / average gross loans",
                                 {"impairment_loans": g("impairment_loans"), "average_gross_loans": avg_gross}),
        "npl_ratio": safe_div(g("stage3_gross_loans"), g("gross_loans"),
                              "stage 3 gross loans / gross loans",
                              {"stage3_gross_loans": g("stage3_gross_loans"), "gross_loans": g("gross_loans")}),
        "coverage": safe_div(_abs(g("ecl_loans")), g("stage3_gross_loans"),
                             "total loan ECL allowance / stage 3 gross loans",
                             {"ecl_loans": g("ecl_loans"), "stage3_gross_loans": g("stage3_gross_loans")}),
        "loan_to_deposit": safe_div(g("loans_advances_net"), g("deposits_customers"),
                                    "net loans to customers / customer deposits",
                                    {"loans_advances_net": g("loans_advances_net"),
                                     "deposits_customers": g("deposits_customers")}),
        "roe": safe_div(g("profit_attributable_owners"), avg_equity,
                        "profit attributable to owners / average equity attributable to owners",
                        {"profit_attributable_owners": g("profit_attributable_owners"),
                         "average_equity_owners": avg_equity}),
        "roa": safe_div(g("profit_for_year"), avg_assets,
                        "profit for the year / average total assets",
                        {"profit_for_year": g("profit_for_year"), "average_total_assets": avg_assets}),
        "car": safe_div(g("total_regulatory_capital"), g("total_rwa"),
                        "total regulatory capital / total risk-weighted assets (bank basis)",
                        {"total_regulatory_capital": g("total_regulatory_capital"),
                         "total_rwa": g("total_rwa")}),
        "dividend_payout": safe_div(g("dps"), g("eps"),
                                    "dividend per share declared out of the year's profit / basic EPS",
                                    {"dps": g("dps"), "eps": g("eps")}),
    }
    return {k: v.to_dict() for k, v in out.items()}


RATIO_LABELS = {
    "nim": "Net interest margin",
    "cost_to_income": "Cost-to-income",
    "cost_of_risk": "Cost of risk",
    "npl_ratio": "NPL ratio (stage 3)",
    "coverage": "NPL coverage",
    "loan_to_deposit": "Loan-to-deposit",
    "roe": "Return on equity",
    "roa": "Return on assets",
    "car": "Capital adequacy (total capital)",
    "dividend_payout": "Dividend payout",
}


def mean_of_ratio(facts: Facts, years: list[int], ratio: str, window: int) -> Result:
    """Mean of a ratio over the most recent `window` years that have it."""
    found: list[tuple[int, float]] = []
    for y in sorted(years, reverse=True):
        r = compute_ratios(facts, y)[ratio]
        if r["available"]:
            found.append((y, r["value"]))
        if len(found) == window:
            break
    if len(found) < window:
        return Unavailable(f"Need {window} years of {ratio}, have {len(found)}")
    return Computed(sum((v for _, v in found), ZERO) / window, f"mean {ratio} over {window} years",
                    {f"{ratio}_{y}": v for y, v in found})
