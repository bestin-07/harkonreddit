import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
from ..config import DATABASE_PATH

DATABASE_FILE = str(DATABASE_PATH)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        # Create subscribers table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create stock_data table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stock_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                sentiment REAL NOT NULL,
                sentiment_label TEXT NOT NULL,
                mentions INTEGER DEFAULT 1,
                source TEXT NOT NULL,
                post_url TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_symbol 
            ON stock_data(symbol)
        ''')
        
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_stock_timestamp 
            ON stock_data(timestamp)
        ''')
        
        conn.commit()

def add_subscriber(email):
    """Add a new email subscriber"""
    with get_db_connection() as conn:
        conn.execute(
            'INSERT OR IGNORE INTO subscribers (email) VALUES (?)',
            (email,)
        )
        conn.commit()

def get_subscribers():
    """Get all active subscribers"""
    with get_db_connection() as conn:
        return conn.execute(
            'SELECT * FROM subscribers WHERE is_active = 1'
        ).fetchall()

def add_stock_data(symbol, sentiment, sentiment_label, mentions, source, post_url, timestamp):
    """Add stock data to the database"""
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO stock_data 
            (symbol, sentiment, sentiment_label, mentions, source, post_url, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (symbol, sentiment, sentiment_label, mentions, source, post_url, timestamp))
        conn.commit()

def get_top_stocks(limit=10, hours=24):
    """
    Get top stocks by mentions and sentiment in the specified time period
    
    Args:
        limit (int): Number of stocks to return
        hours (int): Time period in hours to look back
    
    Returns:
        list: List of stock dictionaries with aggregated data
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    with get_db_connection() as conn:
        results = conn.execute('''
            SELECT 
                symbol,
                COUNT(*) as mentions,
                AVG(sentiment) as avg_sentiment,
                MAX(sentiment) as max_sentiment,
                MIN(sentiment) as min_sentiment,
                GROUP_CONCAT(DISTINCT sentiment_label) as sentiment_labels,
                COUNT(DISTINCT post_url) as unique_posts,
                MAX(timestamp) as latest_mention
            FROM stock_data 
            WHERE timestamp >= ?
            GROUP BY symbol
            ORDER BY mentions DESC, ABS(avg_sentiment) DESC
            LIMIT ?
        ''', (cutoff_time, limit)).fetchall()
        
        stocks = []
        for row in results:
            # Determine overall sentiment label
            avg_sentiment = row['avg_sentiment']
            if avg_sentiment > 0.1:
                overall_sentiment = 'bullish'
            elif avg_sentiment < -0.1:
                overall_sentiment = 'bearish'
            else:
                overall_sentiment = 'neutral'
            
            stocks.append({
                'symbol': row['symbol'],
                'mentions': row['mentions'],
                'avg_sentiment': round(row['avg_sentiment'], 3),
                'max_sentiment': round(row['max_sentiment'], 3),
                'min_sentiment': round(row['min_sentiment'], 3),
                'overall_sentiment': overall_sentiment,
                'unique_posts': row['unique_posts'],
                'latest_mention': row['latest_mention'],
                'sentiment_strength': round(abs(row['avg_sentiment']), 3)
            })
        
        return stocks

def get_stock_history(symbol, days=7):
    """Get historical data for a specific stock"""
    cutoff_time = datetime.now() - timedelta(days=days)
    
    with get_db_connection() as conn:
        return conn.execute('''
            SELECT * FROM stock_data 
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (symbol, cutoff_time)).fetchall()

def get_recent_mentions(hours=1):
    """Get all stock mentions in the last specified hours"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    with get_db_connection() as conn:
        return conn.execute('''
            SELECT * FROM stock_data 
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (cutoff_time,)).fetchall()

def cleanup_old_data(days=30):
    """Remove data older than specified days"""
    cutoff_time = datetime.now() - timedelta(days=days)
    
    with get_db_connection() as conn:
        conn.execute(
            'DELETE FROM stock_data WHERE timestamp < ?',
            (cutoff_time,)
        )
        conn.commit()

def get_database_stats():
    """Get database statistics"""
    with get_db_connection() as conn:
        stock_count = conn.execute('SELECT COUNT(*) FROM stock_data').fetchone()[0]
        subscriber_count = conn.execute('SELECT COUNT(*) FROM subscribers WHERE is_active = 1').fetchone()[0]
        unique_stocks = conn.execute('SELECT COUNT(DISTINCT symbol) FROM stock_data').fetchone()[0]
        
        return {
            'total_mentions': stock_count,
            'active_subscribers': subscriber_count,
            'unique_stocks': unique_stocks
        }