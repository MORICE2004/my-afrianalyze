import pytest
from packages.financial_engine.ratios import (
    gross_margin, operating_margin, net_margin, return_on_assets,
    return_on_equity, return_on_invested_capital, debt_to_equity,
    debt_to_assets, interest_coverage, current_ratio, quick_ratio,
    asset_turnover, inventory_turnover, receivables_turnover,
    pe_ratio, pb_ratio, ev_ebitda, ev_sales, dividend_yield,
    dividend_payout, eps, book_value_per_share, enterprise_value,
    free_cash_flow, growth_rate, peg_ratio, _safe_divide
)

def test_safe_divide():
    """Test safe divide helper"""
    assert _safe_divide(10, 2) == 5.0
    assert _safe_divide(10, 0) is None
    assert _safe_divide(None, 2) is None
    assert _safe_divide(10, None) is None

def test_gross_margin():
    """Test Gross Margin calculation"""
    assert gross_margin(1000, 400) == 0.6
    assert gross_margin(1000, 1000) == 0.0
    assert gross_margin(1000, 1200) == -0.2
    assert gross_margin(None, 400) is None

def test_return_on_equity():
    """Test ROE with realistic NMB-like figures"""
    net_income = 500_000_000_000.0
    equity = 2_000_000_000_000.0
    assert return_on_equity(net_income, equity) == 0.25
    assert return_on_equity(net_income, 0) is None

def test_enterprise_value():
    """Test Enterprise value computation"""
    assert enterprise_value(1000, 200, 50, 10) == 1160.0
    assert enterprise_value(1000, 200, 50) == 1150.0
    assert enterprise_value(None, 200, 50) is None

def test_free_cash_flow():
    """Test Free cash flow"""
    assert free_cash_flow(500, 100) == 400
    assert free_cash_flow(500, -100) == 400
    assert free_cash_flow(None, 100) is None

def test_all_ratios_basic():
    """Test standard ratios"""
    assert operating_margin(200, 1000) == 0.2
    assert net_margin(150, 1000) == 0.15
    assert return_on_assets(150, 2000) == 0.075
    assert return_on_invested_capital(200, 1500) == 0.13333333333333333
    assert debt_to_equity(500, 1500) == 1/3
    assert debt_to_assets(500, 2000) == 0.25
    assert interest_coverage(250, 50) == 5.0
    assert current_ratio(800, 400) == 2.0
    assert quick_ratio(800, 200, 400) == 1.5
    assert asset_turnover(1000, 2000) == 0.5
    assert inventory_turnover(400, 100) == 4.0
    assert receivables_turnover(1000, 200) == 5.0
    assert pe_ratio(50, 5) == 10.0
    assert pb_ratio(50, 25) == 2.0
    assert ev_ebitda(1000, 200) == 5.0
    assert ev_sales(1000, 2000) == 0.5
    assert dividend_yield(2, 50) == 0.04
    assert dividend_payout(2, 5) == 0.4
    assert eps(500, 100) == 5.0
    assert book_value_per_share(2500, 100) == 25.0
    assert growth_rate(110, 100) == 0.1
    assert peg_ratio(10, 0.1) == 100.0
