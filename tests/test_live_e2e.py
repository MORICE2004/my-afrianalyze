import os
import pytest
from datetime import date, timedelta
from connectors.dse.market_provider import DSEMarketProvider

@pytest.mark.skipif(
    os.environ.get("APP_ENV") not in ["PRODUCTION", "DEVELOPMENT"],
    reason="Requires APP_ENV to be PRODUCTION or DEVELOPMENT for live E2E tests."
)
def test_live_dse_e2e_nmb():
    """
    End-to-End test for NMB on DSE.
    """
    # 1. Instantiate the DSE Connector
    provider = DSEMarketProvider()
    
    symbol = "NMB"
    
    # 2. Fetch real NMB historical market data
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    history = provider.get_history(symbol=symbol, start_date=start_date, end_date=end_date)
    
    assert len(history) > 0
    assert history[0].symbol == symbol
    assert history[0].close > 0
    
    # 3. Fetch real NMB quote (simulating profile data proxy)
    quote = provider.get_quote(symbol=symbol)
    assert quote.symbol == symbol
    assert quote.price > 0
    assert quote.currency == "TZS"
