"""Beta estimation for thinly traded stocks.

DSE shares do not trade every day. On a no-trade day the "price" is the last
trade, so the measured daily return is zero while the index moves, which biases
a plain daily OLS beta toward zero. This module computes, side by side:

  a) raw daily OLS beta
  b) weekly and monthly OLS beta
  c) Dimson (1979) beta: sum of slopes on lagged, contemporaneous and leading
     market returns
  d) Scholes-Williams (1977) beta: (b_-1 + b_0 + b_+1) / (1 + 2 * rho_m)
  e) bottom-up beta from listed peers, unlevered and relevered for the target

and selects one with the documented rule in `select_beta`.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np

from packages.analysis.common import Unavailable


@dataclass(frozen=True)
class Regression:
    beta: float
    std_error: float
    r_squared: float
    observations: int

    def to_dict(self) -> dict:
        return {"available": True, "beta": self.beta, "std_error": self.std_error,
                "r_squared": self.r_squared, "observations": self.observations}


def ols(y: np.ndarray, x: np.ndarray) -> Regression | Unavailable:
    """Simple OLS of y on x with intercept."""
    n = len(y)
    if n < 3:
        return Unavailable(f"Only {n} paired observations")
    if np.var(x) == 0:
        return Unavailable("Market returns have zero variance")
    X = np.column_stack([np.ones(n), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    dof = n - 2
    s2 = float(resid @ resid) / dof
    cov = s2 * np.linalg.inv(X.T @ X)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(resid @ resid) / ss_tot if ss_tot > 0 else 0.0
    return Regression(float(coef[1]), float(np.sqrt(cov[1, 1])), r2, n)


def ols_multi(y: np.ndarray, xs: np.ndarray) -> tuple[np.ndarray, np.ndarray, float] | Unavailable:
    """OLS of y on several regressors (columns of xs) with intercept.
    Returns (slopes, covariance of slopes, r_squared)."""
    n, k = xs.shape
    if n <= k + 1:
        return Unavailable(f"Only {n} observations for {k} regressors")
    X = np.column_stack([np.ones(n), xs])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    s2 = float(resid @ resid) / (n - k - 1)
    cov = s2 * np.linalg.inv(X.T @ X)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(resid @ resid) / ss_tot if ss_tot > 0 else 0.0
    return coef[1:], cov[1:, 1:], r2


PriceSeries = dict[date, float]


def _aligned_daily(stock: PriceSeries, index: PriceSeries) -> tuple[list[date], np.ndarray, np.ndarray]:
    """Index trading days define the calendar. The stock price on a day it did not
    trade is carried forward from its last trade (that is how the exchange reports
    it), which produces the zero returns this module corrects for."""
    days = sorted(index)
    s_px, i_px, kept = [], [], []
    last = None
    for d in days:
        if d in stock:
            last = stock[d]
        if last is None:
            continue
        s_px.append(last)
        i_px.append(index[d])
        kept.append(d)
    s = np.array(s_px, dtype=float)
    m = np.array(i_px, dtype=float)
    return kept[1:], s[1:] / s[:-1] - 1, m[1:] / m[:-1] - 1


def _period_returns(stock: PriceSeries, index: PriceSeries, key) -> tuple[np.ndarray, np.ndarray]:
    days = sorted(set(stock) & set(index))
    last_in_period: dict = {}
    for d in days:
        last_in_period[key(d)] = d
    ends = [last_in_period[k] for k in sorted(last_in_period)]
    s = np.array([stock[d] for d in ends], dtype=float)
    m = np.array([index[d] for d in ends], dtype=float)
    return s[1:] / s[:-1] - 1, m[1:] / m[:-1] - 1


def raw_daily(stock: PriceSeries, index: PriceSeries) -> dict:
    _, rs, rm = _aligned_daily(stock, index)
    res = ols(rs, rm)
    return res.to_dict()


def weekly(stock: PriceSeries, index: PriceSeries) -> dict:
    rs, rm = _period_returns(stock, index, lambda d: d.isocalendar()[:2])
    return ols(rs, rm).to_dict()


def monthly(stock: PriceSeries, index: PriceSeries) -> dict:
    rs, rm = _period_returns(stock, index, lambda d: (d.year, d.month))
    return ols(rs, rm).to_dict()


def dimson(stock: PriceSeries, index: PriceSeries, lags: int = 1) -> dict:
    _, rs, rm = _aligned_daily(stock, index)
    n = len(rs)
    if n <= 2 * lags + 3:
        return Unavailable(f"Only {n} daily returns").to_dict()
    y = rs[lags:n - lags]
    cols = [rm[lags + j: n - lags + j] for j in range(-lags, lags + 1)]
    fit = ols_multi(y, np.column_stack(cols))
    if isinstance(fit, Unavailable):
        return fit.to_dict()
    slopes, cov, r2 = fit
    beta = float(slopes.sum())
    se = float(np.sqrt(cov.sum()))  # Var(sum) = sum of all covariance terms
    return {"available": True, "beta": beta, "std_error": se, "r_squared": r2,
            "observations": len(y), "lags": lags, "slopes": [float(v) for v in slopes]}


def scholes_williams(stock: PriceSeries, index: PriceSeries) -> dict:
    _, rs, rm = _aligned_daily(stock, index)
    n = len(rs)
    if n < 10:
        return Unavailable(f"Only {n} daily returns").to_dict()
    y = rs[1:n - 1]
    b_lag = ols(y, rm[0:n - 2])
    b_0 = ols(y, rm[1:n - 1])
    b_lead = ols(y, rm[2:n])
    for b in (b_lag, b_0, b_lead):
        if isinstance(b, Unavailable):
            return b.to_dict()
    rho = float(np.corrcoef(rm[:-1], rm[1:])[0, 1])
    denom = 1 + 2 * rho
    if denom <= 0:
        return Unavailable(f"Market autocorrelation {rho:.3f} makes the correction undefined").to_dict()
    beta = (b_lag.beta + b_0.beta + b_lead.beta) / denom
    # Standard error is not closed-form; report the contemporaneous SE as an indication.
    return {"available": True, "beta": beta, "std_error": b_0.std_error, "r_squared": b_0.r_squared,
            "observations": len(y), "market_autocorrelation": rho,
            "components": {"b_lag": b_lag.beta, "b_0": b_0.beta, "b_lead": b_lead.beta},
            "note": "std_error and r_squared shown are from the contemporaneous regression"}


def bottom_up(peers: list[dict], target_debt_to_equity: float | None, target_tax_rate: float | None) -> dict:
    """peers: [{"name", "levered_beta", "debt_to_equity", "tax_rate", "source"}].
    Hamada: beta_u = beta_L / (1 + (1 - t) * D/E); relever with the target's D/E and t.
    For banks, D is non-deposit borrowings."""
    if not peers:
        return Unavailable("No peer betas with sourced price data are loaded").to_dict()
    if target_debt_to_equity is None or target_tax_rate is None:
        return Unavailable("Target debt-to-equity or tax rate not available").to_dict()
    unlevered = []
    for p in peers:
        unlevered.append(p["levered_beta"] / (1 + (1 - p["tax_rate"]) * p["debt_to_equity"]))
    beta_u = float(np.mean(unlevered))
    beta_l = beta_u * (1 + (1 - target_tax_rate) * target_debt_to_equity)
    return {"available": True, "beta": beta_l, "unlevered_beta": beta_u, "std_error": None,
            "r_squared": None, "observations": len(peers),
            "peers": [{**p, "unlevered_beta": u} for p, u in zip(peers, unlevered)],
            "target_debt_to_equity": target_debt_to_equity, "target_tax_rate": target_tax_rate}


def zero_volume_share(volumes: dict[date, float | None], index_days: list[date]) -> dict:
    """Share of index trading days on which the stock did not trade."""
    if not index_days:
        return Unavailable("No index trading days").to_dict()
    zero = sum(1 for d in index_days if not volumes.get(d))
    return {"available": True, "value": zero / len(index_days), "zero_volume_days": zero,
            "index_trading_days": len(index_days)}


def blume(beta: float) -> float:
    return (2.0 / 3.0) * beta + (1.0 / 3.0)


def select_beta(estimates: dict[str, dict], zero_share: dict, rule: dict) -> dict:
    """Pick the valuation beta.

    rule (config/valuation.json -> beta_selection):
      thin_trading_threshold: zero-volume share above which daily OLS is not used
      min_observations: {"raw_daily", "weekly", "monthly", "dimson", "scholes_williams"}
      order_thin / order_liquid: preference order of methods
      blume_adjust: apply Blume (2/3 * beta + 1/3)
    """
    if not zero_share.get("available"):
        return Unavailable("Cannot assess trading frequency: " + zero_share.get("reason", "")).to_dict()
    thin = zero_share["value"] > rule["thin_trading_threshold"]
    order = rule["order_thin"] if thin else rule["order_liquid"]
    skipped = []
    for method in order:
        est = estimates.get(method, {})
        if not est.get("available"):
            skipped.append(f"{method}: {est.get('reason', 'not computed')}")
            continue
        min_obs = rule["min_observations"].get(method, 0)
        if est["observations"] < min_obs:
            skipped.append(f"{method}: {est['observations']} observations < {min_obs}")
            continue
        beta = est["beta"]
        final = blume(beta) if rule.get("blume_adjust") else beta
        reason = (f"Zero-volume share {zero_share['value']:.1%} is "
                  f"{'above' if thin else 'at or below'} the {rule['thin_trading_threshold']:.0%} threshold, "
                  f"so the {'thin' if thin else 'liquid'}-trading order applies: {', '.join(order)}. "
                  f"First method meeting its minimum observations: {method} (n={est['observations']}).")
        if rule.get("blume_adjust"):
            reason += f" Blume adjustment: 2/3 x {beta:.3f} + 1/3 = {final:.3f}."
        return {"available": True, "method": method, "raw_beta": beta, "beta": final,
                "reason": reason, "skipped": skipped}
    return Unavailable("No beta method met its requirements. " + "; ".join(skipped)).to_dict()
