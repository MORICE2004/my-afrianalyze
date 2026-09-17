import os
import json
import hashlib
from typing import Optional, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
import redis

class CacheSettings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

class CacheManager:
    """
    Redis Caching Layer for LLM responses and Market Data.
    """
    def __init__(self):
        self.app_env = os.environ.get("APP_ENV", "TEST")
        self.settings = CacheSettings()
        self.client = None
        if self.app_env != "TEST":
            try:
                self.client = redis.Redis.from_url(self.settings.redis_url, decode_responses=True)
            except Exception:
                self.client = None

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def get(self, key: str, hash_key: bool = False) -> Optional[str]:
        if self.app_env == "TEST" or not self.client:
            return None
        
        lookup_key = self._hash_key(key) if hash_key else key
        try:
            return self.client.get(lookup_key)
        except Exception:
            return None

    def set(self, key: str, value: str, ttl: int = 3600, hash_key: bool = False) -> bool:
        if self.app_env == "TEST" or not self.client:
            return False
            
        lookup_key = self._hash_key(key) if hash_key else key
        try:
            self.client.setex(lookup_key, ttl, value)
            return True
        except Exception:
            return False

cache_manager = CacheManager()
