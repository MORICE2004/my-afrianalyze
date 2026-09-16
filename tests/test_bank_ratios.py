import pytest
from models.banks.ratios import (
    net_interest_margin, cost_to_income_ratio, loan_to_deposit_ratio,
    non_performing_loan_ratio, provision_coverage_ratio, cost_of_risk,
    capital_adequacy_ratio, tier1_capital_ratio, return_on_assets_bank,
    return_on_equity_bank, loan_growth, deposit_growth, fee_income_ratio,
    liquidity_ratio, earning_asset_yield, cost_of_funds, spread
)

def test_bank_ratios_basic():
    """Test bank-specific ratios with realistic African bank numbers"""
    assert net_interest_margin(150, 3000) == 0.05
    assert cost_to_income_ratio(120, 200) == 0.6
    assert loan_to_deposit_ratio(2500, 3000) == pytest.approx(0.83333333333)
    assert non_performing_loan_ratio(150, 3000) == 0.05
    assert provision_coverage_ratio(180, 150) == 1.2
    assert cost_of_risk(45, 3000) == 0.015
    assert capital_adequacy_ratio(400, 2500) == 0.16
    assert tier1_capital_ratio(350, 2500) == 0.14
    assert return_on_assets_bank(100, 5000) == 0.02
    assert return_on_equity_bank(100, 500) == 0.2
    assert loan_growth(2750, 2500) == 0.1
    assert deposit_growth(3300, 3000) == 0.1
    assert fee_income_ratio(40, 200) == 0.2
    assert liquidity_ratio(900, 3000) == 0.3
    assert earning_asset_yield(300, 3000) == 0.1
    assert cost_of_funds(150, 2500) == 0.06
    assert spread(0.1, 0.06) == pytest.approx(0.04)

def test_bank_ratios_zero_denominators():
    """Test None handling for denominators"""
    assert net_interest_margin(150, 0) is None
    assert cost_to_income_ratio(120, 0) is None
    assert loan_to_deposit_ratio(2500, 0) is None
