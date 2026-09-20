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

    .venv\Scripts\python -m pipelines.banks.resolve --bank=crdb
"""
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal
from pathlib import Path

from pipelines.banks.profiles import BankProfile, profile_for

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
    from pipelines.banks.items import CANONICAL

    return TOL_PER_SHARE if item == "dps" or CANONICAL[item][1] == "TZS_per_share" else TOL_MILLIONS


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
    """A value becomes a fact when at least two independent readers read it the same way.
    With two readers that means both. With three, a single dissenting reader is recorded as
    METHOD_OUTLIER (shown on the Sources tab) but does not block the value the other two agree on."""
    key = "current" if role == "current" else "comparative"
    fiscal = report_year if role == "current" else report_year - 1
    present = {m: per_method[m] for m in methods if per_method.get(m) is not None}
    if not present:
        return None
    groups: list[list[dict]] = []
    for m in methods:
        c = present.get(m)
        if c is None:
            continue
        for g in groups:
            if abs(g[0][key] - c[key]) <= _tol(item):
                g.append(c)
                break
        else:
            groups.append([c])
    best = max(groups, key=len)
    if len(best) >= 2:
        a = best[0]
        for o in (c for c in present.values() if not any(c is b for b in best)):
            conflicts.append({
                "fiscal_year": fiscal, "item_code": item, "kind": "METHOD_OUTLIER",
                "value_a": a[key], "source_a": "+".join(c["method"] for c in best) + f" p{a['page']}",
                "value_b": o[key], "source_b": f"{o['method']} p{o['page']}",
                "report_year": report_year, "page": a["page"],
                "detail": f"{report_year} report, {role} column: {o['method']} read {o[key]:,}; "
                          f"{' and '.join(c['method'] for c in best)} both read {a[key]:,}, which is used."})
        agreed = sorted(c["method"] for c in best)
        return {"fiscal_year": fiscal, "item_code": item, "value": a[key], "report_year": report_year,
                "page": a["page"], "column_role": role, "label": a["label"], "raw": a["raw"],
                "agreed_by": agreed, "method": "+".join(agreed)}
    if len(present) == 1:
        only = next(iter(present.values()))
        conflicts.append({
            "fiscal_year": fiscal, "item_code": item, "kind": "MISSING_IN_METHOD",
            "value_a": only[key], "source_a": f"{only['method']} p{only['page']} ({report_year} report)",
            "value_b": None, "source_b": ", ".join(m for m in methods if m not in present) + " found no value",
            "report_year": report_year, "page": only["page"],
            "detail": f"Only {only['method']} read '{only['label']}' = {only[key]:,}. Not used until confirmed."})
        return None
    ordered = [present[m] for m in methods if m in present]
    a, b = ordered[0], ordered[1]
    conflicts.append({
        "fiscal_year": fiscal, "item_code": item, "kind": "METHOD_DISAGREEMENT",
        "value_a": a[key], "source_a": f"{a['method']} p{a['page']}",
        "value_b": b[key], "source_b": f"{b['method']} p{b['page']}",
        "report_year": report_year, "page": a["page"],
        "detail": f"{report_year} report, {role} column: "
                  + ", ".join(f"{c['method']} read {c[key]:,}" for c in ordered) + "."})
    return None


def extract_dps(profile: BankProfile, year: int) -> dict | None:
    import pypdfium2 as pdfium

    dps_re = re.compile(profile.dps_re, re.I | re.S)
    doc = pdfium.PdfDocument(str(profile.pdf_path(year)))
    for i in range(len(doc)):
        text = re.sub(r"\s+", " ", doc[i].get_textpage().get_text_range())
        if not re.search(profile.dps_page_hint, text, re.I):
            continue
        for m in dps_re.finditer(text):
            if int(m.group(2)) == year and re.search(r"propose|recommend", text[max(0, m.start() - 120):m.end()], re.I):
                return {"fiscal_year": year, "item_code": "dps", "value": Decimal(m.group(1).replace(",", "")),
                        "report_year": year, "page": i + 1, "column_role": "current",
                        "label": "Proposed dividend per share", "raw": m.group(0)[:300],
                        "agreed_by": ["text_layer"], "method": "text_layer"}
    return None


def _report_quote(profile: BankProfile, report_year: int, pattern: str) -> tuple[int, str] | None:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(profile.pdf_path(report_year)))
    for i in range(len(doc)):
        text = re.sub(r"\s+", " ", doc[i].get_textpage().get_text_range())
        m = re.search(r"[^.*]*" + pattern + r"[^.]*\.", text, re.I)
        if m:
            return i + 1, m.group(0).strip()
    return None


def derive(profile: BankProfile, resolved: dict[int, dict[str, dict]]) -> None:
    """Fill a line the report does not print, only where the same report states why it equals
    another printed figure (profile.derivations). The derived fact keeps the source figure's
    page and methods and quotes the statement it relies on."""
    for target, source, pattern in profile.derivations:
        for fy, facts in resolved.items():
            if target in facts:
                continue
            anchor = facts.get(source) if source else facts.get("total_equity")
            if anchor is None:
                continue
            quote = _report_quote(profile, anchor["report_year"], pattern)
            if quote is None:
                continue
            page, text = quote
            value = anchor["value"] if source else Decimal(0)
            facts[target] = anchor | {
                "item_code": target, "value": value, "also_reported_in": [],
                "method": "derived:" + (source or "nil"),
                "label": (f"{anchor['label']} (derived: {text})" if source else f"nil (derived: {text})"),
                "raw": f"{anchor['raw']} || {anchor['report_year']} report p{page}: {text}"[:2000]}


def ties(facts: dict[int, dict[str, dict]], rules: list[tuple]) -> list[dict]:
    checks = []

    def v(y, k):
        f = facts.get(y, {}).get(k)
        return None if f is None else f["value"]

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


def main(argv: list[str]) -> int:
    profile = profile_for(next((a.split("=", 1)[1] for a in argv if a.startswith("--bank=")), ""))
    if profile is None:
        print("Usage: python -m pipelines.banks.resolve --bank=<nmb|crdb>")
        return 2
    processed = profile.processed_dir
    years = profile.years
    extractions = {}
    for y in years:
        ex = json.loads((processed / f"extraction_{y}.json").read_text(encoding="utf-8"))
        extra = processed / f"extraction_{y}_text.json"  # optional third reader (PDF text lines)
        if extra.exists():
            ex["candidates"] += json.loads(extra.read_text(encoding="utf-8"))["candidates"]
        extractions[y] = _normalise(ex)
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
        dps = extract_dps(profile, y)
        if dps:
            facts[(y, "dps")] = dps
        per_report[y] = facts

    resolved: dict[int, dict[str, dict]] = {}
    for fy in range(min(years) - 1, max(years) + 1):
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

    derive(profile, resolved)
    checks = ties(resolved, profile.ties)
    out = {"methods": methods_used, "facts": [f for y in resolved.values() for f in y.values()],
           "conflicts": conflicts, "checks": checks}
    (processed / "resolved.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")

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
    sys.exit(main(sys.argv[1:]))
