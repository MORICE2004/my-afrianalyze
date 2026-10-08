"""A scheduled refresh downloads only recent days. These tests prove it can add to the stored series but
never shrink it, never silently rewrite a past close, and still catches a bad new day. Synthetic prices
in a throwaway database (the `db` fixture from test_dse_public_prices)."""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal as D

from packages.database.models import DataSourceStatus, PriceBar, SourceDocument
from pipelines.dse import import_public_index as idx
from pipelines.dse import import_public_prices as prices
from tests.v1.test_dse_public_prices import _price_file, db, row  # noqa: F401  (fixture)


def _bars(maker, instrument="DSE:NMB"):
    with maker() as s:
        return {b.trade_date: (b.close, b.volume, b.source_document_id)
                for b in s.query(PriceBar).filter_by(instrument_id=instrument)}


def _load(tmp_path, rows, *extra):
    return prices.main(["--instrument", "DSE:NMB", "--file", str(_price_file(tmp_path, rows)), *extra])


HISTORY = [row("2026-09-14", 2000), row("2026-09-15", 2010), row("2026-09-16", 2020),
           row("2026-09-17", 2030), row("2026-09-18", 2070)]


def test_a_short_refresh_adds_new_days_and_keeps_every_old_one(tmp_path, db):
    assert _load(tmp_path, HISTORY) == 0
    before = _bars(db)
    assert _load(tmp_path, [row("2026-09-18", 2070), row("2026-10-01", 2080), row("2026-10-02", 2090)]) == 0
    after = _bars(db)
    assert set(before) <= set(after), "a refresh deleted stored history"
    for day, (close, volume, doc) in before.items():
        assert after[day] == (close, volume, doc), f"{day} changed, or lost its original source"
    assert after[date(2026, 10, 2)][0] == D("2090") and len(after) == 7


def test_the_same_refresh_twice_changes_nothing(tmp_path, db):
    assert _load(tmp_path, HISTORY) == 0
    first = _bars(db)
    assert _load(tmp_path, HISTORY) == 0
    assert _bars(db) == first
    with db() as s:
        assert s.query(SourceDocument).count() == 1, "the same file was recorded twice"


def test_a_past_close_revised_by_the_source_is_kept_and_reported(tmp_path, db, capsys):
    assert _load(tmp_path, HISTORY) == 0
    code = _load(tmp_path, [row("2026-09-17", 2035), row("2026-10-01", 2080)])
    out = capsys.readouterr().out
    assert code == 2, "a held-back revision must fail the run so a person looks at it"
    bars = _bars(db)
    assert bars[date(2026, 9, 17)][0] == D("2030"), "a stored close was overwritten without review"
    assert bars[date(2026, 10, 1)][0] == D("2080"), "the genuinely new day is still added"
    assert "2026-09-17 stored 2030, download says 2035" in out
    with db() as s:
        assert s.get(DataSourceStatus, "dse_prices").status == "partial"


def test_a_reviewed_revision_can_be_applied_on_purpose(tmp_path, db):
    assert _load(tmp_path, HISTORY) == 0
    assert _load(tmp_path, [row("2026-09-17", 2035)], "--accept-revisions") == 0
    assert _bars(db)[date(2026, 9, 17)][0] == D("2035")


def test_a_bad_first_new_day_is_compared_with_the_last_stored_day(tmp_path, db):
    """The download alone (one day) has nothing to compare with; joined to the store it is a 10x jump."""
    assert _load(tmp_path, HISTORY) == 0
    assert _load(tmp_path, [row("2026-10-01", 20700)]) == 1
    assert date(2026, 10, 1) not in _bars(db)


def _index_file(path, days):
    path.write_text("\n".join(json.dumps({"asked_for": d, "indices": [
        {"Code": "DSEI", "ClosingPrice": f"{lvl:,.2f}", "Change": f"{chg:.2f}"}]}) for d, lvl, chg in days),
        encoding="utf-8")
    return path


def test_the_index_refresh_keeps_history_and_checks_its_first_day_against_the_store(tmp_path, db):
    full = _index_file(tmp_path / "full.jsonl", [("2026-09-16", 4600.00, 0), ("2026-09-17", 4610.00, 10.00),
                                                  ("2026-09-18", 4602.26, -7.74)])
    assert idx.main(["--file", str(full)]) == 0
    stored = _bars(db, "DSE:DSEI")
    # A refresh file holding only the new days. The first follows the stored 4602.26 (+5.00 = 4607.26) ...
    good = _index_file(tmp_path / "new.jsonl", [("2026-10-01", 4607.26, 5.00), ("2026-10-02", 4610.00, 2.74)])
    assert idx.main(["--file", str(good)]) == 0
    after = _bars(db, "DSE:DSEI")
    assert all(after[d][0] == stored[d][0] for d in stored) and len(after) == 5
    # ... and one whose change does not follow the stored level is refused, not let through as "first day".
    bad = _index_file(tmp_path / "bad.jsonl", [("2026-10-05", 4800.00, 1.00)])
    idx.main(["--file", str(bad)])
    assert date(2026, 10, 5) not in _bars(db, "DSE:DSEI")


def test_a_source_outage_is_recorded_and_nothing_is_lost(tmp_path, db, monkeypatch):
    """The DSE is unreachable during the scheduled refresh: the run fails visibly, /health says so, and the
    stored history and its last-success time are untouched."""
    import requests

    from pipelines.dse import refresh_prices
    from packages.database.models import Security

    assert _load(tmp_path, HISTORY) == 0
    with db() as s:
        s.add(Security(id="DSE:NMB", exchange="DSE", local_ticker="NMB", name="NMB Bank Plc", sector="Banking",
                       currency="TZS", is_bank=True, industry_template="bank", listing_status="listed",
                       listing_url="https://dse.co.tz", verified_at=date(2026, 9, 1)))
        s.commit()
        before = s.get(DataSourceStatus, "dse_prices").last_success_at
    monkeypatch.setattr(refresh_prices, "SessionLocal", db)
    monkeypatch.setattr(refresh_prices.time, "sleep", lambda *_: None)

    def down(*a, **k):
        raise requests.ConnectionError("dse.co.tz unreachable")
    monkeypatch.setattr(requests, "get", down)          # the DSE adapter (packages/market_data) downloads
    assert refresh_prices.main(["30"]) == 1
    with db() as s:
        st = s.get(DataSourceStatus, "dse_prices")
        assert st.status == "partial" and "Needs attention: NMB" in st.detail
        assert st.last_success_at == before
    assert len(_bars(db)) == len(HISTORY)


def _with_activity(r: dict, turnover, high, low) -> dict:
    return {**r, "turnover": turnover, "high": high, "low": low, "opening_price": r["closing_price"],
            "market_cap": r["closing_price"] * 1000}


def test_published_turnover_fills_an_empty_day_but_never_overwrites_a_stored_one(tmp_path, db):
    assert _load(tmp_path, HISTORY) == 0                       # an old-style file: close and volume only
    day = date(2026, 9, 18)
    with db() as s:
        bar = s.query(PriceBar).filter_by(instrument_id="DSE:NMB", trade_date=day).one()
        assert bar.turnover is None and bar.high is None
        doc_before = bar.source_document_id
    # The same days again, now with the DSE's other published fields: empty fields are filled.
    rich = [_with_activity(r, 207000, 2080, 2060) for r in HISTORY]
    assert _load(tmp_path, rich) == 0
    with db() as s:
        bar = s.query(PriceBar).filter_by(instrument_id="DSE:NMB", trade_date=day).one()
        assert (bar.turnover, bar.high, bar.low) == (D("207000"), D("2080"), D("2060"))
        assert bar.source_document_id == doc_before, "the close still comes from the file it was first read from"
    # A later file stating different turnover for a stored day does not overwrite it.
    other = [_with_activity(r, 999, 9999, 1) for r in HISTORY]
    assert _load(tmp_path, other) == 0
    with db() as s:
        bar = s.query(PriceBar).filter_by(instrument_id="DSE:NMB", trade_date=day).one()
        assert bar.turnover == D("207000") and bar.high == D("2080")
