# StockPredictPro - Docker Deployment Guide

## Overview

StockPredictPro is now fully containerized with Docker, making deployment consistent across any environment. This guide explains how to run the application using Docker.

## Features Included in Docker Deployment

- **FastAPI Backend**: REST API for authentication, data processing, and ML predictions
- **Streamlit Frontend**: Interactive web UI for stock analysis and visualization
- **PostgreSQL Database**: Persistent storage for user data, predictions, alerts, and portfolios
- **Redis Cache**: For session management and improved performance
- **Nginx**: Reverse proxy for production deployment with SSL support

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/StockPredictPro.git
   cd StockPredictPro
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. Start the application:
   ```bash
   docker-compose up -d
   ```

4. Access the application:
   - Frontend UI: http://localhost:8501
   - API Documentation: http://localhost:8000/docs
   - Landing Page: http://localhost

## Docker Compose Services

### 1. API Service (`api`)
- FastAPI backend running on port 8000
- Handles all API endpoints for:
  - User authentication and management
  - Stock price predictions with multiple ML models
  - Technical indicator calculations
  - News and sentiment analysis
  - Price alerts processing
  - Portfolio tracking

### 2. Streamlit Service (`streamlit`)
- Interactive frontend on port 8501
- Features:
  - Stock analysis with technical indicators (MACD, RSI, Bollinger Bands)
  - Prediction visualizations using multiple ML models
  - News & sentiment analysis dashboard
  - Price alert management
  - Portfolio tracking and performance visualization
  - User account management

### 3. Database Service (`db`)
- PostgreSQL database for persistent storage
- Automatically applies migrations on startup
- Stores all user data, prediction history, alerts, and portfolios

### 4. Redis Service (`redis`)
- Caching layer for improved performance
- Session management
- Cache for frequently accessed data

### 5. Nginx Service (`nginx`)
- Reverse proxy handling routing between services
- SSL termination for HTTPS (in production)
- Static file serving

## Production Deployment

For production deployment:

1. Update the Nginx configuration in `nginx/conf.d/default.conf` to:
   - Uncomment the HTTPS server block
   - Add your domain name

2. Add SSL certificates to the `nginx/certs` directory:
   - `fullchain.pem`: Your certificate chain
   - `privkey.pem`: Your private key

3. Update environment variables in the `.env` file:
   - Set `ENV=production`
   - Configure production database credentials
   - Add your Stripe API keys for payment processing

4. Deploy with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Scaling the Application

For horizontal scaling:

1. Deploy the API service with multiple replicas:
   ```bash
   docker-compose up -d --scale api=3
   ```

2. Deploy with Docker Swarm or Kubernetes for production-grade orchestration.

## Troubleshooting

- **Database Connection Issues**: Check the `DATABASE_URL` environment variable
- **Container Health**: Run `docker-compose ps` to check container status
- **Logs**: View service logs with `docker-compose logs -f [service_name]`
- **Database Migrations**: If schema changes aren't applied, run `docker-compose exec api alembic upgrade head`

## Backup and Restore

- **Backup Database**:
  ```bash
  docker-compose exec db pg_dump -U postgres stockpredictpro > backup.sql
  ```

- **Restore Database**:
  ```bash
  cat backup.sql | docker-compose exec -T db psql -U postgres -d stockpredictpro
  ```
