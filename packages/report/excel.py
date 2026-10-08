"""The analyst workbook: the company report as an Excel file (a Pro feature; apps/api/main.py checks the
entitlement before calling this).

Every value is copied from the report payload that the website and the PDF show (packages/report/builder.py,
or in production the published run's frozen snapshot). Nothing is computed here except layout, and no model
writes any of it. A figure the report marks unavailable is written as its status word (for example
INSUFFICIENT_DATA) in grey, never as a number or a zero.

Thirteen sheets: Executive Summary, Company Profile, Income Statement, Balance Sheet, Cash Flow, Financial
Ratios, Bank Metrics, Valuation, Valuation Assumptions, Sensitivity Analysis, Technical Analysis, Risk Analysis,
Sources & Evidence. Values are written as numbers with number formats, so they can be used in formulas; units are
stated in each sheet's header and column. Excel itself holds about 15 significant digits, so a computed value such
as a fair value of 2,354.0703254748237543 TZS is stored as 2,354.07032547482; every statement figure (whole
millions) is exact. The full-precision values stay in the AfriEdge report and its frozen snapshot.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

INK = "111111"
MUTED = "6B6B6B"
HEADER_FILL = PatternFill("solid", fgColor="1F1F1F")
LATEST_FILL = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="D9D9D9")
FMT_MILLIONS = '#,##0;(#,##0);"-"'
FMT_PER_SHARE = '#,##0.00;(#,##0.00)'
FMT_PCT = '0.0%;-0.0%'
FMT_PCT2 = '0.00%;-0.00%'
FMT_NUM = '#,##0.000'

FINANCIAL_RATIOS = ("roe", "roa", "loan_to_deposit", "dividend_payout")
BANK_METRICS = ("nim", "cost_to_income", "cost_of_risk", "npl_ratio", "coverage", "car")


def _num(v) -> Decimal | None:
    """Decimal from a Decimal, int, float or an exact decimal string (the frozen snapshot stores strings)."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, Decimal):
        return v
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError):
        return None


def _status_word(d: dict | None) -> str:
    if not d:
        return "NOT AVAILABLE"
    return str(d.get("status") or "INSUFFICIENT_DATA").replace("_", " ")


class Sheet:
    """A worksheet with the house style: a title block, then a table."""

    def __init__(self, wb: Workbook, title: str, report: dict, subtitle: str):
        self.ws = wb.create_sheet(title)
        sec = report["security"]
        self.ws["A1"] = f"{sec['name']} ({sec['id']})"
        self.ws["A1"].font = Font(bold=True, size=14, color=INK)
        self.ws["A2"] = subtitle
        self.ws["A2"].font = Font(size=10, color=MUTED)
        self.row = 4
        self.ws.sheet_view.showGridLines = False

    def header(self, cells: list[str], freeze: bool = True) -> None:
        for i, text in enumerate(cells, start=1):
            c = self.ws.cell(row=self.row, column=i, value=text)
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = HEADER_FILL
            c.alignment = Alignment(horizontal="left" if i == 1 else "right", vertical="center", wrap_text=True)
        if freeze:
            self.ws.freeze_panes = self.ws.cell(row=self.row + 1, column=2)
        self.row += 1

    def line(self, cells: list, formats: list[str | None] | None = None, bold: bool = False,
             fill: PatternFill | None = None, wrap_first: bool = False) -> None:
        for i, value in enumerate(cells, start=1):
            unavailable = isinstance(value, _Missing)
            c = self.ws.cell(row=self.row, column=i, value=value.word if unavailable else value)
            c.border = Border(bottom=THIN)
            if unavailable:
                c.font = Font(italic=True, color=MUTED, size=9)
                c.alignment = Alignment(horizontal="right")
            else:
                c.font = Font(bold=bold, color=INK)
                if formats and i - 1 < len(formats) and formats[i - 1] and isinstance(value, (int, float, Decimal)):
                    c.number_format = formats[i - 1]
                    c.alignment = Alignment(horizontal="right")
                elif i == 1 or isinstance(value, str):
                    c.alignment = Alignment(wrap_text=wrap_first and i == 1, vertical="top")
            if fill is not None:
                c.fill = fill
        self.row += 1

    def note(self, text: str) -> None:
        c = self.ws.cell(row=self.row, column=1, value=text)
        c.font = Font(size=9, color=MUTED, italic=True)
        self.row += 1

    def gap(self) -> None:
        self.row += 1

    def section(self, text: str) -> None:
        c = self.ws.cell(row=self.row, column=1, value=text)
        c.font = Font(bold=True, size=11, color=INK)
        self.row += 1

    def widths(self, widths: list[int]) -> None:
        for i, w in enumerate(widths, start=1):
            self.ws.column_dimensions[get_column_letter(i)].width = w


class _Missing:
    def __init__(self, word: str):
        self.word = word


def _value_or_status(d: dict | None):
    if d and d.get("available"):
        v = _num(d.get("value"))
        return v if v is not None else _Missing("NOT AVAILABLE")
    return _Missing(_status_word(d))


def _fmt_for_unit(unit: str) -> str:
    return FMT_PER_SHARE if unit == "TZS_per_share" else FMT_PCT if unit in ("percent", "ratio") else FMT_MILLIONS


def build_workbook(report: dict, generated_for: str | None = None) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    sec, header = report["security"], report["header"]
    years = [str(y) for y in report["years"]]
    latest = years[-1] if years else None
    cur = sec["currency"]

    # 1 ---------------------------------------------------------------- Executive Summary
    s = Sheet(wb, "Executive Summary", report,
              f"AfriEdge analyst workbook. Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC from the report "
              f"built {report['generated_at']}. Currency {cur}.")
    rec, price = header["recommendation"], header["price"]
    s.header(["Item", "Value", "Note"], freeze=False)
    s.line(["Price", _value_or_status(price), f"Close on {price.get('trade_date')} (end of day)" if price.get("available")
            else price.get("reason", "")], [None, FMT_PER_SHARE])
    fv = report["valuation"]["result"]
    s.line(["Fair value (per share)", _num(fv.get("fair_value")) if fv.get("available") else _Missing(_status_word(fv)),
            "Probability-weighted across the bear, base and bull scenarios"], [None, FMT_PER_SHARE])
    s.line(["12-month target price", _value_or_status(header["target_price"]), ""], [None, FMT_PER_SHARE])
    rng = header["fair_value_range"]
    s.line(["Fair value range, low", _num(rng.get("low")) if rng.get("available") else _Missing(_status_word(rng)), ""],
           [None, FMT_PER_SHARE])
    s.line(["Fair value range, high", _num(rng.get("high")) if rng.get("available") else _Missing(_status_word(rng)), ""],
           [None, FMT_PER_SHARE])
    if rec.get("available"):
        s.line(["Price upside to target", _num(rec.get("price_upside")), ""], [None, FMT_PCT])
        s.line(["Expected total return", _num(rec.get("expected_total_return")), "Price upside plus dividend yield"],
               [None, FMT_PCT])
        s.line(["Model view", rec.get("model_view"), rec.get("inconclusive_reason") or rec.get("rule", "")])
        if rec.get("trade_label"):
            s.line(["AfriEdge view", rec["trade_label"], "Shown only when the view holds under every cost-of-equity "
                                                        "treatment"])
    else:
        s.line(["Model view", _Missing(_status_word(rec)), rec.get("reason", "")])
    conf = header["confidence"]
    s.line(["Data confidence", f"{conf['level']} ({_num(conf['score'])}/100)", "; ".join(conf.get("notes", []))])
    review = report.get("review", {})
    s.line(["Review", str(review.get("status", "")).replace("_", " "),
            (f"Approved by {review.get('reviewer')} on {review.get('reviewed_at')}" if review.get("status") == "published"
             else "Draft, not reviewed: do not rely on it or share it as research.")])
    s.gap()
    s.note(report["disclaimer"])
    if generated_for:
        s.note(f"Exported for {generated_for}.")
    s.widths([30, 22, 90])

    # 2 ---------------------------------------------------------------- Company Profile
    s = Sheet(wb, "Company Profile", report, "From the AfriEdge security master and the latest annual report.")
    s.header(["Field", "Value"], freeze=False)
    as_of = report["data_as_of"]
    for label, value in (("Name", sec["name"]), ("Ticker", sec.get("ticker") or sec["id"].split(":")[-1]),
                         ("AfriEdge id", sec["id"]), ("Exchange", sec["exchange"]), ("Currency", cur),
                         ("ISIN", sec.get("isin") or "Not published by the exchange"), ("Sector", sec.get("sector")),
                         ("Listing page", sec.get("listing_url")), ("Ticker verified on", sec.get("verified_at")),
                         ("Latest financial year end", as_of.get("fiscal_year_end")),
                         ("Latest annual report", as_of.get("latest_report")),
                         ("Published on", as_of.get("published_on")),
                         ("Capital adequacy basis", report.get("capital_basis") or "Not applicable"),
                         ("Fiscal years covered", ", ".join(years))):
        s.line([label, value])
    s.widths([30, 90])

    # 3-5 ------------------------------------------------------------- Statements
    titles = {"IS": "Income Statement", "BS": "Balance Sheet", "CF": "Cash Flow"}
    for st in report["statements"]:
        if st["code"] not in titles:
            continue
        s = Sheet(wb, titles[st["code"]], report,
                  f"{st['title']}. {cur} millions unless the line says otherwise. Each figure's source page is in "
                  f"Sources & Evidence. Latest year shaded.")
        s.header(["Line item", "Unit", *[f"FY{y}" for y in years], "Status (latest year)"])
        for row in st["rows"]:
            cells = [row["cells"].get(y) for y in years]
            vals = [(_num(c.get("value")) if c and c.get("available") else _Missing(_status_word(c))) for c in cells]
            unit = "per share" if row["unit"] == "TZS_per_share" else f"{cur} m" if row["unit"] == "TZS_millions" else row["unit"]
            last = row["cells"].get(latest) if latest else None
            fmt = _fmt_for_unit(row["unit"])
            s.line([row["label"], unit, *vals, _status_word(last) if last else ""],
                   [None, None, *[fmt] * len(years)])
            if latest:
                s.ws.cell(row=s.row - 1, column=2 + len(years)).fill = LATEST_FILL
        s.gap()
        s.note("VERIFIED: two independent readers of the PDF agree. PARTIALLY VERIFIED: one reader. "
               "CONFLICTING SOURCE: the figures do not add up inside the source document; not used in any calculation.")
        s.widths([46, 12, *[14] * len(years), 22])

    # 6-7 ------------------------------------------------------------- Ratios
    ratios = {r["code"]: r for r in report["ratios"]}
    for title, codes in (("Financial Ratios", FINANCIAL_RATIOS), ("Bank Metrics", BANK_METRICS)):
        s = Sheet(wb, title, report, "Computed by AfriEdge from the statement figures. Averages use opening and "
                                     "closing balances. The formula of each ratio is in the last column.")
        s.header(["Ratio", *[f"FY{y}" for y in years], "Formula"])
        for code in codes:
            r = ratios.get(code)
            if r is None:
                continue
            vals = [_value_or_status(r["values"].get(y)) for y in years]
            formula = next((v.get("formula") for v in r["values"].values() if v.get("available")), "")
            s.line([r["label"], *vals, formula], [None, *[FMT_PCT] * len(years)])
        s.widths([34, *[12] * len(years), 70])

    # 8 ---------------------------------------------------------------- Valuation
    s = Sheet(wb, "Valuation", report, f"Per-share values in {cur}. Three scenarios weighted by probability.")
    if fv.get("available") and fv.get("scenarios"):
        names = list(fv["scenarios"])
        s.header(["Item", *[n.capitalize() for n in names]])
        sc = fv["scenarios"]
        s.line(["Probability", *[_num(sc[n]["probability"]) for n in names]], [None, *[FMT_PCT] * len(names)])
        weights = report["valuation"]["config"]["method_weights"]
        method_labels = {"residual_income": "Residual income", "justified_pb": "Justified P/B", "ddm": "Dividend discount"}
        for m, label in method_labels.items():
            vals = []
            for n in names:
                md = sc[n]["methods"].get(m, {})
                vals.append(_num(md.get("per_share")) if md.get("available") else _Missing(_status_word(md)))
            s.line([f"{label} (weight {_num(weights.get(m, 0)):.0%})", *vals], [None, *[FMT_PER_SHARE] * len(names)])
        s.line(["Fair value", *[_num(sc[n]["fair_value"]) for n in names]], [None, *[FMT_PER_SHARE] * len(names)], bold=True)
        s.line(["12-month target", *[_num(sc[n]["target_price_12m"]) for n in names]], [None, *[FMT_PER_SHARE] * len(names)])
        s.line(["Dividend next 12 months", *[_num(sc[n]["dps_next_12m"]) for n in names]], [None, *[FMT_PER_SHARE] * len(names)])
        s.gap()
        s.line(["Probability-weighted fair value", _num(fv.get("fair_value"))], [None, FMT_PER_SHARE], bold=True)
        s.line(["Probability-weighted 12-month target", _num(fv.get("target_price_12m"))], [None, FMT_PER_SHARE])
        if fv.get("target_formula"):
            s.note(f"Target: {fv['target_formula']}")
    else:
        s.header(["Item", "Value"], freeze=False)
        s.line(["Valuation", _Missing(_status_word(fv)), fv.get("reason", "")])
    s.widths([40, 16, 16, 16])

    # 9 ---------------------------------------------------------------- Valuation Assumptions
    coe = report["cost_of_equity"]
    s = Sheet(wb, "Valuation Assumptions", report, "Inputs to the cost of equity and the forecast, each with its source.")
    s.header(["Input", "Value", "Source", "As of", "Status"], freeze=False)
    for key, inp in coe["inputs"].items():
        if not inp:
            s.line([key.replace("_", " "), _Missing("NOT AVAILABLE"), "", "", ""])
            continue
        s.line([inp.get("label") or key, _num(inp.get("value")), f"{inp.get('source_name', '')} {inp.get('source_url', '')}".strip(),
                inp.get("as_of"), str(inp.get("status") or "VERIFIED").replace("_", " ")], [None, FMT_PCT2])
    beta = report["beta"]["selected"]
    s.line(["Beta used", _num(beta.get("beta")) if beta.get("available") else _Missing(_status_word(beta)),
            beta.get("reason", ""), "", ""], [None, FMT_NUM])
    res = coe["result"]
    s.line(["Cost of equity", _num(res.get("value")) if res.get("available") else _Missing(_status_word(res)),
            res.get("formula", res.get("reason", "")), "", ""], [None, FMT_PCT2], bold=True)
    s.gap()
    s.section("Forecast drivers (base case)")
    s.header(["Driver", "Value", "Basis", "Formula", ""], freeze=False)
    for name, d in report["valuation"]["base_drivers"].items():
        s.line([name.replace("_", " "), _num(d.get("value")) if d.get("available") else _Missing(_status_word(d)),
                d.get("basis", ""), d.get("formula", d.get("reason", "")), ""], [None, FMT_PCT2])
    cfg = report["valuation"]["config"]
    s.gap()
    s.line(["Forecast horizon (years)", _num(cfg["horizon_years"]), "", "", ""], [None, "0"])
    s.line(["Terminal growth", _num(cfg["terminal_growth"]["value"]), cfg["terminal_growth"].get("note", ""), "", ""],
           [None, FMT_PCT2])
    s.widths([44, 14, 70, 50, 10])

    # 10 --------------------------------------------------------------- Sensitivity Analysis
    s = Sheet(wb, "Sensitivity Analysis", report, f"How the fair value ({cur} per share) moves with beta and with the "
                                                  f"cost-of-equity treatment.")
    sens = report["valuation"]["sensitivity"]
    s.header(["Beta", "Cost of equity", "Fair value", "Range low", "Range high"], freeze=False)
    if sens.get("available"):
        for r in sens["rows"]:
            s.line([_num(r["beta"]), _num(r["cost_of_equity"]), _num(r["fair_value"]), _num(r["range_low"]),
                    _num(r["range_high"])], [FMT_NUM, FMT_PCT2, FMT_PER_SHARE, FMT_PER_SHARE, FMT_PER_SHARE])
    else:
        s.line([_Missing(_status_word(sens)), sens.get("reason", "")])
    s.gap()
    s.section("Cost-of-equity treatments")
    s.header(["Treatment", "Cost of equity", "Fair value", "12-month target", "Model view"], freeze=False)
    if res.get("available"):
        s.line(["Configured: " + res.get("formula", ""), _num(res.get("value")), _num(fv.get("fair_value")),
                _num(fv.get("target_price_12m")), rec.get("selected_model_view") or rec.get("model_view")],
               [None, FMT_PCT2, FMT_PER_SHARE, FMT_PER_SHARE])
    for alt in coe.get("alternatives") or []:
        s.line([alt["treatment"], _num(alt.get("cost_of_equity")), _num(alt.get("fair_value")),
                _num(alt.get("target_price_12m")), alt.get("model_view") or ""],
               [None, FMT_PCT2, FMT_PER_SHARE, FMT_PER_SHARE])
    s.widths([52, 16, 16, 16, 18])

    # 11 --------------------------------------------------------------- Technical Analysis
    tech = report["technical"]
    s = Sheet(wb, "Technical Analysis", report, "Descriptive only: these indicators never change the valuation or the "
                                                "model view, and they are not trading signals.")
    s.header(["Indicator", "Value", "Status", "Detail", "Formula"], freeze=False)
    if tech.get("available"):
        for name, ind in tech["indicators"].items():
            if ind.get("available"):
                value = ind.get("value")
                detail = ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in ind.items()
                                   if k in ("price_vs", "zone", "line_vs_signal", "trend_strength"))
                if value is None:
                    extra = {k: v for k, v in ind.items() if k in ("line", "signal", "histogram", "lower", "middle",
                                                                 "upper", "high", "low", "change")}
                    detail = "; ".join(f"{k} {_num(v):,.2f}" for k, v in extra.items() if _num(v) is not None) + (
                        f"; {detail}" if detail else "")
                s.line([name.replace("_", " ").upper(), _num(value), _status_word(ind), detail, ind.get("formula", "")],
                       [None, FMT_PER_SHARE])
            else:
                s.line([name.replace("_", " ").upper(), _Missing(_status_word(ind)), _status_word(ind),
                        ind.get("reason", ""), ""])
        s.gap()
        s.note(f"Closes to {tech.get('last_trade_date')}; split-adjusted: {'yes' if tech.get('split_adjusted') else 'no'}.")
    else:
        s.line(["Technical analysis", _Missing(_status_word(tech)), _status_word(tech), tech.get("reason", ""), ""])
    s.widths([20, 14, 20, 70, 60])

    # 12 --------------------------------------------------------------- Risk Analysis
    s = Sheet(wb, "Risk Analysis", report, "Risks quoted from the company's own documents, and market-risk measures.")
    s.header(["Category", "Risk", "Quote", "Source", "Page"], freeze=False)
    for r in report["risks"]:
        s.line([r["category"].replace("_", " "), r["title"], r["quote"], r["source"]["title"], r["source"].get("page")],
               [None, None, None, None, "0"])
        s.ws.cell(row=s.row - 1, column=3).alignment = Alignment(wrap_text=True, vertical="top")
    s.gap()
    s.section(f"Beta against {report['beta']['benchmark']}")
    s.header(["Method", "Beta", "Std error", "R squared", "Observations"], freeze=False)
    for method, e in report["beta"]["estimates"].items():
        if e.get("available"):
            s.line([method.replace("_", " "), _num(e.get("beta")), _num(e.get("std_error")), _num(e.get("r_squared")),
                    _num(e.get("observations"))], [None, FMT_NUM, FMT_NUM, FMT_NUM, "#,##0"])
        else:
            s.line([method.replace("_", " "), _Missing(_status_word(e)), e.get("reason", "")])
    zv = report["beta"]["zero_volume"]
    if zv.get("available"):
        s.line(["Share of days with no trade", _num(zv.get("value"))], [None, FMT_PCT])
    for a in report["beta"].get("adjustments") or []:
        s.note(a)
    s.widths([26, 30, 80, 40, 8])

    # 13 --------------------------------------------------------------- Sources & Evidence
    s = Sheet(wb, "Sources & Evidence", report, "Every statement figure with the document and page it was read from.")
    s.section("Documents")
    s.header(["Document", "Publisher", "Kind", "Fiscal year", "URL", "Retrieved", "SHA-256"], freeze=False)
    for d in report["sources"]["documents"]:
        s.line([d["title"], d.get("publisher"), d.get("kind"), d.get("fiscal_year"), d.get("url"), d.get("retrieved_at"),
                d.get("sha256")], [None, None, None, "0"])
    s.gap()
    s.section("Figures")
    s.header(["Statement", "Line item", "Period", "Value", "Unit", "Currency", "Document", "Page", "Table / column",
              "Method", "Status", "Retrieved", "URL"], freeze=False)
    for st in report["statements"]:
        for row in st["rows"]:
            for y in years:
                c = row["cells"].get(y)
                if not c:
                    continue
                if c.get("available"):
                    src = c.get("source") or {}
                    s.line([st["title"], row["label"], c.get("period_end") or f"FY{y}", _num(c.get("value")), row["unit"],
                            c.get("currency") or cur, src.get("title"), src.get("page"),
                            f"{c.get('column', '')} column" + (f", as reported: {c['label_as_reported']}"
                                                               if c.get("label_as_reported") else ""),
                            c.get("method") or c.get("derived") or "", _status_word(c), src.get("retrieved_at"),
                            src.get("url")], [None, None, None, _fmt_for_unit(row["unit"]), None, None, None, "0"])
                else:
                    s.line([st["title"], row["label"], f"FY{y}", _Missing(_status_word(c)), row["unit"], cur, "", "", "",
                            "", _status_word(c), "", c.get("reason", "")])
    s.gap()
    s.section("Market and reference inputs")
    s.header(["Series", "Value", "Unit", "As of", "Source", "URL"], freeze=False)
    for m in report["sources"]["macro"] + report["sources"]["reference"]:
        s.line([m["label"], _num(m["value"]), m["unit"], m.get("as_of"), m["source_name"], m["source_url"]],
               [None, "#,##0.0000"])
    s.widths([20, 40, 14, 16, 12, 9, 40, 7, 30, 18, 20, 24, 60])

    buf = io.BytesIO()
    wb.properties.creator = "AfriEdge"
    wb.properties.title = f"{sec['name']} analyst workbook"
    wb.save(buf)
    return buf.getvalue()
