"""Exact decimal storage for money and rates.

PostgreSQL stores NUMERIC exactly. SQLite has no exact decimal type, so values
are stored as text there and converted back to Decimal on read. Either way the
application only ever sees decimal.Decimal, never a float.
"""
from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.types import TypeDecorator


class ExactDecimal(TypeDecorator):
    impl = Numeric(28, 10)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(64))
        return dialect.type_descriptor(Numeric(28, 10))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, float):
            raise TypeError("Floats are not accepted for exact values; pass a Decimal or a string")
        d = value if isinstance(value, Decimal) else Decimal(str(value))
        return str(d) if dialect.name == "sqlite" else d

    def process_result_value(self, value, dialect):
        return None if value is None else Decimal(str(value))
