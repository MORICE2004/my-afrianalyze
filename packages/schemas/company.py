from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from uuid import UUID

class Company(BaseModel):
    company_id: UUID = Field(description="Unique identifier for the company")
    name: str = Field(description="Company legal name")
    ticker: str = Field(description="Stock ticker symbol")
    exchange: str = Field(description="Primary exchange")
    country: str = Field(description="Country of incorporation or primary operation")
    sector: str = Field(description="GICS sector")
    sub_sector: str = Field(description="GICS sub-sector")
    reporting_currency: str = Field(description="Primary reporting currency")
    fiscal_year_end: str = Field(description="Fiscal year end date (e.g., '12-31')")
    incorporation_date: Optional[date] = Field(None, description="Date of incorporation")
    business_description: Optional[str] = Field(None, description="Description of the business")
    website: Optional[str] = Field(None, description="Company website URL")
    investor_relations_url: Optional[str] = Field(None, description="Investor relations URL")
    ownership_structure: Optional[str] = Field(None, description="Details of ownership structure")
    management_team: Optional[str] = Field(None, description="Details of management team")
    listing_date: Optional[date] = Field(None, description="Date of listing on exchange")
    shares_outstanding: Optional[int] = Field(None, description="Total number of shares outstanding")
