from enum import Enum
from pydantic import BaseModel

class DSESource(str, Enum):
    COMPANIES = "https://dse.co.tz/companies"
    MARKET_REPORT = "https://dse.co.tz/market-report"
    ANNOUNCEMENTS = "https://dse.co.tz/announcements"

class RateLimitConfig(BaseModel):
    max_requests_per_minute: int = 30
    delay_between_requests: float = 2.0

dse_rate_limit = RateLimitConfig()
