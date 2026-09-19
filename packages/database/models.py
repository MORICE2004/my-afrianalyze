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
    """End-of-day prices. Only loaded from licensed files (see pipelines/dse/import_prices.py)."""

    __tablename__ = "price_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[str] = mapped_column(String(32), index=True)  # DSE:NMB or DSE:DSEI
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    close: Mapped[Decimal] = mapped_column(ExactDecimal)
    volume: Mapped[Decimal | None] = mapped_column(ExactDecimal)
    source_document_id: Mapped[int] = mapped_column(ForeignKey("source_documents.id"))

    __table_args__ = (UniqueConstraint("instrument_id", "trade_date"),)


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
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="user")
    plan_id: Mapped[str | None] = mapped_column(ForeignKey("plans.id"))

    portfolios: Mapped[list["SavedPortfolio"]] = relationship(back_populates="owner")


class SavedPortfolio(Base):
    __tablename__ = "saved_portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
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
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("saved_portfolios.id"))
    asset_id: Mapped[str] = mapped_column(String(32))
    weight: Mapped[Decimal] = mapped_column(ExactDecimal)
    cost_basis: Mapped[Decimal] = mapped_column(ExactDecimal)
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    portfolio: Mapped[SavedPortfolio] = relationship(back_populates="holdings")
