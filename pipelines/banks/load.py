r"""Load a bank's documents, resolved facts, conflicts, checks and cited risks, and open a
draft research run.

    .venv\Scripts\python -m pipelines.banks.load --bank=crdb

  * Values are loaded as exact Decimals from resolved.json (written as strings).
  * Each annual report gets its publication date: the date the board approved the
    financial statements, read from the statement page (with the quoted evidence).
  * Risk items are verbatim sentences located in the annual report; a quote that is
    not found on its page stops the load.
  * A new research run is created in status "draft". Only a named reviewer can move
    it to "published" (pipelines/review.py). Earlier draft runs are superseded.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from packages.core.config import settings
from packages.database.models import (
    DataSourceStatus,
    ExtractionConflict,
    FinancialFact,
    ResearchRun,
    ReviewEvent,
    RiskItem,
    SourceDocument,
    ValidationCheck,
)
from packages.database.session import SessionLocal
from pipelines.banks.profiles import BankProfile, profile_for


def page_text(profile: BankProfile, year: int, page: int) -> str:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(profile.pdf_path(year)))
    text = doc[page - 1].get_textpage().get_text_range()
    text = text.replace("￾", "-").replace("’", "'")
    return re.sub(r"\s+", " ", text)


def publication_date(profile: BankProfile, year: int, statement_pages: list[int]) -> tuple[date | None, str | None]:
    """Date the board approved the financial statements, read from the statement pages."""
    approval = re.compile(profile.approval_re, re.I)
    for p in statement_pages:
        m = approval.search(page_text(profile, year, p))
        if m and int(m.group(3)) == year + 1:
            d = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%d %B %Y").date()
            return d, f"p{p}: \"{m.group(0)}\""
    return None, None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str]) -> int:
    profile = profile_for(next((a.split("=", 1)[1] for a in argv if a.startswith("--bank=")), ""))
    if profile is None:
        print("Usage: python -m pipelines.banks.load --bank=<nmb|crdb>")
        return 2
    SECURITY = profile.security_id
    RESOLVED = profile.processed_dir / "resolved.json"
    ALL_ITEMS = profile.all_items
    RISKS = profile.risks
    manifest = json.loads((profile.raw_dir / "manifest.json").read_text())
    resolved = json.loads(RESOLVED.read_text(encoding="utf-8"))
    with SessionLocal() as s:
        s.query(RiskItem).filter_by(security_id=SECURITY).delete()
        s.query(FinancialFact).filter_by(security_id=SECURITY).delete()
        s.query(ExtractionConflict).filter_by(security_id=SECURITY).delete()
        s.query(ValidationCheck).filter_by(security_id=SECURITY).delete()
        s.query(SourceDocument).filter_by(security_id=SECURITY, kind="annual_report").delete()
        s.flush()

        pages_by_report: dict[int, set[int]] = {}
        for f in resolved["facts"]:
            if f["item_code"] in ("total_assets", "profit_for_year"):
                pages_by_report.setdefault(f["report_year"], set()).add(f["page"])

        docs: dict[int, SourceDocument] = {}
        for year, m in sorted(manifest.items(), key=lambda kv: int(kv[0])):
            y = int(year)
            pages = sorted(pages_by_report.get(y, set()))
            pages += [p + 1 for p in pages]  # the signature block can fall on the next page
            published, evidence = publication_date(profile, y, pages)
            d = SourceDocument(
                security_id=SECURITY, kind="annual_report", fiscal_year=y,
                title=f"{profile.name} Annual Report {year}", publisher=profile.name,
                url=m["url"], listing_url=m["listing_url"], file_path=m["file"], sha256=m["sha256"],
                published_on=published, published_on_evidence=evidence,
                retrieved_at=datetime.fromisoformat(m["retrieved_at"]), terms_note=profile.terms_note)
            s.add(d)
            docs[y] = d
        s.flush()

        for f in resolved["facts"]:
            code = f["item_code"]
            if code == "dps":
                statement, unit, basis = "NOTE", "TZS_per_share", "bank"
            else:
                section, spec = ALL_ITEMS[code]
                statement, unit, basis = section.statement, spec.unit, section.basis
            s.add(FinancialFact(
                security_id=SECURITY, fiscal_year=f["fiscal_year"], statement=statement, item_code=code,
                label_as_reported=f["label"], value=Decimal(str(f["value"])), unit=unit, currency="TZS",
                period_end=date(f["fiscal_year"], 12, 31), basis=basis,
                document_id=docs[f["report_year"]].id, page=f["page"], column_role=f["column_role"],
                extraction_method=f["method"], agreed_by=f["agreed_by"], raw_text=f["raw"][:2000]))

        def dec(v):
            return None if v is None else Decimal(str(v))

        for c in resolved["conflicts"]:
            s.add(ExtractionConflict(
                security_id=SECURITY, fiscal_year=c["fiscal_year"], item_code=c["item_code"], kind=c["kind"],
                value_a=dec(c["value_a"]), source_a=c["source_a"], value_b=dec(c["value_b"]), source_b=c["source_b"],
                document_id=docs[c["report_year"]].id if c.get("report_year") in docs else None,
                page=c.get("page"), detail=c["detail"], status="OPEN"))

        for c in resolved["checks"]:
            s.add(ValidationCheck(
                security_id=SECURITY, fiscal_year=c["fiscal_year"], check_name=c["check_name"],
                passed=c["passed"], expected=dec(c["expected"]), actual=dec(c["actual"]), detail=c["detail"]))

        # Figures that add up wrongly inside the source document (config/source_issues.json).
        issues = [i for i in json.loads((settings.CONFIG_DIR / "source_issues.json").read_text(encoding="utf-8"))
                  ["issues"] if i["security_id"] == SECURITY]
        by_key = {(f["item_code"], f["fiscal_year"]): f for f in resolved["facts"]}
        stale = []
        for issue in issues:
            y = issue["fiscal_year"]
            check = next((c for c in resolved["checks"]
                          if c["fiscal_year"] == y and c["check_name"] == issue["check_name"]), None)
            if check is None or check["passed"]:
                stale.append(f"FY{y} '{issue['check_name']}' no longer fails")
            for item in issue["items"]:
                f = by_key.get((item, y))
                if f is None or f["report_year"] != issue["report_year"] or f["page"] != issue["page"]:
                    stale.append(f"FY{y} {item} is no longer read from the {issue['report_year']} report "
                                 f"p{issue['page']}")
                    continue
                s.add(ExtractionConflict(
                    security_id=SECURITY, fiscal_year=y, item_code=item, kind="SOURCE_INCONSISTENCY",
                    value_a=dec(f["value"]), source_a=f"{issue['report_year']} report p{issue['page']} (as stated)",
                    value_b=None, source_b="", document_id=docs[issue["report_year"]].id, page=issue["page"],
                    detail=issue["evidence"], status="OPEN"))
        if stale:
            s.rollback()
            print("config/source_issues.json no longer matches the data, nothing loaded: " + "; ".join(stale))
            return 1

        missing = []
        for category, title, year, page, pattern in RISKS:
            m = re.search(pattern, page_text(profile, year, page), re.I)
            if not m:
                missing.append(f"{title} (p{page})")
                continue
            s.add(RiskItem(security_id=SECURITY, category=category, title=title, quote=m.group(0).strip(),
                           document_id=docs[year].id, page=page))
        if missing:
            s.rollback()
            print("Risk quotes not found, nothing loaded: " + "; ".join(missing))
            return 1

        # ---------------------------------------------------------- research run (draft)
        now = datetime.now(timezone.utc)
        data_hash = sha256_file(RESOLVED)
        config_hash = hashlib.sha256(b"".join(
            (settings.CONFIG_DIR / n).read_bytes() for n in ("valuation.json", "recommendation.json", "source_issues.json"))).hexdigest()
        prefix = f"RA-{now:%Y%m%d}-"
        n_today = s.query(ResearchRun).filter(ResearchRun.id.like(prefix + "%")).count()
        run_id = f"{prefix}{n_today + 1:03d}"
        for old in s.query(ResearchRun).filter(ResearchRun.security_id == SECURITY,
                                               ResearchRun.status.in_(["draft", "in_review"])):
            old.status, old.superseded_by = "superseded", run_id
            s.add(ReviewEvent(run_id=old.id, action="supersede", actor="pipeline",
                              note=f"Superseded by new data load {run_id}"))
        failed = [c for c in resolved["checks"] if not c["passed"]]
        s.add(ResearchRun(id=run_id, security_id=SECURITY, status="draft", created_at=now,
                          data_sha256=data_hash, config_sha256=config_hash,
                          summary={"facts": len(resolved["facts"]), "conflicts": len(resolved["conflicts"]),
                                   "checks": len(resolved["checks"]), "failed_checks": len(failed),
                                   "source_issues": len(issues),
                                   "methods": resolved["methods"]}))
        s.flush()
        s.add(ReviewEvent(run_id=run_id, action="create", actor="pipeline",
                          note=f"Draft created from resolved.json sha256 {data_hash[:12]}"))

        s.merge(DataSourceStatus(source=f"{profile.key}_annual_reports", last_success_at=now, last_attempt_at=now,
                                 status="ok", max_age_hours=24 * 400,
                                 detail=f"{len(docs)} annual reports, {len(resolved['facts'])} facts, "
                                        f"{len(resolved['conflicts'])} conflicts"))
        existing = s.get(DataSourceStatus, "dse_prices")
        if existing is None or existing.status != "ok":
            s.merge(DataSourceStatus(
                source="dse_prices", last_success_at=None, last_attempt_at=now, status="blocked",
                max_age_hours=24 * 3,
                detail="DSE end-of-day and historical prices are licensed (DSE Data Vending Policy cl. 16.3.3, 23.1). "
                       "No licensed file has been imported. See pipelines/dse/import_prices.py."))
        s.commit()
        pubs = {y: (d.published_on.isoformat() if d.published_on else None) for y, d in docs.items()}
        print(f"Loaded {len(docs)} documents (published {pubs}), {len(resolved['facts'])} facts, "
              f"{len(resolved['conflicts'])} conflicts, {len(resolved['checks'])} checks, {len(RISKS)} risk items. "
              f"Research run {run_id} created as draft.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
