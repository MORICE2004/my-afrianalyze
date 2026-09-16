import pytest
from packages.financial_engine.forecast import ForecastAssumption
from models.banks.forecast import BankForecaster

def test_financial_reconciliation():
    historical = {
        "company_id": "TEST_BANK",
        "loans": {"2023": 1000.0},
        "deposits": {"2023": 800.0},
        "fee_income": {"2023": 50.0},
        "operating_expenses": {"2023": 40.0},
        "current_book_value": 200.0
    }

    assumptions = {
        "loan_growth": ForecastAssumption(metric_name="Loan Growth", value=0.10, source="test", rationale=""),
        "deposit_growth": ForecastAssumption(metric_name="Deposit Growth", value=0.08, source="test", rationale=""),
        "nim": ForecastAssumption(metric_name="NIM", value=0.05, source="test", rationale=""),
        "cost_of_risk": ForecastAssumption(metric_name="Cost of Risk", value=0.01, source="test", rationale=""),
        "cost_to_income": ForecastAssumption(metric_name="Cost to Income", value=0.50, source="test", rationale=""),
        "fee_income_growth": ForecastAssumption(metric_name="Fee Income Growth", value=0.05, source="test", rationale=""),
        "tax_rate": ForecastAssumption(metric_name="Tax Rate", value=0.30, source="test", rationale=""),
        "payout_ratio": ForecastAssumption(metric_name="Payout Ratio", value=0.40, source="test", rationale=""),
        "shares_outstanding": ForecastAssumption(metric_name="Shares Outstanding", value=100.0, source="test", rationale="")
    }

    forecast = BankForecaster.build_full_bank_forecast(historical, assumptions, years=3)
    
    # Map forecast lines for easy access
    lines = {line.metric_name: line.forecast_values for line in forecast.lines}
    
    pat_values = lines["Profit After Tax (PAT)"]
    bv_values = lines["Book Value"]
    dividends_values = lines["Dividends Per Share (DPS)"] # wait, this is per share.
    # Total dividends = PAT * payout ratio
    payout_ratio = assumptions["payout_ratio"].value
    
    # Test Book Value Roll-Forward Reconciliation: BV(t) = BV(t-1) + PAT(t) - Dividends(t)
    prev_bv = historical["current_book_value"]
    for year in ["2024", "2025", "2026"]:
        pat = pat_values[year]
        total_dividends = pat * payout_ratio
        expected_bv = prev_bv + pat - total_dividends
        
        # Check reconciliation to 4 decimal places
        assert round(bv_values[year], 4) == round(expected_bv, 4), f"Book value reconciliation failed for {year}"
        
        prev_bv = bv_values[year]

    # Test Income Statement Reconciliation
    nii_values = lines["Net Interest Income"]
    fees_values = lines["Fee Income"]
    opex_values = lines["Operating Expenses"]
    prov_values = lines["Provision for Credit Losses"]
    
    for year in ["2024", "2025", "2026"]:
        nii = nii_values[year]
        fees = fees_values[year]
        opex = opex_values[year]
        prov = prov_values[year]
        pat = pat_values[year]
        
        pre_tax = nii + fees - opex - prov
        expected_pat = pre_tax * (1 - assumptions["tax_rate"].value)
        
        assert round(pat, 4) == round(expected_pat, 4), f"Income statement reconciliation failed for {year}"
