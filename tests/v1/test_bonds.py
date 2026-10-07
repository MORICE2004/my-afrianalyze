"""Bond mathematics: identities that must hold exactly, and the Bank of Tanzania's own published prices.

The BoT cases are real auction results stored by pipelines/macro.py (coupon, weighted average yield,
redemption date, weighted average price), copied here so the test needs no database."""
from __future__ import annotations

from datetime import date
from decimal import Decimal as D

import pytest

from packages.analysis import bonds


def test_a_par_bond_on_a_coupon_date_is_priced_at_100():
    r = bonds.analyse(D("0.10"), D("0.10"), date(2026, 1, 15), date(2031, 1, 15), 2)
    assert abs(r["clean_price"] - 100) < D("1e-20") and r["accrued_interest"] == 0


def test_one_remaining_payment_has_duration_equal_to_its_time_to_maturity():
    # Settle exactly one coupon period before maturity: Macaulay duration = 0.5 years.
    r = bonds.analyse(D("0.12"), D("0.08"), date(2026, 1, 15), date(2026, 7, 15), 2)
    assert r["macaulay_duration"] == D("0.5") and r["coupons_remaining"] == 1
    assert r["modified_duration"] == D("0.5") / D("1.04")


def test_accrued_interest_grows_through_the_period():
    early = bonds.analyse(D("0.10"), D("0.10"), date(2026, 2, 15), date(2031, 1, 15), 2)
    late = bonds.analyse(D("0.10"), D("0.10"), date(2026, 6, 15), date(2031, 1, 15), 2)
    assert 0 < early["accrued_interest"] < late["accrued_interest"] < 5


def test_duration_and_convexity_approximate_a_real_repricing():
    base = bonds.analyse(D("0.1125"), D("0.106924"), date(2026, 9, 3), date(2036, 7, 23), 2)
    up = bonds.analyse(D("0.1125"), D("0.116924"), date(2026, 9, 3), date(2036, 7, 23), 2)
    actual = up["dirty_price"] / base["dirty_price"] - 1
    approx = bonds.price_change(base["modified_duration"], base["convexity"], D("0.01"))
    assert abs(actual - approx) < D("0.001")            # second-order approximation within 0.1%


# (tenor, coupon, weighted average yield, auction date, redemption, BoT weighted average price)
BOT = [
    ("5Y", "0.1025", "0.095275", date(2026, 9, 16), date(2031, 4, 30), "102.6275"),
    ("7Y", "0.0948", "0.097101", date(2022, 11, 9), date(2029, 11, 10), "98.8503"),
    ("10Y", "0.1125", "0.106924", date(2026, 9, 2), date(2036, 7, 23), "103.3267"),
    ("15Y", "0.1225", "0.105515", date(2026, 8, 19), date(2041, 2, 19), "112.4713"),
    ("25Y", "0.1325", "0.114799", date(2026, 8, 5), date(2051, 2, 5), "114.4173"),
    ("2Y", "0.095", "0.084033", date(2026, 7, 29), date(2028, 7, 30), "101.9580"),
    ("20Y", "0.1225", "0.113306", date(2026, 7, 8), date(2046, 7, 9), "107.1868"),
]


@pytest.mark.parametrize("tenor, cpn, ytm, auction, maturity, price", BOT)
def test_semi_annual_t_plus_1_reproduces_the_bots_published_prices(tenor, cpn, ytm, auction, maturity, price):
    r = bonds.analyse(D(cpn), D(ytm), date.fromordinal(auction.toordinal() + 1), maturity, 2)
    # Five tenors match to 0.0003 per 100. The 2Y and 20Y settle on a coupon date and differ by 0.02 to 0.03:
    # the BoT averages prices and yields separately, so the price at the average yield is not the average price.
    assert abs(r["clean_price"] - D(price)) < D("0.05"), f"{tenor}: {r['clean_price']} vs {price}"
