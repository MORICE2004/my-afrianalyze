"""Deterministic technical indicators for thinly traded shares (PRODUCT_CONTEXT.md section 74).

Everything is exact Decimal arithmetic on stored, split-adjusted closes. Two rules come first:

1. **Liquidity gate.** On a day without a trade the DSE repeats the previous close. Repeated closes look like
   calm (Bollinger), like strength or weakness (RSI), or like a trend (moving averages) that no trade ever
   made. So each indicator checks the share of zero-volume days in its own window; above
   `max_zero_volume_share` (config/technical.json) it is INSUFFICIENT_DATA, not a number.
2. **Only what the data supports.** Close and volume are stored; daily high, low and turnover are not. ATR and
   ADX (need high and low) and VWAP (needs turnover) are reported as INSUFFICIENT_DATA with that reason
   instead of an approximation from closes.

The output describes price behaviour. It never feeds the valuation, the cost of equity or the model view, and
it uses descriptive words ("above its 200-day average"), not trading signals.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal, getcontext

from packages.analysis import corporate_actions
from packages.analysis.common import INSUFFICIENT_DATA, STALE, VERIFIED, Unavailable

getcontext().prec = 28
ONE, ZERO, HUNDRED = Decimal(1), Decimal(0), Decimal(100)


# ------------------------------------------------------------------ pure indicator maths

def sma(xs: list[Decimal], n: int) -> Decimal:
    return sum(xs[-n:], ZERO) / n


def ema_series(xs: list[Decimal], n: int) -> list[Decimal]:
    """Exponential moving average, seeded with the simple average of the first n values (the common
    convention); alpha = 2 / (n + 1). Element i corresponds to xs[n - 1 + i]."""
    alpha = Decimal(2) / (n + 1)
    out = [sum(xs[:n], ZERO) / n]
    for x in xs[n:]:
        out.append(alpha * x + (ONE - alpha) * out[-1])
    return out


def rsi(xs: list[Decimal], n: int) -> Decimal | None:
    """Wilder's RSI: first averages are simple means of the first n changes, then Wilder smoothing
    avg = (avg * (n - 1) + current) / n. None when the price never moved (RSI is undefined)."""
    changes = [b - a for a, b in zip(xs, xs[1:])]
    gains = [max(c, ZERO) for c in changes]
    losses = [max(-c, ZERO) for c in changes]
    avg_g, avg_l = sum(gains[:n], ZERO) / n, sum(losses[:n], ZERO) / n
    for g, l in zip(gains[n:], losses[n:]):
        avg_g = (avg_g * (n - 1) + g) / n
        avg_l = (avg_l * (n - 1) + l) / n
    if avg_g == 0 and avg_l == 0:
        return None
    if avg_l == 0:
        return HUNDRED
    return HUNDRED - HUNDRED / (ONE + avg_g / avg_l)


def macd(xs: list[Decimal], fast: int, slow: int, signal: int) -> tuple[Decimal, Decimal, Decimal]:
    """(MACD line, signal line, histogram) at the last close. MACD = EMA(fast) - EMA(slow); signal is the
    EMA(signal) of the MACD line from the first day both EMAs exist."""
    e_fast, e_slow = ema_series(xs, fast), ema_series(xs, slow)
    line = [f - s for f, s in zip(e_fast[slow - fast:], e_slow)]
    sig = ema_series(line, signal)
    return line[-1], sig[-1], line[-1] - sig[-1]


def bollinger(xs: list[Decimal], n: int, width: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """(lower, middle, upper): middle = SMA(n); bands = middle +/- width x population standard deviation of
    the same n closes (Bollinger's own definition)."""
    w = xs[-n:]
    mid = sum(w, ZERO) / n
    sd = (sum(((x - mid) ** 2 for x in w), ZERO) / n).sqrt()
    return mid - width * sd, mid, mid + width * sd


def obv_change(closes: list[Decimal], volumes: list[Decimal]) -> Decimal:
    """On-balance volume accumulated over the window: + volume on an up day, - on a down day, 0 when flat."""
    total = ZERO
    for (c0, c1), v in zip(zip(closes, closes[1:]), volumes[1:]):
        total += v if c1 > c0 else -v if c1 < c0 else ZERO
    return total


# ------------------------------------------------------------------ the analysis

def _adjust_volumes(vols: dict[date, Decimal | None], actions: list[dict]) -> dict[date, Decimal | None]:
    """A 1:10 split makes ten shares out of one, so volumes before it are multiplied by the ratio to be
    comparable with today's share count (the inverse of the price adjustment)."""
    out = {}
    for d, v in vols.items():
        factor = ONE
        for a in actions:
            if d < date.fromisoformat(a["effective_date"]):
                factor *= Decimal(str(a["ratio_new_for_old"]))
        out[d] = None if v is None else v * factor
    return out


def analyse(bars: list[tuple[date, Decimal, Decimal | None]], security_id: str, cfg: dict,
            today: date | None = None) -> dict:
    """bars: (trade_date, close as published, volume) in any order. Returns every indicator with a status."""
    today = today or date.today()
    if not bars:
        return {"available": False, "status": INSUFFICIENT_DATA, "reason": "No stored prices for this security."}
    actions = corporate_actions.load_actions(security_id)
    bars = sorted(bars)
    closes_by_day = corporate_actions.adjust_prices({d: c for d, c, _ in bars}, actions)
    vols_by_day = _adjust_volumes({d: v for d, _, v in bars}, actions)
    days = [d for d, _, _ in bars]
    closes = [closes_by_day[d] for d in days]
    volumes = [vols_by_day[d] for d in days]
    last_day = days[-1]
    age = (today - last_day).days
    stale = age > cfg["stale_after_days"]
    status = STALE if stale else VERIFIED
    limit = Decimal(str(cfg["max_zero_volume_share"]))

    def gate(window: int, name: str) -> dict | None:
        """None if the window is usable, else the Unavailable to show instead."""
        if len(closes) < window:
            return Unavailable(f"{name} needs {window} trading days of closes; {len(closes)} are stored.",
                               INSUFFICIENT_DATA).to_dict()
        recent = volumes[-window:]
        zero = sum(1 for v in recent if v is not None and v == 0)
        share = Decimal(zero) / window
        if share > limit:
            return Unavailable(f"{name}: {zero} of the last {window} trading days ({share:.0%}) had no trade, above "
                               f"the {limit:.0%} limit. Repeated closes would be read as price behaviour that no "
                               f"trade made.", INSUFFICIENT_DATA).to_dict()
        return None

    def ok(window: int, **fields) -> dict:
        zero = sum(1 for v in volumes[-window:] if v is not None and v == 0)
        return {"available": True, "status": status, "as_of": last_day.isoformat(), "window": window,
                "zero_volume_days": zero, **fields}

    last = closes[-1]
    out: dict = {}

    for n in cfg["sma_periods"]:
        out[f"sma_{n}"] = gate(n, f"{n}-day simple moving average") or ok(
            n, value=sma(closes, n), formula=f"mean of the last {n} closes",
            price_vs=("above" if last > sma(closes, n) else "below" if last < sma(closes, n) else "at"))

    n = cfg["ema_period"]
    out[f"ema_{n}"] = gate(n, f"{n}-day exponential moving average") or ok(
        n, value=ema_series(closes, n)[-1], formula=f"EMA, alpha = 2/({n}+1), seeded with the first {n}-day mean")

    n = cfg["rsi_period"]
    g = gate(n + 1, f"RSI({n})")
    if g is None:
        r = rsi(closes, n)
        g = (Unavailable(f"RSI({n}) is undefined: the price did not move in the window.", INSUFFICIENT_DATA).to_dict()
             if r is None else ok(n + 1, value=r, formula=f"Wilder RSI over {n} days",
                                  zone="above 70" if r > 70 else "below 30" if r < 30 else "between 30 and 70"))
    out[f"rsi_{n}"] = g

    m = cfg["macd"]
    need = m["slow"] + m["signal"] - 1
    g = gate(need, f"MACD({m['fast']},{m['slow']},{m['signal']})")
    if g is None:
        line, sig, hist = macd(closes, m["fast"], m["slow"], m["signal"])
        g = ok(need, line=line, signal=sig, histogram=hist,
               formula=f"EMA({m['fast']}) - EMA({m['slow']}); signal = EMA({m['signal']}) of that line",
               line_vs_signal="above" if hist > 0 else "below" if hist < 0 else "at")
    out["macd"] = g

    b = cfg["bollinger"]
    g = gate(b["period"], f"Bollinger bands({b['period']},{b['width']})")
    if g is None:
        lo, mid, hi = bollinger(closes, b["period"], Decimal(str(b["width"])))
        g = ok(b["period"], lower=lo, middle=mid, upper=hi,
               percent_b=None if hi == lo else (last - lo) / (hi - lo),
               formula=f"{b['period']}-day mean +/- {b['width']} population standard deviations")
    out["bollinger"] = g

    n = cfg["obv_days"]
    g = gate(n, f"On-balance volume ({n} days)")
    if g is None and any(v is None for v in volumes[-n:]):
        g = Unavailable("On-balance volume needs a volume for every day in the window.", INSUFFICIENT_DATA).to_dict()
    out["obv"] = g or ok(n, change=obv_change(closes[-n:], volumes[-n:]),
                         formula=f"sum over {n} days of +volume on up days and -volume on down days")

    n = min(cfg["range_days"], len(closes))
    window = closes[-n:]
    out["range_52w"] = (Unavailable("The 52-week range needs a year of closes.", INSUFFICIENT_DATA).to_dict()
                        if n < cfg["range_days"] else
                        ok(n, high=max(window), low=min(window),
                           from_high=last / max(window) - 1, from_low=last / min(window) - 1,
                           formula=f"highest and lowest close of the last {n} trading days"))

    for name, why in (("atr_14", "ATR needs each day's high and low"), ("adx_14", "ADX needs each day's high and low"),
                      ("vwap", "VWAP needs each day's turnover")):
        out[name] = Unavailable(f"{why}, which are not stored yet (only the close and volume are).",
                                INSUFFICIENT_DATA).to_dict()

    recent = volumes[-60:]
    return {
        "available": True,
        "status": status,
        "last_close": last, "last_trade_date": last_day.isoformat(), "age_days": age,
        "stale": stale,
        "liquidity": {"window": len(recent),
                      "zero_volume_days": sum(1 for v in recent if v is not None and v == 0),
                      "max_zero_volume_share": limit},
        "split_adjusted": bool(actions),
        "indicators": out,
        "note": ("Descriptive only. These indicators do not change the valuation, the cost of equity or the model "
                 "view, and they are not trading signals."),
    }
