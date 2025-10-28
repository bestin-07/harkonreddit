"""
HarkOnReddit Core Module

Provides core functionality for financial sentiment analysis and stock data management.

Key Components:
- High-performance database operations (database)
- Fast stock symbol validation (validator)
- Service factory for dependency injection (service_factory)
- Modular sentiment analysis system (sentiment/)

Usage:
    from stockhark.core import init_db
    from stockhark.core.database import get_top_stocks
    from stockhark.core.validator import StockValidator
    from stockhark.sentiment_analyzer import get_enhanced_analyzer
"""

# Core imports for external use
from .database import (
    init_db,
    get_db_connection,
    get_top_stocks,
    get_stock_details,
    add_stock_data,
    add_stock_data_batch,
    get_recent_activity,
    get_trending_stocks,
    get_database_stats,
    add_subscriber,
    get_active_subscribers
)
from .validator import (
    StockValidator,
    create_stock_validator,
    validate_stock_symbols,
    is_valid_stock_symbol
)

# Note: FinBERT functionality is now available through the sentiment module
# from stockhark.core.sentiment import create_analyzer

# Version and module info
__version__ = "1.0.0"
__author__ = "HarkOnReddit Team"

# Public API
__all__ = [
    # Database Operations
    'init_db',
    'get_db_connection', 
    'get_top_stocks',
    'get_stock_details',
    'add_stock_data',
    'add_stock_data_batch',
    'get_recent_activity',
    'get_trending_stocks',
    'get_database_stats',
    'add_subscriber',
    'get_active_subscribers',
    
    # Stock Validation
    'StockValidator',
    'create_stock_validator',
    'validate_stock_symbols', 
    'is_valid_stock_symbol',
]

# Note: Enhanced sentiment analysis is now available through:
# from stockhark.sentiment_analyzer import get_enhanced_analyzer
# from stockhark.core.sentiment import create_analyzer