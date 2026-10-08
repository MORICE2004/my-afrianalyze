"""Database models.

Every stored figure carries provenance: the document or URL it came from,
the page, the retrieval time and the extraction method. Nothing in these
tables is a default or a placeholder; a value that could not be sourced is
simply absent, and the API reports why.
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.database.base import Base
from packages.database.types import ExactDecimal


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Security(Base):
    """Security master. `id` is the canonical form EXCHANGE:TICKER, e.g. DSE:NMB."""

    __tablename__ = "securities"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    exchange: Mapped[str] = mapped_column(String(8), index=True)
    local_ticker: Mapped[str] = mapped_column(String(16))
    isin: Mapped[str | None] = mapped_column(String(12))
    name: Mapped[str] = mapped_column(String(200))
    sector: Mapped[str] = mapped_column(String(80))
    currency: Mapped[str] = mapped_column(String(3))
    is_bank: Mapped[bool] = mapped_column(Boolean, default=False)
    industry_template: Mapped[str] = mapped_column(String(20))  # bank, insurer, non_financial, fund
    listing_status: Mapped[str] = mapped_column(String(20))  # listed, suspended, delisted
    listing_url: Mapped[str] = mapped_column(String(500))
    verified_at: Mapped[date] = mapped_column(Date)
    verification_note: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("exchange", "local_ticker"),)


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    security_id: Mapped[str | None] = mapped_column(ForeignKey("securities.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))  # annual_report, auction_result, dataset
    fiscal_year: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(300))
    publisher: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(1000))
    listing_url: Mapped[str | None] = mapped_column(String(1000))
    file_path: Mapped[str | None] = mapped_column(String(500))
    sha256: Mapped[str | None] = mapped_column(String(64))
    # When the publisher made it public (e.g. the date the board approved the statements).
    published_on: Mapped[date | None] = mapped_column(Date)
    published_on_evidence: Mapped[str | None] = mapped_column(Text)
    # When we retrieved it.
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    terms_note: Mapped[str | None] = mapped_column(Text)

    facts: Mapped[list["FinancialFact"]] = relationship(back_populates="document")


class FinancialFact(Base):
    """One reported line item for one fiscal year, as extracted from one document."""

    __tablename__ = "financial_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    security_id: Mapped[str] = mapped_column(ForeignKey("securities.id"), index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer, index=True)
    statement: Mapped[str] = mapped_column(String(8))  # IS, BS, CF, NOTE
    item_code: Mapped[str] = mapped_column(String(60), index=True)
    label_as_reported: Mapped[str] = mapped_column(String(300))
    value: Mapped[Decimal] = mapped_column(ExactDecimal)
    unit: Mapped[str] = mapped_column(String(24))  # TZS_millions, TZS_per_share, percent
    currency: Mapped[str] = mapped_column(String(3))
    period_end: Mapped[date] = mapped_column(Date)
    basis: Mapped[str] = mapped_column(String(16))  # consolidated, bank
    document_id: Mapped[int] = mapped_column(ForeignKey("source_documents.id"))
    page: Mapped[int] = mapped_column(Integer)
    column_role: Mapped[str] = mapped_column(String(12))  # current, comparative
    extraction_method: Mapped[str] = mapped_column(String(60))
    agreed_by: Mapped[list] = mapped_column(JSON, default=list)
    raw_text: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)

    document: Mapped[SourceDocument] = relationship(back_populates="facts")

    __table_args__ = (
        UniqueConstraint("security_id", "fiscal_year", "item_code", "document_id", "column_role"),
    )


class ExtractionConflict(Base):
    """Two extraction methods, or two documents, disagree. Never auto-resolved."""

    __tablename__ = "extraction_conflicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    security_id: Mapped[str] = mapped_column(ForeignKey("securities.id"), index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer)
    item_code: Mapped[str] = mapped_column(String(60))
    kind: Mapped[str] = mapped_column(String(40))  # METHOD_DISAGREEMENT, RESTATEMENT, MISSING_IN_METHOD
    value_a: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    source_a: Mapped[str] = mapped_column(String(200))
    value_b: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    source_b: Mapped[str] = mapped_column(String(200))
    document_id: Mapped[int | None] = mapped_column(ForeignKey("source_documents.id"))
    page: Mapped[int | None] = mapped_column(Integer)
    detail: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="OPEN")


class ValidationCheck(Base):
    __tablename__ = "validation_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    security_id: Mapped[str] = mapped_column(ForeignKey("securities.id"), index=True)
    fiscal_year: Mapped[int] = mapped_column(Integer)
    check_name: Mapped[str] = mapped_column(String(80))
    passed: Mapped[bool] = mapped_column(Boolean)
    expected: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    actual: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    detail: Mapped[str] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class PriceBar(Base):
    """One end-of-day bar, exactly as the source published it (pipelines/dse/import_public_prices.py).

    close and volume are what every calculation uses. open, high, low, turnover and market_cap are the
    other fields the DSE publishes for the day; they are optional because older bars were stored without
    them and an index has none. source_document_id is the stored file the bar was read from.
    """

    __tablename__ = "price_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[str] = mapped_column(String(32), index=True)  # DSE:NMB or DSE:DSEI
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    close: Mapped[Decimal] = mapped_column(ExactDecimal)
    volume: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    open: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    high: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    low: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    turnover: Mapped[Decimal | None] = mapped_column(ExactDecimal)      # value traded, in the currency
    market_cap: Mapped[Decimal | None] = mapped_column(ExactDecimal)    # as the exchange states it
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_documents.id"))

    __table_args__ = (UniqueConstraint("instrument_id", "trade_date"),)


class PriceReconciliation(Base):
    """One comparison of the same day's close from two providers (packages/market_data/reconcile.py).
    A difference beyond the tolerance is CONFLICTING_SOURCE; the two values are never averaged."""

    __tablename__ = "price_reconciliations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[str] = mapped_column(String(32), index=True)
    trade_date: Mapped[date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3))
    provider_a: Mapped[str] = mapped_column(String(40))
    symbol_a: Mapped[str] = mapped_column(String(40))       # the provider's own code for the instrument
    close_a: Mapped[Decimal] = mapped_column(ExactDecimal)
    provider_b: Mapped[str] = mapped_column(String(40))
    symbol_b: Mapped[str] = mapped_column(String(40))
    close_b: Mapped[Decimal] = mapped_column(ExactDecimal)
    difference: Mapped[Decimal] = mapped_column(ExactDecimal)       # close_b - close_a
    difference_pct: Mapped[Decimal] = mapped_column(ExactDecimal)   # relative to close_a
    tolerance_pct: Mapped[Decimal] = mapped_column(ExactDecimal)
    status: Mapped[str] = mapped_column(String(24))                 # MATCH or CONFLICTING_SOURCE
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class MacroObservation(Base):
    """Official macro and market reference data (BoT auctions, policy rate, inflation)."""

    __tablename__ = "macro_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_id: Mapped[str] = mapped_column(String(80), index=True)
    observation_date: Mapped[date] = mapped_column(Date, index=True)
    published_on: Mapped[date | None] = mapped_column(Date)
    value: Mapped[Decimal] = mapped_column(ExactDecimal)
    unit: Mapped[str] = mapped_column(String(24))
    label: Mapped[str] = mapped_column(String(300))
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    source_url: Mapped[str] = mapped_column(String(1000))
    source_name: Mapped[str] = mapped_column(String(200))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("series_id", "observation_date", "label"),)


class ReferenceInput(Base):
    """Named, dated third-party inputs such as Damodaran's country risk premium."""

    __tablename__ = "reference_inputs"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[Decimal] = mapped_column(ExactDecimal)
    unit: Mapped[str] = mapped_column(String(24))
    label: Mapped[str] = mapped_column(String(300))
    source_name: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str] = mapped_column(String(1000))
    as_of: Mapped[date] = mapped_column(Date)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    file_path: Mapped[str | None] = mapped_column(String(500))
    sha256: Mapped[str | None] = mapped_column(String(64))


class RiskItem(Base):
    """A risk statement. Must cite a source document and page."""

    __tablename__ = "risk_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    security_id: Mapped[str] = mapped_column(ForeignKey("securities.id"), index=True)
    category: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(200))
    quote: Mapped[str] = mapped_column(Text)
    document_id: Mapped[int] = mapped_column(ForeignKey("source_documents.id"))
    page: Mapped[int] = mapped_column(Integer)


class DataSourceStatus(Base):
    """Last run of each ingestion job, used by /health to report staleness."""

    __tablename__ = "data_source_status"

    source: Mapped[str] = mapped_column(String(60), primary_key=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16))  # ok, failed, blocked
    max_age_hours: Mapped[int] = mapped_column(Integer)
    detail: Mapped[str] = mapped_column(Text)


class ResearchRun(Base):
    """One reproducible research result (section 29) with its review lifecycle
    (section 72): draft, in_review, published, superseded. Only a named reviewer
    can publish."""

    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(24), primary_key=True)  # RA-YYYYMMDD-NNN
    security_id: Mapped[str] = mapped_column(ForeignKey("securities.id"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    data_sha256: Mapped[str] = mapped_column(String(64))  # hash of the resolved facts used
    config_sha256: Mapped[str] = mapped_column(String(64))  # hash of valuation and recommendation config
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    reviewer: Mapped[str | None] = mapped_column(String(200))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_by: Mapped[str | None] = mapped_column(String(24))
    # Execution (packages/research/engine.py). `status` above is the review lifecycle; this is whether the
    # analysis itself ran: QUEUED, RUNNING, COMPLETED, PARTIAL, FAILED, BLOCKED, INSUFFICIENT_DATA.
    # Runs created before 2026-10-07 by the data loaders were never executed and have no state.
    execution_state: Mapped[str | None] = mapped_column(String(20))
    stages: Mapped[list | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    # The exact report the run produced, as served (exact decimals as strings). What a reviewer approves,
    # and what production shows once published, so approved numbers cannot change underneath the approval.
    snapshot: Mapped[dict | None] = mapped_column(JSON)
    snapshot_sha256: Mapped[str | None] = mapped_column(String(64))


class ReviewEvent(Base):
    """Append-only audit log of review actions and manual overrides."""

    __tablename__ = "review_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("research_runs.id"), index=True)
    action: Mapped[str] = mapped_column(String(40))  # submit, approve, reject, supersede, override
    actor: Mapped[str] = mapped_column(String(200))
    note: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Plan(Base):
    """Subscription plan (section 78). Data model only; there is no payment code."""

    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)


class Entitlement(Base):
    __tablename__ = "entitlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("plans.id"), index=True)
    feature: Mapped[str] = mapped_column(String(80))
    monthly_limit: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (UniqueConstraint("plan_id", "feature"),)


class User(Base):
    """A signed-up person. The password is stored only as an Argon2id hash (apps/api/routers/auth.py)."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)  # stored lower-case
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="user")
    plan_id: Mapped[str | None] = mapped_column(ForeignKey("plans.id"))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=_utcnow)

    portfolios: Mapped[list["SavedPortfolio"]] = relationship(back_populates="owner")


class UserSession(Base):
    """A signed-in session. Only the SHA-256 of the token is stored, so a copy of the database cannot be
    used to sign in; the token itself exists only in the user's cookie."""
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SavedPortfolio(Base):
    __tablename__ = "saved_portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # every query filters on it
    name: Mapped[str] = mapped_column(String(200))
    base_currency: Mapped[str] = mapped_column(String(3))
    target_weights_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    owner: Mapped[User] = relationship(back_populates="portfolios")
    holdings: Mapped[list["PortfolioHolding"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("saved_portfolios.id"), index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("securities.id"))
    # What the user holds. Weights and values are calculated from quantity and the latest sourced price,
    # never stored, so they cannot go out of date.
    quantity: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    weight: Mapped[Decimal | None] = mapped_column(ExactDecimal)       # unused; kept for the old schema
    cost_basis: Mapped[Decimal | None] = mapped_column(ExactDecimal)   # price paid per share, optional
    purchase_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    portfolio: Mapped[SavedPortfolio] = relationship(back_populates="holdings")


class NewsItem(Base):
    """One economic or market story from a whitelisted source (config/news_sources.json). Only the headline,
    the canonical link, the publication time and, where the publisher allows it, its own short description are
    stored; never the article. Relevance and links to markets, indicators and companies come from fixed rules in
    packages/news/classify.py, each with the reason it applied."""

    __tablename__ = "news_items"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)  # SHA-1 of the canonical URL
    source_id: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(8))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    countries: Mapped[list] = mapped_column(JSON, default=list)
    categories: Mapped[list] = mapped_column(JSON, default=list)
    relevance: Mapped[str] = mapped_column(String(16))  # HIGH, MEDIUM, LOW, NOT_ASSESSED
    relevance_reason: Mapped[str] = mapped_column(Text)
    related: Mapped[dict] = mapped_column(JSON, default=dict)
    raw_sha256: Mapped[str] = mapped_column(String(64))
    # The publisher's own preview image (og:image), kept only when it is at least 800 px wide. The image is
    # linked, not copied. image_checked_at records that the page was looked at, so it is not fetched again.
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
