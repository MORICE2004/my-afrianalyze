"""Technical indicators: hand-worked values, an independent cross-check for MACD, and the section-74 rules
(liquidity gate, stale data, split adjustment). Synthetic price series, built in the tests."""
from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path

import pytest

from packages.analysis import technical as ta

CFG = json.loads(Path("config/technical.json").read_text(encoding="utf-8"))


def test_sma_and_ema_by_hand():
    assert ta.sma([D(1), D(2), D(3), D(4), D(5)], 3) == D(4)
    # alpha = 2/3; seed = mean(1, 2) = 1.5; then 2/3*3 + 1/3*1.5 = 2.5; then 2/3*4 + 1/3*2.5 = 3.5
    e = ta.ema_series([D(1), D(2), D(3), D(4)], 2)
    assert [round(x, 10) for x in e] == [D("1.5"), D("2.5"), D("3.5")]


def test_rsi_by_hand():
    # changes +1 -1 +1 -1, n = 2: averages start (0.5, 0.5), then (0.75, 0.25), then (0.375, 0.625)
    # RS = 0.6, RSI = 100 - 100 / 1.6 = 37.5
    assert ta.rsi([D(1), D(2), D(1), D(2), D(1)], 2) == D("37.5")
    assert ta.rsi([D(i) for i in range(1, 20)], 14) == D(100)         # only gains
    assert ta.rsi([D(5)] * 20, 14) is None                              # no movement: undefined


def test_bollinger_by_hand():
    # mean 3, population variance (4+1+0+1+4)/5 = 2, so the bands are 3 -/+ 2*sqrt(2)
    lo, mid, hi = ta.bollinger([D(1), D(2), D(3), D(4), D(5)], 5, D(2))
    assert mid == D(3)
    assert abs(hi - (D(3) + 2 * D(2).sqrt())) < D("1e-20") and abs(lo - (D(3) - 2 * D(2).sqrt())) < D("1e-20")


def test_obv_by_hand():
    # up 10, flat 0, down 30
    assert ta.obv_change([D(1), D(2), D(2), D(1)], [D(0), D(10), D(20), D(30)]) == D(-20)


def _independent_macd(xs, fast, slow, sig):
    """Written separately, in floats, as a cross-check (same SMA-seeded convention)."""
    def ema(v, n):
        k, cur, out = 2 / (n + 1), sum(v[:n]) / n, []
        out.append(cur)
        for x in v[n:]:
            cur = x * k + cur * (1 - k)
            out.append(cur)
        return out
    f, s = ema(xs, fast), ema(xs, slow)
    line = [a - b for a, b in zip(f[slow - fast:], s)]
    signal = ema(line, sig)
    return line[-1], signal[-1]


def test_macd_matches_an_independent_implementation():
    xs = [100 + 5 * ((i * 7919) % 13 - 6) / 6 + i * 0.3 for i in range(120)]
    line, sig, hist = ta.macd([D(str(x)) for x in xs], 12, 26, 9)
    ref_line, ref_sig = _independent_macd(xs, 12, 26, 9)
    assert abs(float(line) - ref_line) < 1e-9 and abs(float(sig) - ref_sig) < 1e-9
    assert hist == line - sig


def _bars(n, start=date(2025, 1, 1), close=lambda i: D(1000 + i), volume=lambda i: D(100)):
    days = [start + timedelta(days=i) for i in range(n)]
    return [(d, close(i), volume(i)) for i, d in enumerate(days)]


def test_a_liquid_fresh_series_gives_every_close_based_indicator():
    bars = _bars(300)
    out = ta.analyse(bars, "DSE:TEST", CFG, today=bars[-1][0])
    ind = out["indicators"]
    for k in ("sma_20", "sma_50", "sma_200", "ema_20", "macd", "bollinger", "obv", "range_52w"):
        assert ind[k]["available"] and ind[k]["status"] == "VERIFIED", k
    assert ind["sma_200"]["price_vs"] == "above"            # a steadily rising price
    assert ind["rsi_14"]["value"] == D(100) and ind["rsi_14"]["zone"] == "above 70"
    for k in ("atr_14", "adx_14", "vwap"):                   # not computable from closes alone
        assert ind[k]["status"] == "INSUFFICIENT_DATA" and "not stored" in ind[k]["reason"]


def test_too_few_closes_is_insufficient_data_not_a_number():
    out = ta.analyse(_bars(30), "DSE:TEST", CFG, today=date(2025, 1, 30))
    assert out["indicators"]["sma_200"]["status"] == "INSUFFICIENT_DATA"
    assert "needs 200 trading days" in out["indicators"]["sma_200"]["reason"]
    assert out["indicators"]["sma_20"]["available"]


def test_a_thinly_traded_window_is_refused():
    # Half the days without a trade: the repeated closes must not become an RSI or a Bollinger band.
    bars = _bars(300, volume=lambda i: D(0) if i % 2 else D(100))
    ind = ta.analyse(bars, "DSE:TEST", CFG, today=bars[-1][0])["indicators"]
    for k in ("rsi_14", "bollinger", "sma_20", "macd"):
        assert ind[k]["status"] == "INSUFFICIENT_DATA" and "had no trade" in ind[k]["reason"], k


def test_old_prices_are_marked_stale():
    bars = _bars(300)
    out = ta.analyse(bars, "DSE:TEST", CFG, today=bars[-1][0] + timedelta(days=30))
    assert out["stale"] and out["indicators"]["sma_20"]["status"] == "STALE"


def test_the_nmb_split_is_not_read_as_a_crash():
    """NMB's 1:10 split on 2026-08-24 (config/corporate_actions.json). Published closes fall from 20,000 to
    2,000; adjusted, the price never moved, so RSI is undefined rather than deeply 'oversold'."""
    split = date(2026, 8, 24)
    bars = [(split - timedelta(days=40 - i), D(20000), D(100)) for i in range(40)]
    bars += [(split + timedelta(days=i), D(2000), D(1000)) for i in range(40)]
    out = ta.analyse(bars, "DSE:NMB", CFG, today=bars[-1][0])
    assert out["split_adjusted"]
    assert out["indicators"]["rsi_14"]["status"] == "INSUFFICIENT_DATA"
    assert out["indicators"]["sma_50"]["value"] == D(2000)
    # Volume is put on today's share basis too: 100 old shares are 1,000 new ones, so OBV sees no flow.
    assert out["indicators"]["obv"]["change"] == D(0)


def test_no_prices_at_all():
    assert ta.analyse([], "DSE:TEST", CFG)["status"] == "INSUFFICIENT_DATA"
