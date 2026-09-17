from enum import Enum
from pydantic import BaseModel, HttpUrl, Field
from datetime import date
from uuid import UUID, uuid4
from typing import Optional, Any
from .registry import SourceRegistry

class VerificationState(str, Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class ManualDataEntry(BaseModel):
    entry_id: UUID = Field(default_factory=uuid4)
    metric_name: str
    value: Any
    source_url: HttpUrl
    publication_date: date
    document_page: int
    state: VerificationState = VerificationState.PENDING_VERIFICATION
    verifier_id: Optional[UUID] = None
    rejection_reason: Optional[str] = None

class IngestionProcessor:
    def submit_entry(self, metric_name: str, value: Any, source_url: HttpUrl, publication_date: date, document_page: int) -> ManualDataEntry:
        """
        Creates a manual data entry and defaults to PENDING_VERIFICATION.
        """
        return ManualDataEntry(
            metric_name=metric_name,
            value=value,
            source_url=source_url,
            publication_date=publication_date,
            document_page=document_page
        )
    
    def verify_entry(self, entry: ManualDataEntry, verifier_role: str, verifier_id: UUID) -> ManualDataEntry:
        """
        Transitions entry to VERIFIED if role has permission.
        """
        if verifier_role not in ["VERIFIER", "ADMIN"]:
            raise PermissionError("Only a VERIFIER or ADMIN can verify entries.")
        entry.state = VerificationState.VERIFIED
        entry.verifier_id = verifier_id
        return entry
    
    def reject_entry(self, entry: ManualDataEntry, verifier_role: str, verifier_id: UUID, reason: str) -> ManualDataEntry:
        """
        Transitions entry to REJECTED if role has permission.
        """
        if verifier_role not in ["VERIFIER", "ADMIN"]:
            raise PermissionError("Only a VERIFIER or ADMIN can reject entries.")
        entry.state = VerificationState.REJECTED
        entry.verifier_id = verifier_id
        entry.rejection_reason = reason
        return entry
