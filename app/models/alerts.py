from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class PriceAlert(Base):
    """
    Price Alert model for storing stock price alerts set by users.
    """
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stock_symbol = Column(String(10), nullable=False)
    target_price = Column(Float, nullable=False)
    is_above = Column(Boolean, default=True)  # True for price above target, False for below
    is_active = Column(Boolean, default=True)
    is_recurring = Column(Boolean, default=False)  # One-time alert or recurring
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_at = Column(DateTime, nullable=True)
    notification_sent = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="price_alerts")
    
    def __repr__(self):
        direction = "above" if self.is_above else "below"
        return f"<PriceAlert {self.stock_symbol} {direction} {self.target_price}>"
