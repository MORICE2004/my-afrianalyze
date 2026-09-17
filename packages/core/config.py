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
    FIRECRAWL_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
