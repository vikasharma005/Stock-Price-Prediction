from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import uuid

from app.auth.jwt import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioStock

router = APIRouter()

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    total_value: Optional[float] = None
    total_gain_loss: Optional[float] = None
    total_gain_loss_percent: Optional[float] = None
    
    class Config:
        from_attributes = True

class PortfolioStockCreate(BaseModel):
    symbol: str
    shares: float
    purchase_price: float
    purchase_date: datetime
    notes: Optional[str] = None

class PortfolioStockResponse(BaseModel):
    id: str
    symbol: str
    shares: float
    purchase_price: float
    purchase_date: datetime
    notes: Optional[str] = None
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    gain_loss: Optional[float] = None
    gain_loss_percent: Optional[float] = None
    
    class Config:
        from_attributes = True

@router.post("/create", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new portfolio"""
    portfolio_id = str(uuid.uuid4())
    
    new_portfolio = Portfolio(
        id=portfolio_id,
        user_id=current_user.id,
        name=portfolio_data.name,
        description=portfolio_data.description,
        created_at=datetime.now()
    )
    
    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)
    
    return new_portfolio

@router.get("/list", response_model=List[PortfolioResponse])
async def list_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all portfolios for the current user"""
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    
    # Calculate portfolio values
    for portfolio in portfolios:
        total_value = 0
        total_cost = 0
        
        for stock in portfolio.stocks:
            try:
                ticker = yf.Ticker(stock.symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    stock_value = current_price * stock.shares
                    total_value += stock_value
                    total_cost += stock.purchase_price * stock.shares
            except:
                pass
        
        portfolio.total_value = total_value
        
        if total_cost > 0:
            portfolio.total_gain_loss = total_value - total_cost
            portfolio.total_gain_loss_percent = (portfolio.total_gain_loss / total_cost) * 100
    
    return portfolios

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Calculate portfolio value
    total_value = 0
    total_cost = 0
    
    for stock in portfolio.stocks:
        try:
            ticker = yf.Ticker(stock.symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                stock_value = current_price * stock.shares
                total_value += stock_value
                total_cost += stock.purchase_price * stock.shares
        except:
            pass
    
    portfolio.total_value = total_value
    
    if total_cost > 0:
        portfolio.total_gain_loss = total_value - total_cost
        portfolio.total_gain_loss_percent = (portfolio.total_gain_loss / total_cost) * 100
    
    return portfolio

@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db.delete(portfolio)
    db.commit()
    
    return {"status": "success", "message": "Portfolio deleted successfully"}

@router.post("/{portfolio_id}/add-stock", response_model=PortfolioStockResponse)
async def add_stock_to_portfolio(
    portfolio_id: str,
    stock_data: PortfolioStockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a stock to a portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Validate the symbol
    try:
        ticker = yf.Ticker(stock_data.symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            raise HTTPException(status_code=400, detail=f"Invalid symbol: {stock_data.symbol}")
        
        current_price = hist['Close'].iloc[-1] if not hist.empty else None
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error validating symbol: {str(e)}")
    
    # Create the stock
    stock_id = str(uuid.uuid4())
    
    new_stock = PortfolioStock(
        id=stock_id,
        portfolio_id=portfolio_id,
        symbol=stock_data.symbol,
        shares=stock_data.shares,
        purchase_price=stock_data.purchase_price,
        purchase_date=stock_data.purchase_date,
        notes=stock_data.notes
    )
    
    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)
    
    # Add calculated fields for response
    new_stock.current_price = current_price
    new_stock.current_value = current_price * new_stock.shares if current_price else None
    
    if new_stock.current_price and new_stock.purchase_price:
        new_stock.gain_loss = (new_stock.current_price - new_stock.purchase_price) * new_stock.shares
        new_stock.gain_loss_percent = ((new_stock.current_price - new_stock.purchase_price) / new_stock.purchase_price) * 100
    
    return new_stock

@router.get("/{portfolio_id}/stocks", response_model=List[PortfolioStockResponse])
async def list_portfolio_stocks(
    portfolio_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all stocks in a portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    stocks = portfolio.stocks
    
    # Get current prices and calculate values
    for stock in stocks:
        try:
            ticker = yf.Ticker(stock.symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                stock.current_price = hist['Close'].iloc[-1]
                stock.current_value = stock.current_price * stock.shares
                
                if stock.purchase_price:
                    stock.gain_loss = (stock.current_price - stock.purchase_price) * stock.shares
                    stock.gain_loss_percent = ((stock.current_price - stock.purchase_price) / stock.purchase_price) * 100
        except:
            stock.current_price = None
            stock.current_value = None
            stock.gain_loss = None
            stock.gain_loss_percent = None
    
    return stocks

@router.delete("/{portfolio_id}/stocks/{stock_id}")
async def delete_portfolio_stock(
    portfolio_id: str,
    stock_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a stock from a portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    stock = db.query(PortfolioStock).filter(
        PortfolioStock.id == stock_id,
        PortfolioStock.portfolio_id == portfolio_id
    ).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found in portfolio")
    
    db.delete(stock)
    db.commit()
    
    return {"status": "success", "message": "Stock deleted from portfolio successfully"}
