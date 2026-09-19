"""Money and rates are stored exactly (CLAUDE.md rule 4)."""
from decimal import Decimal

import pytest
from sqlalchemy import Column, Integer, create_engine, insert, select
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import DeclarativeBase

from packages.analysis.common import to_dec
from packages.database.types import ExactDecimal


class _Base(DeclarativeBase):
    pass


class _Row(_Base):
    __tablename__ = "exact_rows"
    id = Column(Integer, primary_key=True)
    value = Column(ExactDecimal)


@pytest.fixture()
def engine():
    eng = create_engine("sqlite:///:memory:")
    _Base.metadata.create_all(eng)
    return eng


def test_round_trip_keeps_every_digit(engine):
    # 28 significant digits: a float would keep about 16.
    exact = Decimal("12345678901234567.8901234567")
    with engine.begin() as conn:
        conn.execute(insert(_Row).values(id=1, value=exact))
        got = conn.execute(select(_Row.value)).scalar_one()
    assert isinstance(got, Decimal)
    assert got == exact


def test_float_is_refused(engine):
    with engine.begin() as conn, pytest.raises(StatementError) as err:
        conn.execute(insert(_Row).values(id=2, value=0.1))
    assert "Floats are not accepted" in str(err.value)


def test_strings_and_ints_are_accepted(engine):
    with engine.begin() as conn:
        conn.execute(insert(_Row).values(id=3, value="0.1"))
        conn.execute(insert(_Row).values(id=4, value=7))
        rows = dict(conn.execute(select(_Row.id, _Row.value)).all())
    assert rows[3] == Decimal("0.1")
    assert rows[4] == Decimal("7")


def test_to_dec_uses_the_shortest_repr_of_a_float():
    # 0.1 as a binary float is 0.1000000000000000055511151231257827...; config values must not pick that up.
    assert to_dec(0.1) == Decimal("0.1")
    assert to_dec(0.05) == Decimal("0.05")
    assert to_dec(None) is None
    d = Decimal("1.23")
    assert to_dec(d) is d
