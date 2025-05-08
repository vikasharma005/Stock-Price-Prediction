#!/bin/bash

set -e

# Wait for the database to be ready
echo "Waiting for database to be ready..."

if [ "$CONTAINER_TYPE" = "api" ]; then
    # Initialize the database using our dedicated script
    bash /app/init-db.sh
fi

# Determine which service to run based on the CONTAINER_TYPE environment variable
if [ "$CONTAINER_TYPE" = "api" ]; then
    echo "Starting FastAPI backend service..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
elif [ "$CONTAINER_TYPE" = "streamlit" ]; then
    echo "Starting Streamlit frontend service..."
    exec streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
else
    # Default: run both services using background processes
    echo "Starting both FastAPI and Streamlit services..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload & 
    streamlit run app/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
fi
