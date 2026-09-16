from typing import Dict, Optional, List, Any
from . import ratios
from . import valuation

class BankAnalysis:
    def __init__(self, income_statement: Dict[str, float], balance_sheet: Dict[str, float], market_data: Dict[str, float], previous_period: Optional[Dict[str, Any]] = None):
        self.income_statement = income_statement
        self.balance_sheet = balance_sheet
        self.market_data = market_data
        self.previous_period = previous_period

    def get_profitability_metrics(self) -> Dict[str, Optional[float]]:
        return {
            "net_interest_margin": ratios.net_interest_margin(
                self.income_statement.get("net_interest_income", 0.0), 
                self.balance_sheet.get("average_earning_assets", 0.0)
            ),
            "cost_to_income_ratio": ratios.cost_to_income_ratio(
                self.income_statement.get("operating_expenses", 0.0),
                self.income_statement.get("total_operating_income", 0.0)
            ),
            "return_on_assets": ratios.return_on_assets_bank(
                self.income_statement.get("net_income", 0.0),
                self.balance_sheet.get("average_total_assets", 0.0)
            ),
            "return_on_equity": ratios.return_on_equity_bank(
                self.income_statement.get("net_income", 0.0),
                self.balance_sheet.get("average_total_equity", 0.0)
            )
        }

    def get_asset_quality_metrics(self) -> Dict[str, Optional[float]]:
        return {
            "non_performing_loan_ratio": ratios.non_performing_loan_ratio(
                self.balance_sheet.get("non_performing_loans", 0.0),
                self.balance_sheet.get("gross_loans", 0.0)
            ),
            "provision_coverage_ratio": ratios.provision_coverage_ratio(
                self.balance_sheet.get("loan_loss_provisions", 0.0),
                self.balance_sheet.get("non_performing_loans", 0.0)
            ),
            "cost_of_risk": ratios.cost_of_risk(
                self.income_statement.get("provision_charge", 0.0),
                self.balance_sheet.get("average_gross_loans", 0.0)
            )
        }

    def get_capital_metrics(self) -> Dict[str, Optional[float]]:
        return {
            "capital_adequacy_ratio": ratios.capital_adequacy_ratio(
                self.balance_sheet.get("total_capital", 0.0),
                self.balance_sheet.get("risk_weighted_assets", 0.0)
            ),
            "tier1_capital_ratio": ratios.tier1_capital_ratio(
                self.balance_sheet.get("tier1_capital", 0.0),
                self.balance_sheet.get("risk_weighted_assets", 0.0)
            )
        }

    def get_liquidity_metrics(self) -> Dict[str, Optional[float]]:
        return {
            "loan_to_deposit_ratio": ratios.loan_to_deposit_ratio(
                self.balance_sheet.get("total_loans", 0.0),
                self.balance_sheet.get("total_deposits", 0.0)
            ),
            "liquidity_ratio": ratios.liquidity_ratio(
                self.balance_sheet.get("liquid_assets", 0.0),
                self.balance_sheet.get("total_deposits", 0.0)
            )
        }

    def get_growth_metrics(self) -> Dict[str, Optional[float]]:
        if not self.previous_period:
            return {}
        prev_bs = self.previous_period.get("balance_sheet", {})
        return {
            "loan_growth": ratios.loan_growth(
                self.balance_sheet.get("total_loans", 0.0),
                prev_bs.get("total_loans", 0.0)
            ),
            "deposit_growth": ratios.deposit_growth(
                self.balance_sheet.get("total_deposits", 0.0),
                prev_bs.get("total_deposits", 0.0)
            )
        }

    def get_valuation_metrics(self) -> Dict[str, float]:
        target_roe = self.market_data.get("target_roe", 0.15)
        cost_of_equity = self.market_data.get("cost_of_equity", 0.20)
        growth_rate = self.market_data.get("growth_rate", 0.05)
        payout_ratio = self.market_data.get("payout_ratio", 0.40)
        return {
            "justified_pb": valuation.pb_relative_valuation(target_roe, cost_of_equity, growth_rate),
            "justified_pe": valuation.pe_relative_valuation(target_roe, payout_ratio, cost_of_equity, growth_rate)
        }

    def calculate_all_ratios(self) -> Dict[str, Optional[float]]:
        res = {}
        res.update(self.get_profitability_metrics())
        res.update(self.get_asset_quality_metrics())
        res.update(self.get_capital_metrics())
        res.update(self.get_liquidity_metrics())
        res.update(self.get_growth_metrics())
        return res

    def generate_warnings(self) -> List[str]:
        warnings = []
        ratios_calc = self.calculate_all_ratios()
        
        npl_ratio = ratios_calc.get("non_performing_loan_ratio")
        if npl_ratio and npl_ratio > 0.05:
            warnings.append(f"High NPL ratio: {npl_ratio*100:.2f}% (Threshold: 5%)")
            
        car = ratios_calc.get("capital_adequacy_ratio")
        if car and car < 0.12:
            warnings.append(f"Low CAR: {car*100:.2f}% (Threshold: 12%)")
            
        ltd = ratios_calc.get("loan_to_deposit_ratio")
        if ltd and ltd > 1.0:
            warnings.append(f"Loan to Deposit ratio above 100%: {ltd*100:.2f}%. Reliance on wholesale funding.")

        cost_to_income = ratios_calc.get("cost_to_income_ratio")
        if cost_to_income and cost_to_income > 0.65:
            warnings.append(f"High Cost-to-Income ratio: {cost_to_income*100:.2f}%. Poor operational efficiency.")

        return warnings
