from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    
    portfolios = relationship("SavedPortfolio", back_populates="owner")

class SavedPortfolio(Base):
    __tablename__ = 'saved_portfolios'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    base_currency = Column(String, nullable=False)
    target_weights_json = Column(JSON, default={})
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
    purchase_date = Column(DateTime, nullable=False)

    portfolio = relationship("SavedPortfolio", back_populates="holdings")
