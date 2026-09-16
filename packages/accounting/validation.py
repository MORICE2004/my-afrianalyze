from dataclasses import dataclass
from typing import Literal, Optional, List

@dataclass
class ValidationResult:
    is_valid: bool
    status: Literal['VALID', 'MISSING', 'UNVERIFIED', 'CONFLICTING', 'LOW_CONFIDENCE', 'RECONCILIATION_FAILED']
    expected_value: Optional[float]
    actual_value: Optional[float]
    difference: Optional[float]
    message: str

def validate_balance_sheet(total_assets: Optional[float], total_liabilities: Optional[float], total_equity: Optional[float], tolerance: float = 0.01) -> ValidationResult:
    """Validate that Total Assets = Total Liabilities + Total Equity."""
    if total_assets is None or total_liabilities is None or total_equity is None:
        return ValidationResult(False, 'MISSING', None, None, None, "Missing inputs for balance sheet validation.")
        
    expected_assets = total_liabilities + total_equity
    difference = abs(total_assets - expected_assets)
    
    if difference <= tolerance:
        return ValidationResult(True, 'VALID', expected_assets, total_assets, difference, "Balance sheet reconciles.")
    else:
        return ValidationResult(False, 'RECONCILIATION_FAILED', expected_assets, total_assets, difference, "Total assets do not equal liabilities plus equity.")

def validate_cash_flow(opening_cash: Optional[float], operating_cf: Optional[float], investing_cf: Optional[float], financing_cf: Optional[float], closing_cash: Optional[float], tolerance: float = 0.01) -> ValidationResult:
    """Validate that Opening Cash + Net CF = Closing Cash."""
    if None in (opening_cash, operating_cf, investing_cf, financing_cf, closing_cash):
        return ValidationResult(False, 'MISSING', None, None, None, "Missing inputs for cash flow validation.")
        
    expected_closing = opening_cash + operating_cf + investing_cf + financing_cf
    difference = abs(closing_cash - expected_closing)
    
    if difference <= tolerance:
        return ValidationResult(True, 'VALID', expected_closing, closing_cash, difference, "Cash flow reconciles.")
    else:
        return ValidationResult(False, 'RECONCILIATION_FAILED', expected_closing, closing_cash, difference, "Closing cash does not match calculated cash flows.")

def validate_equity_movement(opening_equity: Optional[float], net_income: Optional[float], dividends: Optional[float], other_movements: Optional[float], closing_equity: Optional[float], tolerance: float = 0.01) -> ValidationResult:
    """Validate that Opening Equity + Net Income - Dividends + Other = Closing Equity."""
    if None in (opening_equity, net_income, dividends, other_movements, closing_equity):
        return ValidationResult(False, 'MISSING', None, None, None, "Missing inputs for equity movement validation.")
        
    # Assume dividends are provided as a positive magnitude
    expected_closing = opening_equity + net_income - abs(dividends) + other_movements
    difference = abs(closing_equity - expected_closing)
    
    if difference <= tolerance:
        return ValidationResult(True, 'VALID', expected_closing, closing_equity, difference, "Equity movement reconciles.")
    else:
        return ValidationResult(False, 'RECONCILIATION_FAILED', expected_closing, closing_equity, difference, "Closing equity does not match calculated equity movements.")

def validate_eps(net_income: Optional[float], shares_outstanding: Optional[float], reported_eps: Optional[float], tolerance: float = 0.01) -> ValidationResult:
    """Validate that Reported EPS matches Net Income / Shares Outstanding."""
    if net_income is None or shares_outstanding is None or reported_eps is None:
        return ValidationResult(False, 'MISSING', None, None, None, "Missing inputs for EPS validation.")
    
    if shares_outstanding == 0:
        return ValidationResult(False, 'RECONCILIATION_FAILED', None, reported_eps, None, "Shares outstanding cannot be zero.")
        
    calculated_eps = net_income / shares_outstanding
    difference = abs(reported_eps - calculated_eps)
    
    if difference <= tolerance:
        return ValidationResult(True, 'VALID', calculated_eps, reported_eps, difference, "EPS reconciles.")
    else:
        return ValidationResult(False, 'RECONCILIATION_FAILED', calculated_eps, reported_eps, difference, "Reported EPS does not match calculated EPS.")

def validate_period_consistency(periods: List[str]) -> ValidationResult:
    """Validate that there are no duplicate periods."""
    if not periods:
        return ValidationResult(False, 'MISSING', None, None, None, "No periods provided.")
        
    if len(periods) == len(set(periods)):
        return ValidationResult(True, 'VALID', None, None, None, "Periods are consistent.")
    else:
        return ValidationResult(False, 'CONFLICTING', None, None, None, "Duplicate periods found.")

def validate_currency_consistency(currencies: List[str]) -> ValidationResult:
    """Validate that all items are in the same currency."""
    if not currencies:
        return ValidationResult(False, 'MISSING', None, None, None, "No currencies provided.")
        
    unique_currencies = set(currencies)
    if len(unique_currencies) == 1:
        return ValidationResult(True, 'VALID', None, None, None, "Currencies are consistent.")
    else:
        return ValidationResult(False, 'CONFLICTING', None, None, None, f"Multiple currencies found: {unique_currencies}")
