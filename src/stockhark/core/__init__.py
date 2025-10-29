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
    from stockhark.core.validators.stock_validator import StockValidator
    from stockhark.sentiment_analyzer import get_enhanced_analyzer
"""

# Core imports for external use - now organized by functionality
from .data import (
    init_db,
    get_db_connection,
    get_top_stocks,
    get_stock_details,
    add_stock_data,
    add_stock_data_batch,
    get_recent_activity,
    add_subscriber,
    get_active_subscribers,
    get_database_stats
)
from .validators.stock_validator import (
    StockValidator,
    create_stock_validator,
    validate_stock_symbols,
    is_valid_stock_symbol
)
from .services import (
    ServiceFactory,
    get_service_factory,
    BackgroundDataCollector,
    start_background_collection,
    stop_background_collection
)
from .clients import (
    get_reddit_client
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
    'add_subscriber',
    'get_active_subscribers',
    'get_database_stats',
    
    # Stock Validation
    'StockValidator',
    'create_stock_validator',
    'validate_stock_symbols', 
    'is_valid_stock_symbol',
    
    # Services
    'ServiceFactory',
    'get_service_factory',
    'BackgroundDataCollector',
    'start_background_collection',
    'stop_background_collection',
    
    # External API Clients
    'get_reddit_client',
]

# Note: Enhanced sentiment analysis is now available through:
# from stockhark.sentiment_analyzer import get_enhanced_analyzer
# from stockhark.core.sentiment import create_analyzer