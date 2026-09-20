"""CRDB end to end: the stored figures are the GROUP figures printed in CRDB's annual reports.

CRDB prints four columns (GROUP current, GROUP prior, BANK current, BANK prior). These tests check that the
GROUP columns were read, and that every stored figure appears on the page it cites.
Needs data/raw/crdb and the loaded database:
    .venv\\Scripts\\python -m pipelines.banks.download_reports --bank=crdb
    .venv\\Scripts\\python -m pipelines.banks.extract --bank=crdb
    .venv\\Scripts\\python -m pipelines.banks.resolve --bank=crdb
    .venv\\Scripts\\python -m pipelines.banks.load --bank=crdb
"""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal as D
from pathlib import Path

import pypdfium2 as pdfium
import pytest

from packages.core.config import REPO_ROOT
from packages.database.models import ExtractionConflict, FinancialFact, RiskItem, SourceDocument, ValidationCheck
from packages.database.session import SessionLocal

SECURITY = "DSE:CRDB"
RAW = REPO_ROOT / "data" / "raw" / "crdb"

try:
    with SessionLocal() as _s:
        _loaded = _s.query(FinancialFact).filter_by(security_id=SECURITY).first() is not None
except Exception:  # no database or no tables yet
    _loaded = False
pytestmark = pytest.mark.skipif(not (_loaded and (RAW / "CRDB_Annual_Report_2025.pdf").is_file()),
                                reason="CRDB reports or loaded data missing; run the CRDB pipeline first")

# Read by hand from the PDF pages (report year, PDF page). GROUP column unless noted.
HAND_CHECKED = [
    # item, fiscal year, value, report, page
    ("total_assets", 2025, D("22308936"), 2025, 196),
    ("total_liabilities", 2025, D("19525115"), 2025, 196),
    ("total_equity", 2025, D("2783821"), 2025, 196),
    ("equity_owners", 2025, D("2747055"), 2025, 196),
    ("deposits_customers", 2025, D("14930504"), 2025, 196),
    ("loans_advances_net", 2025, D("13723318"), 2025, 196),
    ("net_interest_income", 2025, D("1393250"), 2025, 195),
    ("profit_before_tax", 2025, D("1030511"), 2025, 195),
    ("profit_for_year", 2025, D("728566"), 2025, 195),
    ("profit_attributable_owners", 2025, D("732457"), 2025, 195),
    ("eps", 2025, D("280.42"), 2025, 195),
    ("gross_loans", 2025, D("13971500"), 2025, 301),
    ("ecl_loans", 2025, D("-248182"), 2025, 301),
    ("stage3_gross_loans", 2025, D("377472"), 2025, 301),
    ("impairment_loans", 2025, D("148387"), 2025, 303),      # credit loss note, loans row, GROUP 2025 total
    ("total_regulatory_capital", 2025, D("2560049"), 2025, 327),
    ("total_rwa", 2025, D("14348303"), 2025, 327),
    ("dps", 2025, D("90"), 2025, 292),
    ("total_assets", 2024, D("16698751"), 2025, 196),         # comparative in the later report is the source of record
    ("impairment_loans", 2024, D("87217"), 2025, 303),
    ("profit_attributable_owners", 2023, D("424690"), 2024, 169),
]

_pages: dict[tuple[str, int], str] = {}


def page_text(path: str, page: int) -> str:
    key = (path, page)
    if key not in _pages:
        doc = pdfium.PdfDocument(str(REPO_ROOT / path))
        _pages[key] = re.sub(r"\s+", " ", doc[page - 1].get_textpage().get_text_range().replace("￾", "-"))
    return _pages[key]


def printed_forms(value: D, unit: str) -> list[str]:
    a = abs(value)
    if unit == "TZS_per_share":
        return [f"{a:,.2f}"] + ([f"{a:,.0f}"] if a == a.to_integral_value() else [])
    return [f"{a:,.0f}"]


@pytest.fixture(scope="module")
def db():
    with SessionLocal() as s:
        yield {
            "docs": {d.id: d for d in s.query(SourceDocument).filter_by(security_id=SECURITY)},
            "facts": s.query(FinancialFact).filter_by(security_id=SECURITY, is_primary=True).all(),
            "checks": s.query(ValidationCheck).filter_by(security_id=SECURITY).all(),
            "conflicts": s.query(ExtractionConflict).filter_by(security_id=SECURITY).all(),
            "risks": s.query(RiskItem).filter_by(security_id=SECURITY).all(),
        }


@pytest.mark.parametrize("item,year,value,report,page", HAND_CHECKED)
def test_hand_checked_group_figures(db, item, year, value, report, page):
    f = next((f for f in db["facts"] if f.item_code == item and f.fiscal_year == year), None)
    assert f is not None, f"{item} FY{year} not loaded"
    doc = db["docs"][f.document_id]
    assert f.value == value
    assert (doc.fiscal_year, f.page) == (report, page), "cited to a different report or page"
    assert any(form in page_text(doc.file_path, page) for form in printed_forms(f.value, f.unit))


def test_every_stored_figure_is_printed_on_its_cited_page(db):
    missing = [(f.item_code, f.fiscal_year, f.page) for f in db["facts"]
               if not any(form in page_text(db["docs"][f.document_id].file_path, f.page)
                          for form in printed_forms(f.value, f.unit))]
    assert missing == []


def test_derived_figures_quote_their_reason(db):
    derived = [f for f in db["facts"] if f.extraction_method.startswith("derived:")]
    for f in derived:
        assert f.item_code in ("equity_owners", "nci") and f.fiscal_year <= 2021
        assert "100% owned by the parent entity" in f.raw_text


def test_group_not_bank_columns(db):
    # GROUP and BANK differ in 2025; reading the BANK column would give 20,763,416 total assets.
    ta = next(f for f in db["facts"] if f.item_code == "total_assets" and f.fiscal_year == 2025)
    assert ta.value != D("20763416")


def test_balance_sheet_ties_every_year(db):
    ties = [c for c in db["checks"] if c.check_name == "assets = liabilities + equity"]
    assert ties and all(c.passed for c in ties), [(c.fiscal_year, c.detail) for c in ties if not c.passed]


# Lines where the readers do not agree in some years (docs/KNOWN_GAPS.md). They are shown as
# CONFLICTING_SOURCE / INSUFFICIENT_DATA, never as a number. Anything outside this list is a new problem.
KNOWN_UNRESOLVED = {"eps", "interest_income_eir", "interest_expense_eir", "impairment_loans", "cash_end"}


def test_only_known_lines_are_unresolved(db):
    open_ = {(c.fiscal_year, c.item_code) for c in db["conflicts"]
             if c.kind in ("MISSING_IN_METHOD", "METHOD_DISAGREEMENT")}
    assert {item for _, item in open_} <= KNOWN_UNRESOLVED, sorted(open_)
    # A disagreement in one report is acceptable only when another report supplies the same year.
    loaded = {(f.fiscal_year, f.item_code) for f in db["facts"]}
    unusable = sorted(x for x in open_ if x not in loaded and x[0] >= 2022)
    assert unusable == [(2022, "impairment_loans"), (2023, "impairment_loans")], unusable


def test_documents_and_risks(db):
    assert {d.fiscal_year for d in db["docs"].values()} == {2021, 2022, 2023, 2024, 2025}
    for d in db["docs"].values():
        assert hashlib.sha256(Path(REPO_ROOT / d.file_path).read_bytes()).hexdigest() == d.sha256
        assert d.terms_note
    assert len(db["risks"]) == 9
    for r in db["risks"]:
        assert r.quote and r.quote in page_text(db["docs"][r.document_id].file_path, r.page).replace("￾", "-") \
            or re.sub(r"\s+", " ", r.quote)[:60] in page_text(db["docs"][r.document_id].file_path, r.page)
