from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    subscription_tier = Column(String, default="free")
    subscription_end_date = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    
    # Relationships
    predictions = relationship("PredictionHistory", back_populates="user")
    alerts = relationship("PriceAlert", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    
    # One-to-many relationship with SavedStocks model
    saved_stocks = relationship("SavedStock", back_populates="user", cascade="all, delete-orphan")
    
    # One-to-many relationship with PredictionHistory model
    prediction_history = relationship("PredictionHistory", back_populates="user", cascade="all, delete-orphan")
    
    # One-to-many relationship with UserSubscription model
    subscriptions = relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Many-to-one relationship with User model
    user = relationship("User", back_populates="api_keys")


class SavedStock(Base):
    __tablename__ = "saved_stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Many-to-one relationship with User model
    user = relationship("User", back_populates="saved_stocks")


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, index=True)
    model_used = Column(String)
    days_forecasted = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    result_json = Column(String)  # JSON string containing prediction results
    r2_score = Column(String, nullable=True)
    mae = Column(String, nullable=True)
    
    # Many-to-one relationship with User model
    user = relationship("User", back_populates="prediction_history")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan_id = Column(String)  # basic, pro, enterprise
    status = Column(String)  # active, canceled, past_due, etc.
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Many-to-one relationship with User model
    user = relationship("User", back_populates="subscriptions")
