from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TableData(BaseModel):
    table_id: str
    html_content: Optional[str] = None
    markdown_content: Optional[str] = None
    raw_data: List[List[str]] = Field(default_factory=list)
    classified_type: Optional[str] = None # e.g., "Income Statement", "Balance Sheet", "Cash Flow", "Unknown"

class DocumentData(BaseModel):
    title: Optional[str] = None
    content: str
    tables: List[TableData] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
