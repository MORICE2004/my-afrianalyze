"""NMB end to end: the stored figures are the figures printed in NMB's annual reports.

Needs the downloaded reports in data/raw/nmb and the loaded database (see test_api.py).
"""
from __future__ import annotations

import re
from decimal import Decimal as D
from pathlib import Path

import pypdfium2 as pdfium
import pytest

from packages.analysis.bank_valuation import run_scenarios
from packages.core.config import REPO_ROOT
from packages.database.models import ExtractionConflict, FinancialFact, SourceDocument, ValidationCheck
from packages.database.session import SessionLocal
from packages.report.builder import _config

RAW = REPO_ROOT / "data" / "raw" / "nmb"

try:
    with SessionLocal() as _s:
        _loaded = _s.query(FinancialFact).filter_by(security_id="DSE:NMB").first() is not None
except Exception:  # no database or no tables yet (e.g. CI before the pipeline has run)
    _loaded = False
pytestmark = pytest.mark.skipif(not (_loaded and (RAW / "NMB_Annual_Report_2025.pdf").is_file()),
                                reason="NMB reports or loaded data missing; run the NMB pipeline first")

# Typed in by hand from the pages of NMB's annual reports (report year, PDF page), then checked below.
HAND_CHECKED = [
    # item, fiscal year, value as printed, report, page
    ("total_assets", 2025, "17,615,944", 2025, 151),
    ("total_liabilities", 2025, "14,509,225", 2025, 151),
    ("total_equity", 2025, "3,106,719", 2025, 151),
    ("deposits_customers", 2025, "12,518,321", 2025, 151),
    ("loans_advances_net", 2025, "10,430,094", 2025, 151),
    ("gross_loans", 2025, "10,688,021", 2025, 203),
    ("stage3_gross_loans", 2025, "253,693", 2025, 182),
    ("net_interest_income", 2025, "1,191,080", 2025, 150),
    ("profit_for_year", 2025, "760,064", 2025, 150),
    ("profit_attributable_owners", 2025, "759,670", 2025, 150),
    ("eps", 2025, "1,519.34", 2025, 150),
    ("total_regulatory_capital", 2025, "2,883,923", 2025, 198),
    ("total_rwa", 2025, "11,654,283", 2025, 198),
    ("dps", 2025, "504.26", 2025, 202),
    ("total_assets", 2024, "13,735,690", 2025, 151),   # comparative in the later report is the source of record
    ("profit_for_year", 2023, "545,207", 2024, 122),
    ("net_interest_income", 2022, "789,636", 2023, 140),
    ("total_assets", 2021, "8,681,421", 2022, 123),
]

_pages: dict[tuple[str, int], str] = {}


def page_text(path: str, page: int) -> str:
    key = (path, page)
    if key not in _pages:
        doc = pdfium.PdfDocument(str(REPO_ROOT / path))
        _pages[key] = re.sub(r"\s+", " ", doc[page - 1].get_textpage().get_text_range().replace("￾", "-"))
    return _pages[key]


def printed(value: D, unit: str) -> str:
    a = abs(value)
    return f"{a:,.2f}" if unit == "TZS_per_share" else f"{a:,.0f}"


def printed_forms(value: D, unit: str) -> list[str]:
    """Per-share amounts can be printed without decimals when whole (e.g. 'TZS 145 per share')."""
    forms = [printed(value, unit)]
    if unit == "TZS_per_share" and value == value.to_integral_value():
        forms.append(f"{abs(value):,.0f}")
    return forms


@pytest.fixture(scope="module")
def db():
    with SessionLocal() as s:
        docs = {d.id: d for d in s.query(SourceDocument).filter_by(security_id="DSE:NMB")}
        facts = s.query(FinancialFact).filter_by(security_id="DSE:NMB", is_primary=True).all()
        checks = s.query(ValidationCheck).filter_by(security_id="DSE:NMB").all()
        conflicts = s.query(ExtractionConflict).filter_by(security_id="DSE:NMB").all()
        yield {"docs": docs, "facts": facts, "checks": checks, "conflicts": conflicts}


@pytest.mark.parametrize("item,year,text,report,page", HAND_CHECKED)
def test_hand_checked_figures(db, item, year, text, report, page):
    f = next(f for f in db["facts"] if f.item_code == item and f.fiscal_year == year)
    doc = db["docs"][f.document_id]
    assert (doc.fiscal_year, f.page) == (report, page), "figure is cited to a different report or page"
    assert printed(f.value, f.unit) == text
    assert text in page_text(doc.file_path, page)


def test_every_stored_figure_is_printed_on_its_cited_page(db):
    missing = [(f.item_code, f.fiscal_year, f.page) for f in db["facts"]
               if not any(form in page_text(db["docs"][f.document_id].file_path, f.page)
                          for form in printed_forms(f.value, f.unit))]
    assert len(db["facts"]) >= 290
    assert missing == []


def test_every_figure_is_exact_and_in_tzs(db):
    for f in db["facts"]:
        assert isinstance(f.value, D)
        assert f.currency == "TZS" and f.period_end.month == 12 and f.period_end.day == 31


def test_documents_have_hash_publication_date_and_terms_note(db):
    assert {d.fiscal_year for d in db["docs"].values() if d.kind == "annual_report"} == {2021, 2022, 2023, 2024, 2025}
    for d in db["docs"].values():
        assert len(d.sha256) == 64 and d.terms_note
        if d.kind != "annual_report":       # price files carry a hash and terms, but no board approval date
            continue
        assert d.published_on is not None and d.published_on.year == d.fiscal_year + 1, d.title
        assert d.published_on_evidence and "authori" in d.published_on_evidence.lower()


def test_balance_sheet_ties_every_year(db):
    ties = [c for c in db["checks"] if c.check_name == "assets = liabilities + equity"]
    assert sorted(c.fiscal_year for c in ties) == [2020, 2021, 2022, 2023, 2024, 2025]
    assert all(c.passed for c in ties)


def test_only_known_source_inconsistency_fails(db):
    failed = [(c.fiscal_year, c.check_name) for c in db["checks"] if not c.passed]
    assert failed == [(2020, "net loans = gross loans + ECL allowance")]
    open_conflicts = [c for c in db["conflicts"] if c.kind not in ("RESTATEMENT", "SOURCE_INCONSISTENCY")]
    assert open_conflicts == [], "Camelot and Docling disagree somewhere"


def test_valuation_runs_on_real_facts_with_a_given_cost_of_equity(db):
    # Beta is BLOCKED, so the report never runs this; the engine itself must still work end to end.
    facts: dict = {}
    for f in db["facts"]:
        facts.setdefault(f.item_code, {})[f.fiscal_year] = f.value
    from packages.analysis.bank_ratios import add_derived

    add_derived(facts)
    years = sorted({y for s in facts.values() for y in s})
    cfg = _config("valuation.json")
    res = run_scenarios(facts, years, D("0.169224"), cfg)
    assert res["available"], res.get("reason")
    probs = [s["probability"] for s in res["scenarios"].values()]
    assert sum(probs) == 1
    assert res["fair_value_range"]["low"] <= res["fair_value"] <= res["fair_value_range"]["high"]
    bad = cfg | {"scenarios": cfg["scenarios"] | {"bull": cfg["scenarios"]["bull"] | {"probability": 0.3}}}
    assert "sum to" in run_scenarios(facts, years, D("0.169224"), bad)["reason"]
    assert run_scenarios(facts, years, D("0.04"), cfg)["available"] is False  # CoE below terminal growth


def test_raw_files_match_their_recorded_hash(db):
    import hashlib

    for d in db["docs"].values():
        data = Path(REPO_ROOT / d.file_path).read_bytes()
        assert hashlib.sha256(data).hexdigest() == d.sha256, d.title
