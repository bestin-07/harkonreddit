"""
Database Operations Module

Efficient SQLite database management for stock sentiment data and subscriptions.
Provides connection pooling, transaction management, and optimized queries.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import List, Dict, Optional, Any, Tuple
try:
    from ...config import DATABASE_PATH
    from ..constants import MIN_STOCK_MENTIONS, MIN_UNIQUE_POSTS
except ImportError:
    from config import DATABASE_PATH
    # Fallback defaults if constants not available
    MIN_STOCK_MENTIONS = 5
    MIN_UNIQUE_POSTS = 2

# Database configuration
DATABASE_FILE = str(DATABASE_PATH)
CONNECTION_TIMEOUT = 30.0  # seconds
MAX_VARIABLE_NUMBER = 999  # SQLite limit for variables in single query

@contextmanager
def get_db_connection():
    """
    Thread-safe database connection context manager
    
    Yields:
        sqlite3.Connection: Database connection with Row factory
    """
    conn = None
    try:
        conn = sqlite3.connect(
            DATABASE_FILE, 
            timeout=CONNECTION_TIMEOUT,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        # Enable foreign keys and WAL mode for better performance
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA journal_mode = WAL')
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# Subscriber Management Functions

def add_subscriber(email: str, preferences: Optional[str] = None) -> bool:
    """
    Add new email subscriber with optional preferences
    
    Args:
        email: Subscriber email address
        preferences: JSON string of user preferences
        
    Returns:
        bool: True if successfully added, False if already exists
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                'INSERT OR IGNORE INTO subscribers (email, preferences) VALUES (?, ?)',
                (email.lower().strip(), preferences or '{}')
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error:
        return False

def get_active_subscribers() -> List[sqlite3.Row]:
    """
    Get all active subscribers for notifications
    
    Returns:
        List of active subscriber records
    """
    with get_db_connection() as conn:
        return conn.execute('''
            SELECT id, email, preferences, last_notification 
            FROM subscribers 
            WHERE is_active = 1
            ORDER BY created_at ASC
        ''').fetchall()

def update_subscriber_notification(subscriber_id: int) -> None:
    """Update last notification timestamp for subscriber"""
    with get_db_connection() as conn:
        conn.execute(
            'UPDATE subscribers SET last_notification = CURRENT_TIMESTAMP WHERE id = ?',
            (subscriber_id,)
        )
        conn.commit()

# Stock Data Management Functions

def add_stock_data_batch(stock_records: List[Dict[str, Any]]) -> int:
    """
    Efficiently add multiple stock data records
    
    Args:
        stock_records: List of stock data dictionaries
        
    Returns:
        Number of records inserted
    """
    if not stock_records:
        return 0
    
    # Prepare batch insert data
    insert_data = []
    for record in stock_records:
        insert_data.append((
            record['symbol'].upper(),
            record['sentiment'],
            record['sentiment_label'],
            record.get('confidence', 0.0),
            record.get('mentions', 1),
            record['source'],
            record.get('post_url'),
            record.get('post_id'),
            record['timestamp']
        ))
    
    try:
        with get_db_connection() as conn:
            cursor = conn.executemany('''
                INSERT INTO stock_data 
                (symbol, sentiment, sentiment_label, confidence, mentions, 
                 source, post_url, post_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', insert_data)
            conn.commit()
            return cursor.rowcount
    except sqlite3.Error:
        return 0

def add_stock_data(symbol: str, sentiment: float, sentiment_label: str, 
                  mentions: int = 1, source: str = 'reddit', 
                  post_url: Optional[str] = None, post_id: Optional[str] = None,
                  timestamp: Optional[str] = None, confidence: float = 0.0) -> bool:
    """
    Add single stock data record
    
    Args:
        symbol: Stock symbol (will be converted to uppercase)
        sentiment: Sentiment score (-1.0 to 1.0)
        sentiment_label: 'bullish', 'bearish', or 'neutral'
        mentions: Number of mentions in post
        source: Data source identifier
        post_url: URL of source post
        post_id: Unique post identifier
        timestamp: ISO timestamp string
        confidence: Confidence score (0.0 to 1.0)
        
    Returns:
        bool: True if successfully added
    """
    try:
        timestamp = timestamp or datetime.now().isoformat()
        
        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO stock_data 
                (symbol, sentiment, sentiment_label, confidence, mentions, 
                 source, post_url, post_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol.upper(), sentiment, sentiment_label, confidence, 
                  mentions, source, post_url, post_id, timestamp))
            conn.commit()
            return True
    except sqlite3.Error:
        return False

# Stock Query Functions

def get_top_stocks(limit: int = 10, hours: int = 24, 
                  min_mentions: int = None, min_unique_posts: int = None) -> List[Dict[str, Any]]:
    """
    Get top stocks ranked by mentions and sentiment strength
    
    Args:
        limit: Maximum number of stocks to return
        hours: Time period in hours to analyze
        min_mentions: Minimum mentions required for inclusion (default: MIN_STOCK_MENTIONS)
        min_unique_posts: Minimum unique posts required (default: MIN_UNIQUE_POSTS)
        
    Returns:
        List of stock dictionaries with comprehensive metrics
    """
    # Use constants as defaults if not specified
    if min_mentions is None:
        min_mentions = MIN_STOCK_MENTIONS
    if min_unique_posts is None:
        min_unique_posts = MIN_UNIQUE_POSTS
        
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    with get_db_connection() as conn:
        results = conn.execute('''
            SELECT 
                symbol,
                COUNT(*) as total_mentions,
                AVG(sentiment) as avg_sentiment,
                AVG(confidence) as avg_confidence,
                MAX(sentiment) as max_sentiment,
                MIN(sentiment) as min_sentiment,
                (MAX(sentiment) - MIN(sentiment)) as sentiment_range,
                COUNT(DISTINCT COALESCE(post_url, source)) as unique_posts,
                COUNT(DISTINCT source) as source_count,
                MAX(timestamp) as latest_mention,
                MIN(timestamp) as first_mention,
                
                -- Sentiment distribution
                SUM(CASE WHEN sentiment_label = 'bullish' THEN 1 ELSE 0 END) as bullish_count,
                SUM(CASE WHEN sentiment_label = 'bearish' THEN 1 ELSE 0 END) as bearish_count,
                SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                
            FROM stock_data 
            WHERE timestamp >= ? 
            GROUP BY symbol
            HAVING COUNT(*) >= ? AND COUNT(DISTINCT COALESCE(post_url, source)) >= ?
            ORDER BY 
                avg_sentiment DESC,
                total_mentions DESC,
                avg_confidence DESC
            LIMIT ?
        ''', (cutoff_time, min_mentions, min_unique_posts, limit)).fetchall()
        
        return [_format_stock_result(row) for row in results]

def get_stock_details(symbol: str, days: int = 7) -> Optional[Dict[str, Any]]:
    """
    Get detailed analysis for specific stock
    
    Args:
        symbol: Stock symbol to analyze
        days: Number of days of history to include
        
    Returns:
        Detailed stock analysis or None if not found
    """
    cutoff_time = datetime.now() - timedelta(days=days)
    symbol = symbol.upper()
    
    with get_db_connection() as conn:
        # Get aggregate statistics
        summary = conn.execute('''
            SELECT 
                symbol,
                COUNT(*) as total_mentions,
                AVG(sentiment) as avg_sentiment,
                AVG(confidence) as avg_confidence,
                MAX(sentiment) as max_sentiment,
                MIN(sentiment) as min_sentiment,
                COUNT(DISTINCT post_url) as unique_posts,
                MAX(timestamp) as latest_mention,
                MIN(timestamp) as first_mention,
                
                -- Sentiment counts
                SUM(CASE WHEN sentiment_label = 'bullish' THEN 1 ELSE 0 END) as bullish_count,
                SUM(CASE WHEN sentiment_label = 'bearish' THEN 1 ELSE 0 END) as bearish_count,
                SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                
            FROM stock_data 
            WHERE symbol = ? AND timestamp >= ?
            GROUP BY symbol
        ''', (symbol, cutoff_time)).fetchone()
        
        if not summary:
            return None
        
        # Get recent mentions for timeline
        recent_mentions = conn.execute('''
            SELECT timestamp, sentiment, sentiment_label, source, post_url, confidence
            FROM stock_data 
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 20
        ''', (symbol, cutoff_time)).fetchall()
        
        return {
            'summary': _format_stock_result(summary),
            'recent_mentions': [dict(mention) for mention in recent_mentions]
        }

def _safe_get(row: sqlite3.Row, key: str, default: Any = None) -> Any:
    """Safely get value from sqlite3.Row with fallback"""
    try:
        return row[key]
    except (KeyError, IndexError):
        return default

def _format_stock_result(row: sqlite3.Row) -> Dict[str, Any]:
    """Format database row into comprehensive stock result"""
    avg_sentiment = row['avg_sentiment']
    
    # Determine overall sentiment label
    if avg_sentiment > 0.1:
        overall_sentiment = 'bullish'
    elif avg_sentiment < -0.1:
        overall_sentiment = 'bearish'
    else:
        overall_sentiment = 'neutral'
    
    return {
        'symbol': row['symbol'],
        'total_mentions': row['total_mentions'],
        'avg_sentiment': round(avg_sentiment, 3),
        'avg_confidence': round(_safe_get(row, 'avg_confidence', 0.0), 3),
        'max_sentiment': round(row['max_sentiment'], 3),
        'min_sentiment': round(row['min_sentiment'], 3),
        'sentiment_range': round(_safe_get(row, 'sentiment_range', 0.0), 3),
        'overall_sentiment': overall_sentiment,
        'sentiment_strength': round(abs(avg_sentiment), 3),
        'unique_posts': row['unique_posts'],
        'source_count': _safe_get(row, 'source_count', 1),
        'latest_mention': row['latest_mention'],
        'first_mention': _safe_get(row, 'first_mention'),
        
        # Sentiment distribution
        'bullish_count': _safe_get(row, 'bullish_count', 0),
        'bearish_count': _safe_get(row, 'bearish_count', 0),
        'neutral_count': _safe_get(row, 'neutral_count', 0)
    }

def get_recent_activity(hours: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent stock mentions for activity feed
    
    Args:
        hours: Hours to look back
        limit: Maximum results to return
        
    Returns:
        List of recent stock mentions
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    with get_db_connection() as conn:
        results = conn.execute('''
            SELECT symbol, sentiment, sentiment_label, confidence, 
                   source, post_url, timestamp
            FROM stock_data 
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (cutoff_time, limit)).fetchall()
        
        return [dict(row) for row in results]

def get_trending_stocks(hours: int = 6, min_mentions: int = 3) -> List[Dict[str, Any]]:
    """
    Get stocks with increasing mention velocity
    
    Args:
        hours: Time window for trend analysis
        min_mentions: Minimum mentions in period
        
    Returns:
        List of trending stocks with velocity metrics
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)
    half_period = datetime.now() - timedelta(hours=hours//2)
    
    with get_db_connection() as conn:
        results = conn.execute('''
            SELECT 
                symbol,
                COUNT(*) as total_mentions,
                AVG(sentiment) as avg_sentiment,
                
                -- Recent vs older mentions
                SUM(CASE WHEN timestamp >= ? THEN 1 ELSE 0 END) as recent_mentions,
                SUM(CASE WHEN timestamp < ? THEN 1 ELSE 0 END) as older_mentions,
                
                -- Calculate velocity (mentions per hour)
                CAST(COUNT(*) AS REAL) / ? as mention_velocity
                
            FROM stock_data 
            WHERE timestamp >= ?
            GROUP BY symbol
            HAVING COUNT(*) >= ?
            ORDER BY mention_velocity DESC, ABS(avg_sentiment) DESC
            LIMIT 20
        ''', (half_period, half_period, hours, cutoff_time, min_mentions)).fetchall()
        
        trending = []
        for row in results:
            # Calculate trend direction
            recent = row['recent_mentions']
            older = row['older_mentions'] or 1  # Avoid division by zero
            trend_ratio = recent / older
            
            trending.append({
                'symbol': row['symbol'],
                'total_mentions': row['total_mentions'],
                'avg_sentiment': round(row['avg_sentiment'], 3),
                'mention_velocity': round(row['mention_velocity'], 2),
                'trend_ratio': round(trend_ratio, 2),
                'trending': trend_ratio > 1.5  # More than 50% increase
            })
        
        return trending

# Database Maintenance Functions

def cleanup_old_data(days: int = 30) -> int:
    """
    Remove stock data older than specified days
    
    Args:
        days: Number of days to retain
        
    Returns:
        Number of records deleted
    """
    cutoff_time = datetime.now() - timedelta(days=days)
    
    with get_db_connection() as conn:
        cursor = conn.execute(
            'DELETE FROM stock_data WHERE timestamp < ?',
            (cutoff_time,)
        )
        conn.commit()
        return cursor.rowcount

def vacuum_database() -> None:
    """Optimize database by reclaiming space and updating statistics"""
    with get_db_connection() as conn:
        conn.execute('VACUUM')
        conn.execute('ANALYZE')

def get_database_stats() -> Dict[str, Any]:
    """
    Get comprehensive database statistics
    
    Returns:
        Dictionary with database metrics
    """
    with get_db_connection() as conn:
        # Basic counts
        stats = conn.execute('''
            SELECT 
                (SELECT COUNT(*) FROM stock_data) as total_mentions,
                (SELECT COUNT(*) FROM subscribers WHERE is_active = 1) as active_subscribers,
                (SELECT COUNT(DISTINCT symbol) FROM stock_data) as unique_stocks,
                (SELECT COUNT(DISTINCT source) FROM stock_data) as unique_sources
        ''').fetchone()
        
        # Recent activity (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_stats = conn.execute('''
            SELECT 
                COUNT(*) as mentions_24h,
                COUNT(DISTINCT symbol) as stocks_24h,
                AVG(sentiment) as avg_sentiment_24h
            FROM stock_data 
            WHERE timestamp >= ?
        ''', (yesterday,)).fetchone()
        
        # Database size info
        db_info = conn.execute('''
            SELECT 
                page_count * page_size as database_size,
                page_count,
                page_size
            FROM pragma_page_count(), pragma_page_size()
        ''').fetchone()
        
        return {
            'total_mentions': stats['total_mentions'],
            'active_subscribers': stats['active_subscribers'],
            'unique_stocks': stats['unique_stocks'],
            'unique_sources': stats['unique_sources'],
            'mentions_24h': recent_stats['mentions_24h'],
            'stocks_24h': recent_stats['stocks_24h'],
            'avg_sentiment_24h': round(recent_stats['avg_sentiment_24h'] or 0, 3),
            'database_size_mb': round(db_info['database_size'] / 1024 / 1024, 2),
            'last_updated': datetime.now().isoformat()
        }

# Database Migration Functions

def migrate_database() -> None:
    """Apply database migrations for schema updates"""
    with get_db_connection() as conn:
        # Check if confidence column exists in stock_data table
        cursor = conn.execute("PRAGMA table_info(stock_data)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add confidence column if it doesn't exist
        if 'confidence' not in columns:
            conn.execute('ALTER TABLE stock_data ADD COLUMN confidence REAL DEFAULT 0.0')
            print("   📊 Added 'confidence' column to stock_data table")
        
        # Add post_id column if it doesn't exist
        if 'post_id' not in columns:
            conn.execute('ALTER TABLE stock_data ADD COLUMN post_id TEXT')
            print("   📊 Added 'post_id' column to stock_data table")
        
        conn.commit()

# Utility function for backwards compatibility
def init_db():  
    """
    Initialize database with required tables, indexes, and apply migrations
    Creates optimized schema for high-performance stock data operations
    """
    # First, create all tables and indexes
    with get_db_connection() as conn:
        # Subscribers table for email alerts
        conn.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                preferences TEXT DEFAULT '{}',
                last_notification TIMESTAMP
            )
        ''')
        
        # Enhanced stock_data table with better normalization
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                sentiment REAL NOT NULL,
                sentiment_label TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                mentions INTEGER DEFAULT 1,
                source TEXT NOT NULL,
                post_url TEXT,
                post_id TEXT,
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Add constraints
                CHECK (sentiment >= -1.0 AND sentiment <= 1.0),
                CHECK (confidence >= 0.0 AND confidence <= 1.0),
                CHECK (sentiment_label IN ('bullish', 'bearish', 'neutral'))
            )
        ''')
        
        # Create optimized indexes for common query patterns
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_stock_symbol ON stock_data(symbol)',
            'CREATE INDEX IF NOT EXISTS idx_stock_timestamp ON stock_data(timestamp DESC)',
            'CREATE INDEX IF NOT EXISTS idx_stock_symbol_timestamp ON stock_data(symbol, timestamp DESC)',
            'CREATE INDEX IF NOT EXISTS idx_sentiment_label ON stock_data(sentiment_label)',
            'CREATE INDEX IF NOT EXISTS idx_source ON stock_data(source)',
            'CREATE INDEX IF NOT EXISTS idx_post_url ON stock_data(post_url)',
            'CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers(is_active, email)'
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
    
    # Apply any necessary migrations
    migrate_database()