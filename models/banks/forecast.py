from typing import Dict, Any, List
from packages.financial_engine.forecast import ForecastAssumption, ForecastLine, ForecastResult, GeneralForecaster

class BankForecaster:
    """Forecast engine specifically tailored for banking operations."""

    @staticmethod
    def forecast_loans(historical_loans: Dict[str, float], growth_assumption: ForecastAssumption, years: int) -> ForecastLine:
        """Forecasts the loan book based on a constant growth assumption."""
        sorted_keys = sorted(historical_loans.keys())
        base_year = sorted_keys[-1] if sorted_keys else "FY0"
        base_value = historical_loans[base_year] if sorted_keys else 0.0
        
        future_keys = GeneralForecaster._generate_future_keys(base_year, years)
        forecast_values = {}
        growth_rates = {}
        
        current_val = base_value
        for key in future_keys:
            current_val *= (1.0 + growth_assumption.value)
            forecast_values[key] = current_val
            growth_rates[key] = growth_assumption.value
            
        return ForecastLine(
            metric_name="Gross Loans",
            historical_values=historical_loans,
            forecast_values=forecast_values,
            growth_rates=growth_rates,
            assumptions_used=[growth_assumption]
        )

    @staticmethod
    def forecast_deposits(historical_deposits: Dict[str, float], growth_assumption: ForecastAssumption, years: int) -> ForecastLine:
        """Forecasts the deposit base based on a constant growth assumption."""
        sorted_keys = sorted(historical_deposits.keys())
        base_year = sorted_keys[-1] if sorted_keys else "FY0"
        base_value = historical_deposits[base_year] if sorted_keys else 0.0
        
        future_keys = GeneralForecaster._generate_future_keys(base_year, years)
        forecast_values = {}
        growth_rates = {}
        
        current_val = base_value
        for key in future_keys:
            current_val *= (1.0 + growth_assumption.value)
            forecast_values[key] = current_val
            growth_rates[key] = growth_assumption.value
            
        return ForecastLine(
            metric_name="Total Deposits",
            historical_values=historical_deposits,
            forecast_values=forecast_values,
            growth_rates=growth_rates,
            assumptions_used=[growth_assumption]
        )

    @staticmethod
    def forecast_net_interest_income(loan_forecast: ForecastLine, nim_assumption: ForecastAssumption) -> ForecastLine:
        """NII ≈ Average Earning Assets × NIM. For simplicity, use loan book as proxy for earning assets."""
        forecast_values = {}
        for key, loans in loan_forecast.forecast_values.items():
            forecast_values[key] = loans * nim_assumption.value
            
        return ForecastLine(
            metric_name="Net Interest Income",
            historical_values={}, 
            forecast_values=forecast_values,
            growth_rates={},
            assumptions_used=[nim_assumption]
        )

    @staticmethod
    def forecast_provision(loan_forecast: ForecastLine, cost_of_risk_assumption: ForecastAssumption) -> ForecastLine:
        """Provision ≈ Average Loan Book × Cost of Risk."""
        forecast_values = {}
        for key, loans in loan_forecast.forecast_values.items():
            forecast_values[key] = loans * cost_of_risk_assumption.value
            
        return ForecastLine(
            metric_name="Provision for Credit Losses",
            historical_values={}, 
            forecast_values=forecast_values,
            growth_rates={},
            assumptions_used=[cost_of_risk_assumption]
        )

    @staticmethod
    def forecast_operating_expenses(historical_opex: Dict[str, float], cost_to_income_assumption: ForecastAssumption, income_forecast: ForecastLine) -> ForecastLine:
        """OpEx = Total Income × Cost-to-Income Ratio."""
        forecast_values = {}
        for key, income in income_forecast.forecast_values.items():
            forecast_values[key] = income * cost_to_income_assumption.value
            
        return ForecastLine(
            metric_name="Operating Expenses",
            historical_values=historical_opex,
            forecast_values=forecast_values,
            growth_rates={},
            assumptions_used=[cost_to_income_assumption]
        )

    @staticmethod
    def forecast_profit(nii_forecast: ForecastLine, fee_income_forecast: ForecastLine, opex_forecast: ForecastLine, provision_forecast: ForecastLine, tax_rate_assumption: ForecastAssumption) -> ForecastLine:
        """PAT = (NII + Fees - OpEx - Provisions) × (1 - Tax Rate)"""
        forecast_values = {}
        for key in nii_forecast.forecast_values.keys():
            nii = nii_forecast.forecast_values.get(key, 0.0)
            fees = fee_income_forecast.forecast_values.get(key, 0.0)
            opex = opex_forecast.forecast_values.get(key, 0.0)
            provision = provision_forecast.forecast_values.get(key, 0.0)
            
            pre_tax_profit = nii + fees - opex - provision
            pat = pre_tax_profit * (1.0 - tax_rate_assumption.value)
            forecast_values[key] = pat
            
        return ForecastLine(
            metric_name="Profit After Tax (PAT)",
            historical_values={}, 
            forecast_values=forecast_values,
            growth_rates={},
            assumptions_used=[tax_rate_assumption]
        )

    @staticmethod
    def forecast_book_value(current_bv: float, profit_forecast: ForecastLine, payout_ratio_assumption: ForecastAssumption) -> ForecastLine:
        """BV(t+1) = BV(t) + PAT(t) - Dividends(t); Dividends = PAT × Payout Ratio"""
        forecast_values = {}
        bv_current = current_bv
        # Need keys to be ordered chronologically, assume they are generated in order
        keys = list(profit_forecast.forecast_values.keys())
        
        for key in keys:
            pat = profit_forecast.forecast_values[key]
            dividends = pat * payout_ratio_assumption.value
            bv_current = bv_current + pat - dividends
            forecast_values[key] = bv_current
            
        return ForecastLine(
            metric_name="Book Value",
            historical_values={"Current": current_bv},
            forecast_values=forecast_values,
            growth_rates={},
            assumptions_used=[payout_ratio_assumption]
        )

    @staticmethod
    def forecast_eps(profit_forecast: ForecastLine, shares_outstanding_assumption: ForecastAssumption) -> ForecastLine:
        forecast_values = {}
        for key, pat in profit_forecast.forecast_values.items():
            forecast_values[key] = pat / shares_outstanding_assumption.value if shares_outstanding_assumption.value else 0.0
            
        return ForecastLine(
            metric_name="Earnings Per Share (EPS)",
            historical_values={},
            forecast_values=forecast_values,
            growth_rates={},
            assumptions_used=[shares_outstanding_assumption]
        )

    @staticmethod
    def forecast_dps(eps_forecast: ForecastLine, payout_ratio_assumption: ForecastAssumption) -> ForecastLine:
        forecast_values = {}
        for key, eps in eps_forecast.forecast_values.items():
            forecast_values[key] = eps * payout_ratio_assumption.value
            
        return ForecastLine(
            metric_name="Dividends Per Share (DPS)",
            historical_values={},
            forecast_values=forecast_values,
            growth_rates={},
            assumptions_used=[payout_ratio_assumption]
        )

    @staticmethod
    def build_full_bank_forecast(historical: dict, assumptions: Dict[str, ForecastAssumption], years: int = 5) -> ForecastResult:
        """Orchestrates all methods into a complete bank forecast."""
        req_assumps = ['loan_growth', 'deposit_growth', 'nim', 'cost_of_risk', 'cost_to_income', 'fee_income_growth', 'tax_rate', 'payout_ratio', 'shares_outstanding']
        for req in req_assumps:
            if req not in assumptions:
                raise ValueError(f"Missing required assumption: {req}")

        historical_loans = historical.get('loans', {})
        historical_deposits = historical.get('deposits', {})
        historical_fees = historical.get('fee_income', {})
        historical_opex = historical.get('operating_expenses', {})
        current_bv = historical.get('current_book_value', 0.0)

        loan_forecast = BankForecaster.forecast_loans(historical_loans, assumptions['loan_growth'], years)
        deposit_forecast = BankForecaster.forecast_deposits(historical_deposits, assumptions['deposit_growth'], years)
        nii_forecast = BankForecaster.forecast_net_interest_income(loan_forecast, assumptions['nim'])
        provision_forecast = BankForecaster.forecast_provision(loan_forecast, assumptions['cost_of_risk'])
        fee_income_forecast = GeneralForecaster.forecast_revenue(historical_fees, assumptions['fee_income_growth'], years)
        fee_income_forecast.metric_name = "Fee Income"
        
        # Total Operating Income for OPEX calculation
        total_income_forecast_values = {}
        for key in nii_forecast.forecast_values:
            total_income_forecast_values[key] = nii_forecast.forecast_values.get(key, 0.0) + fee_income_forecast.forecast_values.get(key, 0.0)
        
        total_income_line = ForecastLine(
            metric_name="Total Operating Income",
            historical_values={},
            forecast_values=total_income_forecast_values,
            growth_rates={},
            assumptions_used=[]
        )

        opex_forecast = BankForecaster.forecast_operating_expenses(historical_opex, assumptions['cost_to_income'], total_income_line)
        profit_forecast = BankForecaster.forecast_profit(nii_forecast, fee_income_forecast, opex_forecast, provision_forecast, assumptions['tax_rate'])
        bv_forecast = BankForecaster.forecast_book_value(current_bv, profit_forecast, assumptions['payout_ratio'])
        eps_forecast = BankForecaster.forecast_eps(profit_forecast, assumptions['shares_outstanding'])
        dps_forecast = BankForecaster.forecast_dps(eps_forecast, assumptions['payout_ratio'])

        sorted_keys = sorted(historical_loans.keys())
        base_year = sorted_keys[-1] if sorted_keys else "FY0"

        return ForecastResult(
            company_id=historical.get("company_id", "UNKNOWN"),
            forecast_years=years,
            base_year=base_year,
            lines=[loan_forecast, deposit_forecast, nii_forecast, provision_forecast, fee_income_forecast, opex_forecast, profit_forecast, bv_forecast, eps_forecast, dps_forecast],
            all_assumptions=list(assumptions.values()),
            warnings=[]
        )
