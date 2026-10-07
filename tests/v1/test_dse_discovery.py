"""Security-master discovery and market breadth. HTML fragments imitate the DSE pages (shape copied from
dse.co.tz on 2026-10-07); the name cases are the ones the first dry run got wrong. Synthetic prices."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import apps.api.main as api
from packages.database.base import Base
from packages.database.models import PriceBar, Security, SourceDocument
from packages.database.session import get_session
from pipelines.dse.discover_securities import name_from_profile, parse_list

LIST = """<table><tbody>
<tr class="x"> <td class="a">1</td> <td class="a">DSE</td> <td class="a"></td> <td><a href="https://dse.co.tz/listed/company/profile?id=1">View</a></td> </tr>
<tr class="x"> <td class="a">2</td> <td class="a">CRDB</td> <td class="a"></td> <td><a href="https://dse.co.tz/listed/company/profile?id=2">View</a></td> </tr>
</tbody></table>"""


def test_the_listed_company_table_is_parsed():
    assert parse_list(LIST) == [("DSE", "https://dse.co.tz/listed/company/profile?id=1"),
                                ("CRDB", "https://dse.co.tz/listed/company/profile?id=2")]


@pytest.mark.parametrize("text, name", [
    ("CRDB Bank PLC is the leading banking institution", "CRDB Bank PLC"),
    ("The AFRIPRISE INVESTMENT PLC was incorporated", "AFRIPRISE INVESTMENT PLC"),
    ("Tanzania Portland Cement Public Limited Company (TPCPLC), a subsidiary", "Tanzania Portland Cement Public Limited Company"),
    # The dry run wrongly read these: the name must open the profile, and a heading is not a name.
    ("KCB Group is registered ... listed on the Dar Es Salaam Stock Exchange PLC", None),
    ("The Dar es Salaam Stock Exchange (DSE) is a market place", None),
    ("HISTORICAL BACKGROUND Mwalimu Commercial Bank PLC. (hereinafter", None),
    ("The historical background of MuCoBa starts in 1984 ... Incomet Fund Ltd", None),
])
def test_names_are_taken_only_when_the_profile_opens_with_one(text, name):
    assert name_from_profile(text) == name


@pytest.fixture()
def client(tmp_path):
    eng = create_engine(f"sqlite:///{(tmp_path / 'm.db').as_posix()}")
    Base.metadata.create_all(eng)
    mk = sessionmaker(bind=eng, expire_on_commit=False)
    with mk() as s:
        doc = SourceDocument(kind="public_price_file", title="t", publisher="DSE", url="https://dse.co.tz",
                             retrieved_at=datetime.now(timezone.utc))
        s.add(doc)
        s.flush()
        bars = {"UP": ("100", "110", "5"), "DOWN": ("100", "90", "7"), "FLAT": ("100", "100", "3"),
                "QUIET": ("100", "100", "0")}            # QUIET did not trade: the DSE repeats the close
        for code, (prev, last, vol) in bars.items():
            s.add(Security(id=f"DSE:{code}", exchange="DSE", local_ticker=code, name=code, sector="Unclassified",
                           currency="TZS", is_bank=False, industry_template="unclassified", listing_status="listed",
                           listing_url="https://dse.co.tz", verified_at=date(2026, 10, 7)))
            s.add(PriceBar(instrument_id=f"DSE:{code}", trade_date=date(2026, 10, 5), close=Decimal(prev), volume=Decimal(9),
                           source_document_id=doc.id))
            s.add(PriceBar(instrument_id=f"DSE:{code}", trade_date=date(2026, 10, 6), close=Decimal(last), volume=Decimal(vol),
                           source_document_id=doc.id))
        s.commit()

    def _s():
        s = mk()
        try:
            yield s
        finally:
            s.close()
    api.app.dependency_overrides[get_session] = _s
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_breadth_counts_a_day_without_a_trade_as_no_trade_not_unchanged(client):
    m = client.get("/api/v1/markets/overview").json()["movers"]
    assert m["breadth"] == {"up": 1, "down": 1, "unchanged": 1, "no_trade": 1, "not_updated": 0}
    assert [x["security_id"] for x in m["gainers"]] == ["DSE:UP"] and Decimal(m["gainers"][0]["change"]) == Decimal("0.1")
    assert [x["security_id"] for x in m["losers"]] == ["DSE:DOWN"]
    assert "Dar es Salaam Stock Exchange" in m["attribution"]
