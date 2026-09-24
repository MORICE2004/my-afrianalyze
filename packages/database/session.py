from typing import Generator
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from packages.core.config import settings

logger = logging.getLogger(__name__)

# Connection arguments for PostgreSQL vs SQLite
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=connect_args
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning(f"Could not initialize database engine for {settings.DATABASE_URL}: {e}")
    engine = None
    SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides an active database session.
    """
    if SessionLocal is None:
        raise RuntimeError("Database connection not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Dependency check for health/readiness probes.
    """
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return False
