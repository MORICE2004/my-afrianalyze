"""Assemble the company report from stored, sourced data.

Every number in the returned payload is either a stored fact (with a source
reference) or computed here from stored facts (with its formula and inputs).
Anything that cannot be sourced is returned as {"available": false, "reason": ...}.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from packages.analysis import beta as beta_mod
from packages.analysis.bank_ratios import RATIO_LABELS, add_derived, compute_ratios
from packages.analysis.bank_valuation import base_drivers, run_scenarios, valuation_sensitivity
from packages.analysis.common import (
    BLOCKED,
    CONFLICTING_SOURCE,
    INSUFFICIENT_DATA,
    PARTIALLY_VERIFIED,
    STALE,
    VERIFIED,
    Unavailable,
)
from packages.analysis.cost_of_equity import cost_of_equity, cost_of_equity_grid
from packages.analysis.line_items import analyse_series
from packages.analysis.notes import line_note
from packages.analysis.recommendation import confidence, recommend
from packages.core.config import settings
from packages.database.models import (
    DataSourceStatus,
    ExtractionConflict,
    FinancialFact,
    MacroObservation,
    PriceBar,
    ReferenceInput,
    ResearchRun,
    RiskItem,
    Security,
    SourceDocument,
    ValidationCheck,
)
from pipelines.nmb.items import ALL_ITEMS, SECTIONS, NOTE_SECTIONS

DISCLAIMER = ("For research and education only. This is not investment advice, an offer, or a solicitation to "
              "buy or sell any security. Figures are extracted from the sources cited; check the source before "
              "relying on any number.")

STATEMENT_TITLES = {"IS": "Income statement", "BS": "Balance sheet", "CF": "Cash flow statement",
                    "NOTE": "Key notes"}
COMMON_SIZE_BASE = {"IS": ("operating_income_pre_impairment", "operating income before impairment"),
                    "BS": ("total_assets", "total assets")}

# Statement lines each ratio reads, and whether it also needs the prior year (averages).
EARNING_ASSET_ITEMS = ["loans_advances_net", "placements_banks", "inv_securities_amortised_cost",
                       "inv_securities_fvoci"]
RATIO_INPUTS: dict[str, tuple[list[str], bool]] = {
    "nim": (["net_interest_income"] + EARNING_ASSET_ITEMS, True),
    "cost_to_income": (["total_operating_expenses", "total_operating_income", "total_impairment"], False),
    "cost_of_risk": (["impairment_loans", "gross_loans"], True),
    "npl_ratio": (["stage3_gross_loans", "gross_loans"], False),
    "coverage": (["ecl_loans", "stage3_gross_loans"], False),
    "loan_to_deposit": (["loans_advances_net", "deposits_customers"], False),
    "roe": (["profit_attributable_owners", "equity_owners"], True),
    "roa": (["profit_for_year", "total_assets"], True),
    "car": (["total_regulatory_capital", "total_rwa"], False),
    "dividend_payout": (["dps", "eps"], False),
}


def fact_status(fact: FinancialFact) -> str:
    """VERIFIED when two independent extraction methods read the same value;
    PARTIALLY_VERIFIED when only one method read it (e.g. dividend per share from text)."""
    return VERIFIED if len(fact.agreed_by or []) >= 2 else PARTIALLY_VERIFIED


def _age_days(d: date) -> int:
    return (date.today() - d).days


def _iso(dt: datetime | date | None) -> str | None:
    """Stored times are UTC. SQLite drops the offset, so put it back before sending. Dates pass through."""
    if dt is None:
        return None
    if isinstance(dt, datetime) and dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _config(name: str) -> dict:
    return json.loads((settings.CONFIG_DIR / name).read_text(encoding="utf-8"))


def _doc_ref(doc: SourceDocument, page: int | None) -> dict:
    return {"document_id": doc.id, "title": doc.title, "page": page, "url": doc.url,
            "file_url": f"/api/v1/sources/{doc.id}/file" + (f"#page={page}" if page else ""),
            "sha256": doc.sha256, "retrieved_at": _iso(doc.retrieved_at)}


def build_report(session: Session, security_id: str) -> dict | None:
    sec = session.get(Security, security_id)
    if sec is None:
        return None
    val_cfg = _config("valuation.json")
    rec_cfg = _config("recommendation.json")
    gaps: list[str] = []

    docs = {d.id: d for d in session.query(SourceDocument).filter_by(security_id=security_id)}
    conflicts = session.query(ExtractionConflict).filter_by(security_id=security_id).all()
    conflict_map: dict[tuple[str, int], list[ExtractionConflict]] = {}
    for c in conflicts:
        conflict_map.setdefault((c.item_code, c.fiscal_year), []).append(c)
    # Figures that do not add up inside the source document: shown as CONFLICTING_SOURCE, never calculated with.
    source_issues = {(c.item_code, c.fiscal_year): c for c in conflicts if c.kind == "SOURCE_INCONSISTENCY"}

    fact_rows = session.query(FinancialFact).filter_by(security_id=security_id, is_primary=True).all()
    facts: dict[str, dict[int, Decimal]] = {}
    fact_ref: dict[tuple[str, int], FinancialFact] = {}
    for f in fact_rows:
        fact_ref[(f.item_code, f.fiscal_year)] = f
        if (f.item_code, f.fiscal_year) not in source_issues:
            facts.setdefault(f.item_code, {})[f.fiscal_year] = f.value
    derived = add_derived(facts)
    years = sorted({y for series in facts.values() for y in series})
    report_years = [y for y in years if y >= (max(years) - 4)] if years else []

    # ------------------------------------------------------------ statements
    statements = {}
    order = [(s.statement, s, i) for s in SECTIONS + NOTE_SECTIONS for i in s.items]
    order.append(("NOTE", None, None))  # dps
    for statement, section, spec in order:
        code = spec.code if spec else "dps"
        label = spec.label if spec else "Dividend per share (proposed for the year)"
        unit = spec.unit if spec else "TZS_per_share"
        series = {y: v for y, v in facts.get(code, {}).items() if y in report_years}
        cells = {}
        for y in report_years:
            ref = fact_ref.get((code, y))
            open_conf = [c for c in conflict_map.get((code, y), []) if c.kind != "RESTATEMENT"]
            restated = [c for c in conflict_map.get((code, y), []) if c.kind == "RESTATEMENT"]
            issue = source_issues.get((code, y))
            if issue is not None:
                cells[str(y)] = {"available": False, "status": CONFLICTING_SOURCE,
                                 "reason": "The source document does not add up: " + issue.detail,
                                 "source": _doc_ref(docs[issue.document_id], issue.page), "conflicts": [issue.id]}
                continue
            if ref is None:
                cells[str(y)] = {"available": False,
                                 "status": CONFLICTING_SOURCE if open_conf else INSUFFICIENT_DATA,
                                 "reason": ("Extraction conflict: " + open_conf[0].detail) if open_conf
                                 else "Not reported or not extracted for this year",
                                 "conflicts": [c.id for c in open_conf]}
                continue
            cells[str(y)] = {"available": True, "status": fact_status(ref), "value": ref.value,
                             "unit": ref.unit, "currency": ref.currency, "period_end": ref.period_end.isoformat(),
                             "label_as_reported": ref.label_as_reported,
                             "source": _doc_ref(docs[ref.document_id], ref.page),
                             "method": ref.extraction_method, "agreed_by": ref.agreed_by,
                             "column": ref.column_role,
                             "restated": [{"id": c.id, "detail": c.detail} for c in restated]}
        base = COMMON_SIZE_BASE.get(statement)
        analysis = analyse_series(series, {y: facts.get(base[0], {}).get(y) for y in report_years}
                                  if base else None, base[1] if base else "",
                                  history=facts.get(code, {})) if series else None
        note = line_note(facts, code, label, max(series)) if series else None
        statements.setdefault(statement, []).append({
            "item_code": code, "label": label, "unit": unit, "cells": cells, "analysis": analysis,
            "note": note, "section": section.code if section else "DPS"})

    for code, info in derived.items():
        series = {y: v for y, v in facts[code].items() if y in report_years}
        statements["IS"].append({
            "item_code": code, "label": info["label"], "unit": "TZS_millions", "derived": info["formula"],
            "cells": {str(y): ({"available": True, "value": series[y], "derived": info["formula"]}
                               if y in series else {"available": False, "reason": "Inputs not available"})
                      for y in report_years},
            "analysis": analyse_series(series, None, "", history=facts[code]) if series else None,
            "note": None, "section": "IS"})

    # ------------------------------------------------------------ ratios
    def ratio_status(code: str, year: int, result: dict) -> dict:
        items, needs_prior = RATIO_INPUTS[code]
        years_used = [year, year - 1] if needs_prior else [year]
        if not result["available"]:
            bad = [(i, yy) for i in items for yy in years_used if (i, yy) in source_issues]
            if bad:
                i, yy = bad[0]
                return {"status": CONFLICTING_SOURCE,
                        "reason": f"Input '{i}' for FY{yy} does not add up in the source document, so it is not "
                                  f"used. {source_issues[(i, yy)].detail}"}
            return {"status": INSUFFICIENT_DATA}
        statuses = {fact_status(fact_ref[(i, yy)]) for i in items for yy in years_used if (i, yy) in fact_ref}
        return {"status": VERIFIED if statuses == {VERIFIED} else PARTIALLY_VERIFIED}

    ratio_rows = []
    for code, label in RATIO_LABELS.items():
        values = {}
        for y in report_years:
            r = compute_ratios(facts, y)[code]
            values[str(y)] = r | ratio_status(code, y, r)
        ratio_rows.append({"code": code, "label": label, "values": values})

    # ------------------------------------------------------------ price
    price_bars = (session.query(PriceBar).filter_by(instrument_id=security_id)
                  .order_by(PriceBar.trade_date).all())
    if price_bars:
        last = price_bars[-1]
        pdoc = session.get(SourceDocument, last.source_document_id)
        price = {"available": True, "value": last.close, "trade_date": last.trade_date.isoformat(),
                 "currency": sec.currency, "source": _doc_ref(pdoc, None)}
    else:
        status = session.get(DataSourceStatus, "dse_prices")
        price = Unavailable("No licensed DSE price data loaded. " + (status.detail if status else ""),
                            BLOCKED).to_dict()
        gaps.append("Share price: DSE end-of-day data is licensed and has not been supplied.")

    # ------------------------------------------------------------ beta
    rule = val_cfg["beta_selection"]
    index_id = "DSE:DSEI"
    index_bars = session.query(PriceBar).filter_by(instrument_id=index_id).order_by(PriceBar.trade_date).all()
    if price_bars and index_bars:
        stock = {b.trade_date: b.close for b in price_bars}
        index = {b.trade_date: b.close for b in index_bars}
        vols = {b.trade_date: b.volume for b in price_bars}
        estimates = {
            "raw_daily": beta_mod.raw_daily(stock, index),
            "weekly": beta_mod.weekly(stock, index),
            "monthly": beta_mod.monthly(stock, index),
            "dimson": beta_mod.dimson(stock, index, rule.get("dimson_lags", 1)),
            "scholes_williams": beta_mod.scholes_williams(stock, index),
            "bottom_up": beta_mod.bottom_up([], None, None),
        }
        zero = beta_mod.zero_volume_share(vols, sorted(index))
        selected = beta_mod.select_beta(estimates, zero, rule)
    else:
        reason = "Needs licensed DSE daily prices for NMB and the DSE All Share Index (DSEI)."
        estimates = {m: Unavailable(reason, BLOCKED).to_dict() for m in
                     ("raw_daily", "weekly", "monthly", "dimson", "scholes_williams")}
        estimates["bottom_up"] = Unavailable(
            "Needs sourced prices for East African listed bank peers (also licensed data).", BLOCKED).to_dict()
        zero = Unavailable(reason, BLOCKED).to_dict()
        selected = Unavailable(reason, BLOCKED).to_dict()
        gaps.append("Beta: all five methods need licensed price data.")
    beta_block = {"benchmark": index_id, "estimates": estimates, "zero_volume": zero,
                  "selected": selected, "rule": rule}

    # ------------------------------------------------------------ cost of equity
    coe_cfg = val_cfg["cost_of_equity"]
    rf = (session.query(MacroObservation).filter_by(series_id=coe_cfg["risk_free_series"])
          .order_by(MacroObservation.observation_date.desc()).first())
    refs = {r.key: r for r in session.query(ReferenceInput)}

    max_age = val_cfg["input_max_age_days"]
    stale_inputs: list[str] = []

    def freshness(name: str, as_of: date, limit: int) -> str:
        if _age_days(as_of) > limit:
            stale_inputs.append(name)
            return STALE
        return VERIFIED

    def ref_input(key: str) -> dict | None:
        r = refs.get(key)
        return None if r is None else {"value": r.value, "label": r.label, "source_name": r.source_name,
                                       "source_url": r.source_url, "as_of": r.as_of.isoformat(),
                                       "age_days": _age_days(r.as_of),
                                       "status": freshness(key, r.as_of, max_age["reference"])}

    coe_inputs = {
        "risk_free": None if rf is None else {
            "value": rf.value, "label": rf.label, "source_name": rf.source_name, "source_url": rf.source_url,
            "as_of": rf.observation_date.isoformat(), "attributes": rf.attributes,
            "age_days": _age_days(rf.observation_date),
            "status": freshness("risk_free", rf.observation_date, max_age["risk_free"])},
        "default_spread": ref_input("TZ_DEFAULT_SPREAD"),
        "mature_erp": ref_input("MATURE_MARKET_ERP"),
        "country_risk_premium": ref_input("TZ_COUNTRY_RISK_PREMIUM"),
    }
    coe = cost_of_equity(coe_inputs, selected, coe_cfg)
    coe_grid = cost_of_equity_grid(coe_inputs, coe_cfg, coe_cfg["sensitivity_betas"])

    # ------------------------------------------------------------ valuation
    fact_years = sorted({y for series in facts.values() for y in series})
    if coe["available"]:
        valuation = run_scenarios(facts, fact_years, coe["value"], val_cfg)
    else:
        valuation = Unavailable("Cost of equity not available: " + coe["reason"],
                                coe.get("status", INSUFFICIENT_DATA)).to_dict()
        gaps.append("Valuation and target price: need a measured cost of equity (needs beta).")
    sensitivity = (valuation_sensitivity(facts, fact_years, coe_grid["rows"], val_cfg)
                   if coe_grid.get("available") else coe_grid)
    # The base-case drivers do not depend on the cost of equity, so show them regardless.
    drivers = base_drivers(facts, fact_years, val_cfg["history_window_years"])

    # ------------------------------------------------------------ recommendation
    recommendation = recommend(price, valuation, coe, rec_cfg, settings.SHOW_TRADE_LABELS)
    required = [code for code in ALL_ITEMS] + ["dps"]
    have = sum(1 for code in required for y in report_years if (code, y) in fact_ref)
    optional_absent = sum(1 for y in report_years if ("inv_securities_fvpl", y) not in fact_ref)
    completeness = have / max(1, len(required) * len(report_years) - optional_absent)
    open_conflicts = sum(1 for c in conflicts if c.status == "OPEN" and c.kind != "RESTATEMENT"
                         and c.fiscal_year in report_years)
    conf = confidence(min(1.0, completeness), open_conflicts,
                      selected | ({"r_squared": estimates.get(selected.get("method"), {}).get("r_squared")}
                                  if selected.get("available") else {}),
                      sorted(set(stale_inputs)), rec_cfg)

    # ------------------------------------------------------------ risks, sources, checks
    risks = [{"id": r.id, "category": r.category, "title": r.title, "quote": r.quote,
              "source": _doc_ref(docs[r.document_id], r.page)}
             for r in session.query(RiskItem).filter_by(security_id=security_id).order_by(RiskItem.id)]
    checks = [{"fiscal_year": c.fiscal_year, "name": c.check_name, "passed": c.passed,
               "detail": c.detail} for c in session.query(ValidationCheck).filter_by(security_id=security_id)
              .order_by(ValidationCheck.fiscal_year, ValidationCheck.id)]
    macro_sources = [{"series_id": m.series_id, "label": m.label, "value": m.value, "unit": m.unit,
                      "as_of": m.observation_date.isoformat(), "source_name": m.source_name,
                      "source_url": m.source_url, "retrieved_at": _iso(m.retrieved_at),
                      "attributes": m.attributes}
                     for m in session.query(MacroObservation).order_by(MacroObservation.series_id)]
    ref_sources = [{"key": r.key, "label": r.label, "value": r.value, "unit": r.unit, "as_of": r.as_of.isoformat(),
                    "source_name": r.source_name, "source_url": r.source_url} for r in refs.values()]

    run = (session.query(ResearchRun).filter(ResearchRun.security_id == security_id,
                                             ResearchRun.status != "superseded")
           .order_by(ResearchRun.created_at.desc()).first())
    review = ({"run_id": run.id, "status": run.status, "created_at": _iso(run.created_at),
               "reviewer": run.reviewer, "reviewed_at": _iso(run.reviewed_at),
               "data_sha256": run.data_sha256, "config_sha256": run.config_sha256}
              if run else {"run_id": None, "status": "none", "reviewer": None})
    annual = [d for d in docs.values() if d.kind == "annual_report"]
    latest_doc = max(annual, key=lambda d: d.fiscal_year or 0) if annual else None
    data_as_of = {
        "fiscal_year_end": f"{max(report_years)}-12-31" if report_years else None,
        "latest_report": latest_doc.title if latest_doc else None,
        "published_on": latest_doc.published_on.isoformat() if latest_doc and latest_doc.published_on else None,
        "retrieved_at": _iso(latest_doc.retrieved_at) if latest_doc else None,
    }
    counts = {"verified": 0, "partially_verified": 0, "conflicting_source": 0, "insufficient_data": 0}
    for rows in statements.values():
        for row in rows:
            for cell in row["cells"].values():
                key = cell.get("status", VERIFIED if cell.get("derived") else INSUFFICIENT_DATA).lower()
                if key in counts:
                    counts[key] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "disclaimer": DISCLAIMER,
        "review": review,
        "data_as_of": data_as_of,
        "status_counts": counts,
        "trade_labels_enabled": settings.SHOW_TRADE_LABELS,
        "security": {"id": sec.id, "name": sec.name, "exchange": sec.exchange, "ticker": sec.local_ticker,
                     "isin": sec.isin, "sector": sec.sector, "currency": sec.currency, "is_bank": sec.is_bank,
                     "industry_template": sec.industry_template, "listing_status": sec.listing_status,
                     "listing_url": sec.listing_url, "verified_at": _iso(sec.verified_at)},
        "header": {
            "price": price,
            "recommendation": recommendation,
            "target_price": ({"available": True, "value": valuation["target_price_12m"]}
                             if valuation.get("available")
                             else Unavailable(valuation["reason"], valuation.get("status", INSUFFICIENT_DATA)).to_dict()),
            "fair_value_range": (valuation["fair_value_range"] | {"available": True}
                                 if valuation.get("available")
                                 else Unavailable(valuation["reason"], valuation.get("status", INSUFFICIENT_DATA)).to_dict()),
            "confidence": conf,
        },
        "years": report_years,
        "statements": [{"code": k, "title": STATEMENT_TITLES[k], "rows": v} for k, v in statements.items()],
        "ratios": ratio_rows,
        "beta": beta_block,
        "cost_of_equity": {"inputs": coe_inputs, "method": coe_cfg, "result": coe, "sensitivity": coe_grid},
        "valuation": {"result": valuation, "sensitivity": sensitivity, "base_drivers": drivers,
                      "config": {k: val_cfg[k] for k in ("horizon_years", "history_window_years",
                                                         "terminal_growth", "method_weights", "scenarios")}},
        "recommendation_rule": rec_cfg,
        "peers": Unavailable("Peer P/E and P/B need sourced peer prices (licensed exchange data). "
                             "No peer data loaded.", BLOCKED).to_dict(),
        "risks": risks,
        "checks": checks,
        "conflicts": [{"id": c.id, "fiscal_year": c.fiscal_year, "item_code": c.item_code, "kind": c.kind,
                       "value_a": c.value_a, "source_a": c.source_a, "value_b": c.value_b,
                       "source_b": c.source_b, "detail": c.detail, "status": c.status,
                       "source": _doc_ref(docs[c.document_id], c.page) if c.document_id in docs else None}
                      for c in conflicts],
        "sources": {"documents": [_doc_ref(d, None) | {"kind": d.kind, "fiscal_year": d.fiscal_year,
                                                       "publisher": d.publisher, "listing_url": d.listing_url,
                                                       "published_on": d.published_on.isoformat()
                                                       if d.published_on else None,
                                                       "published_on_evidence": d.published_on_evidence,
                                                       "terms_note": d.terms_note}
                                  for d in sorted(docs.values(), key=lambda d: (d.kind, d.fiscal_year or 0))],
                    "macro": macro_sources, "reference": ref_sources},
        "gaps": gaps,
    }
