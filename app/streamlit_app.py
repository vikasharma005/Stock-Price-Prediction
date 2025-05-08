import streamlit as st
import pandas as pd
import requests
import json
import datetime
import plotly.graph_objects as go
import plotly.express as px
import base64
import os
from datetime import datetime, timedelta

# Configuration
API_URL = "http://127.0.0.1:8000/api/v1"

# Load the logo from static folder
def get_logo_base64():
    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'logo.svg')
    with open(logo_path, "rb") as f:
        logo_bytes = f.read()
    return base64.b64encode(logo_bytes).decode()

# Apply custom styling
def apply_custom_style():
    css_path = os.path.join(os.path.dirname(__file__), 'static', 'custom.css')
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Set page configuration
st.set_page_config(
    page_title="StockPredictPro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
    }
    .plan-card {
        padding: 20px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .plan-title {
        font-size: 1.2rem;
        font-weight: bold;
    }
    .plan-price {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .feature-list {
        list-style-type: none;
        padding-left: 0;
    }
    .feature-item:before {
        content: "✓ ";
        color: #4CAF50;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

# Authentication functions
def login(email, password):
    try:
        # Debug message
        st.info(f"Connecting to {API_URL}/auth/login/access-token...")
        
        # Use a longer timeout for the request
        response = requests.post(
            f"{API_URL}/auth/login/access-token",
            data={"username": email, "password": password},
            timeout=10
        )
        
        # Log the response status
        st.info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            get_current_user()
            return True
        else:
            error_detail = "Invalid email or password"
            try:
                error_detail = response.json()['detail']
            except Exception:
                if response.text:
                    error_detail = response.text
            
            st.error(f"Login error: {error_detail}")
            return False
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error: Unable to connect to the API server. Please make sure the backend is running on {API_URL}.")
        st.info("Technical details: " + str(e))
        return False
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False

def register(email, password, full_name):
    try:
        # Debug message
        st.info(f"Connecting to {API_URL}/auth/register...")
        
        # Use a longer timeout for the request
        response = requests.post(
            f"{API_URL}/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
            timeout=10
        )
        
        # Log the response status
        st.info(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            return True
        else:
            error_detail = "Unknown error"
            try:
                error_detail = response.json()['detail']
            except Exception:
                if response.text:
                    error_detail = response.text
            
            st.error(f"Registration error: {error_detail}")
            return False
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error: Unable to connect to the API server. Please make sure the backend is running on {API_URL}.")
        st.info("Technical details: " + str(e))
        return False
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False

def get_current_user():
    if st.session_state.token:
        try:
            response = requests.get(
                f"{API_URL}/users/me",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            if response.status_code == 200:
                st.session_state.user = response.json()
                return st.session_state.user
            else:
                st.session_state.token = None
                st.session_state.user = None
        except Exception:
            st.session_state.token = None
            st.session_state.user = None
    return None

def logout():
    st.session_state.token = None
    st.session_state.user = None

# Data fetching functions
def get_stock_info(symbol, days=30):
    try:
        response = requests.get(
            f"{API_URL}/predictions/stock/{symbol}",
            params={"days": days},
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching stock data: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error fetching stock data: {str(e)}")
        return None

def get_technical_indicators(symbol, indicator, days=60):
    try:
        response = requests.get(
            f"{API_URL}/predictions/technical-indicators/{symbol}",
            params={"indicator": indicator, "days": days},
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching indicators: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error fetching indicators: {str(e)}")
        return None

def predict_stock_price(symbol, model_name, days_forecast, training_days):
    try:
        response = requests.post(
            f"{API_URL}/predictions/predict/{symbol}",
            params={
                "model_name": model_name,
                "days_forecast": days_forecast,
                "training_days": training_days
            },
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Prediction error: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Prediction error: {str(e)}")
        return None

def get_subscription_plans():
    try:
        response = requests.get(f"{API_URL}/payments/plans")
        if response.status_code == 200:
            return response.json()["plans"]
        else:
            return None
    except Exception:
        return None

def create_checkout_session(plan_id):
    try:
        response = requests.post(
            f"{API_URL}/payments/create-checkout-session/{plan_id}",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            return response.json()["checkout_url"]
        else:
            st.error(f"Error creating checkout: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error creating checkout: {str(e)}")
        return None

def get_saved_stocks():
    if st.session_state.token:
        try:
            response = requests.get(
                f"{API_URL}/users/saved-stocks",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception:
            return []
    return []

def save_stock(symbol):
    if st.session_state.token:
        try:
            response = requests.post(
                f"{API_URL}/users/saved-stocks",
                json={"symbol": symbol},
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception:
            return False
    return False

def get_prediction_history():
    if st.session_state.token:
        try:
            response = requests.get(
                f"{API_URL}/users/prediction-history",
                headers={"Authorization": f"Bearer {st.session_state.token}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception:
            return []
    return []

# Page layouts
def login_page():
    # Apply custom style
    apply_custom_style()
    
    # Display logo and header
    logo_b64 = get_logo_base64()
    st.markdown(f'''
        <div style="text-align: center; margin-bottom: 30px">
            <img src="data:image/svg+xml;base64,{logo_b64}" width="200">
            <h1 class='main-header'>Welcome to StockPredictPro</h1>
            <p style="font-size: 1.2rem;">Your AI-Powered Stock Market Prediction Platform</p>
        </div>
    ''', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if login(email, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password")
    
    with col2:
        st.markdown("### Register")
        full_name = st.text_input("Full Name", key="register_name")
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        
        if st.button("Register"):
            if register(email, password, full_name):
                st.success("Registration successful! Please log in.")
            else:
                st.error("Registration failed")

def dashboard_page():
    # Apply custom style
    apply_custom_style()
    
    # Header with logo
    logo_b64 = get_logo_base64()
    st.markdown(f'''
        <div class="navbar">
            <img src="data:image/svg+xml;base64,{logo_b64}" class="app-logo" width="60">
            <div>
                <h1 class='main-header'>StockPredictPro Dashboard</h1>
                <p>Welcome, {st.session_state.user['full_name']}!</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Stock Analysis", "Predictions", "News & Sentiment", "Alerts", "Portfolio", "History", "Account"])
    
    with tab1:
        stock_analysis_tab()
    
    with tab2:
        predictions_tab()
    
    with tab3:
        news_sentiment_tab()
        
    with tab4:
        alerts_tab()
        
    with tab5:
        portfolio_tab()
        
    with tab6:
        history_tab()
    
    with tab7:
        account_tab()

def news_sentiment_tab():
    st.markdown("<h2 class='sub-header'>Market News & Sentiment Analysis</h2>", unsafe_allow_html=True)
    
    # Choose between market news and stock-specific news
    news_type = st.radio("Select news type", ["Market News", "Stock News"])
    
    if news_type == "Market News":
        # Get market news
        with st.spinner("Fetching market news..."):
            try:
                response = requests.get(
                    f"{API_URL}/news/market-news",
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    news_data = response.json()
                    
                    # Get market sentiment
                    sentiment_response = requests.get(
                        f"{API_URL}/sentiment/market",
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        timeout=10
                    )
                    
                    if sentiment_response.status_code == 200:
                        sentiment_data = sentiment_response.json()
                        
                        # Display market sentiment
                        st.markdown("### Market Sentiment")
                        sentiment = sentiment_data.get("overall_sentiment", "neutral")
                        polarity = sentiment_data.get("average_polarity", 0)
                        
                        # Create gauge chart for sentiment
                        fig = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = (polarity + 1) * 50,  # Convert from -1,1 to 0,100
                            title = {"text": f"Market Sentiment: {sentiment.title()}"},
                            gauge = {
                                "axis": {"range": [0, 100]},
                                "bar": {"color": "darkblue"},
                                "steps": [
                                    {"range": [0, 30], "color": "red"},
                                    {"range": [30, 40], "color": "orange"},
                                    {"range": [40, 60], "color": "yellow"},
                                    {"range": [60, 70], "color": "lightgreen"},
                                    {"range": [70, 100], "color": "green"}
                                ],
                                "threshold": {
                                    "line": {"color": "black", "width": 4},
                                    "thickness": 0.75,
                                    "value": (polarity + 1) * 50
                                }
                            }
                        ))
                        
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display sentiment distribution
                        distribution = sentiment_data.get("sentiment_distribution", {})
                        
                        dist_data = pd.DataFrame({
                            "Sentiment": ["Positive", "Neutral", "Negative"],
                            "Count": [
                                distribution.get("positive", 0),
                                distribution.get("neutral", 0),
                                distribution.get("negative", 0)
                            ]
                        })
                        
                        # Bar chart for sentiment distribution
                        fig = px.bar(dist_data, x="Sentiment", y="Count", 
                                    color="Sentiment",
                                    color_discrete_map={
                                        "Positive": "green",
                                        "Neutral": "blue",
                                        "Negative": "red"
                                    })
                        fig.update_layout(title="News Sentiment Distribution")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Display news articles
                    st.markdown("### Latest Market News")
                    news_articles = news_data.get("news", [])
                    
                    for i, article in enumerate(news_articles):
                        with st.expander(f"{article.get('title', 'Unnamed Article')}"):
                            st.write(f"**Source:** {article.get('source', 'Unknown')}")
                            st.write(f"**Published:** {article.get('published', 'Unknown')}")
                            
                            if sentiment_response.status_code == 200:
                                # Find article in sentiment data
                                for s_article in sentiment_data.get("articles", []):
                                    if s_article.get("title") == article.get("title"):
                                        sentiment = s_article.get("sentiment", {})
                                        polarity = sentiment.get("polarity", 0)
                                        category = sentiment.get("category", "neutral")
                                        
                                        # Color code by sentiment
                                        color = "blue"
                                        if category == "positive":
                                            color = "green"
                                        elif category == "negative":
                                            color = "red"
                                            
                                        st.markdown(f"**Sentiment:** <span style='color:{color}'>{category.title()} ({polarity:.2f})</span>", unsafe_allow_html=True)
                            
                            if article.get("url"):
                                st.markdown(f"[Read full article]({article.get('url')})")
                else:
                    st.error(f"Error fetching market news: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        # Stock-specific news
        symbol = st.text_input("Enter Stock Symbol for News", value="AAPL").upper()
        
        if st.button("Get Stock News & Sentiment"):
            with st.spinner(f"Fetching news for {symbol}..."):
                try:
                    # Get stock news
                    response = requests.get(
                        f"{API_URL}/news/stock-news/{symbol}",
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        news_data = response.json()
                        
                        # Get stock sentiment
                        sentiment_response = requests.get(
                            f"{API_URL}/sentiment/stock/{symbol}",
                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                            timeout=10
                        )
                        
                        if sentiment_response.status_code == 200:
                            sentiment_data = sentiment_response.json()
                            
                            # Get prediction confidence
                            confidence_response = requests.get(
                                f"{API_URL}/sentiment/prediction-confidence/{symbol}",
                                headers={"Authorization": f"Bearer {st.session_state.token}"},
                                timeout=10
                            )
                            
                            # Display stock sentiment
                            st.markdown(f"### {symbol} Sentiment Analysis")
                            sentiment = sentiment_data.get("overall_sentiment", "neutral")
                            polarity = sentiment_data.get("average_polarity", 0)
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Create gauge chart for sentiment
                                fig = go.Figure(go.Indicator(
                                    mode = "gauge+number",
                                    value = (polarity + 1) * 50,  # Convert from -1,1 to 0,100
                                    title = {"text": f"Sentiment: {sentiment.title()}"},
                                    gauge = {
                                        "axis": {"range": [0, 100]},
                                        "bar": {"color": "darkblue"},
                                        "steps": [
                                            {"range": [0, 30], "color": "red"},
                                            {"range": [30, 40], "color": "orange"},
                                            {"range": [40, 60], "color": "yellow"},
                                            {"range": [60, 70], "color": "lightgreen"},
                                            {"range": [70, 100], "color": "green"}
                                        ],
                                        "threshold": {
                                            "line": {"color": "black", "width": 4},
                                            "thickness": 0.75,
                                            "value": (polarity + 1) * 50
                                        }
                                    }
                                ))
                                
                                fig.update_layout(height=300)
                                st.plotly_chart(fig, use_container_width=True)
                            
                            with col2:
                                if confidence_response.status_code == 200:
                                    confidence_data = confidence_response.json()
                                    confidence_score = confidence_data.get("confidence_score", 50)
                                    assessment = confidence_data.get("confidence_assessment", "Moderate")
                                    color = confidence_data.get("confidence_color", "yellow")
                                    
                                    # Create gauge chart for prediction confidence
                                    fig = go.Figure(go.Indicator(
                                        mode = "gauge+number",
                                        value = confidence_score,
                                        title = {"text": f"Prediction Confidence: {assessment}"},
                                        gauge = {
                                            "axis": {"range": [0, 100]},
                                            "bar": {"color": "darkblue"},
                                            "steps": [
                                                {"range": [0, 25], "color": "red"},
                                                {"range": [25, 40], "color": "orange"},
                                                {"range": [40, 60], "color": "yellow"},
                                                {"range": [60, 75], "color": "lightgreen"},
                                                {"range": [75, 100], "color": "green"}
                                            ],
                                            "threshold": {
                                                "line": {"color": "black", "width": 4},
                                                "thickness": 0.75,
                                                "value": confidence_score
                                            }
                                        }
                                    ))
                                    
                                    fig.update_layout(height=300)
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            # Display sentiment distribution
                            distribution = sentiment_data.get("sentiment_distribution", {})
                            
                            dist_data = pd.DataFrame({
                                "Sentiment": ["Positive", "Neutral", "Negative"],
                                "Count": [
                                    distribution.get("positive", 0),
                                    distribution.get("neutral", 0),
                                    distribution.get("negative", 0)
                                ]
                            })
                            
                            # Bar chart for sentiment distribution
                            fig = px.bar(dist_data, x="Sentiment", y="Count", 
                                        color="Sentiment",
                                        color_discrete_map={
                                            "Positive": "green",
                                            "Neutral": "blue",
                                            "Negative": "red"
                                        })
                            fig.update_layout(title=f"{symbol} News Sentiment Distribution")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Display news articles
                        st.markdown(f"### Latest {symbol} News")
                        news_articles = news_data.get("news", [])
                        
                        for i, article in enumerate(news_articles):
                            with st.expander(f"{article.get('title', 'Unnamed Article')}"):
                                st.write(f"**Source:** {article.get('source', 'Unknown')}")
                                st.write(f"**Published:** {article.get('published', 'Unknown')}")
                                
                                if sentiment_response.status_code == 200:
                                    # Find article in sentiment data
                                    for s_article in sentiment_data.get("articles", []):
                                        if s_article.get("title") == article.get("title"):
                                            sentiment = s_article.get("sentiment", {})
                                            polarity = sentiment.get("polarity", 0)
                                            category = sentiment.get("category", "neutral")
                                            
                                            # Color code by sentiment
                                            color = "blue"
                                            if category == "positive":
                                                color = "green"
                                            elif category == "negative":
                                                color = "red"
                                                
                                            st.markdown(f"**Sentiment:** <span style='color:{color}'>{category.title()} ({polarity:.2f})</span>", unsafe_allow_html=True)
                                
                                if article.get("url"):
                                    st.markdown(f"[Read full article]({article.get('url')})")
                    else:
                        st.error(f"Error fetching news for {symbol}: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

def stock_analysis_tab():
    st.markdown("<h2 class='sub-header'>Stock Analysis</h2>", unsafe_allow_html=True)
    
    # Stock symbol input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        symbol = st.text_input("Enter Stock Symbol (e.g., AAPL, MSFT, GOOG)", value="AAPL").upper()
    
    with col2:
        days = st.number_input("Data Period (days)", min_value=7, max_value=365, value=60)
    
    if st.button("Analyze Stock"):
        with st.spinner("Fetching stock data..."):
            stock_data = get_stock_info(symbol, days)
            
            if stock_data:
                # Display stock info
                st.subheader(f"{stock_data['name']} ({symbol})")
                
                # Create DataFrame from recent data
                df = pd.DataFrame(stock_data['recent_data'])
                
                # Inspect dataframe columns and handle date column
                st.write("Debug: DataFrame columns:", df.columns.tolist())
                
                # Check if we have a date column and standardize its name
                date_column = None
                for col in df.columns:
                    if col.lower() in ['date', 'datetime', 'time', 'timestamp', 'index']:
                        date_column = col
                        break
                
                # If no date column found, create a simple index
                if date_column is None:
                    df['date_idx'] = list(range(len(df)))
                    date_column = 'date_idx'
                    st.warning("No date column found in data. Using index as date.")
                
                # Ensure numeric columns are properly typed
                numeric_columns = ['Open', 'High', 'Low', 'Close']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Display price chart if we have the required columns
                st.markdown("#### Price History")
                fig = go.Figure()
                
                if all(col in df.columns for col in numeric_columns):
                    fig.add_trace(go.Candlestick(
                        x=df[date_column],
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name="Candlestick"
                    ))
                else:
                    # Fallback to line chart if we don't have OHLC data
                    st.warning("Complete OHLC data not available. Showing Close prices only.")
                    if 'Close' in df.columns:
                        fig.add_trace(go.Scatter(
                            x=df[date_column],
                            y=df['Close'],
                            mode='lines',
                            name="Close Price"
                        ))
                    else:
                        st.error("Price data not available in expected format.")
                        return
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Price (USD)",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Technical indicators
                st.markdown("#### Technical Indicators")
                indicator_options = ["close", "bb", "macd", "rsi", "sma", "ema"]
                indicator = st.selectbox("Select Technical Indicator", indicator_options)
                
                with st.spinner("Calculating indicators..."):
                    indicator_data = get_technical_indicators(symbol, indicator, days)
                    
                    if indicator_data:
                        if indicator == "close":
                            df_ind = pd.DataFrame(indicator_data['data'])
                            fig = px.line(df_ind, x='Date', y='Close', title="Close Price")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        elif indicator == "bb":
                            df_ind = pd.DataFrame(indicator_data['data'])
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=df_ind['Date'], y=df_ind['Close'], name="Close"))
                            fig.add_trace(go.Scatter(x=df_ind['Date'], y=df_ind['bb_h'], name="Upper Band"))
                            fig.add_trace(go.Scatter(x=df_ind['Date'], y=df_ind['bb_l'], name="Lower Band"))
                            fig.update_layout(title="Bollinger Bands")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        elif indicator == "macd":
                            df_ind = pd.DataFrame(indicator_data['data'])
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=df_ind['Date'], y=df_ind['MACD'], name="MACD"))
                            fig.add_trace(go.Scatter(x=df_ind['Date'], y=df_ind['Signal'], name="Signal"))
                            fig.add_trace(go.Bar(x=df_ind['Date'], y=df_ind['Histogram'], name="Histogram"))
                            fig.update_layout(title="MACD")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        elif indicator == "rsi":
                            df_ind = pd.DataFrame(indicator_data['data'])
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=df_ind['Date'], y=df_ind['RSI'], name="RSI"))
                            fig.add_shape(type="line", x0=df_ind['Date'].min(), x1=df_ind['Date'].max(),
                                          y0=70, y1=70, line=dict(color="red", width=1, dash="dash"))
                            fig.add_shape(type="line", x0=df_ind['Date'].min(), x1=df_ind['Date'].max(),
                                          y0=30, y1=30, line=dict(color="green", width=1, dash="dash"))
                            fig.update_layout(title="RSI")
                            st.plotly_chart(fig, use_container_width=True)
                        
                        elif indicator in ["sma", "ema"]:
                            df_ind = pd.DataFrame(indicator_data['data'])
                            title = "Simple Moving Average" if indicator == "sma" else "Exponential Moving Average"
                            y_col = "SMA" if indicator == "sma" else "EMA"
                            fig = px.line(df_ind, x='Date', y=y_col, title=title)
                            st.plotly_chart(fig, use_container_width=True)
                
                # Save stock button
                if st.button("Save to My Stocks"):
                    if save_stock(symbol):
                        st.success(f"Added {symbol} to your saved stocks")
                    else:
                        st.error("Failed to save stock")

def predictions_tab():
    st.markdown("<h2 class='sub-header'>Stock Price Predictions</h2>", unsafe_allow_html=True)
    
    # Get user's subscription tier to determine available models
    user_tier = st.session_state.user.get("subscription_tier", "free")
    
    # Define available models based on tier
    model_options = {
        "free": ["LinearRegression"],
        "basic": ["LinearRegression", "RandomForestRegressor"],
        "pro": ["LinearRegression", "RandomForestRegressor", "KNeighborsRegressor", "ExtraTreesRegressor"],
        "enterprise": ["LinearRegression", "RandomForestRegressor", "KNeighborsRegressor", "ExtraTreesRegressor", "XGBRegressor"]
    }
    
    # Define max forecast days based on tier
    max_days = {
        "free": 7,
        "basic": 14,
        "pro": 30,
        "enterprise": 60
    }
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        symbol = st.text_input("Enter Stock Symbol for Prediction", value="AAPL").upper()
    
    with col2:
        available_models = model_options.get(user_tier, ["LinearRegression"])
        model = st.selectbox("Select Prediction Model", available_models)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_forecast = st.slider("Forecast Days", min_value=1, max_value=max_days.get(user_tier, 7), value=5)
    
    with col2:
        training_days = st.slider("Training Period (days)", min_value=30, max_value=365, value=100)
    
    if st.button("Generate Prediction"):
        with st.spinner("Generating prediction..."):
            prediction = predict_stock_price(symbol, model, days_forecast, training_days)
            
            if prediction:
                # Parse prediction results
                result = json.loads(prediction['result_json'])
                
                # Display metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("R² Score", f"{float(result['r2_score']):.4f}")
                with col2:
                    st.metric("Mean Absolute Error", f"{float(result['mae']):.4f}")
                
                # Display predictions table
                st.subheader("Price Predictions")
                prediction_df = pd.DataFrame(result['predictions'])
                st.dataframe(prediction_df)
                
                # Plot predictions
                fig = px.line(prediction_df, x='date', y='price',
                              title=f"{symbol} Price Prediction for Next {days_forecast} Days",
                              labels={'date': 'Date', 'price': 'Predicted Price (USD)'})
                st.plotly_chart(fig, use_container_width=True)
                
                # Disclaimer
                st.warning("Disclaimer: These predictions are based on historical data and should not be used as the sole basis for investment decisions. Past performance is not indicative of future results.")

def history_tab():
    st.markdown("<h2 class='sub-header'>My Activity</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Saved Stocks", "Prediction History"])
    
    with tab1:
        st.subheader("My Saved Stocks")
        saved_stocks = get_saved_stocks()
        
        if saved_stocks:
            for stock in saved_stocks:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**{stock['symbol']}** (Saved on {stock['created_at'][:10]})")
                with col2:
                    if st.button("Analyze", key=f"analyze_{stock['id']}"):
                        # Set the symbol in session state and switch to analysis tab
                        st.session_state.selected_symbol = stock['symbol']
                        st.rerun()
        else:
            st.info("You haven't saved any stocks yet. Go to Stock Analysis to add some!")
    
    with tab2:
        st.subheader("My Prediction History")
        predictions = get_prediction_history()
        
        if predictions:
            for pred in predictions:
                with st.expander(f"{pred['symbol']} - {pred['model_used']} ({pred['created_at'][:10]})"):
                    result = json.loads(pred['result_json'])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Symbol:** {result['symbol']}")
                    with col2:
                        st.write(f"**Model:** {result['model']}")
                    with col3:
                        st.write(f"**Days Forecast:** {result['days_forecast']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("R² Score", f"{float(result['r2_score']):.4f}")
                    with col2:
                        st.metric("Mean Absolute Error", f"{float(result['mae']):.4f}")
                    
                    # Display predictions table
                    prediction_df = pd.DataFrame(result['predictions'])
                    st.dataframe(prediction_df)
        else:
            st.info("You haven't made any predictions yet. Go to the Predictions tab to create some!")

def portfolio_tab():
    st.markdown("<h2 class='sub-header'>Investment Portfolio</h2>", unsafe_allow_html=True)
    
    # Create two sections with tabs
    portfolio_action = st.radio("Portfolio Management", ["View Portfolios", "Create New Portfolio"])
    
    if portfolio_action == "Create New Portfolio":
        # Create new portfolio form
        st.markdown("### Create New Portfolio")
        
        portfolio_name = st.text_input("Portfolio Name", placeholder="e.g., Retirement Fund, Tech Stocks, etc.")
        portfolio_desc = st.text_area("Description", placeholder="Optional description of your portfolio strategy...")
        
        if st.button("Create Portfolio"):
            if not portfolio_name:
                st.error("Portfolio name is required")
            else:
                try:
                    portfolio_data = {
                        "name": portfolio_name,
                        "description": portfolio_desc
                    }
                    
                    response = requests.post(
                        f"{API_URL}/portfolio/create",
                        json=portfolio_data,
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        st.success("Portfolio created successfully!")
                        # Switch to view portfolios
                        st.rerun()
                    else:
                        st.error(f"Error creating portfolio: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        # View existing portfolios
        try:
            response = requests.get(
                f"{API_URL}/portfolio/list",
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                portfolios = response.json()
                
                if not portfolios:
                    st.info("You don't have any portfolios yet. Create a new portfolio to get started!")
                else:
                    # Display portfolio summary cards
                    st.markdown("### My Portfolios")
                    
                    portfolio_summary = []
                    for p in portfolios:
                        portfolio_summary.append({
                            "id": p.get("id"),
                            "name": p.get("name"),
                            "value": p.get("total_value", 0),
                            "gain_loss": p.get("total_gain_loss", 0),
                            "gain_loss_percent": p.get("total_gain_loss_percent", 0)
                        })
                    
                    # Layout portfolio cards in columns
                    cols = st.columns(min(3, len(portfolio_summary)))
                    for i, portfolio in enumerate(portfolio_summary):
                        with cols[i % len(cols)]:
                            value = portfolio.get("value", 0) or 0
                            gain_loss = portfolio.get("gain_loss", 0) or 0
                            gain_loss_percent = portfolio.get("gain_loss_percent", 0) or 0
                            
                            # Color based on performance
                            color = "gray"
                            if gain_loss > 0:
                                color = "green"
                            elif gain_loss < 0:
                                color = "red"
                                
                            with st.container(border=True):
                                st.markdown(f"**{portfolio.get('name')}**")
                                st.markdown(f"Total Value: **${value:,.2f}**")
                                st.markdown(f"Gain/Loss: <span style='color:{color}'>**${gain_loss:,.2f} ({gain_loss_percent:.2f}%)**</span>", unsafe_allow_html=True)
                                
                                # Button to view portfolio details
                                if st.button(f"View {portfolio.get('name')}", key=f"view_{portfolio.get('id')}"):
                                    st.session_state.active_portfolio = portfolio.get('id')
                                    st.session_state.active_portfolio_name = portfolio.get('name')
                    
                    # Portfolio details view
                    if "active_portfolio" in st.session_state:
                        st.markdown(f"### {st.session_state.active_portfolio_name} Details")
                        
                        # Tabs for portfolio details
                        p_tab1, p_tab2 = st.tabs(["Holdings", "Add Stock"])
                        
                        with p_tab1:
                            # Get portfolio stocks
                            stocks_response = requests.get(
                                f"{API_URL}/portfolio/{st.session_state.active_portfolio}/stocks",
                                headers={"Authorization": f"Bearer {st.session_state.token}"},
                                timeout=10
                            )
                            
                            if stocks_response.status_code == 200:
                                stocks = stocks_response.json()
                                
                                if not stocks:
                                    st.info("This portfolio doesn't have any stocks yet. Add some to get started!")
                                else:
                                    # Prepare stock data for display
                                    stock_data = []
                                    for s in stocks:
                                        # Color for gain/loss
                                        color = "gray"
                                        gain_loss = s.get("gain_loss", 0) or 0
                                        if gain_loss > 0:
                                            color = "green"
                                        elif gain_loss < 0:
                                            color = "red"
                                            
                                        stock_data.append({
                                            "id": s.get("id"),
                                            "Symbol": s.get("symbol"),
                                            "Shares": s.get("shares"),
                                            "Purchase Price": f"${s.get('purchase_price'):.2f}",
                                            "Current Price": f"${s.get('current_price'):.2f}" if s.get("current_price") else "N/A",
                                            "Current Value": f"${s.get('current_value'):.2f}" if s.get("current_value") else "N/A",
                                            "Gain/Loss": f"<span style='color:{color}'>${gain_loss:.2f} ({s.get('gain_loss_percent', 0):.2f}%)</span>",
                                            "Purchase Date": s.get("purchase_date").split("T")[0] if s.get("purchase_date") else "N/A"
                                        })
                                    
                                    # Create DataFrame and display as table
                                    df = pd.DataFrame(stock_data)
                                    df = df.drop(columns=["id"])
                                    
                                    # Convert to HTML to preserve styling
                                    html = df.to_html(escape=False, index=False)
                                    st.markdown(html, unsafe_allow_html=True)
                                    
                                    # Allow deletion of stocks
                                    st.markdown("### Remove Stock")
                                    stock_to_delete = st.selectbox("Select Stock to Remove", 
                                                            options=range(len(stock_data)),
                                                            format_func=lambda x: f"{stock_data[x]['Symbol']} - {stock_data[x]['Shares']} shares @ {stock_data[x]['Purchase Price']}",
                                                            key="delete_stock")
                                    
                                    if st.button("Remove Selected Stock"):
                                        stock_id = stock_data[stock_to_delete]["id"]
                                        delete_response = requests.delete(
                                            f"{API_URL}/portfolio/{st.session_state.active_portfolio}/stocks/{stock_id}",
                                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                                            timeout=10
                                        )
                                        
                                        if delete_response.status_code == 200:
                                            st.success("Stock removed successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"Error removing stock: {delete_response.text}")
                            else:
                                st.error(f"Error fetching portfolio stocks: {stocks_response.text}")
                        
                        with p_tab2:
                            # Form to add a new stock
                            st.markdown("### Add Stock to Portfolio")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                symbol = st.text_input("Symbol", value="AAPL").upper()
                                shares = st.number_input("Number of Shares", min_value=0.01, value=1.0, step=0.01)
                                
                                # Get current price
                                try:
                                    price_response = requests.get(
                                        f"{API_URL}/predictions/stock-price/{symbol}",
                                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                                        timeout=10
                                    )
                                    if price_response.status_code == 200:
                                        price_data = price_response.json()
                                        current_price = price_data.get("current_price")
                                        st.info(f"Current price: ${current_price:.2f}")
                                except Exception as e:
                                    st.warning(f"Could not get current price. Error: {str(e)}")
                                    current_price = 0
                            
                            with col2:
                                purchase_price = st.number_input("Purchase Price per Share", min_value=0.01, value=float(current_price) if current_price else 100.0, step=0.01)
                                purchase_date = st.date_input("Purchase Date", value=datetime.now().date())
                            
                            notes = st.text_area("Notes", placeholder="Any notes about this investment...")
                            
                            if st.button("Add Stock to Portfolio"):
                                try:
                                    stock_data = {
                                        "symbol": symbol,
                                        "shares": shares,
                                        "purchase_price": purchase_price,
                                        "purchase_date": purchase_date.isoformat() + "T00:00:00",
                                        "notes": notes
                                    }
                                    
                                    response = requests.post(
                                        f"{API_URL}/portfolio/{st.session_state.active_portfolio}/add-stock",
                                        json=stock_data,
                                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                                        timeout=10
                                    )
                                    
                                    if response.status_code == 200:
                                        st.success(f"{symbol} added to portfolio successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error adding stock: {response.text}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        
                        # Option to delete the entire portfolio
                        st.markdown("### Delete Portfolio")
                        st.warning("Warning: This will delete the entire portfolio and all its stocks. This action cannot be undone.")
                        if st.button("Delete Entire Portfolio"):
                            try:
                                delete_response = requests.delete(
                                    f"{API_URL}/portfolio/{st.session_state.active_portfolio}",
                                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                                    timeout=10
                                )
                                
                                if delete_response.status_code == 200:
                                    st.success("Portfolio deleted successfully!")
                                    if "active_portfolio" in st.session_state:
                                        del st.session_state.active_portfolio
                                        del st.session_state.active_portfolio_name
                                    st.rerun()
                                else:
                                    st.error(f"Error deleting portfolio: {delete_response.text}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            else:
                st.error(f"Error fetching portfolios: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

def alerts_tab():
    st.markdown("<h2 class='sub-header'>Price Alerts</h2>", unsafe_allow_html=True)
    
    # Create two sections with tabs
    alert_action = st.radio("Alerts", ["View My Alerts", "Create New Alert"])
    
    if alert_action == "Create New Alert":
        # Create new alert form
        st.markdown("### Create New Price Alert")
        
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Symbol", value="AAPL").upper()
            alert_type = st.selectbox("Alert Type", ["Price", "Technical", "Sentiment"])
            
            # Get current price
            try:
                response = requests.get(
                    f"{API_URL}/predictions/stock-price/{symbol}",
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    timeout=10
                )
                if response.status_code == 200:
                    price_data = response.json()
                    current_price = price_data.get("current_price")
                    st.info(f"Current price: ${current_price:.2f}")
            except Exception as e:
                st.warning(f"Could not get current price. Error: {str(e)}")
                current_price = 0
        
        with col2:
            condition = st.selectbox(
                "Condition", 
                ["Above", "Below", "Crosses Above", "Crosses Below"],
                help="'Above/Below': Alert triggers when price is above/below target. 'Crosses': Alert triggers when price crosses the target value."
            )
            target_value = st.number_input("Target Value", min_value=0.01, value=float(current_price) if current_price else 100.0, step=0.01)
            
            # Convert condition to API format
            condition_api = condition.lower().replace(" ", "_")
        
        expiration = st.slider("Expires after (days)", min_value=1, max_value=90, value=30)
        is_recurring = st.checkbox("Recurring Alert", help="If checked, the alert will reset after being triggered and continue monitoring.")
        notes = st.text_area("Notes", placeholder="Add any notes about this alert...")
        
        if st.button("Create Alert"):
            try:
                alert_data = {
                    "symbol": symbol,
                    "alert_type": alert_type.lower(),
                    "condition": condition_api,
                    "target_value": target_value,
                    "expiration_days": expiration,
                    "is_recurring": is_recurring,
                    "notes": notes
                }
                
                response = requests.post(
                    f"{API_URL}/alerts/create",
                    json=alert_data,
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("Alert created successfully!")
                    # Auto-switch to view alerts
                    st.rerun()
                else:
                    st.error(f"Error creating alert: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        # View existing alerts
        st.markdown("### My Price Alerts")
        
        # Options for filtering
        col1, col2 = st.columns(2)
        with col1:
            active_only = st.checkbox("Show Active Alerts Only", value=True)
        with col2:
            symbol_filter = st.text_input("Filter by Symbol", value="").upper()
        
        try:
            # Construct query parameters
            params = {"active_only": active_only}
            if symbol_filter:
                params["symbol"] = symbol_filter
                
            response = requests.get(
                f"{API_URL}/alerts/list",
                params=params,
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                alerts = response.json()
                
                if not alerts:
                    st.info("No alerts found. Create a new alert to get started!")
                else:
                    # Check for triggers
                    if st.button("Check For Triggered Alerts"):
                        check_response = requests.post(
                            f"{API_URL}/alerts/check",
                            headers={"Authorization": f"Bearer {st.session_state.token}"},
                            timeout=10
                        )
                        
                        if check_response.status_code == 200:
                            result = check_response.json()
                            triggered = result.get("triggered", [])
                            
                            if triggered:
                                st.success(f"🔔 {len(triggered)} alerts triggered!")
                                for alert in triggered:
                                    st.markdown(f"**{alert['symbol']}** {alert['condition']} ${alert['target_value']:.2f} (Current: ${alert['current_value']:.2f})")
                            else:
                                st.info("No alerts triggered at this time.")
                                
                            # Refresh the alerts list
                            response = requests.get(
                                f"{API_URL}/alerts/list",
                                params=params,
                                headers={"Authorization": f"Bearer {st.session_state.token}"},
                                timeout=10
                            )
                            if response.status_code == 200:
                                alerts = response.json()
                    
                    # Display alerts in a table
                    alert_data = []
                    for alert in alerts:
                        status = "✅ Active" if not alert.get("triggered") and alert.get("expires_at") > datetime.now().isoformat() else "❌ Inactive"
                        alert_data.append({
                            "Symbol": alert.get("symbol"),
                            "Type": alert.get("alert_type").title(),
                            "Condition": alert.get("condition").replace("_", " ").title(),
                            "Target": f"${alert.get('target_value'):.2f}",
                            "Current": f"${alert.get('current_value'):.2f}" if alert.get("current_value") else "Unknown",
                            "Status": status,
                            "Created": alert.get("created_at").split("T")[0],
                            "ID": alert.get("id")
                        })
                    
                    df = pd.DataFrame(alert_data)
                    
                    # Use AgGrid for interactive table
                    st.dataframe(df.drop(columns=["ID"]), use_container_width=True)
                    
                    # Allow deletion of alerts
                    if alert_data:
                        st.markdown("### Delete Alert")
                        selected_alert = st.selectbox("Select Alert to Delete", 
                                                    options=[f"{a['Symbol']} - {a['Condition']} ${float(a['Target'].replace('$', '')):,.2f} ({a['Created']})" for a in alert_data],
                                                    key="delete_alert")
                        
                        selected_index = st.selectbox("Select Alert to Delete", 
                                                    options=range(len(alert_data)),
                                                    format_func=lambda x: f"{alert_data[x]['Symbol']} - {alert_data[x]['Condition']} ${float(alert_data[x]['Target'].replace('$', '')):,.2f} ({alert_data[x]['Created']})",
                                                    key="delete_alert_index")
                        
                        if st.button("Delete Selected Alert"):
                            alert_id = alert_data[selected_index]["ID"]
                            delete_response = requests.delete(
                                f"{API_URL}/alerts/delete/{alert_id}",
                                headers={"Authorization": f"Bearer {st.session_state.token}"},
                                timeout=10
                            )
                            
                            if delete_response.status_code == 200:
                                st.success("Alert deleted successfully!")
                                st.rerun()
                            else:
                                st.error(f"Error deleting alert: {delete_response.text}")
            else:
                st.error(f"Error fetching alerts: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

def account_tab():
    st.markdown("<h2 class='sub-header'>My Account</h2>", unsafe_allow_html=True)
    
    # Check if user data exists in session state
    if not hasattr(st.session_state, 'user') or st.session_state.user is None:
        st.error("User data not available. Please log in again.")
        return
    
    # Safe access to user properties with defaults if missing
    user = st.session_state.user
    full_name = user.get('full_name', 'Not available')
    email = user.get('email', 'Not available')
    subscription_tier = user.get('subscription_tier', 'free')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Profile Information")
        st.write(f"**Name:** {full_name}")
        st.write(f"**Email:** {email}")
        st.write(f"**Current Plan:** {subscription_tier.title()}")
        st.write("**Account Created:** Not available") # Removed potentially problematic created_at reference
    
    with col2:
        st.markdown("### Update Profile")
        new_name = st.text_input("Full Name", value=full_name)
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        
        if st.button("Update Profile"):
            st.warning("Profile update functionality will be implemented soon")
    
    st.markdown("### Subscription Plans")
    plans = get_subscription_plans()
    
    if plans:
        col1, col2, col3 = st.columns(3)
        
        # Basic plan
        with col1:
            with st.container():
                st.markdown(f"""
                <div class="plan-card" style="background-color: #E3F2FD;">
                    <div class="plan-title">{plans['basic']['name']}</div>
                    <div class="plan-price">${plans['basic']['price_monthly_usd']}/month</div>
                    <p>{plans['basic']['description']}</p>
                    <ul class="feature-list">
                        {"".join([f'<li class="feature-item">{feature}</li>' for feature in plans['basic']['features']])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                if st.session_state.user['subscription_tier'] == "basic":
                    st.success("Current Plan")
                else:
                    if st.button("Upgrade to Basic"):
                        checkout_url = create_checkout_session("basic")
                        if checkout_url:
                            st.markdown(f"[Click here to complete your payment]({checkout_url})")
        
        # Pro plan
        with col2:
            with st.container():
                st.markdown(f"""
                <div class="plan-card" style="background-color: #E8F5E9;">
                    <div class="plan-title">{plans['pro']['name']}</div>
                    <div class="plan-price">${plans['pro']['price_monthly_usd']}/month</div>
                    <p>{plans['pro']['description']}</p>
                    <ul class="feature-list">
                        {"".join([f'<li class="feature-item">{feature}</li>' for feature in plans['pro']['features']])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                if st.session_state.user['subscription_tier'] == "pro":
                    st.success("Current Plan")
                else:
                    if st.button("Upgrade to Pro"):
                        checkout_url = create_checkout_session("pro")
                        if checkout_url:
                            st.markdown(f"[Click here to complete your payment]({checkout_url})")
        
        # Enterprise plan
        with col3:
            with st.container():
                st.markdown(f"""
                <div class="plan-card" style="background-color: #FFF8E1;">
                    <div class="plan-title">{plans['enterprise']['name']}</div>
                    <div class="plan-price">${plans['enterprise']['price_monthly_usd']}/month</div>
                    <p>{plans['enterprise']['description']}</p>
                    <ul class="feature-list">
                        {"".join([f'<li class="feature-item">{feature}</li>' for feature in plans['enterprise']['features']])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
                if st.session_state.user['subscription_tier'] == "enterprise":
                    st.success("Current Plan")
                else:
                    if st.button("Upgrade to Enterprise"):
                        checkout_url = create_checkout_session("enterprise")
                        if checkout_url:
                            st.markdown(f"[Click here to complete your payment]({checkout_url})")
    
    if st.button("Logout"):
        logout()
        st.rerun()

# Main app 
def main():
    # Create sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/48/000000/stock-market.png", width=80)
        st.title("StockPredictPro")
        st.markdown("---")
        
        if st.session_state.user:
            st.markdown(f"**Plan:** {st.session_state.user['subscription_tier'].title()}")
            st.markdown("---")
        
    # Check if user is logged in
    if st.session_state.token and st.session_state.user:
        dashboard_page()
    else:
        login_page()

if __name__ == "__main__":
    main()
