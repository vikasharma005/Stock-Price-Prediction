from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter()

@router.get("")
async def health_check():
    """
    Health check endpoint for monitoring the API status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("ENV", "development"),
        "system": {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent
        }
    }
