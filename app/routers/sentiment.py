from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
import requests
from datetime import datetime, timedelta
import re
import numpy as np
from textblob import TextBlob

from app.auth.jwt import get_current_active_user
from app.db.database import get_db
from app.models.user import User, PredictionHistory
from app.routers.news import get_stock_news, get_market_news
from sqlalchemy.orm import Session

router = APIRouter()

# Cache for sentiment data to avoid reprocessing
sentiment_cache = {}
cache_time = {}

def analyze_text_sentiment(text):
    """Analyze sentiment of text using TextBlob"""
    blob = TextBlob(text)
    sentiment = blob.sentiment
    
    # Map polarity (-1 to 1) to sentiment category
    if sentiment.polarity > 0.2:
        category = "positive"
    elif sentiment.polarity < -0.2:
        category = "negative"
    else:
        category = "neutral"
    
    return {
        "polarity": sentiment.polarity,
        "subjectivity": sentiment.subjectivity,
        "category": category
    }

@router.get("/stock/{symbol}")
async def get_stock_sentiment(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get sentiment analysis for a specific stock based on news"""
    cache_key = f"sentiment_{symbol}"
    
    # Return cached results if available and fresh (less than 6 hours old)
    if cache_key in sentiment_cache and (datetime.now() - cache_time[cache_key]).seconds < 21600:
        return sentiment_cache[cache_key]
    
    try:
        # Get news for the stock
        news_data = await get_stock_news(symbol=symbol, limit=20, current_user=current_user)
        news_articles = news_data.get("news", [])
        
        if not news_articles:
            raise HTTPException(status_code=404, detail=f"No news found for {symbol}")
        
        # Analyze sentiment for each article
        sentiments = []
        for article in news_articles:
            title = article.get("title", "")
            if title:
                sentiment = analyze_text_sentiment(title)
                sentiments.append({
                    "title": title,
                    "source": article.get("source", "Unknown"),
                    "published": article.get("published", "Unknown"),
                    "url": article.get("url", ""),
                    "sentiment": sentiment
                })
        
        # Calculate overall sentiment
        if sentiments:
            polarities = [s["sentiment"]["polarity"] for s in sentiments]
            subjectivities = [s["sentiment"]["subjectivity"] for s in sentiments]
            
            avg_polarity = sum(polarities) / len(polarities)
            avg_subjectivity = sum(subjectivities) / len(subjectivities)
            
            # Count sentiment categories
            categories = [s["sentiment"]["category"] for s in sentiments]
            category_counts = {
                "positive": categories.count("positive"),
                "neutral": categories.count("neutral"),
                "negative": categories.count("negative")
            }
            
            # Determine overall sentiment
            if avg_polarity > 0.1:
                overall = "bullish"
            elif avg_polarity < -0.1:
                overall = "bearish"
            else:
                overall = "neutral"
                
            result = {
                "symbol": symbol,
                "overall_sentiment": overall,
                "average_polarity": avg_polarity,
                "average_subjectivity": avg_subjectivity,
                "sentiment_distribution": category_counts,
                "analysis_time": datetime.now().isoformat(),
                "articles": sentiments
            }
            
            # Cache results
            sentiment_cache[cache_key] = result
            cache_time[cache_key] = datetime.now()
            
            return result
        else:
            raise HTTPException(status_code=404, detail=f"Could not analyze sentiment for {symbol}")
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error analyzing sentiment: {str(e)}")

@router.get("/market")
async def get_market_sentiment(
    current_user: User = Depends(get_current_active_user)
):
    """Get overall market sentiment based on general financial news"""
    cache_key = "sentiment_market"
    
    # Return cached results if available and fresh (less than 6 hours old)
    if cache_key in sentiment_cache and (datetime.now() - cache_time[cache_key]).seconds < 21600:
        return sentiment_cache[cache_key]
    
    try:
        # Get general market news
        news_data = await get_market_news(limit=30, current_user=current_user)
        news_articles = news_data.get("news", [])
        
        if not news_articles:
            raise HTTPException(status_code=404, detail="No market news found")
        
        # Analyze sentiment for each article
        sentiments = []
        for article in news_articles:
            title = article.get("title", "")
            if title:
                sentiment = analyze_text_sentiment(title)
                sentiments.append({
                    "title": title,
                    "source": article.get("source", "Unknown"),
                    "published": article.get("published", "Unknown"),
                    "url": article.get("url", ""),
                    "sentiment": sentiment
                })
        
        # Calculate overall sentiment
        if sentiments:
            polarities = [s["sentiment"]["polarity"] for s in sentiments]
            subjectivities = [s["sentiment"]["subjectivity"] for s in sentiments]
            
            avg_polarity = sum(polarities) / len(polarities)
            avg_subjectivity = sum(subjectivities) / len(subjectivities)
            
            # Count sentiment categories
            categories = [s["sentiment"]["category"] for s in sentiments]
            category_counts = {
                "positive": categories.count("positive"),
                "neutral": categories.count("neutral"),
                "negative": categories.count("negative")
            }
            
            # Determine overall sentiment
            if avg_polarity > 0.1:
                overall = "bullish"
            elif avg_polarity < -0.1:
                overall = "bearish"
            else:
                overall = "neutral"
                
            result = {
                "overall_sentiment": overall,
                "average_polarity": avg_polarity,
                "average_subjectivity": avg_subjectivity,
                "sentiment_distribution": category_counts,
                "analysis_time": datetime.now().isoformat(),
                "articles": sentiments[:10]  # Limit to top 10 articles in response
            }
            
            # Cache results
            sentiment_cache[cache_key] = result
            cache_time[cache_key] = datetime.now()
            
            return result
        else:
            raise HTTPException(status_code=404, detail="Could not analyze market sentiment")
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error analyzing market sentiment: {str(e)}")

@router.get("/prediction-confidence/{symbol}")
async def get_prediction_confidence(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Calculate prediction confidence based on model performance and sentiment"""
    try:
        # Get recent predictions for this symbol
        predictions = (
            db.query(PredictionHistory)
            .filter(PredictionHistory.user_id == current_user.id, 
                    PredictionHistory.symbol == symbol)
            .order_by(PredictionHistory.created_at.desc())
            .limit(5)
            .all()
        )
        
        if not predictions:
            raise HTTPException(status_code=404, detail=f"No prediction history found for {symbol}")
        
        # Get sentiment data
        sentiment_data = await get_stock_sentiment(symbol=symbol, db=db, current_user=current_user)
        sentiment_score = sentiment_data.get("average_polarity", 0)
        
        # Calculate average R2 score from predictions
        r2_scores = []
        for pred in predictions:
            try:
                r2 = float(pred.r2_score)
                r2_scores.append(r2)
            except:
                pass
        
        avg_r2 = sum(r2_scores) / len(r2_scores) if r2_scores else 0
        
        # Calculate confidence score (0-100%)
        # 50% based on model performance, 50% based on sentiment alignment
        model_confidence = min(avg_r2 * 100, 100) * 0.5
        
        # Convert sentiment to 0-100 range (From -1 to 1 scale)
        sentiment_confidence = (sentiment_score + 1) * 50
        
        # Calculate combined confidence
        combined_confidence = model_confidence + (sentiment_confidence * 0.5)
        
        # Generate confidence assessment
        assessment = "Low"
        color = "red"
        if combined_confidence >= 75:
            assessment = "Very High"
            color = "green"
        elif combined_confidence >= 60:
            assessment = "High"
            color = "lightgreen"
        elif combined_confidence >= 40:
            assessment = "Moderate"
            color = "yellow"
        elif combined_confidence >= 25:
            assessment = "Low"
            color = "orange"
            
        return {
            "symbol": symbol,
            "confidence_score": combined_confidence,
            "confidence_assessment": assessment,
            "confidence_color": color,
            "model_performance": avg_r2,
            "sentiment_alignment": sentiment_score,
            "analysis_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error calculating prediction confidence: {str(e)}")
