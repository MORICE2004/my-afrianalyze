from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class DocumentType(str, Enum):
    ANNUAL_REPORT = "ANNUAL_REPORT"
    INTERIM_REPORT = "INTERIM_REPORT"
    QUARTERLY_REPORT = "QUARTERLY_REPORT"
    INVESTOR_PRESENTATION = "INVESTOR_PRESENTATION"
    PROSPECTUS = "PROSPECTUS"
    CIRCULAR = "CIRCULAR"
    EXCHANGE_ANNOUNCEMENT = "EXCHANGE_ANNOUNCEMENT"
    REGULATORY_FILING = "REGULATORY_FILING"
    OTHER = "OTHER"

class DocumentRecord(BaseModel):
    document_id: UUID = Field(description="Unique ID for the document")
    company_id: UUID = Field(description="Target company ID")
    document_type: DocumentType = Field(description="Type of the document")
    title: str = Field(description="Document title")
    source_url: Optional[str] = Field(None, description="Original URL")
    file_path: str = Field(description="Local file path")
    file_hash: str = Field(description="Hash of the file contents")
    file_size: int = Field(description="File size in bytes")
    mime_type: str = Field(description="MIME type")
    downloaded_at: datetime = Field(description="Download timestamp")
    parsed_at: Optional[datetime] = Field(None, description="Parsing timestamp")
    page_count: Optional[int] = Field(None, description="Number of pages")
    extraction_status: str = Field(description="Status of data extraction")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
