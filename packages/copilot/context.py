"""Turn a research run's report snapshot into the copilot's only knowledge: a list of keyed entries.

Every entry is one of
  SOURCE_FACT  a figure or quote read from a document, with its document and page
  CALCULATED   a result of the deterministic engines (ratios, valuation, cost of equity, technicals), with how
  STATUS       something that is not available, and why
and carries `display`, the exact text the copilot must use when it quotes the value. The model never sees
the database, the web or anything else, so it cannot cite what is not here; packages/copilot/grounding.py
checks that it did not try.
"""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation

STATEMENT_NAMES = {"IS": "income statement", "BS": "balance sheet", "CF": "cash flow statement", "NOTE": "notes"}


def _d(v) -> Decimal | None:
    try:
        return None if v is None else Decimal(str(v))
    except InvalidOperation:
        return None


def _money(v: Decimal, unit: str) -> str:
    if unit == "TZS_per_share":
        return f"TZS {v:,.2f} per share"
    if unit == "TZS_millions":
        return f"TZS {v:,.0f} million"
    return f"{v:,}"


def _pct(v: Decimal, places: int = 1) -> str:
    return f"{v * 100:.{places}f}%"


def _src(source: dict | None) -> str | None:
    if not source:
        return None
    page = f", page {source['page']}" if source.get("page") else ""
    return f"{source.get('title')}{page}"


def build_context(report: dict) -> dict:
    """Entries keyed and sorted, so the same run always yields byte-identical context (cacheable)."""
    entries: list[dict] = []

    def add(key, kind, label, display, value=None, period=None, source=None, how=None):
        entries.append({k: v for k, v in {"key": key, "kind": kind, "label": label, "display": display,
                                          "value": None if value is None else str(value), "period": period,
                                          "source": source, "how": how}.items() if v is not None})

    sec = report["security"]
    add("company", "SOURCE_FACT", "Company", f"{sec['name']} ({sec['id']}), {sec.get('sector')}, reports in {sec.get('currency')}")
    asof = report.get("data_as_of") or {}
    add("data_as_of", "SOURCE_FACT", "Latest accounts", f"Financial year ending {asof.get('fiscal_year_end')}; "
        f"{asof.get('latest_report')} published {asof.get('published_on')}")
    review = report.get("review") or {}
    add("review", "STATUS", "Review state", f"Research run {review.get('run_id')} is {review.get('status')}"
        + (f", approved by {review['reviewer']}" if review.get("reviewer") else ", not approved by a reviewer"))

    price = report["header"]["price"]
    if price.get("available"):
        add("price.last", "SOURCE_FACT", "Last close", f"TZS {_d(price['value']):,.2f}", price["value"],
            price.get("trade_date"), _src(price.get("source")), "End-of-day DSE close, not live")
    else:
        add("price.last", "STATUS", "Share price", "Not available: " + price.get("reason", ""))

    for st in report["statements"]:
        for row in st["rows"]:
            for year, cell in row["cells"].items():
                key = f"{st['code']}.{row['item_code']}.{year}"
                if cell.get("available") and _d(cell.get("value")) is not None:
                    kind = "CALCULATED" if cell.get("derived") else "SOURCE_FACT"
                    add(key, kind, f"{row['label']} ({STATEMENT_NAMES.get(st['code'], st['code'])})",
                        _money(_d(cell["value"]), row.get("unit") or cell.get("unit", "")), cell["value"], f"FY{year}",
                        _src(cell.get("source")), cell.get("derived"))

    for r in report["ratios"]:
        for year, v in r["values"].items():
            key = f"ratio.{r['code']}.{year}"
            if v.get("available"):
                add(key, "CALCULATED", r["label"], _pct(_d(v["value"])), v["value"], f"FY{year}", None, v.get("formula"))
            else:
                add(key, "STATUS", r["label"], f"Not calculated for FY{year}: {v.get('reason', 'inputs missing')}")

    coe = report["cost_of_equity"]
    if coe["result"].get("available"):
        add("coe.value", "CALCULATED", "Cost of equity (configured method)", _pct(_d(coe["result"]["value"]), 2),
            coe["result"]["value"], None, None, coe["result"].get("formula"))
        for step in coe["result"].get("steps") or []:
            ref = step.get("ref")
            inp = (coe.get("inputs") or {}).get(ref) if ref else None
            add(f"coe.step.{step['label']}", "SOURCE_FACT" if inp else "CALCULATED", step["label"],
                _pct(_d(step["value"]), 2) if "beta" not in step["label"] else f"{_d(step['value']):.3f}",
                step["value"], inp.get("as_of") if inp else None, inp.get("source_name") if inp else None)
    for i, alt in enumerate(coe.get("alternatives") or [], 1):
        if alt.get("cost_of_equity") is not None:
            add(f"coe.alternative.{i}", "CALCULATED", f"Cost of equity, {alt['treatment']}",
                f"{_pct(_d(alt['cost_of_equity']), 2)}; fair value TZS {_d(alt.get('fair_value') or 0):,.2f}; "
                f"model view {alt.get('model_view')}", alt["cost_of_equity"], None, None, alt.get("formula"))

    val = report["valuation"]["result"]
    if val.get("available"):
        add("valuation.fair_value", "CALCULATED", "Fair value per share", f"TZS {_d(val['fair_value']):,.2f}",
            val["fair_value"], None, None, "Probability-weighted residual income, justified P/B and dividend discount")
        add("valuation.target_12m", "CALCULATED", "12-month target price", f"TZS {_d(val['target_price_12m']):,.2f}",
            val["target_price_12m"], None, None, val.get("target_formula"))
        rng = val.get("fair_value_range") or {}
        if rng:
            add("valuation.range", "CALCULATED", "Fair value range (bear to bull)",
                f"TZS {_d(rng['low']):,.2f} to TZS {_d(rng['high']):,.2f}")
    else:
        add("valuation.fair_value", "STATUS", "Valuation", "Not available: " + val.get("reason", ""))
    for row in (report["valuation"].get("sensitivity") or {}).get("rows") or []:
        add(f"valuation.sensitivity.beta_{row['beta']}", "CALCULATED", f"Fair value if beta were {row['beta']}",
            f"cost of equity {_pct(_d(row['cost_of_equity']), 2)}, fair value TZS {_d(row['fair_value']):,.2f}",
            row["fair_value"])

    rec = report["header"]["recommendation"]
    if rec.get("available"):
        add("model_view", "CALCULATED", "Model view", rec["model_view"]
            + (f" ({rec['inconclusive_reason']})" if rec.get("inconclusive_reason") else "")
            + (f"; expected 12-month total return {_pct(_d(rec['expected_total_return']))}"
               if rec.get("expected_total_return") is not None else ""), None, None, None, rec.get("rule"))
    else:
        add("model_view", "STATUS", "Model view", "Not available: " + rec.get("reason", ""))

    tech = report.get("technical") or {}
    for name, ind in (tech.get("indicators") or {}).items():
        if ind.get("available"):
            shown = {k: v for k, v in ind.items() if k in ("value", "line", "signal", "lower", "upper", "high", "low",
                                                            "change", "price_vs", "zone", "line_vs_signal")}
            add(f"technical.{name}", "CALCULATED", f"Technical indicator {name}",
                "; ".join(f"{k} {(_d(v) if _d(v) is not None else v):.2f}" if _d(v) is not None else f"{k} {v}"
                          for k, v in shown.items()), None, ind.get("as_of"), None,
                f"{ind.get('formula')}; descriptive only, not part of the valuation")
        else:
            add(f"technical.{name}", "STATUS", f"Technical indicator {name}", "Not available: " + ind.get("reason", ""))

    for risk in report.get("risks") or []:
        add(f"risk.{risk['id']}", "SOURCE_FACT", f"Risk: {risk['title']} ({risk['category']})",
            f"\"{risk['quote']}\"", None, None, _src(risk.get("source")))

    for i, gap in enumerate(report.get("gaps") or [], 1):
        add(f"gap.{i}", "STATUS", "Known gap", gap)

    entries.sort(key=lambda e: e["key"])
    return {"security_id": sec["id"], "run_id": review.get("run_id"), "entries": entries}


def context_text(ctx: dict) -> str:
    """Deterministic serialisation (sorted keys, no timestamps) so the prompt-cache prefix is stable."""
    return json.dumps(ctx, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
