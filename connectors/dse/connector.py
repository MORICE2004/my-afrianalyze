import requests
from datetime import date
from typing import List, Dict, Any, Union
import uuid
from decimal import Decimal

from connectors.base import ExchangeConnector
from packages.schemas.company import Company
from packages.schemas.market import PricePoint

class DSEConnector(ExchangeConnector):
    """
    Implementation of the ExchangeConnector for the Dar es Salaam Stock Exchange (DSE).
    This serves as the initial reference connector for Phase 1 MVP.
    """
    
    def __init__(self):
        self.base_url = "https://www.dse.co.tz"
        self.firecrawl_url = "http://localhost:3002/v1"

    def _scrape_url(self, target_url: str) -> str:
        """
        Helper method to scrape a URL using Firecrawl.
        """
        try:
            response = requests.post(
                f"{self.firecrawl_url}/scrape",
                json={"url": target_url, "formats": ["markdown"]},
                timeout=5
            )
            response.raise_for_status()
            return response.json().get("data", {}).get("markdown", "")
        except requests.exceptions.RequestException:
            # Fallback to empty string on failure
            return ""

    def list_companies(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("DSE list_companies not yet implemented")

    def get_company_profile(self, ticker: str) -> Company:
        target_url = f"{self.base_url}/companies/{ticker.lower()}"
        scraped_markdown = self._scrape_url(target_url)
        
        # Stub logic specifically for NMB
        if ticker.upper() == "NMB":
            return Company(
                company_id=uuid.uuid4(),
                name="NMB Bank Plc",
                ticker="NMB",
                exchange="DSE",
                country="Tanzania",
                sector="Financials",
                sub_sector="Banks",
                reporting_currency="TZS",
                fiscal_year_end="12-31",
                business_description="NMB Bank Plc is a commercial bank in Tanzania...",
                shares_outstanding=500000000
            )
        
        raise NotImplementedError("DSE get_company_profile not fully implemented for other tickers")

    def get_price_history(self, ticker: str, start_date: str, end_date: str) -> List[PricePoint]:
        target_url = f"{self.base_url}/price-history/{ticker.lower()}?start={start_date}&end={end_date}"
        scraped_markdown = self._scrape_url(target_url)
        
        # Stub logic specifically for NMB
        if ticker.upper() == "NMB":
            # Just returning a single stubbed day for demonstration
            return [
                PricePoint(
                    ticker="NMB",
                    exchange="DSE",
                    date=date.fromisoformat(start_date) if len(start_date) == 10 else date(2023, 1, 1),
                    open=Decimal("3500.00"),
                    high=Decimal("3550.00"),
                    low=Decimal("3500.00"),
                    close=Decimal("3520.00"),
                    volume=15000,
                    is_trading_day=True,
                    is_suspended=False,
                    is_stale=False
                )
            ]
        
        raise NotImplementedError("DSE get_price_history not fully implemented for other tickers")

    def get_filings(self, ticker: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("DSE get_filings not yet implemented")

    def get_announcements(self, ticker: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("DSE get_announcements not yet implemented")

    def get_dividends(self, ticker: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("DSE get_dividends not yet implemented")

    def get_corporate_actions(self, ticker: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("DSE get_corporate_actions not yet implemented")
