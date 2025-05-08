from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    subscription_tier: str = "free"

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Additional properties to return via API
class User(UserInDBBase):
    pass

# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str

# Token schema
class Token(BaseModel):
    access_token: str
    token_type: str

# Token payload
class TokenPayload(BaseModel):
    sub: Optional[str] = None

# Schema for subscriptions
class SubscriptionBase(BaseModel):
    plan_id: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None

class SubscriptionCreate(SubscriptionBase):
    user_id: int
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None

class SubscriptionUpdate(SubscriptionBase):
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None

class SubscriptionInDBBase(SubscriptionBase):
    id: int
    user_id: int
    created_at: datetime
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class Subscription(SubscriptionInDBBase):
    pass

# Schema for saved stocks
class SavedStockBase(BaseModel):
    symbol: str

class SavedStockCreate(SavedStockBase):
    user_id: int

class SavedStockInDBBase(SavedStockBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SavedStock(SavedStockInDBBase):
    pass

# Schema for prediction history
class PredictionHistoryBase(BaseModel):
    symbol: str
    model_used: str
    days_forecasted: int
    result_json: str
    r2_score: Optional[str] = None
    mae: Optional[str] = None

class PredictionHistoryCreate(PredictionHistoryBase):
    user_id: int

class PredictionHistoryInDBBase(PredictionHistoryBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PredictionHistory(PredictionHistoryInDBBase):
    pass
