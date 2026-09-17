import logging
from typing import Dict, List, Any
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Mock implementations of technical indicators and fundamental checks for benchmarking

def calculate_sma(prices: List[Decimal], period: int = 14) -> Decimal:
    if len(prices) < period:
        return Decimal('0')
    return sum(prices[-period:]) / period

def calculate_rsi(prices: List[Decimal], period: int = 14) -> Decimal:
    return Decimal('55.5')  # Mock value

def calculate_macd(prices: List[Decimal]) -> Dict[str, Decimal]:
    return {"macd": Decimal('1.2'), "signal": Decimal('1.0'), "hist": Decimal('0.2')}

def calculate_bollinger_bands(prices: List[Decimal], period: int = 20) -> Dict[str, Decimal]:
    sma = calculate_sma(prices, period)
    return {"upper": sma * Decimal('1.05'), "lower": sma * Decimal('0.95'), "mid": sma}

def check_fundamental_equation(assets: Decimal, liabilities: Decimal, equity: Decimal) -> bool:
    """Fundamental suite: Assets = Liabilities + Equity"""
    # Using small tolerance for floating point / decimal precision issues in real world
    tolerance = Decimal('0.01')
    return abs(assets - (liabilities + equity)) <= tolerance

def evaluate_valuation(ticker: str, sector: str, financials: Dict[str, Decimal]) -> Dict[str, Any]:
    """Dynamically select valuation model by sector"""
    logger.info(f"Selecting valuation model for {ticker} in sector {sector}...")
    if sector.lower() == 'bank':
        # Use P/B for Banks
        book_value = financials.get('book_value', Decimal('1'))
        market_cap = financials.get('market_cap', Decimal('1'))
        pb_ratio = market_cap / book_value
        logger.info(f"[{ticker}] Selected P/B Model. P/B Ratio: {pb_ratio:.2f}")
        return {"model": "P/B", "value": pb_ratio}
    elif sector.lower() == 'telecom':
        # Use DCF for Telecoms
        fcf = financials.get('fcf', Decimal('100'))
        wacc = financials.get('wacc', Decimal('0.1'))
        growth = financials.get('growth_rate', Decimal('0.03'))
        dcf_value = fcf * (Decimal('1') + growth) / (wacc - growth)
        logger.info(f"[{ticker}] Selected DCF Model. DCF Value: {dcf_value:.2f}")
        return {"model": "DCF", "value": dcf_value}
    else:
        logger.warning(f"[{ticker}] Unknown sector {sector}, falling back to generic DCF.")
        return {"model": "Generic DCF", "value": Decimal('0')}

def run_benchmarks():
    companies = [
        {"ticker": "NMB", "sector": "Bank", "prices": [Decimal('2000'), Decimal('2100'), Decimal('2050')] * 10,
         "financials": {"assets": Decimal('10000'), "liabilities": Decimal('8000'), "equity": Decimal('2000'),
                        "book_value": Decimal('2000'), "market_cap": Decimal('2500')}},
        {"ticker": "CRDB", "sector": "Bank", "prices": [Decimal('400'), Decimal('420'), Decimal('410')] * 10,
         "financials": {"assets": Decimal('8000'), "liabilities": Decimal('6500'), "equity": Decimal('1500'),
                        "book_value": Decimal('1500'), "market_cap": Decimal('1800')}},
        {"ticker": "Safaricom", "sector": "Telecom", "prices": [Decimal('15'), Decimal('16'), Decimal('15.5')] * 10,
         "financials": {"assets": Decimal('5000'), "liabilities": Decimal('3000'), "equity": Decimal('2000'),
                        "fcf": Decimal('500'), "wacc": Decimal('0.12'), "growth_rate": Decimal('0.05')}},
        {"ticker": "Stanbic Uganda", "sector": "Bank", "prices": [Decimal('30'), Decimal('32'), Decimal('31')] * 10,
         "financials": {"assets": Decimal('6000'), "liabilities": Decimal('4800'), "equity": Decimal('1200'),
                        "book_value": Decimal('1200'), "market_cap": Decimal('1400')}},
    ]

    logger.info("=== Starting Phase 21 Benchmarking ===")

    for company in companies:
        ticker = company['ticker']
        sector = company['sector']
        prices = company['prices']
        fins = company['financials']
        
        logger.info(f"\n--- Benchmarking {ticker} ({sector}) ---")
        
        # 1. Technical Benchmarks
        sma = calculate_sma(prices)
        rsi = calculate_rsi(prices)
        macd = calculate_macd(prices)
        bb = calculate_bollinger_bands(prices)
        logger.info(f"[{ticker}] Technicals -> SMA: {sma:.2f}, RSI: {rsi}, MACD: {macd['macd']}, BB_Mid: {bb['mid']:.2f}")

        # 2. Fundamental Benchmarks
        is_balanced = check_fundamental_equation(fins['assets'], fins['liabilities'], fins['equity'])
        logger.info(f"[{ticker}] Fundamentals -> Assets = Liabilities + Equity: {'PASSED' if is_balanced else 'FAILED'}")

        # 3. Valuation Benchmark
        evaluate_valuation(ticker, sector, fins)

    logger.info("\n=== Phase 21 Benchmarking Complete ===")

if __name__ == '__main__':
    run_benchmarks()
