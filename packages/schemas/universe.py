from enum import Enum
from pydantic import BaseModel
from typing import Optional

class ResearchUniverseStatus(str, Enum):
    EQUITIES_ONLY = "EQUITIES_ONLY"
    FULL_TANZANIA_UNIVERSE = "FULL_TANZANIA_UNIVERSE"

class PortfolioMode(str, Enum):
    FULL_UNIVERSE = "FULL_UNIVERSE"
    PARTIAL_UNIVERSE = "PARTIAL_UNIVERSE"
    CUSTOM_UNIVERSE = "CUSTOM_UNIVERSE"

class UniverseConfig(BaseModel):
    universe_status: ResearchUniverseStatus
    portfolio_mode: PortfolioMode
    description: Optional[str] = None
