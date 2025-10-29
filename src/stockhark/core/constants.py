"""
StockHark Constants

Centralized constants to eliminate magic numbers and hardcoded values
throughout the codebase for better maintainability and configuration.
"""

from datetime import timedelta
from typing import Dict, List, Set

# ==============================================================================
# APPLICATION METADATA
# ==============================================================================

APP_NAME = "StockHark"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Reddit Stock Sentiment Analyzer with Background Data Collection"
DEFAULT_USER_AGENT = f"{APP_NAME}/{APP_VERSION}"

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

# Database file settings
DATABASE_FILENAME = "stocks.db"
DATABASE_TIMEOUT_SECONDS = 30.0
DATABASE_MAX_CONNECTIONS = 10
DATABASE_JOURNAL_MODE = "WAL"  # Write-Ahead Logging for better performance

# Query limits and pagination
DEFAULT_STOCK_LIMIT = 10
MAX_STOCK_LIMIT = 100
DEFAULT_HOURS_WINDOW = 24
EXTENDED_HOURS_WINDOW = 720  # 30 days
MAX_HOURS_WINDOW = 8760  # 1 year

# Database batch sizes
BATCH_INSERT_SIZE = 100
MAX_VARIABLE_NUMBER = 999  # SQLite limit for variables in single query

# ==============================================================================
# REDDIT API CONFIGURATION
# ==============================================================================

# API rate limiting
REDDIT_API_DELAY_SECONDS = 0.2
REDDIT_RATE_LIMIT_DELAY = 5
REDDIT_MAX_RETRIES = 3

# Post fetching limits
DEFAULT_POSTS_PER_SUBREDDIT = 20
MAX_POSTS_PER_SUBREDDIT = 100
MIN_POSTS_PER_SUBREDDIT = 5

# Content filtering
MAX_POST_TITLE_LENGTH = 300
MAX_POST_CONTENT_LENGTH = 10000
MAX_COMMENT_LENGTH = 1000

# ==============================================================================
# BACKGROUND DATA COLLECTION
# ==============================================================================

# Collection timing
DEFAULT_COLLECTION_INTERVAL_MINUTES = 30
MIN_COLLECTION_INTERVAL_MINUTES = 5
MAX_COLLECTION_INTERVAL_MINUTES = 1440  # 24 hours

# Collection limits
DEFAULT_COLLECTION_DURATION_MINUTES = 15
MAX_COLLECTION_CYCLES = 1000
BACKGROUND_SLEEP_SECONDS = 1200  # 20 minutes for periodic monitoring

# Collection statistics
COLLECTION_SUCCESS_THRESHOLD = 0.8  # 80% success rate
MIN_STOCKS_PER_COLLECTION = 5
TARGET_STOCKS_PER_COLLECTION = 50

# ==============================================================================
# SENTIMENT ANALYSIS
# ==============================================================================

# Post count weighting - gives more importance to stocks mentioned in multiple posts
# Formula: post_weight = 1.0 + (log(unique_posts) * POST_COUNT_WEIGHT_MULTIPLIER)
POST_COUNT_WEIGHT_MULTIPLIER = 0.3  # Boost factor for multiple posts
MIN_POST_COUNT_WEIGHT = 1.0  # Minimum weight (single post)
MAX_POST_COUNT_WEIGHT = 2.0  # Maximum weight cap

# Minimum mention threshold - filters out stocks with insufficient discussion
MIN_STOCK_MENTIONS = 5  # Minimum mentions required for a stock to be considered
MIN_UNIQUE_POSTS = 2    # Minimum unique posts required for a stock to be considered

# FinBERT configuration
FINBERT_MODEL_NAME = "ProsusAI/finbert"
FINBERT_MAX_LENGTH = 512
FINBERT_BATCH_SIZE = 16

# Sentiment thresholds
SENTIMENT_BULLISH_THRESHOLD = 0.1
SENTIMENT_BEARISH_THRESHOLD = -0.1
SENTIMENT_CONFIDENCE_THRESHOLD = 0.7

# Sentiment scoring
MIN_SENTIMENT_SCORE = -1.0
MAX_SENTIMENT_SCORE = 1.0
NEUTRAL_SENTIMENT_SCORE = 0.0

# Time decay for sentiment analysis
SENTIMENT_TIME_DECAY_LAMBDA = 0.1
SENTIMENT_TIME_WINDOW_HOURS = 24

# Source reliability weights (as per methodology specification)
SOURCE_WEIGHTS = {
    'reddit': 1.0,  # Baseline weight for Reddit posts
    'reddit/r/investing': 1.0,
    'reddit/r/stocks': 1.0,
    'reddit/r/SecurityAnalysis': 1.0,
    'reddit/r/ValueInvesting': 1.0,
    'reddit/r/wallstreetbets': 0.8,  # Lower reliability due to meme nature
    'reddit/r/pennystocks': 0.7,  # Lower reliability due to speculation
    'default': 1.0  # Default weight for unknown sources
}

# Symbol weight penalties for common English words that are legitimate stock symbols
# but likely to be false positives in casual text
COMMON_WORD_SYMBOL_WEIGHTS = {
    # Legitimate stock symbols that are also common English words - reduced weight
    'ANY': 0.3, 'BEAT': 0.4, 'CARE': 0.4, 'CASH': 0.6, 'COST': 0.7, 'GAME': 0.5,
    'GOOD': 0.2, 'GROW': 0.6, 'HOPE': 0.3, 'LAND': 0.5, 'LINE': 0.4, 'LINK': 0.4,
    'LIVE': 0.3, 'LOVE': 0.2, 'MIND': 0.4, 'MOVE': 0.3, 'NEXT': 0.4, 'ON': 0.2,
    'OPEN': 0.3, 'PLAY': 0.3, 'PLUS': 0.5, 'REAL': 0.3, 'ROAD': 0.6, 'ROCK': 0.6,
    'SELF': 0.4, 'STEP': 0.4, 'TALK': 0.3, 'TEAM': 0.4, 'TECH': 0.5, 'TRIP': 0.5,
    'UNIT': 0.5, 'WAVE': 0.6, 'ZONE': 0.5,
    
    # Pure false positives - very common words that are NOT legitimate stock symbols
    # These get heavy penalties to minimize their impact
    'FREE': 0.05, 'HELP': 0.05, 'HOME': 0.1, 'LIFE': 0.05, 'LOOK': 0.05, 'MAKE': 0.05,
    'MORE': 0.05, 'NEED': 0.05, 'PLAN': 0.1, 'POST': 0.1, 'RACE': 0.1, 'RIDE': 0.1,
    'RISE': 0.1, 'SAFE': 0.1, 'SAME': 0.05, 'SAVE': 0.1, 'SHOW': 0.1, 'SIDE': 0.1,
    'SIZE': 0.1, 'STOP': 0.1, 'SURE': 0.05, 'TAKE': 0.05, 'TIME': 0.05, 'TURN': 0.1,
    'VIEW': 0.1, 'WALK': 0.1, 'WANT': 0.05, 'WEAR': 0.1, 'WEEK': 0.1, 'WELL': 0.05,
    'WILL': 0.05, 'WORK': 0.1, 'YEAR': 0.1, 'YOUR': 0.05,
    
    # Default weight for other symbols
    'default': 1.0
}

# ==============================================================================
# STOCK VALIDATION
# ==============================================================================

# Symbol validation
MIN_STOCK_SYMBOL_LENGTH = 1
MAX_STOCK_SYMBOL_LENGTH = 5
STOCK_SYMBOL_PATTERN = r'\b[A-Z]{1,5}\b'

# Validation caching
VALIDATOR_CACHE_SIZE = 1000
VALIDATION_TIMEOUT_SECONDS = 5.0

# Symbol counts
EXPECTED_NASDAQ_SYMBOLS = 3000
EXPECTED_AMEX_SYMBOLS = 1000
TOTAL_EXPECTED_SYMBOLS = 4278

# ==============================================================================
# WEB APPLICATION
# ==============================================================================

# Flask configuration
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
SECRET_KEY_LENGTH = 32

# HTTP response codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_ERROR = 500

# Web UI limits
MAX_STOCKS_DISPLAY = 50
DEFAULT_STOCKS_DISPLAY = 10
STOCK_DETAILS_LIMIT = 100

# ==============================================================================
# FILE SYSTEM PATHS
# ==============================================================================

# Directory names
DATA_DIR_NAME = "data"
JSON_DIR_NAME = "json"
LOGS_DIR_NAME = "logs"
SCRIPTS_DIR_NAME = "scripts"
TEMPLATES_DIR_NAME = "templates"
STATIC_DIR_NAME = "static"

# File names
NASDAQ_TICKERS_FILE = "nasdaq_tickers.json"
AMEX_TICKERS_FILE = "amex_tickers.json"
LOG_FILE_EXTENSION = ".log"

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

# Log levels
DEFAULT_LOG_LEVEL = "INFO"
DEBUG_LOG_LEVEL = "DEBUG"
ERROR_LOG_LEVEL = "ERROR"

# Log formatting
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MESSAGE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# Log file management
MAX_LOG_FILE_SIZE_MB = 10
LOG_BACKUP_COUNT = 5
LOG_ROTATION_WHEN = "midnight"

# ==============================================================================
# MONITORING AND HEALTH CHECKS
# ==============================================================================

# Health check intervals
HEALTH_CHECK_INTERVAL_SECONDS = 60
SERVICE_TIMEOUT_SECONDS = 30

# Performance thresholds
MAX_RESPONSE_TIME_MS = 5000
MAX_MEMORY_USAGE_MB = 500
MAX_CPU_USAGE_PERCENT = 80

# Error thresholds
MAX_ERROR_RATE_PERCENT = 5
MAX_CONSECUTIVE_ERRORS = 10

# ==============================================================================
# SUBREDDIT CATEGORIES
# ==============================================================================

# Primary financial subreddits
PRIMARY_US_SUBREDDITS: List[str] = [
    'wallstreetbets', 'stocks', 'investing', 'SecurityAnalysis',
    'ValueInvesting', 'dividends', 'StockMarket', 'financialindependence'
]

# Trading and options subreddits
TRADING_SUBREDDITS: List[str] = [
    'options', 'thetagang', 'daytrading', 'SwingTrading', 
    'pennystocks', 'RobinHood', 'smallstreetbets'
]

# International market subreddits
INTERNATIONAL_SUBREDDITS: List[str] = [
    'CanadianInvestor', 'AusFinance', 'IndiaInvestments', 'JapanFinance',
    'AsianStocks', 'EmergingMarkets', 'GlobalMarkets'
]

# European market subreddits
EUROPEAN_SUBREDDITS: List[str] = [
    'EuropeFIRE', 'UKInvesting', 'UKPersonalFinance', 'eupersonalfinance',
    'Finanzen', 'investing_discussion', 'SecurityAnalysisEU'
]

# All monitored subreddits combined
ALL_MONITORED_SUBREDDITS = (
    PRIMARY_US_SUBREDDITS + TRADING_SUBREDDITS + 
    INTERNATIONAL_SUBREDDITS + EUROPEAN_SUBREDDITS
)

# ==============================================================================
# SENTIMENT LEXICON
# ==============================================================================

# Bullish keywords and phrases
BULLISH_KEYWORDS: Set[str] = {
    'moon', 'rocket', 'surge', 'breakout', 'rally', 'pump',
    'diamond hands', 'hodl', 'to the moon', 'bull run',
    'buy', 'long', 'bull', 'bullish', 'strong', 'positive',
    'growth', 'gain', 'rise', 'up', 'green', 'calls',
    'hold', 'support', 'bounce', 'recovery',
    'beat earnings', 'exceed expectations', 'strong revenue',
    'good news', 'upgrade', 'outperform', 'overweight'
}

# Bearish keywords and phrases
BEARISH_KEYWORDS: Set[str] = {
    'crash', 'dump', 'panic sell', 'paper hands', 'rug pull',
    'dead cat bounce', 'bear trap', 'capitulation',
    'sell', 'short', 'bear', 'bearish', 'weak', 'negative',
    'loss', 'drop', 'fall', 'decline', 'down', 'red', 'puts',
    'resistance', 'breakdown', 'correction',
    'miss earnings', 'below expectations', 'weak revenue',
    'bad news', 'downgrade', 'underperform', 'underweight'
}

# False positive filter for stock symbol validation
FALSE_POSITIVE_SYMBOLS: Set[str] = {
    # Common English words (2-4 letters that appear as false stock symbols)
    'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER',
    'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW',
    'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID',
    'ANY', 'TECH', 'REAL', 'NEXT', 'OPEN', 'MOVE', 'GOOD', 'COST', 'CASH', 
    'LINE', 'STEP', 'HOPE', 'BEAT', 'PLAY', 'TALK', 'TEAM', 'FORM', 'CARE',
    'LOVE', 'LIVE', 'TRUE', 'NICE', 'ELSE', 'EVEN', 'EVER', 'FIVE', 'FOUR',
    'FREE', 'FULL', 'GAME', 'GIVE', 'GONE', 'GROW', 'HAND', 'HEAD', 'HELP',
    'HERE', 'HIGH', 'HOME', 'HOUR', 'HUGE', 'IDEA', 'INTO', 'ITEM', 'JUST',
    'KEEP', 'KIND', 'KNOW', 'LAND', 'LAST', 'LATE', 'LEFT', 'LESS', 'LIFE',
    'LIKE', 'LINK', 'LIST', 'LOOK', 'LOST', 'LOTS', 'MADE', 'MAKE', 'MANY',
    'MASS', 'MATH', 'MEAN', 'MIND', 'MODE', 'MORE', 'MOST', 'MUCH', 'MUST',
    'NAME', 'NEED', 'NEWS', 'NICE', 'ODDS', 'ONLY', 'OPEN', 'OVER', 'PAID',
    'PART', 'PAST', 'PATH', 'PICK', 'PLAN', 'PLUS', 'POOL', 'PORT', 'POST',
    'PROF', 'PUSH', 'RACE', 'RARE', 'RATE', 'READ', 'REST', 'RIDE', 'RISE',
    'RISK', 'ROAD', 'ROCK', 'ROLE', 'ROOM', 'RULE', 'SAFE', 'SAME', 'SAVE',
    'SEEM', 'SELF', 'SEND', 'SHOW', 'SIDE', 'SIZE', 'SLOW', 'SOME', 'SOON',
    'SORT', 'STOP', 'SUCH', 'SURE', 'TAKE', 'TELL', 'TEST', 'TEXT', 'THAN',
    'THAT', 'THEM', 'THEY', 'THIS', 'TIME', 'TOLD', 'TOOK', 'TOWN', 'TRIP',
    'TURN', 'TYPE', 'UNIT', 'USED', 'USER', 'VERY', 'VIEW', 'WAIT', 'WALK',
    'WANT', 'WAVE', 'WAYS', 'WEEK', 'WELL', 'WENT', 'WERE', 'WHAT', 'WHEN',
    'WILL', 'WITH', 'WORD', 'WORK', 'YEAR', 'YOUR', 'ZONE',
    
    # Social media abbreviations
    'LOL', 'OMG', 'WTF', 'TBH', 'IMO', 'YOLO', 'WSB', 'TLDR', 'ELI',
    'AMA', 'TIL', 'DAE', 'PSA', 'LPT', 'TIFU', 'HODL',
    
    # Financial terms (not stock symbols)
    'BUY', 'SELL', 'HOLD', 'LONG', 'SHORT', 'CALL', 'PUT', 'MOON',
    'BEAR', 'BULL', 'YOLO', 'FOMO', 'ATH', 'ATL', 'RSI', 'MACD',
    'FUND', 'APPS', 'CAPS', 'TOPS', 'GAIN', 'LOSS', 'HUGE', 'BOOM',
    'FAST', 'SLOW', 'HIGH', 'DOWN', 'PUMP', 'DUMP', 'IRON', 'GOLD',
    
    # Time references
    'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN',
    'JAN', 'FEB', 'MAR', 'APR', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'
}

# ==============================================================================
# ERROR CODES AND MESSAGES
# ==============================================================================

# Error code prefixes
ERROR_PREFIX_CONFIG = "CONFIG"
ERROR_PREFIX_REDDIT = "REDDIT"
ERROR_PREFIX_DATABASE = "DB"
ERROR_PREFIX_VALIDATION = "VALID"
ERROR_PREFIX_SENTIMENT = "SENT"
ERROR_PREFIX_SERVICE = "SVC"

# Common error codes
ERROR_CODE_INVALID_CONFIG = f"{ERROR_PREFIX_CONFIG}_001"
ERROR_CODE_REDDIT_API_FAIL = f"{ERROR_PREFIX_REDDIT}_001"
ERROR_CODE_DATABASE_CONN = f"{ERROR_PREFIX_DATABASE}_001"
ERROR_CODE_VALIDATION_FAIL = f"{ERROR_PREFIX_VALIDATION}_001"
ERROR_CODE_SENTIMENT_FAIL = f"{ERROR_PREFIX_SENTIMENT}_001"
ERROR_CODE_SERVICE_INIT = f"{ERROR_PREFIX_SERVICE}_001"

# ==============================================================================
# FEATURE FLAGS
# ==============================================================================

# Feature toggles for development and testing
FEATURE_FLAGS: Dict[str, bool] = {
    'ENABLE_FINBERT': True,            # Use FinBERT for sentiment analysis
    'ENABLE_BACKGROUND_COLLECTION': True,  # Background data collection
    'ENABLE_EMAIL_ALERTS': False,     # Email notification system
    'ENABLE_ENHANCED_LOGGING': True,  # Detailed logging
    'ENABLE_HEALTH_CHECKS': True,     # System health monitoring
    'ENABLE_PERFORMANCE_METRICS': False,  # Performance monitoring
    'ENABLE_DEBUG_MODE': False,       # Debug information display
    'ENABLE_AI_VALIDATOR': True,     # AI-powered stock validation (requires spaCy)
}

# ==============================================================================
# AI VALIDATOR CONFIGURATION
# ==============================================================================

# AI Validator settings (used when ENABLE_AI_VALIDATOR is True)
AI_VALIDATOR_MODEL: str = "en_core_web_sm"  # spaCy model for NER
AI_VALIDATOR_MIN_CONFIDENCE: float = 0.5    # Minimum confidence threshold
AI_VALIDATOR_COMBINE_MODE: str = "union"    # How to combine with current validator ("union", "intersection", "ai_priority")

# ==============================================================================
# PERFORMANCE TUNING
# ==============================================================================

# Memory management
MAX_MEMORY_CACHE_SIZE = 1000
CACHE_CLEANUP_INTERVAL = 3600  # 1 hour
MEMORY_WARNING_THRESHOLD_MB = 200

# Connection pooling
DATABASE_POOL_SIZE = 5
CONNECTION_TIMEOUT = 30
MAX_OVERFLOW = 10

# Processing limits
MAX_CONCURRENT_REQUESTS = 10
MAX_BATCH_SIZE = 1000
PROCESSING_TIMEOUT_SECONDS = 120

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def get_time_window_hours(window_type: str) -> int:
    """Get hours for different time window types"""
    windows = {
        'short': DEFAULT_HOURS_WINDOW,      # 24 hours
        'medium': 168,                      # 1 week  
        'long': EXTENDED_HOURS_WINDOW,      # 30 days
        'max': MAX_HOURS_WINDOW             # 1 year
    }
    return windows.get(window_type, DEFAULT_HOURS_WINDOW)

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature flag is enabled"""
    return FEATURE_FLAGS.get(feature_name, False)

def get_subreddits_by_category(category: str) -> List[str]:
    """Get subreddits by category name"""
    categories = {
        'primary_us': PRIMARY_US_SUBREDDITS,
        'trading': TRADING_SUBREDDITS,
        'international': INTERNATIONAL_SUBREDDITS,
        'european': EUROPEAN_SUBREDDITS,
        'all': ALL_MONITORED_SUBREDDITS
    }
    return categories.get(category, PRIMARY_US_SUBREDDITS)

def validate_constant_ranges():
    """Validate that all constants are within expected ranges"""
    validations = []
    
    # Validate sentiment thresholds
    if not (-1.0 <= SENTIMENT_BEARISH_THRESHOLD <= SENTIMENT_BULLISH_THRESHOLD <= 1.0):
        validations.append("Invalid sentiment thresholds")
    
    # Validate time intervals
    if not (MIN_COLLECTION_INTERVAL_MINUTES <= DEFAULT_COLLECTION_INTERVAL_MINUTES <= MAX_COLLECTION_INTERVAL_MINUTES):
        validations.append("Invalid collection interval")
    
    # Validate stock limits
    if not (1 <= DEFAULT_STOCK_LIMIT <= MAX_STOCK_LIMIT):
        validations.append("Invalid stock limits")
    
    return validations

# Validate constants on import
_validation_errors = validate_constant_ranges()
if _validation_errors:
    import warnings
    warnings.warn(f"Constant validation errors: {_validation_errors}")

# ==============================================================================
# CONSTANTS SUMMARY
# ==============================================================================

def get_constants_summary() -> Dict[str, any]:
    """Get a summary of all defined constants"""
    return {
        'app_info': {
            'name': APP_NAME,
            'version': APP_VERSION,
            'description': APP_DESCRIPTION
        },
        'database': {
            'timeout': DATABASE_TIMEOUT_SECONDS,
            'default_limit': DEFAULT_STOCK_LIMIT,
            'hours_window': DEFAULT_HOURS_WINDOW
        },
        'reddit': {
            'posts_per_subreddit': DEFAULT_POSTS_PER_SUBREDDIT,
            'api_delay': REDDIT_API_DELAY_SECONDS,
            'monitored_subreddits': len(ALL_MONITORED_SUBREDDITS)
        },
        'background_collection': {
            'interval_minutes': DEFAULT_COLLECTION_INTERVAL_MINUTES,
            'duration_minutes': DEFAULT_COLLECTION_DURATION_MINUTES
        },
        'sentiment': {
            'bullish_threshold': SENTIMENT_BULLISH_THRESHOLD,
            'bearish_threshold': SENTIMENT_BEARISH_THRESHOLD,
            'keywords_count': len(BULLISH_KEYWORDS) + len(BEARISH_KEYWORDS)
        },
        'validation': {
            'symbol_length_range': (MIN_STOCK_SYMBOL_LENGTH, MAX_STOCK_SYMBOL_LENGTH),
            'expected_symbols': TOTAL_EXPECTED_SYMBOLS,
            'false_positives': len(FALSE_POSITIVE_SYMBOLS)
        },
        'feature_flags': FEATURE_FLAGS
    }