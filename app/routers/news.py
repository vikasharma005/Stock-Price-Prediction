from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta

from app.auth.jwt import get_current_active_user
from app.models.user import User
from app.core.config import settings

router = APIRouter()

# Cache news results to avoid hitting rate limits
news_cache = {}
cache_time = {}

@router.get("/market-news")
async def get_market_news(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user)
):
    """Get general market news"""
    cache_key = f"market_{limit}"
    
    # Return cached results if available and fresh
    if cache_key in news_cache and (datetime.now() - cache_time[cache_key]).seconds < 3600:
        return news_cache[cache_key]
    
    try:
        # Using Yahoo Finance for market news
        url = "https://finance.yahoo.com/news/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        for article in soup.find_all('div', attrs={'data-test': 'stream-item'})[:limit]:
            try:
                title_elem = article.find('h3')
                if not title_elem:
                    continue
                    
                title = title_elem.text
                
                link_elem = article.find('a')
                link = f"https://finance.yahoo.com{link_elem['href']}" if link_elem and 'href' in link_elem.attrs else None
                
                time_elem = article.find('div', attrs={'class': 'C(#959595)'})
                pub_time = time_elem.text if time_elem else "Unknown"
                
                source_elem = article.find('div', attrs={'class': 'C(#959595)'}).find_all('span')
                source = source_elem[0].text if source_elem and len(source_elem) > 0 else "Yahoo Finance"
                
                articles.append({
                    "title": title,
                    "source": source,
                    "published": pub_time,
                    "url": link
                })
            except Exception as e:
                continue
        
        result = {"news": articles}
        
        # Cache the results
        news_cache[cache_key] = result
        cache_time[cache_key] = datetime.now()
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch market news: {str(e)}")

@router.get("/stock-news/{symbol}")
async def get_stock_news(
    symbol: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user)
):
    """Get news for a specific stock"""
    cache_key = f"{symbol}_{limit}"
    
    # Return cached results if available and fresh
    if cache_key in news_cache and (datetime.now() - cache_time[cache_key]).seconds < 3600:
        return news_cache[cache_key]
    
    try:
        # Using Yahoo Finance for stock-specific news
        url = f"https://finance.yahoo.com/quote/{symbol}/news"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        for article in soup.find_all('div', attrs={'data-test': 'stream-item'})[:limit]:
            try:
                title_elem = article.find('h3')
                if not title_elem:
                    continue
                    
                title = title_elem.text
                
                link_elem = article.find('a')
                link = f"https://finance.yahoo.com{link_elem['href']}" if link_elem and 'href' in link_elem.attrs else None
                
                time_elem = article.find('div', attrs={'class': 'C(#959595)'})
                pub_time = time_elem.text if time_elem else "Unknown"
                
                source_elem = article.find('div', attrs={'class': 'C(#959595)'}).find_all('span')
                source = source_elem[0].text if source_elem and len(source_elem) > 0 else "Yahoo Finance"
                
                articles.append({
                    "title": title,
                    "source": source,
                    "published": pub_time,
                    "url": link,
                    "symbol": symbol
                })
            except Exception as e:
                continue
        
        result = {"symbol": symbol, "news": articles}
        
        # Cache the results
        news_cache[cache_key] = result
        cache_time[cache_key] = datetime.now()
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news for {symbol}: {str(e)}")
