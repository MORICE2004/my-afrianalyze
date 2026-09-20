"""Bank valuation: projection, residual income, justified P/B, multi-stage DDM,
scenarios and the probability-weighted 12-month target.

All drivers are either computed from extracted history or are explicit
scenario shocks in config/valuation.json. Nothing is hardcoded here.
"""
from __future__ import annotations

from decimal import Decimal

from packages.analysis.bank_ratios import Facts, compute_ratios, get, mean_of_ratio
from packages.analysis.common import MILLION, ZERO, Unavailable, to_dec
from packages.analysis.line_items import cagr

DRIVERS = ("loan_growth", "nim", "cost_of_risk", "cost_to_income", "payout")


def base_drivers(facts: Facts, years: list[int], window: int) -> dict:
    """Base-case drivers derived from the last `window` years of extracted data."""
    last = max(years)
    out: dict[str, dict] = {}
    first = last - window
    g = cagr(get(facts, "loans_advances_net", first), get(facts, "loans_advances_net", last), window)
    out["loan_growth"] = g.to_dict() | {"basis": f"net loans CAGR {first}-{last}"}
    for key, ratio in (("nim", "nim"), ("cost_of_risk", "cost_of_risk"),
                       ("cost_to_income", "cost_to_income"), ("payout", "dividend_payout")):
        out[key] = mean_of_ratio(facts, years, ratio, window).to_dict() | {"basis": f"mean {ratio}, last {window} years"}
    return out


def base_year_structure(facts: Facts, year: int, share_factor: Decimal | int = 1) -> dict | Unavailable:
    """Ratios held constant in the projection, all from the base year's statements.

    `share_factor` is how many of today's shares one share of the base year has become, from
    `packages.analysis.corporate_actions`. It is 1 when there has been no split.
    """
    need = {k: get(facts, k, year) for k in (
        "loans_advances_net", "gross_loans", "placements_banks", "inv_securities_amortised_cost",
        "inv_securities_fvoci", "net_interest_income", "operating_income_pre_impairment",
        "profit_before_tax", "income_tax", "equity_owners", "eps", "profit_attributable_owners")}
    missing = [k for k, v in need.items() if v is None]
    if missing:
        return Unavailable(f"Base year {year} missing: {', '.join(missing)}")
    ea = (need["loans_advances_net"] + need["placements_banks"] + need["inv_securities_amortised_cost"]
          + need["inv_securities_fvoci"] + (get(facts, "inv_securities_fvpl", year) or ZERO))
    return {
        "year": year,
        "earning_assets_to_loans": ea / need["loans_advances_net"],
        "gross_to_net_loans": need["gross_loans"] / need["loans_advances_net"],
        "non_interest_to_nii": (need["operating_income_pre_impairment"] - need["net_interest_income"])
        / need["net_interest_income"],
        "effective_tax_rate": abs(need["income_tax"]) / need["profit_before_tax"],
        # Shares implied by profit / EPS (facts are TZS millions, EPS is TZS per share). The result is on
        # that year's share basis, so a split since then is applied to bring it onto today's basis;
        # otherwise a per-share fair value would be compared with a price that is not on the same footing.
        "shares": need["profit_attributable_owners"] * MILLION / need["eps"] * to_dec(share_factor),
        "share_factor": to_dec(share_factor),
        "loans": need["loans_advances_net"],
        "earning_assets": ea,
        "gross_loans": need["gross_loans"],
        "book_value": need["equity_owners"],
    }


def project(structure: dict, drivers: dict[str, Decimal], horizon: int) -> list[dict]:
    """Year-by-year projection in TZS millions."""
    rows = []
    loans, ea, gross, bv = (structure["loans"], structure["earning_assets"],
                            structure["gross_loans"], structure["book_value"])
    for t in range(1, horizon + 1):
        loans_t = loans * (1 + drivers["loan_growth"])
        ea_t = loans_t * structure["earning_assets_to_loans"]
        gross_t = loans_t * structure["gross_to_net_loans"]
        nii = drivers["nim"] * (ea + ea_t) / 2
        toi = nii * (1 + structure["non_interest_to_nii"])
        opex = drivers["cost_to_income"] * toi
        impairment = drivers["cost_of_risk"] * (gross + gross_t) / 2
        pbt = toi - opex - impairment
        ni = pbt * (1 - structure["effective_tax_rate"])
        div = ni * drivers["payout"]
        bv_t = bv + ni - div
        rows.append({
            "t": t, "year": structure["year"] + t, "loans": loans_t, "earning_assets": ea_t,
            "net_interest_income": nii, "total_operating_income": toi, "operating_expenses": opex,
            "impairment": impairment, "profit_before_tax": pbt, "net_income": ni, "dividends": div,
            "opening_book_value": bv, "closing_book_value": bv_t, "roe": ni / ((bv + bv_t) / 2),
            "eps": ni * MILLION / structure["shares"], "dps": div * MILLION / structure["shares"],
        })
        loans, ea, gross, bv = loans_t, ea_t, gross_t, bv_t
    return rows


def residual_income(structure: dict, rows: list[dict], coe: Decimal, g: Decimal) -> dict:
    if coe <= g:
        return Unavailable("Cost of equity must exceed terminal growth").to_dict()
    pv = ZERO
    steps = []
    for r in rows:
        ri = r["net_income"] - coe * r["opening_book_value"]
        disc = ri / (1 + coe) ** r["t"]
        pv += disc
        steps.append({"year": r["year"], "residual_income": ri, "pv": disc})
    last = rows[-1]
    terminal_ri = (last["net_income"] - coe * last["opening_book_value"]) * (1 + g)
    tv = terminal_ri / (coe - g)
    pv_tv = tv / (1 + coe) ** last["t"]
    equity = structure["book_value"] + pv + pv_tv
    return {"available": True, "equity_value": equity,
            "per_share": equity * MILLION / structure["shares"],
            "book_value": structure["book_value"], "pv_residual_income": pv,
            "pv_terminal": pv_tv, "terminal_share": pv_tv / equity if equity else None,
            "steps": steps,
            "formula": "BV0 + sum PV(NI_t - CoE x BV_(t-1)) + PV(RI_N x (1+g) / (CoE - g))"}


def justified_pb(structure: dict, roe: Decimal, coe: Decimal, g: Decimal) -> dict:
    if coe <= g:
        return Unavailable("Cost of equity must exceed terminal growth").to_dict()
    pb = (roe - g) / (coe - g)
    bvps = structure["book_value"] * MILLION / structure["shares"]
    return {"available": True, "pb": pb, "bvps": bvps, "per_share": pb * bvps,
            "inputs": {"sustainable_roe": roe, "cost_of_equity": coe, "growth": g},
            "formula": "P/B = (ROE - g) / (CoE - g); value = P/B x BVPS"}


def ddm(rows: list[dict], coe: Decimal, g: Decimal) -> dict:
    if coe <= g:
        return Unavailable("Cost of equity must exceed terminal growth").to_dict()
    pv = sum((r["dps"] / (1 + coe) ** r["t"] for r in rows), ZERO)
    last = rows[-1]
    tv = last["dps"] * (1 + g) / (coe - g)
    pv_tv = tv / (1 + coe) ** last["t"]
    return {"available": True, "per_share": pv + pv_tv, "pv_dividends": pv, "pv_terminal": pv_tv,
            "formula": f"sum PV(DPS_t) over {len(rows)} years + PV(DPS_N x (1+g) / (CoE - g))"}


def run_scenarios(facts: Facts, years: list[int], coe: Decimal, cfg: dict,
                  share_factor: Decimal | int = 1) -> dict:
    """Bear/base/bull valuation and the probability-weighted 12-month target.

    `share_factor` puts the base year's per-share figures on today's share basis after a split.
    """
    base = base_drivers(facts, years, cfg["history_window_years"])
    missing = [k for k in DRIVERS if not base[k]["available"]]
    if missing:
        return Unavailable("Base-case driver(s) not available: " + "; ".join(
            f"{k} ({base[k]['reason']})" for k in missing)).to_dict()
    structure = base_year_structure(facts, max(years), share_factor)
    if isinstance(structure, Unavailable):
        return structure.to_dict()

    coe = to_dec(coe)
    g = to_dec(cfg["terminal_growth"]["value"])
    if coe <= g:
        return Unavailable(f"Cost of equity {coe:.4f} must exceed terminal growth {g:.4f}; "
                           "the terminal value is undefined otherwise").to_dict()
    weights = {m: to_dec(w) for m, w in cfg["method_weights"].items()}
    if sum(weights.values(), ZERO) != 1:
        return Unavailable(f"Method weights sum to {sum(weights.values(), ZERO)}, not 1").to_dict()
    scenarios = {}
    for name, sc in cfg["scenarios"].items():
        drivers = {k: base[k]["value"] + to_dec(sc["shocks"].get(k, 0)) for k in DRIVERS}
        rows = project(structure, drivers, cfg["horizon_years"])
        sustainable = sum((r["roe"] for r in rows), ZERO) / len(rows)
        methods = {
            "residual_income": residual_income(structure, rows, coe, g),
            "justified_pb": justified_pb(structure, sustainable, coe, g),
            "ddm": ddm(rows, coe, g),
        }
        blended = sum((weights[m] * methods[m]["per_share"] for m in weights), ZERO)
        dps_next = rows[0]["dps"]
        target = blended * (1 + coe) - dps_next
        scenarios[name] = {"probability": to_dec(sc["probability"]), "drivers": drivers, "shocks": sc["shocks"],
                           "projection": rows, "methods": methods, "fair_value": blended,
                           "dps_next_12m": dps_next, "target_price_12m": target}

    prob_total = sum((s["probability"] for s in scenarios.values()), ZERO)
    if prob_total != 1:
        return Unavailable(f"Scenario probabilities sum to {prob_total}, not 1").to_dict()
    weighted_fv = sum((s["probability"] * s["fair_value"] for s in scenarios.values()), ZERO)
    weighted_tp = sum((s["probability"] * s["target_price_12m"] for s in scenarios.values()), ZERO)
    weighted_dps = sum((s["probability"] * s["dps_next_12m"] for s in scenarios.values()), ZERO)
    values = [s["fair_value"] for s in scenarios.values()]
    return {"available": True, "base_drivers": base, "structure": structure,
            "terminal_growth": cfg["terminal_growth"], "method_weights": weights,
            "scenarios": scenarios, "fair_value": weighted_fv,
            "fair_value_range": {"low": min(values), "high": max(values)},
            "target_price_12m": weighted_tp, "expected_dps_12m": weighted_dps,
            "target_formula": "sum over scenarios of p x (blended fair value x (1 + CoE) - next-year DPS)"}


def valuation_sensitivity(facts: Facts, years: list[int], coe_grid: list[dict], cfg: dict,
                          share_factor: Decimal | int = 1) -> dict:
    """Probability-weighted fair value for each cost of equity in the grid."""
    rows = []
    for point in coe_grid:
        res = run_scenarios(facts, years, to_dec(point["cost_of_equity"]), cfg, share_factor)
        if not res["available"]:
            return res
        rows.append({**point, "fair_value": res["fair_value"],
                     "range_low": res["fair_value_range"]["low"],
                     "range_high": res["fair_value_range"]["high"]})
    return {"available": True, "rows": rows}


__all__ = ["base_drivers", "run_scenarios", "valuation_sensitivity", "compute_ratios"]
