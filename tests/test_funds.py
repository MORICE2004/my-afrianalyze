import pytest
from decimal import Decimal
from packages.funds.analyzer import FundAnalyzer

def test_fund_total_return():
    ret = FundAnalyzer.calculate_total_return(
        start_nav=Decimal('100.0'),
        end_nav=Decimal('110.0'),
        distributions=Decimal('5.0')
    )
    # (110 - 100 + 5) / 100 = 0.15
    assert ret == Decimal('0.150000')

def test_fund_cagr():
    cagr = FundAnalyzer.calculate_annualized_return(
        start_nav=Decimal('100.0'),
        end_nav=Decimal('121.0'),
        years=Decimal('2.0')
    )
    # sqrt(1.21) - 1 = 0.1
    assert cagr == Decimal('0.100000')

def test_max_drawdown():
    navs = [Decimal('100.0'), Decimal('110.0'), Decimal('99.0'), Decimal('120.0')]
    md = FundAnalyzer.calculate_max_drawdown(navs)
    # peak is 110. drops to 99. drawdown = 11/110 = 0.1
    assert md == Decimal('0.100000')
