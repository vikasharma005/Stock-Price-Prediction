"""
Script to reset the database and create all tables from the current models
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import Base, engine
from app.core.config import settings

# Import all models to ensure they're included in Base.metadata
from app.models.user import User, ApiKey, SavedStock, PredictionHistory, UserSubscription
from app.models.alert import PriceAlert
from app.models.portfolio import Portfolio, PortfolioStock

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Creating all tables from models...")
    Base.metadata.create_all(bind=engine)
    
    print("Database reset complete.")
    
if __name__ == "__main__":
    confirm = input("This will RESET the database and DELETE ALL DATA. Continue? (y/n): ")
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("Operation cancelled.")
