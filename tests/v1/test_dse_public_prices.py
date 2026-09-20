"""The DSE price and index importers: what they keep, what they refuse, and what they never serve on.

These are the newest and least proven parts of the pipeline, and they are the only place where a
number reaches the product from a web address rather than from an audited PDF. So the checks here
are about refusing bad input, not about pretty output.
"""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal as D
from pathlib import Path

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.database.models import Base, PriceBar, SourceDocument
from packages.database.session import SessionLocal
from pipelines.dse import import_public_index as idx
from pipelines.dse import import_public_prices as prices


@pytest.fixture
def db(tmp_path, monkeypatch):
    """A database of its own, so the importers cannot touch the real one."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", future=True)
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(prices, "SessionLocal", maker)
    monkeypatch.setattr(idx, "SessionLocal", maker)
    monkeypatch.setattr(prices, "STORE", tmp_path / "store")
    return maker


def _price_file(tmp_path: Path, rows: list[dict], success: bool = True) -> Path:
    p = tmp_path / "prices.json"
    p.write_text(json.dumps({"success": success, "data": rows}), encoding="utf-8")
    return p


def row(day: str, close, company="NMB", volume=100) -> dict:
    return {"trade_date": f"{day}T00:00:00", "closing_price": close, "volume": volume, "company": company}


def test_a_file_for_the_wrong_company_is_refused(tmp_path, capsys):
    f = _price_file(tmp_path, [row("2026-01-02", 2000, company="CRDB")])
    assert prices.main(["--instrument", "DSE:NMB", "--file", str(f)]) == 1
    assert "Refusing" in capsys.readouterr().out


def test_an_empty_or_failed_answer_is_refused(tmp_path):
    assert prices.main(["--instrument", "DSE:NMB", "--file", str(_price_file(tmp_path, []))]) == 1
    f = _price_file(tmp_path, [row("2026-01-02", 2000)], success=False)
    assert prices.main(["--instrument", "DSE:NMB", "--file", str(f)]) == 1


def test_a_missing_file_is_refused(tmp_path):
    assert prices.main(["--instrument", "DSE:NMB", "--file", str(tmp_path / "nope.json")]) == 1


def test_days_without_a_published_close_are_dropped_not_guessed(tmp_path, db):
    """A blank close is a day the exchange published no level. We must not carry one forward."""
    f = _price_file(tmp_path, [row("2026-01-02", 2000), row("2026-01-05", None), row("2026-01-06", "")])
    assert prices.main(["--instrument", "DSE:NMB", "--file", str(f)]) == 0
    with db() as s:
        bars = s.query(PriceBar).order_by(PriceBar.trade_date).all()
    assert [(b.trade_date, b.close) for b in bars] == [(date(2026, 1, 2), D("2000"))]


def test_prices_are_stored_as_exact_decimals_never_floats(tmp_path, db):
    f = _price_file(tmp_path, [row("2026-01-02", 2070.5, volume=0)])
    assert prices.main(["--instrument", "DSE:NMB", "--file", str(f)]) == 0
    with db() as s:
        bar = s.query(PriceBar).one()
        doc = s.query(SourceDocument).one()
    assert isinstance(bar.close, D) and bar.close == D("2070.5")
    assert bar.volume == D("0"), "a zero-volume day is recorded, not dropped (section 74)"
    assert len(doc.sha256) == 64 and "dse.co.tz" in doc.url and doc.retrieved_at
    assert "owner decided" in doc.terms_note, "the file must record whose decision this was"


def test_an_unexplained_tenfold_fall_stops_the_import(tmp_path, db, capsys):
    """The NMB split arrived as a 90% one-day fall. The next one must not slip through silently."""
    f = _price_file(tmp_path, [row("2026-08-19", 17700, company="ZZZZ"),
                               row("2026-08-24", 1850, company="ZZZZ")])
    assert prices.main(["--instrument", "DSE:ZZZZ", "--file", str(f)]) == 1
    out = capsys.readouterr().out
    assert "no recorded corporate action explains" in out and "17700" in out
    with db() as s:
        assert s.query(PriceBar).count() == 0, "nothing may be stored when the series is not understood"


def test_a_recorded_split_explains_the_fall(tmp_path, db):
    """NMB's own split is recorded, so its series imports without complaint."""
    f = _price_file(tmp_path, [row("2026-08-19", 17700), row("2026-08-24", 1850)])
    assert prices.main(["--instrument", "DSE:NMB", "--file", str(f)]) == 0
    with db() as s:
        assert s.query(PriceBar).count() == 2


def test_the_guard_can_be_overridden_deliberately(tmp_path, db):
    f = _price_file(tmp_path, [row("2026-08-19", 17700, company="ZZZZ"),
                               row("2026-08-24", 1850, company="ZZZZ")])
    assert prices.main(["--instrument", "DSE:ZZZZ", "--file", str(f), "--allow-unexplained-jumps"]) == 0
    with db() as s:
        assert s.query(PriceBar).count() == 2


# ------------------------------------------------------------------ the index


def _jsonl(tmp_path: Path, records: list[dict]) -> Path:
    p = tmp_path / "dsei.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    return p


def dsei(day: str, level: str, change: float) -> dict:
    return {"asked_for": day, "indices": [{"Code": "DSEI", "ClosingPrice": level, "Change": change}]}


def test_a_level_that_does_not_follow_its_own_change_is_not_loaded():
    """The endpoint publishes the day's change too, so the series must reconcile with itself."""
    levels = {date(2026, 1, 2): (D("4600.00"), D("0")),
              date(2026, 1, 5): (D("4610.00"), D("10.00")),     # 4600 + 10 = 4610, agrees
              date(2026, 1, 6): (D("4700.00"), D("5.00"))}      # 4610 + 5 != 4700, does not
    good, bad = idx.reconcile(levels)
    assert sorted(good) == [date(2026, 1, 2), date(2026, 1, 5)]
    assert len(bad) == 1 and "2026-01-06" in bad[0]


def test_a_quiet_day_is_kept():
    levels = {date(2026, 1, 2): (D("4600.00"), D("0")),
              date(2026, 1, 5): (D("4600.00"), D("0"))}
    good, bad = idx.reconcile(levels)
    assert len(good) == 2 and bad == []


def test_rounding_of_a_hundredth_is_tolerated_but_a_real_gap_is_not():
    within = {date(2026, 1, 2): (D("4600.00"), D("0")), date(2026, 1, 5): (D("4610.01"), D("10.00"))}
    outside = {date(2026, 1, 2): (D("4600.00"), D("0")), date(2026, 1, 5): (D("4610.50"), D("10.00"))}
    assert idx.reconcile(within)[1] == []
    assert len(idx.reconcile(outside)[1]) == 1


def test_read_levels_reports_failed_and_empty_dates_instead_of_skipping_them(tmp_path):
    path = _jsonl(tmp_path, [dsei("2026-01-02", "4,600.00", 0),
                             {"asked_for": "2026-01-05", "error": "timed out"},
                             {"asked_for": "2026-01-06", "indices": [{"Code": "TSI", "ClosingPrice": "1", "Change": 0}]}])
    levels, problems = idx.read_levels(path, "DSEI")
    assert list(levels) == [date(2026, 1, 2)]
    assert levels[date(2026, 1, 2)] == (D("4600.00"), D("0"))   # commas stripped
    assert len(problems) == 2 and "timed out" in problems[0] and "no DSEI" in problems[1]


def test_price_and_index_files_are_never_served_on():
    """The DSE restricts redistribution: we calculate from its data, we do not republish the file."""
    from fastapi.testclient import TestClient

    from apps.api.main import app
    client = TestClient(app)
    with SessionLocal() as s:
        docs = s.query(SourceDocument).filter(
            SourceDocument.kind.in_(["public_price_file", "public_index_file"])).all()
        ids = [d.id for d in docs]
    if not ids:
        pytest.skip("no price files loaded in this database")
    for doc_id in ids:
        assert client.get(f"/api/v1/sources/{doc_id}/file").status_code == 403
