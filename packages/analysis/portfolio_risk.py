"""Deterministic portfolio analysis: risk, concentration, liquidity, drift, stress tests, optimisation.

Conventions (config/portfolio.json):
- Prices are split-adjusted closes, so quantities and history are on today's share basis.
- Volatility, correlation and the optimisers use WEEKLY returns (last close of each week), over the weeks in
  which every holding has a close. Daily returns of thinly traded shares are rarely synchronous, which
  understates co-movement (PRODUCT_CONTEXT.md section 74).
- History applies TODAY's quantities to past prices: "what these holdings would have done", not the owner's
  actual performance (we do not know when they bought).
- Statistics are computed in floating point (numpy) and reported rounded; money is Decimal.
- Optimisers need no forecast of returns (minimum variance, risk parity). Mean-variance would need expected
  returns, which no source here supports, so it is INSUFFICIENT_DATA rather than a guess.
- A stress scenario without an evidence-backed link to the holdings (rates or commodities on bank shares)
  is INSUFFICIENT_DATA with the reason, not a made-up sensitivity.
"""
from __future__ import annotations

import math
from datetime import date
from decimal import ROUND_DOWN, Decimal

import numpy as np

from packages.analysis import corporate_actions

Q6 = Decimal("0.000001")


def _r(x: float) -> Decimal:
    return Decimal(repr(float(x))).quantize(Q6)


def _unavailable(reason: str, status: str = "INSUFFICIENT_DATA") -> dict:
    return {"available": False, "status": status, "reason": reason}


def _adjusted(security_id: str, bars: list[tuple[date, Decimal, Decimal | None]]) -> tuple[dict, dict]:
    actions = corporate_actions.load_actions(security_id)
    closes = corporate_actions.adjust_prices({d: c for d, c, _ in bars}, actions)
    vols = {}
    for d, _, v in bars:
        factor = Decimal(1)
        for a in actions:
            if d < date.fromisoformat(a["effective_date"]):
                factor *= Decimal(str(a["ratio_new_for_old"]))
        vols[d] = None if v is None else v * factor
    return closes, vols


def _weekly(closes: dict[date, Decimal]) -> dict[tuple[int, int], tuple[date, float]]:
    out: dict[tuple[int, int], tuple[date, float]] = {}
    for d in sorted(closes):
        out[tuple(d.isocalendar())[:2]] = (d, float(closes[d]))       # the week's last close wins
    return out


def _min_variance(cov: np.ndarray) -> np.ndarray:
    """Long-only minimum variance by active set: solve w ~ inv(S) 1 on the free assets, drop any negative."""
    n = cov.shape[0]
    free = list(range(n))
    while True:
        sub = cov[np.ix_(free, free)]
        raw = np.linalg.solve(sub, np.ones(len(free)))
        w = raw / raw.sum()
        if (w >= 0).all():
            full = np.zeros(n)
            full[free] = w
            return full
        free = [f for f, x in zip(free, w) if x > 0]


def _risk_parity(cov: np.ndarray) -> np.ndarray:
    """Equal risk contribution, long-only, by the standard multiplicative fixed point from inverse volatility."""
    w = 1 / np.sqrt(np.diag(cov))
    w /= w.sum()
    for _ in range(10_000):
        rc = w * (cov @ w)
        new = w * np.sqrt(rc.mean() / rc)
        new /= new.sum()
        if np.max(np.abs(new - w)) < 1e-12:
            return new
        w = new
    return w


def analyse(holdings: list[dict], history: dict[str, list[tuple[date, Decimal, Decimal | None]]], cfg: dict,
            inflation: dict | None = None, target_weights: dict[str, Decimal] | None = None,
            today: date | None = None) -> dict:
    """holdings: [{security_id, quantity (Decimal), sector, currency}]; history: stored bars per security;
    inflation: {"value": Decimal, "as_of": str, "source": str} or None."""
    today = today or date.today()
    if not holdings:
        return _unavailable("The portfolio has no holdings.", "NO_DATA")

    priced, unpriced = [], []
    adj: dict[str, tuple[dict, dict]] = {}
    for h in holdings:
        bars = history.get(h["security_id"]) or []
        if bars:
            adj[h["security_id"]] = _adjusted(h["security_id"], bars)
            priced.append(h)
        else:
            unpriced.append(h["security_id"])
    if not priced:
        return _unavailable("None of the holdings has stored prices, so nothing can be measured.")

    # ---------------------------------------------------------------- value, weights, concentration
    last_close = {h["security_id"]: adj[h["security_id"]][0][max(adj[h["security_id"]][0])] for h in priced}
    values = {h["security_id"]: h["quantity"] * last_close[h["security_id"]] for h in priced}
    total = sum(values.values(), Decimal(0))
    weights = {k: v / total for k, v in values.items()}
    hhi = sum((w * w for w in weights.values()), Decimal(0))
    out: dict = {
        "available": True, "status": "PARTIAL" if unpriced else "VERIFIED",
        "unpriced_holdings": unpriced, "market_value": total, "currency": "TZS",
        "weights": weights,
        "concentration": {"largest_weight": max(weights.values()), "herfindahl": hhi,
                          "effective_holdings": (Decimal(1) / hhi) if hhi else None,
                          "how": "Herfindahl index = sum of squared weights; effective holdings = 1 / Herfindahl"},
        "currency_exposure": {},
        "notes": ["History applies today's quantities to past split-adjusted closes: what these holdings would "
                  "have done, not your actual performance."],
    }
    for h in priced:
        cur = h.get("currency", "TZS")
        out["currency_exposure"][cur] = out["currency_exposure"].get(cur, Decimal(0)) + weights[h["security_id"]]

    # ---------------------------------------------------------------- liquidity
    liq = []
    limit = Decimal(str(cfg["max_zero_volume_share"]))
    part = Decimal(str(cfg["participation_of_daily_volume"]))
    for h in priced:
        closes, vols = adj[h["security_id"]]
        days = sorted(closes)[-cfg["liquidity_days"]:]
        v = [vols[d] for d in days if vols[d] is not None]
        zero = sum(1 for x in v if x == 0)
        adv = (sum(v, Decimal(0)) / len(v)) if v else None
        liq.append({"security_id": h["security_id"], "window_days": len(days), "zero_volume_days": zero,
                    "average_daily_volume": adv,
                    "average_daily_value": None if adv is None else adv * last_close[h["security_id"]],
                    "days_to_sell": None if not adv else (h["quantity"] / (adv * part)).quantize(Decimal("0.1")),
                    "thin": bool(days) and Decimal(zero) / len(days) > limit})
    out["liquidity"] = {"holdings": liq, "how": f"days to sell = quantity / ({part:.0%} of average daily volume "
                                                f"over the last {cfg['liquidity_days']} trading days)"}

    # ---------------------------------------------------------------- drift and rebalancing
    if target_weights:
        rows = []
        for sid, w in sorted(weights.items()):
            t = Decimal(str(target_weights.get(sid, 0)))
            trade_value = t * total - values[sid]
            shares = (trade_value / last_close[sid]).to_integral_value(rounding=ROUND_DOWN)
            rows.append({"security_id": sid, "current": w, "target": t, "drift": w - t,
                         "outside_tolerance": abs(w - t) > Decimal(str(cfg["drift_tolerance"])),
                         "trade_shares": shares, "trade_value": shares * last_close[sid]})
        out["drift"] = {"available": True, "rows": rows, "tolerance": Decimal(str(cfg["drift_tolerance"])),
                        "note": "Trades are whole shares at the last close, rounded toward zero. DSE board lots and "
                                "fees are not applied (not in the system)."}
    else:
        out["drift"] = _unavailable("No target weights set for this portfolio.", "NO_DATA")

    # ---------------------------------------------------------------- weekly history
    weekly = {sid: _weekly(adj[sid][0]) for sid in weights}
    common = sorted(set.intersection(*(set(w) for w in weekly.values())))
    window = common[-(cfg["history_weeks"] + 1):]
    if len(window) - 1 < cfg["min_weeks"]:
        risk = _unavailable(f"Needs {cfg['min_weeks']} weeks in which every holding traded; {max(0, len(window) - 1)} available.")
        out.update(risk=risk, optimisation=risk)
    else:
        sids = sorted(weights)
        px = np.array([[weekly[s][wk][1] for s in sids] for wk in window])
        qty = np.array([float(next(h["quantity"] for h in priced if h["security_id"] == s)) for s in sids])
        value = px @ qty
        rets = value[1:] / value[:-1] - 1
        peak = np.maximum.accumulate(value)
        dd = value / peak - 1
        asset_rets = px[1:] / px[:-1] - 1
        cov = np.cov(asset_rets, rowvar=False) * 52 if len(sids) > 1 else np.array([[np.var(asset_rets, ddof=1) * 52]])
        thin = [x["security_id"] for x in liq if x["thin"]]
        out["risk"] = {
            "available": True, "status": "PARTIAL" if thin else "VERIFIED",
            "weeks": len(rets), "from": weekly[sids[0]][window[0]][0].isoformat(),
            "to": weekly[sids[0]][window[-1]][0].isoformat(),
            "annualised_volatility": _r(np.std(rets, ddof=1) * math.sqrt(52)),
            "return_over_window": _r(value[-1] / value[0] - 1),
            "return_last_52_weeks": _r(value[-1] / value[-53] - 1) if len(value) > 52 else None,
            "max_drawdown": _r(dd.min()),
            "asset_volatility": {s: _r(math.sqrt(cov[i, i])) for i, s in enumerate(sids)},
            "correlation": ({f"{a}|{b}": _r(np.corrcoef(asset_rets[:, i], asset_rets[:, j])[0, 1])
                             for i, a in enumerate(sids) for j, b in enumerate(sids) if i < j} if len(sids) > 1 else {}),
            "thinly_traded": thin,
            "how": "Weekly returns of today's holdings at past split-adjusted closes; volatility annualised by "
                   "the square root of 52; drawdown from the running peak of weekly values.",
        }
        if len(sids) < 2:
            out["optimisation"] = _unavailable("Optimisation needs at least two priced holdings.")
        else:
            current = np.array([float(weights[s]) for s in sids])
            port_vol = lambda w: math.sqrt(float(w @ cov @ w))  # noqa: E731
            mv, rp = _min_variance(cov), _risk_parity(cov)
            out["optimisation"] = {
                "available": True, "status": "PARTIAL" if thin else "VERIFIED",
                "current": {"weights": dict(zip(sids, map(_r, current))), "volatility": _r(port_vol(current)),
                            "how": "Today's weights held constant. Differs from the risk volatility above, which "
                                   "holds today's quantities, so the weights drift with prices"},
                "minimum_variance": {"weights": dict(zip(sids, map(_r, mv))), "volatility": _r(port_vol(mv)),
                                     "how": "Long-only weights with the lowest volatility from the weekly covariance"},
                "risk_parity": {"weights": dict(zip(sids, map(_r, rp))), "volatility": _r(port_vol(rp)),
                                "how": "Long-only weights where each holding contributes the same share of risk"},
                "mean_variance": _unavailable("Needs expected returns for each share. No source supports a forecast "
                                              "for DSE shares, so none is assumed."),
                "note": "Uses only past volatility and correlation, which change. A description of the past "
                        "trade-offs, not advice." + (f" Thinly traded: {', '.join(thin)}." if thin else ""),
            }

    # ---------------------------------------------------------------- stress tests
    sector = {h["security_id"]: h.get("sector") for h in priced}
    currency = {h["security_id"]: h.get("currency", "TZS") for h in priced}

    def result(name: str, sid_effect: dict[str, Decimal], how: str) -> dict:
        eff = sum(sid_effect.values(), Decimal(0))
        by_sector: dict[str, Decimal] = {}
        by_cur: dict[str, Decimal] = {}
        for sid, e in sid_effect.items():
            by_sector[sector[sid] or "Unknown"] = by_sector.get(sector[sid] or "Unknown", Decimal(0)) + e
            by_cur[currency[sid]] = by_cur.get(currency[sid], Decimal(0)) + e
        return {"available": True, "name": name, "portfolio_effect": eff, "portfolio_effect_pct": eff / total,
                "by_asset": [{"security_id": s, "effect": e, "effect_pct": e / values[s]} for s, e in sorted(sid_effect.items())],
                "by_sector": by_sector, "by_currency": by_cur, "how": how}

    stress = []
    for sc in cfg["stress_scenarios"]:
        kind = sc["kind"]
        if kind == "equity_shock":
            s = Decimal(str(sc["shock"]))
            stress.append(result(sc["name"], {k: v * s for k, v in values.items()}, f"every listed share x {s:+.0%}"))
        elif kind == "sector_shock":
            s = Decimal(str(sc["shock"]))
            stress.append(result(sc["name"], {k: (v * s if sector[k] == sc["sector"] else Decimal(0)) for k, v in values.items()},
                                 f"{sc['sector']} holdings x {s:+.0%}; others unchanged"))
        elif kind == "fx_shock":
            dep = Decimal(str(sc["depreciation"]))
            usd = Decimal(1) / (Decimal(1) + dep) - 1
            r = result(sc["name"], {k: (v * usd if currency[k] == sc["currency"] else Decimal(0)) for k, v in values.items()},
                       f"Value seen by an investor who measures in US dollars: x (1 / {1 + dep}) - 1 = {usd:.2%}. "
                       f"In shillings the holdings are unchanged.")
            r["measured_in"] = "USD"
            stress.append(r)
        elif kind == "inflation":
            if not inflation:
                stress.append({"name": sc["name"], **_unavailable("No stored inflation rate.")})
            else:
                pi = Decimal(str(inflation["value"]))
                real = Decimal(1) / (Decimal(1) + pi) - 1
                r = result(sc["name"], {k: v * real for k, v in values.items()},
                           f"Purchasing power after one year at {pi:.1%} inflation ({inflation.get('source')}, "
                           f"{inflation.get('as_of')}), with prices unchanged: x {real:.2%}")
                r["measured_in"] = "real TZS"
                stress.append(r)
        elif kind == "historical":
            n = sc["weeks"]
            sids = sorted(weights)
            if len(common) <= n:
                stress.append({"name": sc["name"], **_unavailable(f"Needs more than {n} common weeks of prices.")})
                continue
            qty = {h["security_id"]: h["quantity"] for h in priced}
            vals = [sum((qty[s] * Decimal(repr(weekly[s][wk][1])) for s in sids), Decimal(0)) for wk in common]
            worst, at = min(((vals[i + n] / vals[i] - 1, i) for i in range(len(vals) - n)), key=lambda x: x[0])
            start, end = common[at], common[at + n]
            r = result(sc["name"], {s: values[s] * (Decimal(repr(weekly[s][end][1])) / Decimal(repr(weekly[s][start][1])) - 1)
                                    for s in sids},
                       f"The worst {n}-week change of these holdings in the stored history: "
                       f"{weekly[sids[0]][start][0]} to {weekly[sids[0]][end][0]} ({worst:+.1%}), applied to today's values")
            stress.append(r)
        elif kind == "rate_shock":
            stress.append({"name": sc["name"], **_unavailable(
                "No evidence-based link between interest rates and these share prices is stored. Bond holdings "
                "would use duration, but portfolios hold listed shares only.")})
        elif kind == "commodity_shock":
            stress.append({"name": sc["name"], **_unavailable(
                "No stored exposure of these holdings to commodity prices.")})
    out["stress_tests"] = stress
    return out
