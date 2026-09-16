from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from uuid import UUID
from decimal import Decimal

class FinancialMetric(BaseModel):
    """
    Represents a single financial figure extracted from a source,
    tied deterministically to evidence.
    """
    canonical_label: str = Field(description="Standardized name across all companies (e.g., 'net_profit')")
    original_label: str = Field(description="Exact name from the document (e.g., 'Profit for the year')")
    value: Decimal = Field(description="Numerical value extracted")
    currency: str = Field(description="Currency of the value (e.g., 'TZS')")
    evidence_id: UUID = Field(description="Foreign key to the evidence table for full provenance")

class IncomeStatement(BaseModel):
    interest_income: Optional[FinancialMetric] = Field(None, description="Interest income")
    interest_expense: Optional[FinancialMetric] = Field(None, description="Interest expense")
    net_interest_income: Optional[FinancialMetric] = Field(None, description="Net interest income")
    fee_and_commission_income: Optional[FinancialMetric] = Field(None, description="Fee and commission income")
    trading_income: Optional[FinancialMetric] = Field(None, description="Trading income")
    other_operating_income: Optional[FinancialMetric] = Field(None, description="Other operating income")
    total_operating_income: Optional[FinancialMetric] = Field(None, description="Total operating income")
    operating_expenses: Optional[FinancialMetric] = Field(None, description="Operating expenses")
    staff_costs: Optional[FinancialMetric] = Field(None, description="Staff costs")
    depreciation: Optional[FinancialMetric] = Field(None, description="Depreciation and amortization")
    impairment_charges: Optional[FinancialMetric] = Field(None, description="Impairment charges")
    provision_for_credit_losses: Optional[FinancialMetric] = Field(None, description="Provision for credit losses")
    profit_before_tax: Optional[FinancialMetric] = Field(None, description="Profit before tax")
    income_tax: Optional[FinancialMetric] = Field(None, description="Income tax expense")
    profit_after_tax: Optional[FinancialMetric] = Field(None, description="Profit after tax")
    eps_basic: Optional[FinancialMetric] = Field(None, description="Basic earnings per share")
    eps_diluted: Optional[FinancialMetric] = Field(None, description="Diluted earnings per share")
    dividends_per_share: Optional[FinancialMetric] = Field(None, description="Dividends per share")

class BalanceSheet(BaseModel):
    cash_and_equivalents: Optional[FinancialMetric] = Field(None, description="Cash and cash equivalents")
    due_from_banks: Optional[FinancialMetric] = Field(None, description="Amounts due from other banks")
    investment_securities: Optional[FinancialMetric] = Field(None, description="Investment securities")
    loans_and_advances: Optional[FinancialMetric] = Field(None, description="Loans and advances to customers")
    other_assets: Optional[FinancialMetric] = Field(None, description="Other assets")
    property_plant_equipment: Optional[FinancialMetric] = Field(None, description="Property, plant, and equipment")
    intangible_assets: Optional[FinancialMetric] = Field(None, description="Intangible assets")
    total_assets: Optional[FinancialMetric] = Field(None, description="Total assets")
    
    customer_deposits: Optional[FinancialMetric] = Field(None, description="Customer deposits")
    due_to_banks: Optional[FinancialMetric] = Field(None, description="Amounts due to other banks")
    borrowings: Optional[FinancialMetric] = Field(None, description="Borrowings")
    other_liabilities: Optional[FinancialMetric] = Field(None, description="Other liabilities")
    total_liabilities: Optional[FinancialMetric] = Field(None, description="Total liabilities")
    
    share_capital: Optional[FinancialMetric] = Field(None, description="Share capital")
    share_premium: Optional[FinancialMetric] = Field(None, description="Share premium")
    retained_earnings: Optional[FinancialMetric] = Field(None, description="Retained earnings")
    other_reserves: Optional[FinancialMetric] = Field(None, description="Other reserves")
    total_equity: Optional[FinancialMetric] = Field(None, description="Total equity")

class CashFlowStatement(BaseModel):
    operating_cash_flow: Optional[FinancialMetric] = Field(None, description="Cash flow from operating activities")
    investing_cash_flow: Optional[FinancialMetric] = Field(None, description="Cash flow from investing activities")
    financing_cash_flow: Optional[FinancialMetric] = Field(None, description="Cash flow from financing activities")
    net_cash_change: Optional[FinancialMetric] = Field(None, description="Net change in cash")
    opening_cash: Optional[FinancialMetric] = Field(None, description="Cash at beginning of period")
    closing_cash: Optional[FinancialMetric] = Field(None, description="Cash at end of period")

class FinancialStatementSet(BaseModel):
    company_id: UUID = Field(description="Company identifier")
    reporting_period: str = Field(description="Reporting period string (e.g., FY2023)")
    period_start: date = Field(description="Start date of the reporting period")
    period_end: date = Field(description="End date of the reporting period")
    currency: str = Field(description="Reporting currency")
    is_consolidated: bool = Field(description="Whether the statements are consolidated")
    is_audited: bool = Field(description="Whether the statements are audited")
    auditor_name: Optional[str] = Field(None, description="Name of the auditor")
    
    income_statement: Optional[IncomeStatement] = Field(None, description="Income statement data")
    balance_sheet: Optional[BalanceSheet] = Field(None, description="Balance sheet data")
    cash_flow_statement: Optional[CashFlowStatement] = Field(None, description="Cash flow statement data")

class CurrencyValue(BaseModel):
    original_value: Decimal = Field(description="Original value")
    original_currency: str = Field(description="Original currency")
    normalized_value: Decimal = Field(description="Normalized value")
    normalized_currency: str = Field(description="Normalized currency")
    fx_rate: Decimal = Field(description="Exchange rate used")
    fx_source: str = Field(description="Source of exchange rate")
    fx_date: date = Field(description="Date of exchange rate")
