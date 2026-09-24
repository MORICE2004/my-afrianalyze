from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from packages.database.base import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    portfolios = relationship("SavedPortfolio", back_populates="owner", cascade="all, delete-orphan")


class SavedPortfolio(Base):
    __tablename__ = 'saved_portfolios'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    base_currency = Column(String, nullable=False)
    target_weights_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="portfolios")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioHolding(Base):
    __tablename__ = 'portfolio_holdings'
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey('saved_portfolios.id'), nullable=False)
    asset_id = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    cost_basis = Column(Float, nullable=False)
    purchase_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    portfolio = relationship("SavedPortfolio", back_populates="holdings")


class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    country = Column(String, default="Tanzania", nullable=True)
    exchange = Column(String, default="DSE", nullable=True)
    currency = Column(String, default="TZS", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")
    market_prices = relationship("MarketPrice", back_populates="company", cascade="all, delete-orphan")
    research_runs = relationship("ResearchRun", back_populates="company", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="company", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    published_date = Column(Date, nullable=True)
    processed = Column(Boolean, default=False)
    doc_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="documents")
    evidence = relationship("Evidence", back_populates="document")


class MarketPrice(Base):
    __tablename__ = 'market_prices'
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    date = Column(Date, nullable=False)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, default=0)

    company = relationship("Company", back_populates="market_prices")


class ResearchRun(Base):
    __tablename__ = 'research_runs'
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    run_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED, BLOCKED
    report_url = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    recommendation = Column(String, nullable=True)  # BUY, HOLD, SELL, INSUFFICIENT_DATA

    company = relationship("Company", back_populates="research_runs")


class Evidence(Base):
    __tablename__ = 'evidence'
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=True)
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    page_number = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    validation_status = Column(String, default="VERIFIED")
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="evidence")
    document = relationship("Document", back_populates="evidence")
