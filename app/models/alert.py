from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String, index=True)
    alert_type = Column(String)  # price, technical, sentiment
    condition = Column(String)  # above, below, crosses_above, crosses_below
    target_value = Column(Float)
    current_value = Column(Float, nullable=True)
    triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)
    is_recurring = Column(Boolean, default=False)
    notes = Column(String, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="alerts")
