from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_active_user, get_current_active_superuser
from app.auth.password import get_password_hash
from app.db.database import get_db
from app.models.user import User, SavedStock, PredictionHistory
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate, SavedStock as SavedStockSchema, PredictionHistory as PredictionHistorySchema

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user
    """
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update own user
    """
    user_data = jsonable_encoder(current_user)
    update_data = user_in.dict(exclude_unset=True)
    
    if update_data.get("password"):
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
        
    for field in user_data:
        if field in update_data:
            setattr(current_user, field, update_data[field])
            
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/saved-stocks", response_model=List[SavedStockSchema])
def read_saved_stocks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve saved stocks
    """
    saved_stocks = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return saved_stocks

@router.post("/saved-stocks", response_model=SavedStockSchema)
def create_saved_stock(
    *,
    db: Session = Depends(get_db),
    symbol: str = Body(...),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Save a stock symbol
    """
    # Check if stock already saved
    existing_stock = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.id, SavedStock.symbol == symbol)
        .first()
    )
    if existing_stock:
        return existing_stock
        
    saved_stock = SavedStock(user_id=current_user.id, symbol=symbol)
    db.add(saved_stock)
    db.commit()
    db.refresh(saved_stock)
    return saved_stock

@router.delete("/saved-stocks/{stock_id}", response_model=SavedStockSchema)
def delete_saved_stock(
    *,
    db: Session = Depends(get_db),
    stock_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a saved stock
    """
    saved_stock = (
        db.query(SavedStock)
        .filter(SavedStock.id == stock_id, SavedStock.user_id == current_user.id)
        .first()
    )
    if not saved_stock:
        raise HTTPException(status_code=404, detail="Stock not found")
        
    db.delete(saved_stock)
    db.commit()
    return saved_stock

@router.get("/prediction-history", response_model=List[PredictionHistorySchema])
def read_prediction_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve prediction history
    """
    prediction_history = (
        db.query(PredictionHistory)
        .filter(PredictionHistory.user_id == current_user.id)
        .order_by(PredictionHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return prediction_history

# Admin routes
@router.get("/", response_model=List[UserSchema])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users
