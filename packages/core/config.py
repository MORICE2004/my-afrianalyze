from enum import Enum
from pathlib import Path

from pydantic import field_validator, model_validator
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
    # BUY / HOLD / SELL next to the model view (PRODUCT_CONTEXT.md section 71). The owner confirmed on
    # 2026-09-19 that no licence is needed, so labels are on. Set SHOW_TRADE_LABELS=false to hide them.
    SHOW_TRADE_LABELS: bool = True
    # Host names the API answers to, comma separated. "*" (the default) accepts any; set it to the API's own
    # domain in production so a request with a forged Host header is refused.
    ALLOWED_HOSTS: str = "*"
    # Error reporting. Empty means Sentry is off; the DSN is not a password but is kept out of git anyway.
    SENTRY_DSN: str = ""
    # Requests per minute per client for the expensive endpoints (report and PDF builds).
    EXPENSIVE_REQUESTS_PER_MINUTE: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("DATABASE_URL")
    @classmethod
    def _sqlalchemy_scheme(cls, url: str) -> str:
        # Render and Heroku hand out "postgres://" URLs, which SQLAlchemy 2 refuses.
        return "postgresql://" + url[len("postgres://"):] if url.startswith("postgres://") else url

    @model_validator(mode="after")
    def _production_is_not_a_laptop(self) -> "Settings":
        if self.APP_ENV != AppEnvironment.PRODUCTION:
            return self
        problems = []
        if not self.DATABASE_URL.startswith("postgresql"):
            problems.append("DATABASE_URL must be a PostgreSQL URL (SQLite is for local development only)")
        if any(h in self.CORS_ORIGINS for h in ("localhost", "127.0.0.1")) or "*" in self.CORS_ORIGINS:
            problems.append("CORS_ORIGINS must list the web app's real domain, not localhost or *")
        if problems:
            raise ValueError("Refusing to start in PRODUCTION: " + "; ".join(problems))
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_hosts(self) -> list[str]:
        return [h.strip() for h in self.ALLOWED_HOSTS.split(",") if h.strip()] or ["*"]


settings = Settings()
