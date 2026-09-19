"""Cost of equity in local currency (TZS).

Method (Damodaran, local-currency version):
  1. The TZS government bond yield contains Tanzania's default risk. Subtract the
     sovereign default spread to get a default-free TZS risk-free rate
     (switch: subtract_default_spread).
  2. Total equity risk premium = mature-market ERP + Tanzania country risk premium.
  3. crp_scaling = "beta":    CoE = rf + beta * (mature ERP + CRP)
     crp_scaling = "additive": CoE = rf + beta * mature ERP + CRP
"""
from __future__ import annotations

from packages.analysis.common import BLOCKED, ZERO, Unavailable, to_dec


def cost_of_equity(inputs: dict, beta: dict, method: dict) -> dict:
    """inputs: {"risk_free": {...value, source...}, "mature_erp": {...}, "country_risk_premium": {...},
    "default_spread": {...}} each with at least "value"; beta: output of select_beta."""
    missing = [k for k in ("risk_free", "mature_erp", "country_risk_premium") if not inputs.get(k)]
    if method.get("subtract_default_spread") and not inputs.get("default_spread"):
        missing.append("default_spread")
    if missing:
        return Unavailable(f"Missing sourced input: {', '.join(missing)}").to_dict()
    if not beta.get("available"):
        return Unavailable("Beta not available: " + beta.get("reason", ""),
                           beta.get("status", BLOCKED)).to_dict()

    rf_local = to_dec(inputs["risk_free"]["value"])
    spread = to_dec(inputs["default_spread"]["value"]) if method.get("subtract_default_spread") else ZERO
    rf = rf_local - spread
    erp = to_dec(inputs["mature_erp"]["value"])
    crp = to_dec(inputs["country_risk_premium"]["value"])
    b = to_dec(beta["beta"])
    if method.get("crp_scaling", "beta") == "beta":
        coe = rf + b * (erp + crp)
        formula = "(rf_TZS - default spread) + beta x (mature ERP + CRP)"
    else:
        coe = rf + b * erp + crp
        formula = "(rf_TZS - default spread) + beta x mature ERP + CRP"
    if not method.get("subtract_default_spread"):
        formula = formula.replace("(rf_TZS - default spread)", "rf_TZS")
    return {
        "available": True,
        "value": coe,
        "formula": formula,
        "steps": [
            {"label": "TZS government bond yield", "value": rf_local, "ref": "risk_free"},
            {"label": "less sovereign default spread", "value": -spread, "ref": "default_spread"},
            {"label": "TZS risk-free rate", "value": rf},
            {"label": "mature-market ERP", "value": erp, "ref": "mature_erp"},
            {"label": "Tanzania country risk premium", "value": crp, "ref": "country_risk_premium"},
            {"label": f"beta ({beta['method']})", "value": b},
            {"label": "cost of equity", "value": coe},
        ],
    }


def cost_of_equity_grid(inputs: dict, method: dict, betas: list[float]) -> dict:
    """Cost of equity for a list of beta values. Used as a sensitivity when beta
    itself cannot be measured; it never replaces the measured beta."""
    rows = []
    for b in betas:
        res = cost_of_equity(inputs, {"available": True, "beta": b, "method": "sensitivity input"}, method)
        if not res["available"]:
            return res
        rows.append({"beta": to_dec(b), "cost_of_equity": res["value"]})
    return {"available": True, "rows": rows}
