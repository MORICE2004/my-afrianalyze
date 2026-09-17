from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

# Placeholders for DB dependency and Auth dependency
def get_db():
    yield None

class DummyUser:
    id = 1

def get_current_user():
    return DummyUser()

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

# Pydantic schemas for request/response
class PortfolioCreate(BaseModel):
    name: str
    base_currency: str
    target_weights_json: Optional[Dict[str, Any]] = {}

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    base_currency: Optional[str] = None
    target_weights_json: Optional[Dict[str, Any]] = None

class PortfolioResponse(PortfolioCreate):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

@router.post("/", response_model=PortfolioResponse)
def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from packages.database.models import SavedPortfolio
    db_portfolio = SavedPortfolio(**portfolio.dict(), user_id=current_user.id)
    if db is not None:
        db.add(db_portfolio)
        db.commit()
        db.refresh(db_portfolio)
    return db_portfolio

@router.get("/", response_model=List[PortfolioResponse])
def get_portfolios(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from packages.database.models import SavedPortfolio
    if db is not None:
        return db.query(SavedPortfolio).filter(SavedPortfolio.user_id == current_user.id).all()
    return []

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from packages.database.models import SavedPortfolio
    if db is not None:
        portfolio = db.query(SavedPortfolio).filter(SavedPortfolio.id == portfolio_id, SavedPortfolio.user_id == current_user.id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return portfolio
    raise HTTPException(status_code=404, detail="Portfolio not found")

@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(portfolio_id: int, portfolio_update: PortfolioUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from packages.database.models import SavedPortfolio
    if db is not None:
        portfolio = db.query(SavedPortfolio).filter(SavedPortfolio.id == portfolio_id, SavedPortfolio.user_id == current_user.id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        update_data = portfolio_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(portfolio, key, value)
            
        db.commit()
        db.refresh(portfolio)
        return portfolio
    raise HTTPException(status_code=404, detail="Portfolio not found")

@router.delete("/{portfolio_id}")
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from packages.database.models import SavedPortfolio
    if db is not None:
        portfolio = db.query(SavedPortfolio).filter(SavedPortfolio.id == portfolio_id, SavedPortfolio.user_id == current_user.id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        db.delete(portfolio)
        db.commit()
        return {"detail": "Portfolio deleted successfully"}
    return {"detail": "Portfolio deleted successfully"}
