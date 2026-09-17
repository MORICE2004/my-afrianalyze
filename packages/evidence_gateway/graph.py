from typing import Dict, List, Optional
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field

class VerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    CONFLICT = "CONFLICT"
    REJECTED = "REJECTED"

class ExtractionMethod(str, Enum):
    MANUAL = "MANUAL"
    DOCLING_PARSER = "DOCLING_PARSER"
    REGEX = "REGEX"
    LLM_EXTRACTED = "LLM_EXTRACTED"

class EvidenceSource(BaseModel):
    source_name: str
    document_id: str
    page_number: Optional[int] = None
    extraction_method: ExtractionMethod
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

class EvidenceNode(BaseModel):
    metric_name: str
    metric_value: float
    as_of_date: date
    source: EvidenceSource

class EvidenceGraph(BaseModel):
    nodes: List[EvidenceNode] = Field(default_factory=list)
    
    def add_evidence(self, node: EvidenceNode) -> None:
        self.nodes.append(node)
        
    def get_evidence_for_metric(self, metric_name: str) -> List[EvidenceNode]:
        return [node for node in self.nodes if node.metric_name == metric_name]
