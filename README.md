# StockPredictPro - Stock Price Prediction SaaS Platform

<div align="center">
  <img src="app/static/logo.svg" alt="StockPredictPro Logo" width="150" height="150">
</div>

StockPredictPro is a comprehensive SaaS (Software as a Service) platform that allows users to analyze historical stock price data, visualize technical indicators, and make short-term price predictions using advanced machine learning models.

Originally based on the work by [Vikas Sharma](https://www.linkedin.com/in/vikas-sharma005/), this enhanced version provides a full SaaS experience with user authentication, subscription tiers, portfolio management, price alerts, sentiment analysis, and containerized deployment.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Subscription Tiers](#subscription-tiers)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
  - [Local Development Setup](#local-development-setup)
  - [Docker Deployment](#docker-deployment)
- [API Documentation](#api-documentation)
- [License](#license)

## Overview

StockPredictPro provides a modern, user-friendly platform for stock market analysis and prediction. It combines traditional technical analysis with advanced machine learning models to help users make informed investment decisions.

## Features

- **User Authentication & Management**: Secure user registration, login, and profile management.

- **Subscription System**: Tiered subscription plans with Stripe integration for payment processing.

- **Portfolio Management**: Create and track investment portfolios with real-time performance metrics.

- **Price Alert System**: Set custom price threshold alerts for your favorite stocks.

- **Market News & Sentiment Analysis**: Get the latest financial news with AI-powered sentiment scoring.

- **Stock Data Visualization**: Interactive charts for stock price history and volume.

- **Technical Indicators**: Visualize key indicators including:
  - Bollinger Bands
  - Moving Average Convergence Divergence (MACD)
  - Relative Strength Index (RSI)
  - Simple Moving Average (SMA)
  - Exponential Moving Average (EMA)

- **Machine Learning Predictions**: Multiple models with varying complexity:
  - Linear Regression
  - Random Forest Regressor
  - Extra Trees Regressor
  - K-Neighbors Regressor
  - XGBoost Regressor

- **User Dashboard**: Track prediction history, save favorite stocks, and manage account settings.

- **RESTful API**: Programmatic access to all platform features.

## Architecture

The system follows a modern, scalable, containerized architecture:

- **Backend**: FastAPI REST API for high-performance data processing and ML predictions
- **Frontend**: Streamlit for an interactive, data-focused user interface
- **Database**: PostgreSQL for storing user data, preferences, portfolios, and predictions
- **Caching**: Redis for performance optimization, session management, and rate limiting
- **Reverse Proxy**: Nginx for routing and SSL termination
- **Authentication**: JWT-based token authentication
- **Payment Processing**: Stripe integration
- **Containerization**: Docker and Docker Compose for easy deployment

## Subscription Tiers

The platform offers multiple subscription tiers:

1. **Free**:
   - Up to 5 predictions per day
   - Maximum 7-day forecast
   - Access to Linear Regression model only

2. **Basic ($9.99/month)**:
   - Up to 20 predictions per day
   - Maximum 14-day forecast
   - Access to Linear Regression and Random Forest models

3. **Professional ($19.99/month)**:
   - Up to 50 predictions per day
   - Maximum 30-day forecast
   - Access to 4 prediction models
   - Priority support

4. **Enterprise ($49.99/month)**:
   - Up to 200 predictions per day
   - Maximum 60-day forecast
   - Access to all prediction models
   - Premium support
   - Bulk API access

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Alembic, JWT
- **Frontend**: Streamlit, Plotly
- **Database**: PostgreSQL, Redis
- **Data Analysis**: Pandas, NumPy, TA-Lib
- **Machine Learning**: Scikit-learn, XGBoost
- **DevOps**: Docker, Docker Compose
- **Payments**: Stripe Integration
- **Stock Data**: Yahoo Finance API

## Installation

### Local Development Setup

1. Clone the repository:
   ```sh
   git clone https://github.com/vikasharma005/Stock-Price-Prediction.git
   cd Stock-Price-Prediction
   ```

2. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the example:
   ```sh
   cp .env.example .env
   # Edit the .env file with your configuration
   ```

5. Initialize the database:
   ```sh
   alembic upgrade head
   ```

6. Start the FastAPI server:
   ```sh
   uvicorn app.main:app --reload --port 8000
   ```

7. In a separate terminal, start the Streamlit frontend:
   ```sh
   streamlit run app/streamlit_app.py
   ```

8. Access the application:
   - FastAPI backend: http://localhost:8000
   - FastAPI docs: http://localhost:8000/docs
   - Streamlit frontend: http://localhost:8501

### Docker Deployment

1. Make sure Docker and Docker Compose are installed on your system.

2. Configure environment variables:
   ```sh
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. Build and start the containers:
   ```sh
   docker-compose up -d --build
   ```

4. Access the application:
   - Main UI: http://localhost:8501
   - API Documentation: http://localhost:8000/docs
   - Landing Page: http://localhost

5. Monitor running containers:
   ```sh
   docker-compose ps
   ```

6. View service logs:
   ```sh
   docker-compose logs -f [service_name]
   ```

7. To stop the containers:
   ```sh
   docker-compose down
   ```

For more detailed Docker deployment instructions, see the [docker-readme.md](docker-readme.md) file.

## API Documentation

StockPredictPro offers a comprehensive REST API for programmatic access to all features. API endpoints are organized into the following categories:

### Authentication

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login/access-token` - Get access token

### Users

- `GET /api/v1/users/me` - Get current user data
- `PUT /api/v1/users/me` - Update user profile
- `GET /api/v1/users/saved-stocks` - Get saved stocks
- `POST /api/v1/users/saved-stocks` - Save a stock
- `DELETE /api/v1/users/saved-stocks/{stock_id}` - Delete a saved stock
- `GET /api/v1/users/prediction-history` - Get prediction history

### Predictions

- `GET /api/v1/predictions/stock/{symbol}` - Get stock information
- `GET /api/v1/predictions/technical-indicators/{symbol}` - Get technical indicators
- `POST /api/v1/predictions/predict/{symbol}` - Predict stock prices

### Payments

- `GET /api/v1/payments/plans` - Get subscription plans
- `POST /api/v1/payments/create-checkout-session/{plan_id}` - Create checkout session
- `POST /api/v1/payments/webhook` - Handle Stripe webhooks

### Portfolio Management

- `GET /api/v1/portfolio` - Get user portfolios
- `POST /api/v1/portfolio` - Create a new portfolio
- `GET /api/v1/portfolio/{portfolio_id}` - Get portfolio details
- `PUT /api/v1/portfolio/{portfolio_id}` - Update portfolio
- `DELETE /api/v1/portfolio/{portfolio_id}` - Delete portfolio
- `POST /api/v1/portfolio/{portfolio_id}/stocks` - Add stock to portfolio
- `DELETE /api/v1/portfolio/{portfolio_id}/stocks/{stock_id}` - Remove stock from portfolio

### Price Alerts

- `GET /api/v1/alerts` - Get user price alerts
- `POST /api/v1/alerts` - Create a new price alert
- `PUT /api/v1/alerts/{alert_id}` - Update a price alert
- `DELETE /api/v1/alerts/{alert_id}` - Delete a price alert

### News & Sentiment

- `GET /api/v1/news/{symbol}` - Get latest news for a stock
- `GET /api/v1/sentiment/{symbol}` - Get sentiment analysis for a stock

For detailed API documentation, visit the `/docs` endpoint after starting the server.

## Extending the Platform

### Adding New Prediction Models

To add a new prediction model:

1. Add the model class to the predictions router
2. Update the subscription tier limits
3. Add the model to the Streamlit frontend

### Custom Technical Indicators

To add custom indicators:

1. Implement the indicator function in the predictions router
2. Add the indicator option to the Streamlit frontend

### Custom Sentiment Analysis

To modify the sentiment analysis:

1. Update the sentiment analysis logic in the sentiment router
2. Adjust the visualization in the Streamlit frontend

### Docker Production Deployment

For production deployment:

1. Update the Nginx configuration in `nginx/conf.d/default.conf` with your domain
2. Add SSL certificates to the `nginx/certs` directory
3. Update the `.env` file with production settings
4. Deploy using `docker-compose up -d`

## Original Author

<div id="header" align="center">
  <img src="https://media.giphy.com/media/M9gbBd9nbDrOTu1Mqx/giphy.gif" width="100"/>
</div>

<h3 align="center">Hi there 👋, I'm Vikas</h3>
<h4 align="center">Just learning New Skills😀</h4>

<div id="socials" align="center">
  <a href="https://www.linkedin.com/in/vikas-sharma005">
    <img src="https://user-images.githubusercontent.com/76098066/186728913-a66ef85f-4644-4e3a-b847-98309c8cff42.svg">
  </a>
  <a href="https://www.instagram.com/_thisisvikas">
    <img src="https://user-images.githubusercontent.com/76098066/186728908-f1a9919a-f4b2-4262-9515-683e77f8aabf.svg">
  </a>
  <a href="https://twitter.com/hitechvikas05">
    <img src="https://user-images.githubusercontent.com/76098066/186728901-a4d90f01-2cdf-45c1-a1b3-73467c3d2698.svg">
  </a>
</div>

You can find more about me and my projects on my [GitHub profile](https://github.com/vikasharma005).

## License

This project is licensed under the [MIT License](LICENSE).

---
