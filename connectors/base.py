from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ExchangeConnector(ABC):
    """
    Abstract base class for all African exchange connectors.
    Ensures standard methodology for data ingestion across varying exchanges.
    """
    
    @abstractmethod
    def list_companies(self) -> List[Dict[str, Any]]:
        """Returns a list of listed companies on the exchange."""
        pass

    @abstractmethod
    def get_company_profile(self, ticker: str) -> Dict[str, Any]:
        """Returns the profile of a specific company."""
        pass

    @abstractmethod
    def get_price_history(self, ticker: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Returns price history.
        Must accurately handle and report non-trading days, zero-volume periods, and suspensions.
        """
        pass

    @abstractmethod
    def get_filings(self, ticker: str) -> List[Dict[str, Any]]:
        """Returns a list of available regulatory filings (e.g., Annual Reports)."""
        pass

    @abstractmethod
    def get_announcements(self, ticker: str) -> List[Dict[str, Any]]:
        """Returns a list of corporate announcements."""
        pass

    @abstractmethod
    def get_dividends(self, ticker: str) -> List[Dict[str, Any]]:
        """Returns dividend history."""
        pass

    @abstractmethod
    def get_corporate_actions(self, ticker: str) -> List[Dict[str, Any]]:
        """Returns corporate actions (splits, rights issues, etc.)."""
        pass
