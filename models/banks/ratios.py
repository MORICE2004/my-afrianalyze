from typing import Optional

def net_interest_margin(net_interest_income: float, average_earning_assets: float) -> Optional[float]:
    """NIM measures how much a bank earns on its lending versus what it pays on deposits. A higher NIM indicates more profitable core banking operations."""
    if not average_earning_assets:
        return None
    return net_interest_income / average_earning_assets

def cost_to_income_ratio(operating_expenses: float, total_operating_income: float) -> Optional[float]:
    """Measures operational efficiency. Lower is better. African banks typically range 40-65%."""
    if not total_operating_income:
        return None
    return operating_expenses / total_operating_income

def loan_to_deposit_ratio(total_loans: float, total_deposits: float) -> Optional[float]:
    """Measures liquidity risk. Above 100% means the bank lends more than it collects in deposits, relying on wholesale funding."""
    if not total_deposits:
        return None
    return total_loans / total_deposits

def non_performing_loan_ratio(non_performing_loans: float, gross_loans: float) -> Optional[float]:
    """Asset quality indicator. Higher NPL ratio means more loans are in default or near-default."""
    if not gross_loans:
        return None
    return non_performing_loans / gross_loans

def provision_coverage_ratio(loan_loss_provisions: float, non_performing_loans: float) -> Optional[float]:
    """How well provisioned the bank is against bad loans. Above 100% means full coverage."""
    if not non_performing_loans:
        return None
    return loan_loss_provisions / non_performing_loans

def cost_of_risk(provision_charge: float, average_gross_loans: float) -> Optional[float]:
    """Annual credit cost relative to the loan book. Rising cost of risk signals deteriorating asset quality."""
    if not average_gross_loans:
        return None
    return provision_charge / average_gross_loans

def capital_adequacy_ratio(total_capital: float, risk_weighted_assets: float) -> Optional[float]:
    """Regulatory capital ratio. Banks must maintain this above regulatory minimums (typically 10-15% in Africa)."""
    if not risk_weighted_assets:
        return None
    return total_capital / risk_weighted_assets

def tier1_capital_ratio(tier1_capital: float, risk_weighted_assets: float) -> Optional[float]:
    """Regulatory tier 1 capital ratio."""
    if not risk_weighted_assets:
        return None
    return tier1_capital / risk_weighted_assets

def return_on_assets_bank(net_income: float, average_total_assets: float) -> Optional[float]:
    """For banks, ROA is typically 1-3%. Measures how efficiently the bank uses its total asset base."""
    if not average_total_assets:
        return None
    return net_income / average_total_assets

def return_on_equity_bank(net_income: float, average_total_equity: float) -> Optional[float]:
    """For banks, ROE is the key profitability measure. Good African banks achieve 15-25%."""
    if not average_total_equity:
        return None
    return net_income / average_total_equity

def loan_growth(current_loans: float, previous_loans: float) -> Optional[float]:
    """Measures the growth rate of the loan portfolio."""
    if not previous_loans:
        return None
    return (current_loans - previous_loans) / previous_loans

def deposit_growth(current_deposits: float, previous_deposits: float) -> Optional[float]:
    """Measures the growth rate of the deposit base."""
    if not previous_deposits:
        return None
    return (current_deposits - previous_deposits) / previous_deposits

def fee_income_ratio(fee_income: float, total_operating_income: float) -> Optional[float]:
    """Diversification indicator. Higher fee income ratio means less dependence on interest income."""
    if not total_operating_income:
        return None
    return fee_income / total_operating_income

def liquidity_ratio(liquid_assets: float, total_deposits: float) -> Optional[float]:
    """Measures the proportion of deposits covered by liquid assets."""
    if not total_deposits:
        return None
    return liquid_assets / total_deposits

def earning_asset_yield(interest_income: float, average_earning_assets: float) -> Optional[float]:
    """Yield on earning assets."""
    if not average_earning_assets:
        return None
    return interest_income / average_earning_assets

def cost_of_funds(interest_expense: float, average_interest_bearing_liabilities: float) -> Optional[float]:
    """Cost of interest-bearing liabilities."""
    if not average_interest_bearing_liabilities:
        return None
    return interest_expense / average_interest_bearing_liabilities

def spread(earning_asset_yield_val: float, cost_of_funds_val: float) -> Optional[float]:
    """Difference between the yield on earning assets and the cost of funds."""
    if earning_asset_yield_val is None or cost_of_funds_val is None:
        return None
    return earning_asset_yield_val - cost_of_funds_val
