"""
Configuration management for StockHark application
"""
import os
from pathlib import Path

# Base directory paths
BASE_DIR = Path(__file__).parent.parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = SRC_DIR / "data"
JSON_DIR = DATA_DIR / "json"

# Database configuration
DATABASE_PATH = DATA_DIR / "stocks.db"

# Reddit API configuration
REDDIT_CONFIG = {
    'client_id': os.getenv('REDDIT_CLIENT_ID'),
    'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
    'user_agent': os.getenv('REDDIT_USER_AGENT', 'StockHark/1.0'),
}

# Stock validation configuration
STOCK_CONFIG = {
    'nasdaq_file': JSON_DIR / "nasdaq_tickers.json",
    'amex_file': JSON_DIR / "amex_tickers.json",
}

# Flask configuration
FLASK_CONFIG = {
    'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-key-change-in-production'),
    'DEBUG': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
    'HOST': os.getenv('FLASK_HOST', '0.0.0.0'),
    'PORT': int(os.getenv('FLASK_PORT', 5000)),
}

# Email configuration (if needed)
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'email': os.getenv('EMAIL_ADDRESS'),
    'password': os.getenv('EMAIL_PASSWORD'),
}