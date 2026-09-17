from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Any, Optional
from .manual_ingestion import ManualDataEntry

class SourceConflict(BaseModel):
    conflict_id: UUID = Field(default_factory=uuid4)
    metric_name: str
    existing_entry_id: UUID
    new_entry_id: UUID
    existing_value: Any
    new_value: Any
    resolved: bool = False
    resolution_entry_id: Optional[UUID] = None

class ConflictEngine:
    def __init__(self):
        # In a real app this would query the DB
        self.verified_metrics = {}

    def process_entry(self, entry: ManualDataEntry) -> Optional[SourceConflict]:
        """
        Checks if the incoming entry conflicts with existing verified data for the same metric.
        If it conflicts, returns a SourceConflict record rather than silently overwriting.
        """
        if entry.metric_name in self.verified_metrics:
            existing = self.verified_metrics[entry.metric_name]
            # Simple equality check for conflict. We can enhance for float tolerance later.
            if existing.value != entry.value:
                return SourceConflict(
                    metric_name=entry.metric_name,
                    existing_entry_id=existing.entry_id,
                    new_entry_id=entry.entry_id,
                    existing_value=existing.value,
                    new_value=entry.value
                )
        else:
            self.verified_metrics[entry.metric_name] = entry
            
        return None
