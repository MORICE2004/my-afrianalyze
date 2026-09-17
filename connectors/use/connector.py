import uuid
from typing import List, Dict, Any
from datetime import date
from decimal import Decimal
from connectors.base import ExchangeConnector
from packages.schemas.company import Company
from packages.schemas.market import PricePoint

class USEConnector(ExchangeConnector):
    """
    Uganda Securities Exchange (USE) connector.
    """
    
    def list_companies(self) -> List[Dict[str, Any]]:
        return [
            {"ticker": "SBU", "name": "Stanbic Bank Uganda"},
            {"ticker": "UMEME", "name": "Umeme Limited"}
        ]

    def get_company_profile(self, ticker: str) -> Company:
        if ticker.upper() == "SBU":
            return Company(
                company_id=uuid.uuid4(),
                name="Stanbic Bank Uganda",
                ticker="SBU",
                exchange="USE",
                country="Uganda",
                sector="Financials",
                sub_sector="Banks",
                reporting_currency="UGX",
                fiscal_year_end="12-31",
                business_description="Stanbic Bank Uganda is a commercial bank...",
                shares_outstanding=51188669700
            )
        elif ticker.upper() == "UMEME":
            return Company(
                company_id=uuid.uuid4(),
                name="Umeme Limited",
                ticker="UMEME",
                exchange="USE",
                country="Uganda",
                sector="Utilities",
                sub_sector="Electricity",
                reporting_currency="UGX",
                fiscal_year_end="12-31",
                business_description="Umeme Limited is an electricity distribution company...",
                shares_outstanding=1623878005
            )
        raise ValueError(f"Company profile for {ticker} not found")

    def get_price_history(self, ticker: str, start_date: str, end_date: str) -> List[PricePoint]:
        return [
            PricePoint(
                ticker=ticker.upper(),
                exchange="USE",
                date=date.fromisoformat(start_date) if len(start_date) == 10 else date(2023, 1, 1),
                open=Decimal("30.00"),
                high=Decimal("31.00"),
                low=Decimal("30.00"),
                close=Decimal("30.50"),
                volume=100000,
                is_trading_day=True,
                is_suspended=False,
                is_stale=False
            )
        ]

    def get_filings(self, ticker: str) -> List[Dict[str, Any]]:
        return []

    def get_announcements(self, ticker: str) -> List[Dict[str, Any]]:
        return []

    def get_dividends(self, ticker: str) -> List[Dict[str, Any]]:
        return []

    def get_corporate_actions(self, ticker: str) -> List[Dict[str, Any]]:
        return []
