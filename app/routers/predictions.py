from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import pandas as pd
import yfinance as yf
import json
from datetime import datetime, timedelta
from ta.volatility import BollingerBands
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import r2_score, mean_absolute_error

from app.auth.jwt import get_current_active_user
from app.db.database import get_db
from app.models.user import User, PredictionHistory
from app.schemas.user import PredictionHistory as PredictionHistorySchema
from app.core.config import settings

router = APIRouter()

# Define subscription tiers with their limits
TIER_LIMITS = {
    "free": {"predictions_per_day": 5, "max_days_forecast": 7, "models": ["LinearRegression"]},
    "basic": {"predictions_per_day": 20, "max_days_forecast": 14, "models": ["LinearRegression", "RandomForestRegressor"]},
    "pro": {"predictions_per_day": 50, "max_days_forecast": 30, "models": ["LinearRegression", "RandomForestRegressor", "KNeighborsRegressor", "ExtraTreesRegressor"]},
    "enterprise": {"predictions_per_day": 200, "max_days_forecast": 60, "models": ["LinearRegression", "RandomForestRegressor", "KNeighborsRegressor", "ExtraTreesRegressor", "XGBRegressor"]}
}

def get_stock_data(symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Get stock data from Yahoo Finance API"""
    try:
        df = yf.download(symbol, start=start_date, end=end_date, progress=False)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

def check_user_limits(user: User, model: str, days_forecast: int) -> None:
    """Check if user has exceeded their subscription tier limits"""
    tier = user.subscription_tier
    
    # Check if model is available in user's tier
    if model not in TIER_LIMITS[tier]["models"]:
        raise HTTPException(
            status_code=403, 
            detail=f"Model {model} not available in your {tier} subscription. Please upgrade."
        )
    
    # Check forecast days limit
    if days_forecast > TIER_LIMITS[tier]["max_days_forecast"]:
        raise HTTPException(
            status_code=403, 
            detail=f"Maximum forecast days for {tier} subscription is {TIER_LIMITS[tier]['max_days_forecast']}. Please upgrade."
        )

@router.get("/stock/{symbol}")
def get_stock_info(
    symbol: str,
    days: int = Query(30, ge=1, le=3650),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """
    Get basic stock information and recent data
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    df = get_stock_data(symbol, start_date, end_date)
    
    # Convert to dict for JSON response
    recent_data = df.tail(10).reset_index().to_dict(orient="records")
    
    return {
        "symbol": symbol,
        "name": yf.Ticker(symbol).info.get("shortName", symbol),
        "recent_data": recent_data,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }

@router.get("/technical-indicators/{symbol}")
def get_technical_indicators(
    symbol: str,
    indicator: str = Query(..., enum=["close", "bb", "macd", "rsi", "sma", "ema"]),
    days: int = Query(60, ge=30, le=3650),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """
    Get technical indicators for a stock
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    data = get_stock_data(symbol, start_date, end_date)
    
    if indicator == "close":
        result = data[["Close"]].reset_index().to_dict(orient="records")
        return {"indicator": "Close Price", "data": result}
    
    elif indicator == "bb":
        # Bollinger bands
        bb_indicator = BollingerBands(data.Close)
        bb = data.copy()
        bb["bb_h"] = bb_indicator.bollinger_hband()
        bb["bb_l"] = bb_indicator.bollinger_lband()
        bb = bb[["Close", "bb_h", "bb_l"]].reset_index().to_dict(orient="records")
        return {"indicator": "Bollinger Bands", "data": bb}
    
    elif indicator == "macd":
        # MACD
        macd_data = MACD(data.Close)
        result = pd.DataFrame({
            "Date": data.index,
            "MACD": macd_data.macd(),
            "Signal": macd_data.macd_signal(),
            "Histogram": macd_data.macd_diff()
        }).to_dict(orient="records")
        return {"indicator": "MACD", "data": result}
    
    elif indicator == "rsi":
        # RSI
        rsi = pd.DataFrame({
            "Date": data.index,
            "RSI": RSIIndicator(data.Close).rsi()
        }).to_dict(orient="records")
        return {"indicator": "RSI", "data": rsi}
    
    elif indicator == "sma":
        # SMA
        sma = pd.DataFrame({
            "Date": data.index,
            "SMA": SMAIndicator(data.Close, window=14).sma_indicator()
        }).to_dict(orient="records")
        return {"indicator": "SMA", "data": sma}
    
    elif indicator == "ema":
        # EMA
        ema = pd.DataFrame({
            "Date": data.index,
            "EMA": EMAIndicator(data.Close).ema_indicator()
        }).to_dict(orient="records")
        return {"indicator": "EMA", "data": ema}

@router.post("/predict/{symbol}", response_model=PredictionHistorySchema)
def predict_stock_price(
    symbol: str,
    model_name: str = Query(..., enum=["LinearRegression", "RandomForestRegressor", "ExtraTreesRegressor", "KNeighborsRegressor", "XGBRegressor"]),
    days_forecast: int = Query(5, ge=1, le=60),
    training_days: int = Query(100, ge=30, le=3650),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Predict stock price using selected model
    """
    # Check if user has exceeded their subscription tier limits
    check_user_limits(current_user, model_name, days_forecast)
    
    # Get stock data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=training_days + days_forecast)  # Extra data for training
    
    data = get_stock_data(symbol, start_date, end_date)
    
    # Model selection
    if model_name == "LinearRegression":
        model = LinearRegression()
    elif model_name == "RandomForestRegressor":
        model = RandomForestRegressor()
    elif model_name == "ExtraTreesRegressor":
        model = ExtraTreesRegressor()
    elif model_name == "KNeighborsRegressor":
        model = KNeighborsRegressor()
    elif model_name == "XGBRegressor":
        model = XGBRegressor()
    else:
        raise HTTPException(status_code=400, detail="Invalid model name")
    
    # Prepare data for prediction
    df = data[["Close"]].copy()
    df["preds"] = data.Close.shift(-days_forecast)
    
    # Scale the data
    scaler = StandardScaler()
    x = df.drop(["preds"], axis=1).values
    x = scaler.fit_transform(x)
    
    # Store last days_forecast data for prediction
    x_forecast = x[-days_forecast:]
    
    # Select data for training
    x = x[:-days_forecast]
    y = df.preds.values[:-days_forecast]
    
    # Split data
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=.2, random_state=7)
    
    # Train model
    model.fit(x_train, y_train)
    
    # Evaluate model
    preds = model.predict(x_test)
    r2 = r2_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    
    # Predict future prices
    forecast_pred = model.predict(x_forecast)
    
    # Format predictions
    prediction_dates = [(end_date + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(days_forecast)]
    predictions = [{"date": date, "price": float(price)} for date, price in zip(prediction_dates, forecast_pred)]
    
    # Create result JSON
    result_json = json.dumps({
        "symbol": symbol,
        "model": model_name,
        "days_forecast": days_forecast,
        "predictions": predictions,
        "r2_score": r2,
        "mae": mae
    })
    
    # Save prediction to history
    prediction_history = PredictionHistory(
        user_id=current_user.id,
        symbol=symbol,
        model_used=model_name,
        days_forecasted=days_forecast,
        result_json=result_json,
        r2_score=str(r2),
        mae=str(mae)
    )
    
    db.add(prediction_history)
    db.commit()
    db.refresh(prediction_history)
    
    return prediction_history
