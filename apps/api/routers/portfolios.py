"""Saved portfolios, one owner each.

Every query filters on the signed-in user's id (from the session, never from the request). Another user's
portfolio answers 404, not 403, so its existence is not revealed. Values are calculated here from the
quantity and the latest stored close, in Decimal; nothing is estimated. A holding with no stored price is
shown as INSUFFICIENT_DATA and left out of the totals, and the totals say so.

Replaces an earlier unmounted draft in this file that returned a fixed "user 1" for every request.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from apps.api.routers.auth import current_user
from packages.database.models import DataSourceStatus, PortfolioHolding, PriceBar, SavedPortfolio, Security, User
from packages.core.config import DSE_ATTRIBUTION, DSE_DISPLAY_BLOCKED, dse_display_allowed
from packages.database.session import get_session

MAX_PORTFOLIOS = 20
MAX_HOLDINGS = 50
V1_CURRENCIES = {"TZS"}        # CLAUDE.md "Scope right now": TZS only, no FX conversion yet

router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])


class HoldingIn(BaseModel):
    security_id: str = Field(max_length=32)
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    cost_per_share: Decimal | None = Field(None, gt=0, max_digits=18, decimal_places=4)
    purchase_date: date | None = None

    @field_validator("security_id")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()


class PortfolioIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_currency: str = Field("TZS", pattern="^[A-Z]{3}$")
    holdings: list[HoldingIn] = Field(default_factory=list, max_length=MAX_HOLDINGS)
    # Optional target allocation, for drift and rebalancing. Weights must sum to 1 over held securities.
    target_weights: dict[str, Decimal] | None = None


def _owned(session: Session, user: User, portfolio_id: int) -> SavedPortfolio:
    p = session.query(SavedPortfolio).filter_by(id=portfolio_id, user_id=user.id).first()
    if p is None:
        raise HTTPException(404, "Portfolio not found.")
    return p


def _check(session: Session, body: PortfolioIn) -> None:
    if body.base_currency not in V1_CURRENCIES:
        raise HTTPException(422, f"Portfolios are in TZS for now; {body.base_currency} needs FX conversion, "
                                 "which is not built.")
    seen = set()
    for h in body.holdings:
        if h.security_id in seen:
            raise HTTPException(422, f"{h.security_id} is listed twice. Combine it into one holding.")
        seen.add(h.security_id)
        sec = session.get(Security, h.security_id)
        if sec is None:
            raise HTTPException(422, f"Unknown security {h.security_id}. Use EXCHANGE:TICKER, e.g. DSE:NMB.")
        if sec.currency != body.base_currency:
            raise HTTPException(422, f"{sec.id} trades in {sec.currency}; this portfolio is in "
                                     f"{body.base_currency}, and FX conversion is not built.")


def _check_targets(body: PortfolioIn) -> dict:
    if not body.target_weights:
        return {}
    targets = {k.strip().upper(): v for k, v in body.target_weights.items()}
    held = {h.security_id for h in body.holdings}
    if not set(targets) <= held:
        raise HTTPException(422, f"Target weights name securities not held: {sorted(set(targets) - held)}")
    if any(v < 0 or v > 1 for v in targets.values()):
        raise HTTPException(422, "Each target weight must be between 0 and 1.")
    if abs(sum(targets.values(), Decimal(0)) - 1) > Decimal("0.0001"):
        raise HTTPException(422, "Target weights must add up to 1 (100%).")
    return {k: str(v) for k, v in targets.items()}


def _write_holdings(p: SavedPortfolio, body: PortfolioIn) -> None:
    p.holdings.clear()
    for h in body.holdings:
        p.holdings.append(PortfolioHolding(
            asset_id=h.security_id, quantity=h.quantity, cost_basis=h.cost_per_share,
            purchase_date=datetime.combine(h.purchase_date, datetime.min.time(), timezone.utc)
            if h.purchase_date else None))


def _price_limit_hours(session: Session) -> int:
    row = session.get(DataSourceStatus, "dse_prices")
    return row.max_age_hours if row else 120


def _view(session: Session, p: SavedPortfolio) -> dict:
    today = datetime.now(timezone.utc).date()
    limit_h = _price_limit_hours(session)
    rows, priced_total = [], Decimal(0)
    for h in sorted(p.holdings, key=lambda x: x.asset_id):
        sec = session.get(Security, h.asset_id)
        bar = (session.query(PriceBar).filter_by(instrument_id=h.asset_id)
               .order_by(PriceBar.trade_date.desc()).first()) if dse_display_allowed() else None
        row = {"security_id": h.asset_id, "name": sec.name if sec else h.asset_id,
               "quantity": h.quantity, "cost_per_share": h.cost_basis,
               "purchase_date": h.purchase_date.date().isoformat() if h.purchase_date else None}
        if bar is None and not dse_display_allowed():
            row["price"] = {"available": False, "status": "BLOCKED", "reason": DSE_DISPLAY_BLOCKED}
        elif bar is None:
            row["price"] = {"available": False, "status": "INSUFFICIENT_DATA",
                            "reason": "No stored price for this security."}
        else:
            stale = (today - bar.trade_date).days * 24 > limit_h
            value = h.quantity * bar.close
            priced_total += value
            row["price"] = {"available": True, "value": bar.close, "date": bar.trade_date.isoformat(),
                            "source_document_id": bar.source_document_id, "attribution": DSE_ATTRIBUTION,
                            "status": "STALE" if stale else "VERIFIED"}
            row["market_value"] = value
            if h.cost_basis is not None:
                row["cost_value"] = h.quantity * h.cost_basis
                row["gain"] = value - row["cost_value"]
        rows.append(row)
    for row in rows:
        if "market_value" in row and priced_total > 0:
            row["weight"] = row["market_value"] / priced_total
    unpriced = [r["security_id"] for r in rows if not r["price"]["available"]]
    stale = [r["security_id"] for r in rows if r["price"].get("status") == "STALE"]
    if not rows:
        status = "NO_DATA"
    elif len(unpriced) == len(rows):
        status = "INSUFFICIENT_DATA"
    elif unpriced:
        status = "PARTIAL"
    elif stale:
        status = "STALE"
    else:
        status = "VERIFIED"
    weights = [r["weight"] for r in rows if "weight" in r]
    return {
        "id": p.id, "name": p.name, "base_currency": p.base_currency,
        "target_weights": p.target_weights_json or {},
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "holdings": rows,
        "totals": {
            "status": status,
            "market_value": priced_total if weights else None,
            "priced_holdings": len(weights), "unpriced_holdings": unpriced, "stale_prices": stale,
            "largest_weight": max(weights) if weights else None,
            "note": ("Values use the latest stored close. Weights are shares of the priced holdings only."
                     if unpriced else "Values use the latest stored close."),
        },
    }


@router.get("")
def list_portfolios(user: User = Depends(current_user), session: Session = Depends(get_session)) -> dict:
    ps = session.query(SavedPortfolio).filter_by(user_id=user.id).order_by(SavedPortfolio.id).all()
    return {"portfolios": [_view(session, p) for p in ps]}


@router.post("", status_code=201)
def create_portfolio(body: PortfolioIn, user: User = Depends(current_user),
                     session: Session = Depends(get_session)) -> dict:
    if session.query(SavedPortfolio).filter_by(user_id=user.id).count() >= MAX_PORTFOLIOS:
        raise HTTPException(422, f"You can keep up to {MAX_PORTFOLIOS} portfolios.")
    _check(session, body)
    p = SavedPortfolio(user_id=user.id, name=body.name.strip(), base_currency=body.base_currency,
                       target_weights_json=_check_targets(body))
    _write_holdings(p, body)
    session.add(p)
    session.commit()
    return _view(session, p)


@router.get("/{portfolio_id}")
def get_portfolio(portfolio_id: int, user: User = Depends(current_user),
                  session: Session = Depends(get_session)) -> dict:
    return _view(session, _owned(session, user, portfolio_id))


@router.put("/{portfolio_id}")
def replace_portfolio(portfolio_id: int, body: PortfolioIn, user: User = Depends(current_user),
                      session: Session = Depends(get_session)) -> dict:
    p = _owned(session, user, portfolio_id)
    _check(session, body)
    p.name, p.base_currency = body.name.strip(), body.base_currency
    p.target_weights_json = _check_targets(body)
    _write_holdings(p, body)
    session.commit()
    return _view(session, p)


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(portfolio_id: int, user: User = Depends(current_user),
                     session: Session = Depends(get_session)) -> None:
    session.delete(_owned(session, user, portfolio_id))
    session.commit()


@router.get("/{portfolio_id}/analysis")
def analyse_portfolio(portfolio_id: int, user: User = Depends(current_user),
                      session: Session = Depends(get_session)) -> dict:
    """Risk, concentration, liquidity, drift, stress tests and optimisation for one owned portfolio
    (packages/analysis/portfolio_risk.py). Owner only: another user's id answers 404."""
    import json

    from packages.analysis import portfolio_risk
    from packages.core.config import settings
    from packages.database.models import MacroObservation

    p = _owned(session, user, portfolio_id)
    if not dse_display_allowed():
        return {"available": False, "status": "BLOCKED", "reason": DSE_DISPLAY_BLOCKED}
    holdings, history = [], {}
    for h in p.holdings:
        sec = session.get(Security, h.asset_id)
        holdings.append({"security_id": h.asset_id, "quantity": h.quantity, "sector": sec.sector if sec else None,
                         "currency": sec.currency if sec else p.base_currency})
        history[h.asset_id] = [(b.trade_date, b.close, b.volume) for b in
                               session.query(PriceBar).filter_by(instrument_id=h.asset_id).order_by(PriceBar.trade_date)]
    cpi = (session.query(MacroObservation).filter_by(series_id="NBS_CPI_HEADLINE_YOY")
           .order_by(MacroObservation.observation_date.desc()).first())
    inflation = None if cpi is None else {"value": cpi.value, "as_of": cpi.observation_date.isoformat(),
                                          "source": cpi.source_name}
    cfg = json.loads((settings.CONFIG_DIR / "portfolio.json").read_text(encoding="utf-8"))
    targets = {k: Decimal(v) for k, v in (p.target_weights_json or {}).items()}
    return {"portfolio_id": p.id, **portfolio_risk.analyse(holdings, history, cfg, inflation, targets or None)}
