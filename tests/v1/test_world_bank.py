"""World Bank loader: exact decimals, empty years stay empty, implausible values stop the job. The response
imitates the World Bank API's shape; no network is used. Throwaway database."""
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pipelines.macro as macro
from packages.database.base import Base
from packages.database.models import MacroObservation


def _answer(rows):
    return json.dumps([{"page": 1, "pages": 1, "lastupdated": "2026-07-13"},
                       [{"indicator": {"id": "X", "value": "Indicator"}, "country": {"id": "TZ", "value": "Tanzania"},
                         "countryiso3code": iso3, "date": year, "value": value} for iso3, year, value in rows]])


class _Resp:
    def __init__(self, text):
        self.text, self.status_code = text, 200

    def raise_for_status(self):
        pass


@pytest.fixture()
def session(tmp_path):
    eng = create_engine(f"sqlite:///{(tmp_path / 'wb.db').as_posix()}")
    Base.metadata.create_all(eng)
    with sessionmaker(bind=eng)() as s:
        yield s


def test_values_are_exact_and_empty_years_stay_empty(session, monkeypatch):
    # 5.85286828692739 as JSON; parsed as a float it would not be exact.
    text = _answer([("TZA", "2025", 5.85286828692739), ("TZA", "2024", None), ("KEN", "2025", 4.0)])
    monkeypatch.setattr(macro.requests, "get", lambda *a, **k: _Resp(text))
    macro.world_bank(session)
    rows = session.query(MacroObservation).filter_by(series_id="WB_TZA_NY.GDP.MKTP.KD.ZG").all()
    assert [(r.observation_date, r.value) for r in rows] == [(date(2025, 12, 31), Decimal("0.0585286828692739"))]
    assert rows[0].attributes["as_published"] == "5.85286828692739" and rows[0].attributes["licence"] == "CC BY 4.0"


def test_an_implausible_value_stops_the_job_instead_of_being_stored(session, monkeypatch):
    monkeypatch.setattr(macro.requests, "get", lambda *a, **k: _Resp(_answer([("UGA", "2025", 85.0)])))   # 85% growth
    with pytest.raises(ValueError, match="plausible"):
        macro.world_bank(session)


def test_an_unexpected_answer_shape_is_refused(session, monkeypatch):
    monkeypatch.setattr(macro.requests, "get", lambda *a, **k: _Resp('[{"message": "Invalid value"}]'))
    with pytest.raises(ValueError, match="unexpected shape"):
        macro.world_bank(session)
