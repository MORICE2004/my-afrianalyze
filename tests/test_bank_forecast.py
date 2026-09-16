import pytest
from pytest import approx
from packages.financial_engine.forecast import ForecastAssumption
from models.banks.forecast import BankForecaster

def test_bank_forecast_components():
    """Test full bank forecast calculations."""
    historical_loans = {"FY22": 8000.0}
    historical_deposits = {"FY22": 9000.0}
    historical_fees = {"FY22": 500.0}
    historical_opex = {"FY22": 400.0}
    current_bv = 1500.0
    
    assumptions = {
        'loan_growth': ForecastAssumption(metric_name="Loan Growth", value=0.15, source="Test", rationale="Test"),
        'deposit_growth': ForecastAssumption(metric_name="Deposit Growth", value=0.10, source="Test", rationale="Test"),
        'nim': ForecastAssumption(metric_name="NIM", value=0.07, source="Test", rationale="Test"),
        'cost_of_risk': ForecastAssumption(metric_name="Cost of Risk", value=0.015, source="Test", rationale="Test"),
        'cost_to_income': ForecastAssumption(metric_name="Cost to Income", value=0.50, source="Test", rationale="Test"),
        'fee_income_growth': ForecastAssumption(metric_name="Fee Growth", value=0.10, source="Test", rationale="Test"),
        'tax_rate': ForecastAssumption(metric_name="Tax Rate", value=0.30, source="Test", rationale="Test"),
        'payout_ratio': ForecastAssumption(metric_name="Payout Ratio", value=0.40, source="Test", rationale="Test"),
        'shares_outstanding': ForecastAssumption(metric_name="Shares", value=100.0, source="Test", rationale="Test")
    }
    
    # 1. Test loan forecast
    loan_forecast = BankForecaster.forecast_loans(historical_loans, assumptions['loan_growth'], 5)
    keys = sorted(loan_forecast.forecast_values.keys())
    assert loan_forecast.forecast_values[keys[0]] == approx(8000.0 * 1.15) # 9200
    
    # 2. Test NII
    nii_forecast = BankForecaster.forecast_net_interest_income(loan_forecast, assumptions['nim'])
    assert nii_forecast.forecast_values[keys[0]] == approx(9200.0 * 0.07) # 644.0
    
    # 3. Test Provision
    prov_forecast = BankForecaster.forecast_provision(loan_forecast, assumptions['cost_of_risk'])
    assert prov_forecast.forecast_values[keys[0]] == approx(9200.0 * 0.015) # 138.0
    
    # 4. Test profit calculation
    from packages.financial_engine.forecast import GeneralForecaster
    fee_forecast = GeneralForecaster.forecast_revenue(historical_fees, assumptions['fee_income_growth'], 5)
    fee_forecast.metric_name = "Fee Income"
    
    total_income_vals = {k: nii_forecast.forecast_values[k] + fee_forecast.forecast_values[k] for k in keys}
    total_income_line = type(loan_forecast)(metric_name="Total", historical_values={}, forecast_values=total_income_vals, growth_rates={}, assumptions_used=[])
    
    opex_forecast = BankForecaster.forecast_operating_expenses(historical_opex, assumptions['cost_to_income'], total_income_line)
    
    profit_forecast = BankForecaster.forecast_profit(nii_forecast, fee_forecast, opex_forecast, prov_forecast, assumptions['tax_rate'])
    
    # PAT = (644 + 550 - 597 - 138) * 0.7 = 321.3
    assert profit_forecast.forecast_values[keys[0]] == approx(321.3)
    
    # 5. Test book value evolution
    bv_forecast = BankForecaster.forecast_book_value(current_bv, profit_forecast, assumptions['payout_ratio'])
    assert bv_forecast.forecast_values[keys[0]] == approx(1500 + 321.3 - 321.3 * 0.4)
    
    # 6. Test EPS & DPS
    eps = BankForecaster.forecast_eps(profit_forecast, assumptions['shares_outstanding'])
    assert eps.forecast_values[keys[0]] == approx(321.3 / 100.0)
    
    dps = BankForecaster.forecast_dps(eps, assumptions['payout_ratio'])
    assert dps.forecast_values[keys[0]] == approx(3.213 * 0.40)
    
    # 7. Test full build
    historical = {
        'company_id': "NMB",
        'loans': historical_loans,
        'deposits': historical_deposits,
        'fee_income': historical_fees,
        'operating_expenses': historical_opex,
        'current_book_value': current_bv
    }
    full_result = BankForecaster.build_full_bank_forecast(historical, assumptions, 5)
    assert len(full_result.lines) == 10
    assert full_result.company_id == "NMB"
