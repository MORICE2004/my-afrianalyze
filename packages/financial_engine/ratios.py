from typing import Optional

def _safe_divide(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Helper to safely divide two numbers, returning None on division by zero or None inputs."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator

def gross_margin(revenue: Optional[float], cost_of_goods_sold: Optional[float]) -> Optional[float]:
    """
    Calculate the Gross Margin.
    Represents the percentage of total sales revenue that the company retains after incurring the direct costs associated with producing the goods and services it sells.
    """
    if revenue is None or cost_of_goods_sold is None:
        return None
    gross_profit = revenue - cost_of_goods_sold
    return _safe_divide(gross_profit, revenue)

def operating_margin(operating_income: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """
    Calculate Operating Margin.
    Measures how much profit a company makes on a dollar of sales, after paying for variable costs of production but before paying interest or tax.
    """
    return _safe_divide(operating_income, revenue)

def net_margin(net_income: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """
    Calculate Net Margin.
    Measures how much net income or profit is generated as a percentage of revenue.
    """
    return _safe_divide(net_income, revenue)

def return_on_assets(net_income: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """
    Calculate Return on Assets (ROA).
    Indicates how profitable a company is relative to its total assets.
    """
    return _safe_divide(net_income, total_assets)

def return_on_equity(net_income: Optional[float], total_equity: Optional[float]) -> Optional[float]:
    """
    Calculate Return on Equity (ROE).
    Measures financial performance calculated by dividing net income by shareholders' equity.
    """
    return _safe_divide(net_income, total_equity)

def return_on_invested_capital(nopat: Optional[float], invested_capital: Optional[float]) -> Optional[float]:
    """
    Calculate Return on Invested Capital (ROIC).
    Assesses a company's efficiency at allocating the capital under its control to profitable investments.
    """
    return _safe_divide(nopat, invested_capital)

def debt_to_equity(total_debt: Optional[float], total_equity: Optional[float]) -> Optional[float]:
    """
    Calculate Debt to Equity Ratio.
    Evaluates a company's financial leverage.
    """
    return _safe_divide(total_debt, total_equity)

def debt_to_assets(total_debt: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """
    Calculate Debt to Assets Ratio.
    Indicates the proportion of a company's assets that are financed with debt.
    """
    return _safe_divide(total_debt, total_assets)

def interest_coverage(ebit: Optional[float], interest_expense: Optional[float]) -> Optional[float]:
    """
    Calculate Interest Coverage Ratio.
    Determines how easily a company can pay its interest expenses on outstanding debt.
    """
    return _safe_divide(ebit, interest_expense)

def current_ratio(current_assets: Optional[float], current_liabilities: Optional[float]) -> Optional[float]:
    """
    Calculate Current Ratio.
    Measures a company's ability to pay short-term obligations or those due within one year.
    """
    return _safe_divide(current_assets, current_liabilities)

def quick_ratio(current_assets: Optional[float], inventory: Optional[float], current_liabilities: Optional[float]) -> Optional[float]:
    """
    Calculate Quick Ratio.
    Measures the ability of a company to pay its current liabilities without relying on the sale of inventory.
    """
    if current_assets is None or inventory is None:
        return None
    liquid_assets = current_assets - inventory
    return _safe_divide(liquid_assets, current_liabilities)

def asset_turnover(revenue: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """
    Calculate Asset Turnover Ratio.
    Measures the value of a company's sales or revenues relative to the value of its assets.
    """
    return _safe_divide(revenue, total_assets)

def inventory_turnover(cogs: Optional[float], average_inventory: Optional[float]) -> Optional[float]:
    """
    Calculate Inventory Turnover.
    Shows how many times a company has sold and replaced inventory during a given period.
    """
    return _safe_divide(cogs, average_inventory)

def receivables_turnover(revenue: Optional[float], average_receivables: Optional[float]) -> Optional[float]:
    """
    Calculate Receivables Turnover Ratio.
    Quantifies a company's effectiveness in collecting its receivables or money owed by clients.
    """
    return _safe_divide(revenue, average_receivables)

def pe_ratio(price: Optional[float], eps: Optional[float]) -> Optional[float]:
    """
    Calculate Price to Earnings (P/E) Ratio.
    Relates a company's share price to its earnings per share.
    """
    return _safe_divide(price, eps)

def pb_ratio(price: Optional[float], book_value_per_share: Optional[float]) -> Optional[float]:
    """
    Calculate Price to Book (P/B) Ratio.
    Compares a company's market value to its book value.
    """
    return _safe_divide(price, book_value_per_share)

def ev_ebitda(enterprise_value: Optional[float], ebitda: Optional[float]) -> Optional[float]:
    """
    Calculate EV/EBITDA Ratio.
    Compares enterprise value to earnings before interest, taxes, depreciation, and amortization.
    """
    return _safe_divide(enterprise_value, ebitda)

def ev_sales(enterprise_value: Optional[float], revenue: Optional[float]) -> Optional[float]:
    """
    Calculate EV/Sales Ratio.
    Compares the enterprise value of a company to its sales.
    """
    return _safe_divide(enterprise_value, revenue)

def dividend_yield(dps: Optional[float], price: Optional[float]) -> Optional[float]:
    """
    Calculate Dividend Yield.
    Shows how much a company pays out in dividends each year relative to its stock price.
    """
    return _safe_divide(dps, price)

def dividend_payout(dps: Optional[float], eps: Optional[float]) -> Optional[float]:
    """
    Calculate Dividend Payout Ratio.
    The ratio of the total amount of dividends paid out to shareholders relative to the net income of the company.
    """
    return _safe_divide(dps, eps)

def eps(net_income: Optional[float], shares_outstanding: Optional[float]) -> Optional[float]:
    """
    Calculate Earnings Per Share (EPS).
    Calculated as a company's profit divided by the outstanding shares of its common stock.
    """
    return _safe_divide(net_income, shares_outstanding)

def book_value_per_share(total_equity: Optional[float], shares_outstanding: Optional[float]) -> Optional[float]:
    """
    Calculate Book Value Per Share (BVPS).
    Calculated by dividing the company's equity by the number of outstanding shares.
    """
    return _safe_divide(total_equity, shares_outstanding)

def enterprise_value(market_cap: Optional[float], total_debt: Optional[float], cash: Optional[float], minority_interest: Optional[float] = 0.0) -> Optional[float]:
    """
    Calculate Enterprise Value (EV).
    A measure of a company's total value, often used as a more comprehensive alternative to equity market capitalization.
    EV = Market Cap + Total Debt + Minority Interest - Cash
    """
    if market_cap is None or total_debt is None or cash is None:
        return None
    min_int = minority_interest if minority_interest is not None else 0.0
    return market_cap + total_debt + min_int - cash

def free_cash_flow(operating_cf: Optional[float], capex: Optional[float]) -> Optional[float]:
    """
    Calculate Free Cash Flow (FCF).
    The cash a company generates after accounting for cash outflows to support operations and maintain its capital assets.
    FCF = Operating Cash Flow - Capital Expenditures
    Note: capex is often reported as a negative number in cash flow statements. This function assumes capex is a positive magnitude of expenditure. If reported negative, the input should be negated before passing, or adjusted accordingly. Assuming absolute value of capex for subtraction.
    """
    if operating_cf is None or capex is None:
        return None
    # Assuming capex is positive expenditure
    return operating_cf - abs(capex)

def growth_rate(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """
    Calculate Growth Rate.
    The percentage change of a specific variable within a specific time period.
    """
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / abs(previous)

def peg_ratio(pe: Optional[float], earnings_growth: Optional[float]) -> Optional[float]:
    """
    Calculate Price/Earnings to Growth (PEG) Ratio.
    A stock's price-to-earnings ratio divided by the growth rate of its earnings for a specified time period.
    Note: earnings_growth is expected as a percentage (e.g., 0.15 for 15% or 15.0 for 15%). Typically PEG uses the whole number format (e.g., PE 15, Growth 15 -> PEG 1.0). Assuming percentage format (0.15) if small, but will just blindly divide here. Usually, it's (PE) / (Growth * 100).
    Here we implement a direct division.
    """
    return _safe_divide(pe, earnings_growth)
