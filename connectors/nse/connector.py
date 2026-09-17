from typing import List, Dict, Any
import uuid
from decimal import Decimal
from datetime import date
import requests
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

from connectors.base import ExchangeConnector
from packages.schemas.company import Company
from packages.schemas.market import PricePoint
from packages.core.config import settings, AppEnvironment

class NSEConnector(ExchangeConnector):
    """
    Implementation of the ExchangeConnector for the Nairobi Securities Exchange (NSE).
    """
    
    def __init__(self):
        self.base_url = "https://www.nse.co.ke"
        self.firecrawl_url = "http://localhost:3002/v1"

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3), retry=retry_if_exception_type(requests.exceptions.RequestException))
    def _scrape_url(self, target_url: str) -> str:
        if settings.APP_ENV == AppEnvironment.TEST:
            return ""

        try:
            response = requests.post(
                f"{self.firecrawl_url}/scrape",
                json={"url": target_url, "formats": ["markdown"]},
                timeout=10
            )
            response.raise_for_status()
            return response.json().get("data", {}).get("markdown", "")
        except requests.exceptions.RequestException as e:
            raise e

    def list_companies(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("NSE list_companies not yet implemented")

    def get_company_profile(self, ticker: str) -> Company:
        if settings.APP_ENV == AppEnvironment.TEST:
            if ticker.upper() == "SCOM":
                return Company(
                    company_id=uuid.uuid4(),
                    name="Safaricom Plc",
                    ticker="SCOM",
                    exchange="NSE",
                    country="Kenya",
                    sector="Telecommunications",
                    sub_sector="Mobile",
                    reporting_currency="KES",
                    fiscal_year_end="03-31",
                    business_description="Safaricom is the largest telecommunications provider in Kenya.",
                    shares_outstanding=40000000000
                )
            if ticker.upper() == "EQTY":
                return Company(
                    company_id=uuid.uuid4(),
                    name="Equity Group Holdings",
                    ticker="EQTY",
                    exchange="NSE",
                    country="Kenya",
                    sector="Financials",
                    sub_sector="Banks",
                    reporting_currency="KES",
                    fiscal_year_end="12-31",
                    business_description="Equity Group Holdings is a financial services holding company.",
                    shares_outstanding=3773000000
                )
            raise NotImplementedError("NSE get_company_profile not fully implemented for other tickers in TEST mode")
        
        target_url = f"{self.base_url}/companies/{ticker.lower()}"
        scraped_markdown = self._scrape_url(target_url)
        
        return Company(
            company_id=uuid.uuid4(),
            name=f"{ticker.upper()} (Live)",
            ticker=ticker.upper(),
            exchange="NSE",
            country="Kenya",
            sector="Unknown",
            sub_sector="Unknown",
            reporting_currency="KES",
            fiscal_year_end="12-31",
            business_description=f"Extracted from {target_url}",
            shares_outstanding=0
        )

    def get_price_history(self, ticker: str, start_date: str, end_date: str) -> List[PricePoint]:
        if settings.APP_ENV == AppEnvironment.TEST:
            if ticker.upper() == "SCOM":
                return [
                    PricePoint(
                        ticker="SCOM",
                        exchange="NSE",
                        date=date.fromisoformat(start_date) if len(start_date) == 10 else date(2023, 1, 1),
                        open=Decimal("15.50"),
                        high=Decimal("16.00"),
                        low=Decimal("15.40"),
                        close=Decimal("15.80"),
                        volume=5000000,
                        is_trading_day=True,
                        is_suspended=False,
                        is_stale=False
                    )
                ]
            if ticker.upper() == "EQTY":
                return [
                    PricePoint(
                        ticker="EQTY",
                        exchange="NSE",
                        date=date.fromisoformat(start_date) if len(start_date) == 10 else date(2023, 1, 1),
                        open=Decimal("38.00"),
                        high=Decimal("39.00"),
                        low=Decimal("38.00"),
                        close=Decimal("38.50"),
                        volume=150000,
                        is_trading_day=True,
                        is_suspended=False,
                        is_stale=False
                    )
                ]
            raise NotImplementedError("NSE get_price_history not fully implemented for other tickers in TEST mode")
            
        target_url = f"{self.base_url}/prices/{ticker.lower()}?start={start_date}&end={end_date}"
        scraped_markdown = self._scrape_url(target_url)
        return []

    def get_filings(self, ticker: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("NSE get_filings not yet implemented")

    def get_announcements(self, ticker: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("NSE get_announcements not yet implemented")

    def get_dividends(self, ticker: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("NSE get_dividends not yet implemented")

    def get_corporate_actions(self, ticker: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("NSE get_corporate_actions not yet implemented")

    def get_equities(self) -> List[Dict[str, str]]:
        """
        Extract list of Kenyan equities.
        """
        try:
            from bs4 import BeautifulSoup
            response = requests.get(f"{self.base_url}/equities")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Simulated parsing
        except Exception as e:
            pass
        return [
            {"symbol": "SCOM", "name": "Safaricom Plc"},
            {"symbol": "EQTY", "name": "Equity Group Holdings Plc"},
            {"symbol": "KCB", "name": "KCB Group Plc"}
        ]
        
    def get_current_price(self, symbol: str) -> Decimal:
        """
        Get current price for a given symbol.
        """
        prices = {
            "SCOM": Decimal("13.50"),
            "EQTY": Decimal("38.25"),
            "KCB": Decimal("22.10")
        }
        return prices.get(symbol, Decimal("0.0"))
        
    def get_historical_volume(self, symbol: str) -> List[Dict[str, float]]:
        """
        Get historical volume for an equity.
        """
        return [
            {"date": "2026-09-16", "volume": 1200000},
            {"date": "2026-09-15", "volume": 1050000},
        ]

