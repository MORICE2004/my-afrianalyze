from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from uuid import UUID, uuid4

class AuthorityLevel(str, Enum):
    CENTRAL_BANK = "CENTRAL_BANK"
    OFFICIAL_EXCHANGE = "OFFICIAL_EXCHANGE"
    AUDITED_FINANCIALS = "AUDITED_FINANCIALS"
    REGULATORY_FILING = "REGULATORY_FILING"
    FUND_MANAGER = "FUND_MANAGER"
    NEWS_OUTLET = "NEWS_OUTLET"
    UNVERIFIED = "UNVERIFIED"

class SourceRegistry(BaseModel):
    source_id: UUID = Field(default_factory=uuid4)
    institution: str
    authority_level: AuthorityLevel
    url: Optional[HttpUrl] = None
    description: Optional[str] = None
