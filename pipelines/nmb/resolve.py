r"""Compare extraction methods, reconcile reports, and run tie checks.

Rules (all visible in the UI):
  * A figure becomes a fact only when Camelot and Docling read the same value.
    Any disagreement, or a value only one method found, is an EXTRACTION_CONFLICT
    and the figure is not used.
  * Each fiscal year appears twice: as the current column of its own report and
    as the comparative column of the next report. If both agree, the later
    report is the source of record (it reflects any restatement). If they
    differ, a RESTATEMENT conflict is recorded and the later report's value is
    used, because it is the bank's latest published figure for that year.
  * Stage 3 rows are only accepted when their total ties to gross loans.
  * Dividend per share is read from the text of the dividend note (single
    method, flagged as such).
  * Tie checks: assets = liabilities + equity, and income statement arithmetic.
    A failed balance-sheet tie makes this script exit non-zero.

    .venv\Scripts\python -m pipelines.nmb.resolve
"""
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal
from pathlib import Path

from pipelines.nmb.items import ALL_ITEMS

PROCESSED = Path("data/processed/nmb")
YEARS = [2021, 2022, 2023, 2024, 2025]
TOL_MILLIONS = Decimal("0.5")
TOL_PER_SHARE = Decimal("0.005")
TIE_TOLERANCE = Decimal(1)  # statements are rounded to TZS millions


def dec(v) -> Decimal | None:
    """Exact conversion. Values in extraction files are strings (or floats written by
    an older run, whose repr is exact for these integers and 2-decimal figures)."""
    return None if v is None else Decimal(str(v))


def _normalise(extraction: dict) -> dict:
    for c in extraction["candidates"]:
        c["current"], c["comparative"] = dec(c["current"]), dec(c["comparative"])
        c["numbers"] = [dec(n) for n in c["numbers"]]
    return extraction


def _tol(item: str) -> Decimal:
    return TOL_PER_SHARE if ALL_ITEMS[item][1].unit == "TZS_per_share" else TOL_MILLIONS


def _first(cands: list[dict], role: str) -> dict | None:
    key = "current" if role == "current" else "comparative"
    for c in sorted(cands, key=lambda c: c["page"]):
        if c[key] is not None:
            return c
    return None


def method_values(extraction: dict, gross: dict[str, float | None]) -> dict:
    """-> {item: {role: {method: candidate}}} using the first matching row per method."""
    out: dict = {}
    by_item: dict = {}
    for c in extraction["candidates"]:
        by_item.setdefault(c["item"], {}).setdefault(c["method"], []).append(c)
    for item, per_method in by_item.items():
        for method, cands in per_method.items():
            for role in ("current", "comparative"):
                pool = cands
                if item == "stage3_gross_loans":
                    total = gross.get(role)
                    pool = [c for c in cands if total is not None and c["numbers"]
                            and abs(c["numbers"][-1] - total) <= TOL_MILLIONS]
                cand = _first(pool, role)
                if cand:
                    out.setdefault(item, {}).setdefault(role, {})[method] = cand
    return out


def agree(item: str, role: str, per_method: dict, methods: list[str], report_year: int,
          conflicts: list) -> dict | None:
    key = "current" if role == "current" else "comparative"
    fiscal = report_year if role == "current" else report_year - 1
    vals = {m: per_method.get(m) for m in methods}
    present = {m: c for m, c in vals.items() if c is not None}
    if not present:
        return None
    if len(present) < len(methods):
        only = next(iter(present.values()))
        conflicts.append({
            "fiscal_year": fiscal, "item_code": item, "kind": "MISSING_IN_METHOD",
            "value_a": only[key], "source_a": f"{only['method']} p{only['page']} ({report_year} report)",
            "value_b": None, "source_b": ", ".join(m for m in methods if m not in present) + " found no value",
            "report_year": report_year, "page": only["page"],
            "detail": f"Only {only['method']} read '{only['label']}' = {only[key]:,}. Not used until confirmed."})
        return None
    a, b = present[methods[0]], present[methods[1]] if len(methods) > 1 else present[methods[0]]
    if abs(a[key] - b[key]) > _tol(item):
        conflicts.append({
            "fiscal_year": fiscal, "item_code": item, "kind": "METHOD_DISAGREEMENT",
            "value_a": a[key], "source_a": f"{a['method']} p{a['page']}",
            "value_b": b[key], "source_b": f"{b['method']} p{b['page']}",
            "report_year": report_year, "page": a["page"],
            "detail": f"{report_year} report, {role} column: {a['method']} read {a[key]:,}, "
                      f"{b['method']} read {b[key]:,}."})
        return None
    return {"fiscal_year": fiscal, "item_code": item, "value": a[key], "report_year": report_year,
            "page": a["page"], "column_role": role, "label": a["label"], "raw": a["raw"],
            "agreed_by": sorted(present), "method": "+".join(sorted(present))}


DPS_RE = re.compile(
    r"dividend of TZS\s*([\d,]+(?:\.\d+)?)\s*per\s+share[^.]{0,160}?(?:out of|for)\s+(?:the\s+)?(?:year\s+)?(\d{4})",
    re.I | re.S)


def extract_dps(year: int) -> dict | None:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(f"data/raw/nmb/NMB_Annual_Report_{year}.pdf")
    for i in range(len(doc)):
        text = re.sub(r"\s+", " ", doc[i].get_textpage().get_text_range())
        if not re.search(r"dividend per share", text, re.I):
            continue
        for m in DPS_RE.finditer(text):
            if int(m.group(2)) == year and re.search(r"propose|recommend", text[max(0, m.start() - 120):m.end()], re.I):
                return {"fiscal_year": year, "item_code": "dps", "value": Decimal(m.group(1).replace(",", "")),
                        "report_year": year, "page": i + 1, "column_role": "current",
                        "label": "Proposed dividend per share", "raw": m.group(0)[:300],
                        "agreed_by": ["text_layer"], "method": "text_layer"}
    return None


def ties(facts: dict[int, dict[str, dict]]) -> list[dict]:
    checks = []

    def v(y, k):
        f = facts.get(y, {}).get(k)
        return None if f is None else f["value"]

    rules = [
        ("assets = liabilities + equity", "total_assets", ["total_liabilities", "total_equity"], True),
        ("total equity and liabilities = total assets", "total_equity_and_liabilities", ["total_assets"], True),
        ("total equity = owners + non-controlling", "total_equity", ["equity_owners", "nci"], False),
        ("net interest income = interest income + interest expense", "net_interest_income",
         ["interest_income", "interest_expense"], False),
        ("profit before tax = operating income + operating expenses", "profit_before_tax",
         ["total_operating_income", "total_operating_expenses"], False),
        ("profit for the year = profit before tax + income tax", "profit_for_year",
         ["profit_before_tax", "income_tax"], False),
        ("net loans = gross loans + ECL allowance", "loans_advances_net", ["gross_loans", "ecl_loans"], False),
    ]
    for y in sorted(facts):
        for name, lhs, rhs, critical in rules:
            left, parts = v(y, lhs), [v(y, k) for k in rhs]
            if left is None or any(p is None for p in parts):
                checks.append({"fiscal_year": y, "check_name": name, "passed": False, "critical": critical,
                               "expected": left, "actual": None,
                               "detail": "Not checked: missing " + ", ".join(
                                   k for k, p in zip([lhs] + rhs, [left] + parts) if p is None)})
                continue
            total = sum(parts, Decimal(0))
            ok = abs(left - total) <= TIE_TOLERANCE
            checks.append({"fiscal_year": y, "check_name": name, "passed": ok, "critical": critical,
                           "expected": left, "actual": total,
                           "detail": f"{lhs} {left:,.0f} vs {' + '.join(rhs)} {total:,.0f}"
                                     + ("" if ok else f" (difference {left - total:,.0f})")})
    return checks


def main() -> int:
    extractions = {y: _normalise(json.loads((PROCESSED / f"extraction_{y}.json").read_text(encoding="utf-8")))
                   for y in YEARS}
    methods_used = sorted({c["method"] for e in extractions.values() for c in e["candidates"]})
    if len(methods_used) < 2:
        print(f"ERROR: only {methods_used} ran. Dual extraction needs camelot and docling.")
        return 2
    conflicts: list[dict] = []
    per_report: dict[int, dict[tuple[int, str], dict]] = {}

    for y, ex in extractions.items():
        # Gross loans first, so stage 3 rows can be tied to it.
        gross_mv = method_values(ex, {}).get("gross_loans", {})
        gross = {}
        for role in ("current", "comparative"):
            fact = agree("gross_loans", role, gross_mv.get(role, {}), methods_used, y, [])
            gross[role] = fact["value"] if fact else None
        mv = method_values(ex, gross)
        facts = {}
        for item, roles in mv.items():
            for role, per_method in roles.items():
                fact = agree(item, role, per_method, methods_used, y, conflicts)
                if fact:
                    facts[(fact["fiscal_year"], item)] = fact
        dps = extract_dps(y)
        if dps:
            facts[(y, "dps")] = dps
        per_report[y] = facts

    resolved: dict[int, dict[str, dict]] = {}
    for fy in range(min(YEARS) - 1, max(YEARS) + 1):
        own = per_report.get(fy, {})
        later = per_report.get(fy + 1, {})
        items = {k for (y, k) in own if y == fy} | {k for (y, k) in later if y == fy}
        for item in items:
            a, b = own.get((fy, item)), later.get((fy, item))
            chosen = b or a
            if a and b and abs(a["value"] - b["value"]) > _tol(item):
                conflicts.append({
                    "fiscal_year": fy, "item_code": item, "kind": "RESTATEMENT",
                    "value_a": a["value"], "source_a": f"{fy} report p{a['page']} (as first reported)",
                    "value_b": b["value"], "source_b": f"{fy + 1} report p{b['page']} (comparative)",
                    "report_year": fy + 1, "page": b["page"],
                    "detail": f"{item} for {fy} changed from {a['value']:,} to {b['value']:,} in the "
                              f"{fy + 1} report. The later figure is used."})
            if chosen:
                resolved.setdefault(fy, {})[item] = chosen | {
                    "also_reported_in": [r["report_year"] for r in (a, b) if r and r is not chosen]}

    checks = ties(resolved)
    out = {"methods": methods_used, "facts": [f for y in resolved.values() for f in y.values()],
           "conflicts": conflicts, "checks": checks}
    (PROCESSED / "resolved.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")

    kinds: dict[str, int] = {}
    for c in conflicts:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    print(f"facts={len(out['facts'])} conflicts={len(conflicts)} {kinds}")
    failed_critical = [c for c in checks if c["critical"] and not c["passed"]]
    for c in checks:
        mark = "PASS" if c["passed"] else ("FAIL" if c["actual"] is not None else "SKIP")
        print(f"  {mark} {c['fiscal_year']} {c['check_name']}: {c['detail']}")
    if failed_critical:
        print(f"BALANCE SHEET DOES NOT TIE for {sorted({c['fiscal_year'] for c in failed_critical})}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
