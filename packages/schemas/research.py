from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class ResearchRunState(str, Enum):
    DISCOVERING = "DISCOVERING"
    COLLECTING = "COLLECTING"
    PROCESSING = "PROCESSING"
    EXTRACTING = "EXTRACTING"
    VALIDATING = "VALIDATING"
    ANALYZING = "ANALYZING"
    VALUING = "VALUING"
    AUDITING = "AUDITING"
    REPORTING = "REPORTING"
    COMPLETE = "COMPLETE"
    DATA_INSUFFICIENT = "DATA_INSUFFICIENT"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    VALUATION_BLOCKED = "VALUATION_BLOCKED"
    RESEARCH_FAILED = "RESEARCH_FAILED"

class DataQualityScore(BaseModel):
    source_quality: float = Field(description="Score for reliability of sources (0-1)")
    completeness: float = Field(description="Score for data completeness (0-1)")
    recency: float = Field(description="Score for how recent the data is (0-1)")
    consistency: float = Field(description="Score for internal consistency (0-1)")
    extraction_confidence: float = Field(description="Average confidence from extraction (0-1)")
    market_price_completeness: float = Field(description="Score for market data availability (0-1)")
    overall_score: float = Field(description="Weighted average overall score (0-1)")
    explanation: str = Field(description="Qualitative explanation of the score")

class CriticalDataGate(BaseModel):
    company_identity_verified: bool = Field(description="Company identity is verified")
    company_identity_verified_reason: Optional[str] = Field(None, description="Reason if false")
    latest_filing_identified: bool = Field(description="Latest filing is identified")
    latest_filing_identified_reason: Optional[str] = Field(None, description="Reason if false")
    historical_data_sufficient: bool = Field(description="Historical data is sufficient")
    historical_data_sufficient_reason: Optional[str] = Field(None, description="Reason if false")
    market_price_available: bool = Field(description="Market price is available")
    market_price_available_reason: Optional[str] = Field(None, description="Reason if false")
    currency_identified: bool = Field(description="Currency is identified")
    currency_identified_reason: Optional[str] = Field(None, description="Reason if false")
    financial_validation_passed: bool = Field(description="Financial validation passed")
    financial_validation_passed_reason: Optional[str] = Field(None, description="Reason if false")
    valuation_inputs_available: bool = Field(description="Valuation inputs available")
    valuation_inputs_available_reason: Optional[str] = Field(None, description="Reason if false")
    assumptions_populated: bool = Field(description="Assumptions populated")
    assumptions_populated_reason: Optional[str] = Field(None, description="Reason if false")
    source_conflicts_resolved: bool = Field(description="Source conflicts resolved")
    source_conflicts_resolved_reason: Optional[str] = Field(None, description="Reason if false")

class ResearchRun(BaseModel):
    research_run_id: UUID = Field(description="Unique ID for this research run")
    company_id: UUID = Field(description="Target company ID")
    state: ResearchRunState = Field(description="Current state of the run")
    started_at: datetime = Field(description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    agents_executed: List[str] = Field(default_factory=list, description="List of agents run")
    sources_retrieved: int = Field(default=0, description="Number of sources retrieved")
    documents_processed: int = Field(default=0, description="Number of documents processed")
    calculations_performed: int = Field(default=0, description="Number of calculations done")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    auditor_result: Optional[str] = Field(None, description="Result from the auditor agent")
    data_quality_score: Optional[DataQualityScore] = Field(None, description="Final data quality score")
