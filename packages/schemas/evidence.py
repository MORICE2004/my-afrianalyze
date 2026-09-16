from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID

class EvidenceRecord(BaseModel):
    """
    Core schema for data provenance.
    Every financial figure must map back to an EvidenceRecord.
    """
    id: UUID = Field(description="Unique identifier for the evidence record")
    company_id: UUID = Field(description="Company identifier")
    metric_id: str = Field(description="Canonical metric ID (e.g., 'net_profit')")
    value: float
    unit: Optional[str] = None
    currency: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    reporting_period: str = Field(description="e.g., 'FY2025'")
    statement_type: str = Field(description="e.g., 'income_statement', 'balance_sheet'")
    source_type: str = Field(description="e.g., 'annual_report', 'exchange_announcement'")
    source_name: str
    source_url: Optional[str] = None
    document_id: Optional[UUID] = None
    page_number: Optional[int] = None
    table_reference: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    extraction_method: str = Field(description="e.g., 'docling_llm', 'manual'")
    confidence: Optional[float] = None
    verification_status: str = Field(default="UNVERIFIED", description="'UNVERIFIED', 'VERIFIED', 'CONFLICTING'")
