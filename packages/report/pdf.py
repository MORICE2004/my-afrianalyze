"""PDF export of the report payload, laid out like a CFA Research Challenge report.

It renders only what build_report returned, so the PDF can never show a number
that the web page does not.
"""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#0B2545")
GREY = colors.HexColor("#6B7280")
LIGHT = colors.HexColor("#EEF2F7")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Title"], fontSize=20, textColor=NAVY, alignment=TA_LEFT, spaceAfter=4)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, textColor=NAVY, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("B", parent=styles["BodyText"], fontSize=8.5, leading=11)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=7, leading=9, textColor=GREY)


def _num(v: float | None, unit: str = "TZS_millions") -> str:
    if v is None:
        return "n/a"
    if unit == "TZS_per_share":
        return f"{v:,.2f}"
    return f"({abs(v):,.0f})" if v < 0 else f"{v:,.0f}"


def _pct(v: float | None) -> str:
    return "n/a" if v is None else f"{v * 100:.1f}%"


def _na(block: dict) -> str:
    return f"Not available: {block.get('reason', '')}"


def _table(rows: list[list], widths: list[float], header: bool = True) -> Table:
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    style = [("FONT", (0, 0), (-1, -1), "Helvetica", 7.5),
             ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
             ("LINEBELOW", (0, 0), (-1, 0), 0.6, NAVY),
             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
             ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]
    if header:
        style.append(("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 7.5))
    t.setStyle(TableStyle(style))
    return t


def _footer(canvas, doc, report):
    canvas.saveState()
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(GREY)
    canvas.drawString(15 * mm, 10 * mm, "My AfriAnalyze. Research and education only, not investment advice. "
                                        f"Generated {report['generated_at']}.")
    canvas.drawRightString(195 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def render_pdf(report: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=16 * mm,
                            title=f"{report['security']['name']} research report")
    sec, head = report["security"], report["header"]
    years = [str(y) for y in report["years"]]
    story: list = []

    review = report["review"]
    as_of = report["data_as_of"]
    story += [Paragraph(f"{sec['name']} ({sec['id']})", H1),
              Paragraph(f"{sec['sector']} | {sec['exchange']} | Currency {sec['currency']} | "
                        f"Report generated {report['generated_at'][:10]} | Data as of FY ending "
                        f"{as_of['fiscal_year_end']} ({as_of['latest_report']}, published {as_of['published_on']})",
                        SMALL)]
    if review["status"] != "published":
        story.append(Paragraph(
            f"<b>DRAFT, NOT REVIEWED.</b> Research run {review['run_id']} has status '{review['status']}'. "
            "It has not been approved by a named reviewer and must not be relied on or shared as research.",
            ParagraphStyle("draft", parent=BODY, textColor=colors.HexColor("#B45309"))))
    else:
        story.append(Paragraph(f"Research run {review['run_id']}, reviewed by {review['reviewer']} on "
                               f"{review['reviewed_at'][:10]}.", SMALL))
    story.append(Spacer(1, 6))
    rec = head["recommendation"]
    price = head["price"]
    if rec["available"]:
        view = rec["model_view"] + (f" ({rec['trade_label']})" if rec.get("trade_label") else "")
    else:
        view = f"Not available ({rec.get('status', '')})"
    key = [["Model view", view],
           ["Price", f"{price['value']:,.2f} ({price['trade_date']})" if price["available"] else "Not available"],
           ["12-month target", _num(head["target_price"]["value"], "TZS_per_share")
            if head["target_price"]["available"] else "Not available"],
           ["Fair value range", f"{_num(head['fair_value_range']['low'], 'TZS_per_share')} - "
                                f"{_num(head['fair_value_range']['high'], 'TZS_per_share')}"
            if head["fair_value_range"]["available"] else "Not available"],
           ["Confidence", f"{head['confidence']['level']} ({head['confidence']['score']:.0f}/100)"]]
    story.append(_table(key, [45 * mm, 135 * mm], header=False))
    if not rec["available"]:
        story.append(Paragraph(_na(rec), SMALL))
    story.append(Paragraph("Why some headline figures are missing", H2))
    for g in report["gaps"] or ["None."]:
        story.append(Paragraph(f"- {g}", BODY))

    story.append(Paragraph("What moved in the latest year", H2))
    for st in report["statements"]:
        for row in st["rows"]:
            if row.get("note") and row["item_code"] in {"net_interest_income", "impairment_loans",
                                                        "total_operating_expenses", "loans_advances_net",
                                                        "profit_attributable_owners"}:
                story.append(Paragraph(f"- {row['note']['text']}", BODY))
    story += [Spacer(1, 6), Paragraph(report["disclaimer"], SMALL), PageBreak()]

    for st in report["statements"]:
        story.append(Paragraph(f"{st['title']} (TZS millions unless stated)", H2))
        rows = [["Line item"] + years + ["CAGR"]]
        for r in st["rows"]:
            cells = [(_num(r["cells"][y]["value"], r["unit"]) if r["cells"][y]["available"] else "n/a")
                     for y in years]
            cagr = r["analysis"]["cagr"] if r.get("analysis") else {"available": False}
            rows.append([Paragraph(r["label"], BODY)] + cells + [_pct(cagr["value"]) if cagr["available"] else "n/a"])
        story.append(_table(rows, [62 * mm] + [20 * mm] * len(years) + [18 * mm]))
        story.append(Paragraph("Each figure is linked to its page in the source report in the web version. "
                               "n/a = not reported, not extracted, or in extraction conflict.", SMALL))

    story.append(Paragraph("Bank ratios", H2))
    rows = [["Ratio"] + years]
    for r in report["ratios"]:
        rows.append([r["label"]] + [_pct(r["values"][y]["value"]) if r["values"][y]["available"] else "n/a"
                                    for y in years])
    story.append(_table(rows, [62 * mm] + [22 * mm] * len(years)))
    story.append(PageBreak())

    story.append(Paragraph("Beta", H2))
    b = report["beta"]
    rows = [["Method", "Beta", "Std err", "R-squared", "Obs."]]
    for name, est in b["estimates"].items():
        if est.get("available"):
            rows.append([name, f"{est['beta']:.3f}", "n/a" if est.get("std_error") is None else f"{est['std_error']:.3f}",
                         "n/a" if est.get("r_squared") is None else f"{est['r_squared']:.3f}", str(est["observations"])])
        else:
            rows.append([name, "n/a", "", "", Paragraph(est["reason"], SMALL)])
    story.append(_table(rows, [35 * mm, 20 * mm, 20 * mm, 20 * mm, 85 * mm]))
    story.append(Paragraph("Selected: " + (b["selected"]["reason"] if b["selected"].get("available")
                                           else _na(b["selected"])), BODY))

    story.append(Paragraph("Cost of equity (TZS)", H2))
    coe = report["cost_of_equity"]
    rows = [["Input", "Value", "Source"]]
    for k, v in coe["inputs"].items():
        rows.append([k.replace("_", " "), _pct(v["value"]) if v else "missing",
                     Paragraph(f"{v['source_name']} ({v['as_of']})" if v else "", SMALL)])
    story.append(_table(rows, [40 * mm, 25 * mm, 115 * mm]))
    story.append(Paragraph(("Cost of equity: " + _pct(coe["result"]["value"]) + " = " + coe["result"]["formula"])
                           if coe["result"]["available"] else _na(coe["result"]), BODY))
    if coe["sensitivity"].get("available"):
        story.append(Paragraph("Sensitivity (beta is not measured; these rows are not a forecast):", SMALL))
        sens = report["valuation"]["sensitivity"]
        rows = [["Beta", "Cost of equity", "Fair value (prob.-weighted)", "Scenario range"]]
        for r in sens.get("rows", []):
            rows.append([f"{r['beta']:.2f}", _pct(r["cost_of_equity"]), _num(r["fair_value"], "TZS_per_share"),
                         f"{_num(r['range_low'], 'TZS_per_share')} - {_num(r['range_high'], 'TZS_per_share')}"])
        if len(rows) > 1:
            story.append(_table(rows, [25 * mm, 35 * mm, 55 * mm, 65 * mm]))

    story.append(Paragraph("Valuation drivers (base case from history)", H2))
    rows = [["Driver", "Base value", "Basis"]]
    for k, d in report["valuation"]["base_drivers"].items():
        rows.append([k.replace("_", " "), _pct(d["value"]) if d["available"] else "n/a",
                     Paragraph(d.get("basis", "") + ("" if d["available"] else f" ({d['reason']})"), SMALL)])
    story.append(_table(rows, [40 * mm, 25 * mm, 115 * mm]))
    cfg = report["valuation"]["config"]
    rows = [["Scenario", "Probability"] + list(next(iter(cfg["scenarios"].values()))["shocks"].keys())]
    for name, sc in cfg["scenarios"].items():
        rows.append([name, _pct(sc["probability"])] + [f"{v * 100:+.1f} pp" for v in sc["shocks"].values()])
    story.append(_table(rows, [25 * mm, 22 * mm] + [26.6 * mm] * 5))
    story.append(Paragraph(f"Terminal growth {_pct(cfg['terminal_growth']['value'])}: {cfg['terminal_growth']['note']} "
                           f"Method weights: {cfg['method_weights']}.", SMALL))
    val = report["valuation"]["result"]
    story.append(Paragraph(("Probability-weighted fair value " + _num(val["fair_value"], "TZS_per_share"))
                           if val.get("available") else _na(val), BODY))
    story.append(PageBreak())

    story.append(Paragraph("Risks (each quoted from a source document)", H2))
    for r in report["risks"]:
        story.append(Paragraph(f"<b>{r['title']}</b> [{r['category'].replace('_', ' ')}]: \"{r['quote']}\" "
                               f"<i>({r['source']['title']}, p.{r['source']['page']})</i>", BODY))
        story.append(Spacer(1, 2))

    story.append(Paragraph("Data quality", H2))
    passed = sum(c["passed"] for c in report["checks"])
    story.append(Paragraph(f"{passed} of {len(report['checks'])} tie checks passed. "
                           f"{sum(1 for c in report['conflicts'] if c['kind'] not in ('RESTATEMENT', 'METHOD_OUTLIER', 'SOURCE_INCONSISTENCY'))} open extraction "
                           f"conflicts; {sum(1 for c in report['conflicts'] if c['kind'] == 'RESTATEMENT')} restated "
                           f"comparatives.", BODY))
    for c in [c for c in report["checks"] if not c["passed"]][:15]:
        story.append(Paragraph(f"- FY{c['fiscal_year']} {c['name']}: {c['detail']}", SMALL))

    story.append(Paragraph("Sources", H2))
    for d in report["sources"]["documents"]:
        story.append(Paragraph(f"{d['title']}. {d['publisher']}. {d['url']} (retrieved {d['retrieved_at'][:10]}, "
                               f"SHA-256 {d['sha256'][:16]}...)", SMALL))
    for m in report["sources"]["macro"]:
        story.append(Paragraph(f"{m['label']}: {m['source_name']}, {m['source_url']} (as of {m['as_of']})", SMALL))
    for r in report["sources"]["reference"]:
        story.append(Paragraph(f"{r['label']}: {r['source_name']}, {r['source_url']}", SMALL))
    story += [Spacer(1, 6), Paragraph(report["disclaimer"], SMALL)]

    doc.build(story, onFirstPage=lambda c, d: _footer(c, d, report),
              onLaterPages=lambda c, d: _footer(c, d, report))
    return buf.getvalue()
