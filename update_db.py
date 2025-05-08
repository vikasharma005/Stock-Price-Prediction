"""
Script to update the database structure without losing data
"""
import os
import sys
import sqlite3
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine
from app.core.config import settings

def update_database():
    print("Updating database structure...")
    
    # Connect directly using sqlite3 to perform schema changes
    # Get database path from settings
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if subscription_end_date column exists in users table
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        # Add missing columns to users table
        if "subscription_end_date" not in columns:
            print("Adding subscription_end_date column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN subscription_end_date TIMESTAMP")
        
        if "stripe_customer_id" not in columns:
            print("Adding stripe_customer_id column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN stripe_customer_id TEXT")
        
        # Create new tables for alerts
        print("Creating price_alerts table if not exists...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_alerts (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            symbol TEXT,
            alert_type TEXT,
            condition TEXT,
            target_value REAL,
            current_value REAL,
            triggered BOOLEAN,
            created_at TIMESTAMP,
            expires_at TIMESTAMP,
            is_recurring BOOLEAN,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # Create new tables for portfolios
        print("Creating portfolios table if not exists...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            name TEXT,
            description TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        print("Creating portfolio_stocks table if not exists...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_stocks (
            id TEXT PRIMARY KEY,
            portfolio_id TEXT,
            symbol TEXT,
            shares REAL,
            purchase_price REAL,
            purchase_date TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
        )
        """)
        
        # Commit all changes
        conn.commit()
        print("Database update completed successfully.")
        
    except Exception as e:
        print(f"Error updating database: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    confirm = input("This will update the database structure. Continue? (y/n): ")
    if confirm.lower() == 'y':
        update_database()
    else:
        print("Operation cancelled.")
