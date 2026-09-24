import os
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(str, Enum):
    TEST = "TEST"
    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTION = "PRODUCTION"


class Settings(BaseSettings):
    APP_ENV: AppEnvironment = AppEnvironment.TEST
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/afrianalyze"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    LLM_API_KEY: str = ""
    FIRECRAWL_API_KEY: str = ""
    SENTRY_DSN: str = ""
    POSTHOG_API_KEY: str = ""
    S3_BUCKET: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
