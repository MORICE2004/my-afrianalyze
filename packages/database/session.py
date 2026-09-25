from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from packages.core.config import settings

if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False}, future=True)
else:
    # Managed Postgres (Neon, Render, Supabase) closes idle connections, so test each one before use and
    # replace it after five minutes. The pool is small because a free-tier database allows few connections.
    engine = create_engine(settings.DATABASE_URL, future=True, pool_pre_ping=True, pool_recycle=300,
                           pool_size=5, max_overflow=5, pool_timeout=10,
                           connect_args={"connect_timeout": 10})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
