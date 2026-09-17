import os
import pytest
from decimal import Decimal

# Set APP_ENV to TEST to ensure offline execution and mock data loading
os.environ["APP_ENV"] = "TEST"

from connectors.nse.connector import NSEConnector
from connectors.use.connector import USEConnector

def test_nse_connector_get_company_profile():
    connector = NSEConnector()
    profile = connector.get_company_profile("SCOM")
    assert profile.ticker == "SCOM"
    assert profile.exchange == "NSE"
    assert profile.country == "Kenya"
    assert profile.reporting_currency == "KES"
    assert profile.shares_outstanding == 40000000000

def test_nse_connector_get_price_history():
    connector = NSEConnector()
    history = connector.get_price_history("EQTY", "2023-01-01", "2023-01-02")
    assert len(history) == 1
    assert history[0].ticker == "EQTY"
    assert history[0].exchange == "NSE"
    assert history[0].close == Decimal("38.50")

def test_use_connector_get_company_profile():
    connector = USEConnector()
    profile = connector.get_company_profile("MTNU")
    assert profile.ticker == "MTNU"
    assert profile.exchange == "USE"
    assert profile.country == "Uganda"
    assert profile.reporting_currency == "UGX"
    assert profile.shares_outstanding == 22389000000

def test_use_connector_get_price_history():
    connector = USEConnector()
    history = connector.get_price_history("STAN", "2023-01-01", "2023-01-02")
    assert len(history) == 1
    assert history[0].ticker == "STAN"
    assert history[0].exchange == "USE"
    assert history[0].close == Decimal("31.50")
