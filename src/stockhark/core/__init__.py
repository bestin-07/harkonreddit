"""
HarkOnReddit Core Module

Provides core functionality for financial sentiment analysis and stock data management.

Key Components:
- FinBERT-powered sentiment analysis (finbert_analyzer)
- Enhanced sentiment analyzer with fallback (enhanced_sentiment) 
- High-performance database operations (database)
- Fast stock symbol validation (validator)

Usage:
    from stockhark.core import EnhancedSentimentAnalyzer, init_database
    from stockhark.core.database import get_top_stocks
    from stockhark.core.validator import StockValidator
"""

# Core imports for external use
from .enhanced_sentiment import EnhancedSentimentAnalyzer
from .database import (
    init_database,
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

# FinBERT imports are lazy-loaded to avoid startup delays
FINBERT_AVAILABLE = None  # Will be determined on first use
FinBERTSentimentAnalyzer = None
analyze_single_post = None

def _lazy_import_finbert():
    """Lazy import FinBERT components only when needed"""
    global FINBERT_AVAILABLE, FinBERTSentimentAnalyzer, analyze_single_post
    
    if FINBERT_AVAILABLE is not None:
        return FINBERT_AVAILABLE
        
    try:
        from .finbert_analyzer import (
            FinBERTSentimentAnalyzer as _FinBERTSentimentAnalyzer,
            analyze_single_post as _analyze_single_post
        )
        FINBERT_AVAILABLE = True
        FinBERTSentimentAnalyzer = _FinBERTSentimentAnalyzer
        analyze_single_post = _analyze_single_post
        return True
    except (ImportError, Exception):
        FINBERT_AVAILABLE = False
        return False

# Version and module info
__version__ = "1.0.0"
__author__ = "HarkOnReddit Team"

# Public API
__all__ = [
    # Sentiment Analysis
    'EnhancedSentimentAnalyzer',
    'FINBERT_AVAILABLE',
    
    # Database Operations
    'init_database',
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
    
    # FinBERT (lazy-loaded)
    '_lazy_import_finbert',
    'FINBERT_AVAILABLE',
]

# Note: FinBERT components are exported but will be None until lazy-loaded