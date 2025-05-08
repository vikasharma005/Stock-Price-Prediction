import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "StockPredictPro SaaS"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Environment setting
    ENV: str = os.getenv("ENV", "development")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./stock_predict_pro.db")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Stripe settings
    STRIPE_API_KEY: Optional[str] = os.getenv("STRIPE_API_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # Subscription plans
    BASIC_PLAN_ID: str = os.getenv("BASIC_PLAN_ID", "price_basic")
    PRO_PLAN_ID: str = os.getenv("PRO_PLAN_ID", "price_pro")
    ENTERPRISE_PLAN_ID: str = os.getenv("ENTERPRISE_PLAN_ID", "price_enterprise")
    
    # Security
    ALGORITHM: str = "HS256"
    
    # Yahoo Finance API settings
    YF_API_RATE_LIMIT: int = 2000  # Requests per hour, adjust as needed

    # Redis for caching and rate limiting
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

settings = Settings()
