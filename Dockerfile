FROM python:3.9-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make the startup script executable
RUN chmod +x /app/start.sh

# Expose ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Create a non-root user and switch to it for security
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Set the entrypoint to the startup script
ENTRYPOINT ["/app/start.sh"]
