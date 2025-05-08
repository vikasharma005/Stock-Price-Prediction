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
from app.models.alert import PriceAlert

router = APIRouter()

class AlertCreate(BaseModel):
    symbol: str
    alert_type: str  # price, technical, sentiment
    condition: str  # above, below, crosses_above, crosses_below
    target_value: float
    expiration_days: int = 30
    is_recurring: bool = False
    notes: Optional[str] = None

class AlertResponse(BaseModel):
    id: str
    user_id: int
    symbol: str
    alert_type: str
    condition: str
    target_value: float
    current_value: Optional[float] = None
    triggered: bool
    created_at: datetime
    expires_at: datetime
    is_recurring: bool
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.post("/create", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new price alert"""
    # Validate the symbol
    try:
        ticker = yf.Ticker(alert_data.symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            raise HTTPException(status_code=400, detail=f"Invalid symbol: {alert_data.symbol}")
        
        current_price = hist['Close'].iloc[-1] if not hist.empty else None
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error validating symbol: {str(e)}")
    
    # Create the alert
    alert_id = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=alert_data.expiration_days)
    
    new_alert = PriceAlert(
        id=alert_id,
        user_id=current_user.id,
        symbol=alert_data.symbol,
        alert_type=alert_data.alert_type,
        condition=alert_data.condition,
        target_value=alert_data.target_value,
        current_value=current_price,
        triggered=False,
        created_at=datetime.now(),
        expires_at=expires_at,
        is_recurring=alert_data.is_recurring,
        notes=alert_data.notes
    )
    
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    
    return new_alert

@router.get("/list", response_model=List[AlertResponse])
async def list_alerts(
    active_only: bool = True,
    symbol: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all alerts for the current user"""
    query = db.query(PriceAlert).filter(PriceAlert.user_id == current_user.id)
    
    if active_only:
        query = query.filter(
            PriceAlert.expires_at > datetime.now(),
            PriceAlert.triggered == False
        )
    
    if symbol:
        query = query.filter(PriceAlert.symbol == symbol.upper())
    
    alerts = query.order_by(desc(PriceAlert.created_at)).all()
    
    # Update current prices for active alerts
    symbols = set(alert.symbol for alert in alerts)
    current_prices = {}
    
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="1d")
            if not hist.empty:
                current_prices[sym] = hist['Close'].iloc[-1]
        except:
            pass
    
    for alert in alerts:
        if alert.symbol in current_prices:
            alert.current_value = current_prices[alert.symbol]
    
    return alerts

@router.delete("/delete/{alert_id}")
async def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an alert"""
    alert = db.query(PriceAlert).filter(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(alert)
    db.commit()
    
    return {"status": "success", "message": "Alert deleted successfully"}

@router.post("/check")
async def check_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check if any alerts have been triggered"""
    # Get active alerts
    active_alerts = db.query(PriceAlert).filter(
        PriceAlert.user_id == current_user.id,
        PriceAlert.expires_at > datetime.now(),
        PriceAlert.triggered == False
    ).all()
    
    if not active_alerts:
        return {"status": "success", "message": "No active alerts found", "triggered": []}
    
    # Get current prices
    symbols = set(alert.symbol for alert in active_alerts)
    current_prices = {}
    
    for sym in symbols:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="1d")
            if not hist.empty:
                current_prices[sym] = hist['Close'].iloc[-1]
        except:
            pass
    
    # Check alerts
    triggered_alerts = []
    
    for alert in active_alerts:
        if alert.symbol not in current_prices:
            continue
        
        current_price = current_prices[alert.symbol]
        alert.current_value = current_price
        
        is_triggered = False
        
        if alert.alert_type == "price":
            if alert.condition == "above" and current_price > alert.target_value:
                is_triggered = True
            elif alert.condition == "below" and current_price < alert.target_value:
                is_triggered = True
            # Handle crosses_above and crosses_below with historical data if needed
        
        if is_triggered:
            alert.triggered = True
            if not alert.is_recurring:
                db.commit()
                triggered_alerts.append({
                    "id": alert.id,
                    "symbol": alert.symbol,
                    "alert_type": alert.alert_type,
                    "condition": alert.condition,
                    "target_value": alert.target_value,
                    "current_value": current_price
                })
            else:
                # For recurring alerts, mark as not triggered and update expiration
                alert.triggered = False
                alert.expires_at = datetime.now() + timedelta(days=30)  # Reset for another 30 days
                db.commit()
                triggered_alerts.append({
                    "id": alert.id,
                    "symbol": alert.symbol,
                    "alert_type": alert.alert_type,
                    "condition": alert.condition,
                    "target_value": alert.target_value,
                    "current_value": current_price,
                    "recurring": True
                })
    
    db.commit()
    
    return {
        "status": "success", 
        "message": f"{len(triggered_alerts)} alerts triggered",
        "triggered": triggered_alerts
    }
