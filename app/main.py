from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import engine, Base, get_db
from app.routers import auth, users, predictions, payments, news, sentiment, alerts, portfolio, health
from app.models.user import User

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Simplified for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(predictions.router, prefix=f"{settings.API_V1_STR}/predictions", tags=["predictions"])
app.include_router(payments.router, prefix=f"{settings.API_V1_STR}/payments", tags=["payments"])
app.include_router(news.router, prefix=f"{settings.API_V1_STR}/news", tags=["news"])
app.include_router(sentiment.router, prefix=f"{settings.API_V1_STR}/sentiment", tags=["sentiment"])
app.include_router(alerts.router, prefix=f"{settings.API_V1_STR}/alerts", tags=["alerts"])
app.include_router(portfolio.router, prefix=f"{settings.API_V1_STR}/portfolio", tags=["portfolio"])
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["health"])

# Initialize database and create tables
from app.db.database import Base, engine
Base.metadata.create_all(bind=engine)

# Simplified startup event
@app.on_event("startup")
async def startup_event():
    pass

@app.get("/")
def read_root():
    return {
        "name": settings.PROJECT_NAME,
        "description": "Stock Price Prediction SaaS Platform",
        "version": "1.0.0",
        "documentation": f"/docs"
    }
