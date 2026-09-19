from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class AppEnvironment(str, Enum):
    TEST = "TEST"
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"


class Settings(BaseSettings):
    # TEST makes some legacy connectors return fixture data, so it must be opted into
    # explicitly (tests/conftest.py does this). It is never the default.
    APP_ENV: AppEnvironment = AppEnvironment.DEVELOPMENT
    # Local development uses SQLite because PostgreSQL is not required to run the
    # vertical slice. docker-compose.yml sets a PostgreSQL URL.
    DATABASE_URL: str = f"sqlite:///{(REPO_ROOT / 'data' / 'afrianalyze.db').as_posix()}"
    DATA_DIR: Path = REPO_ROOT / "data"
    CONFIG_DIR: Path = REPO_ROOT / "config"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"
    FIRECRAWL_API_KEY: str = ""
    # BUY / HOLD / SELL labels may need an investment adviser licence (PRODUCT_CONTEXT.md
    # section 71). Off until the owner confirms the legal position.
    SHOW_TRADE_LABELS: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
