#!/bin/bash
set -e

# This script initializes the database schema and runs migrations
# It's designed to be run from the API container

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be available..."
max_attempts=30
current_attempt=0

until pg_isready -h db -U postgres -d stockpredictpro || [ $current_attempt -eq $max_attempts ]; do
    current_attempt=$(( current_attempt + 1 ))
    echo "Waiting for PostgreSQL to become available... (${current_attempt}/${max_attempts})"
    sleep 2
done

if [ $current_attempt -eq $max_attempts ]; then
    echo "Error: PostgreSQL did not become available in time"
    exit 1
fi

echo "PostgreSQL is available!"

# Create database tables using SQLAlchemy models
echo "Creating database tables..."
python <<EOF
from app.db.database import Base, engine
from app.models.user import User, ApiKey, SavedStock, PredictionHistory, UserSubscription
from app.models.portfolio import Portfolio, PortfolioStock
from app.models.alerts import PriceAlert
import sqlalchemy as sa

# Create all tables
Base.metadata.create_all(bind=engine)

# Check if required columns exist, add them if not
try:
    with engine.connect() as conn:
        inspector = sa.inspect(engine)
        
        # Check if subscription_end_date column exists in users table
        user_columns = [col['name'] for col in inspector.get_columns('users')]
        if 'subscription_end_date' not in user_columns:
            print("Adding subscription_end_date column to users table")
            conn.execute(sa.text("ALTER TABLE users ADD COLUMN subscription_end_date TIMESTAMP WITH TIME ZONE"))
            
        # Check if created_at column exists in users table
        if 'created_at' not in user_columns:
            print("Adding created_at column to users table")
            conn.execute(sa.text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))
            
        conn.commit()
except Exception as e:
    print(f"Error during schema check: {e}")
EOF

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head

echo "Database initialization complete!"
