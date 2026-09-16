import enum
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

from agents.llm_provider import LLMClient

class AgentRole(enum.Enum):
    COMPANY_RESEARCHER = "company_researcher"
    FINANCIAL_STATEMENT = "financial_statement"
    ACCOUNTING = "accounting"
    MARKET = "market"
    MACRO = "macro"
    SECTOR = "sector"
    VALUATION = "valuation"
    RISK = "risk"
    SCENARIO = "scenario"
    TECHNICAL_ANALYSIS = "technical_analysis"
    SYNTHESIS = "synthesis"
    AUDITOR = "auditor"
    RESEARCH_DIRECTOR = "research_director"

class AgentResult(BaseModel):
    agent_role: AgentRole
    success: bool
    findings: List[str]
    evidence_ids: List[UUID] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    raw_output: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=datetime.utcnow)

class ResearchContext(BaseModel):
    company: dict = Field(default_factory=dict)
    financial_data: dict = Field(default_factory=dict)
    market_data: dict = Field(default_factory=dict)
    macro_data: dict = Field(default_factory=dict)
    sector_data: dict = Field(default_factory=dict)
    valuation_data: dict = Field(default_factory=dict)
    previous_agent_results: List[AgentResult] = Field(default_factory=list)
    research_run_id: UUID = Field(default_factory=uuid4)
    available_documents: List[str] = Field(default_factory=list)

class BaseResearchAgent(ABC):
    """
    Agents may interpret, compare, explain, research, identify risks, identify inconsistencies, suggest assumptions.
    Agents may NOT invent financial figures or overwrite deterministic calculations.
    Every factual financial claim must reference evidence.
    """
    role: AgentRole

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    @abstractmethod
    async def execute(self, context: ResearchContext) -> AgentResult:
        pass
