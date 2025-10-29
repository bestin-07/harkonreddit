"""
API Routes Blueprint
Handles all JSON API endpoints for the StockHark application
"""

from flask import Blueprint, jsonify
import threading
import time
from datetime import datetime

from ...core.data import get_database_stats, get_top_stocks, get_db_connection, add_stock_data
from ...core.services.background_collector import get_collection_status, force_collection, collect_stock_data
from ...core.services.service_factory import get_service_factory

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Get service factory instance
factory = get_service_factory()

@api_bp.route('/status')
def status():
    """API status and background collection status"""
    try:
        # Get database stats
        db_stats = get_database_stats()
        
        # Get background collection status
        collection_status = get_collection_status()
        
        return jsonify({
            'status': 'success',
            'database': db_stats,
            'background_collection': collection_status,
            'api_version': '1.0'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/test')
def test():
    """Test API endpoint"""
    try:
        stocks = get_top_stocks(limit=5, hours=720)
        return jsonify({
            'status': 'success',
            'count': len(stocks),
            'first_stock': stocks[0] if stocks else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stocks')
def stocks():
    """API endpoint for stock data"""
    try:
        # Use 30-day window to capture historical data
        print(f"DEBUG: Calling get_top_stocks(limit=20, hours=720)")
        stocks = get_top_stocks(limit=20, hours=720)
        print(f"DEBUG: Got {len(stocks)} stocks")
        if len(stocks) == 0:
            print("DEBUG: No stocks returned - this is the problem!")
            # Try direct database query to debug
            stats = get_database_stats()
            print(f"DEBUG: Database stats: {stats}")
        return jsonify(stocks)
    except Exception as e:
        print(f"DEBUG: Error in api_stocks: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stock/<symbol>')
def stock_details(symbol):
    """API endpoint for detailed stock information"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get basic stock info
            cursor.execute('''
                SELECT symbol, COUNT(*) as mentions, 
                       AVG(sentiment) as avg_sentiment,
                       SUM(CASE WHEN sentiment_label = 'bullish' THEN 1 ELSE 0 END) as bullish,
                       SUM(CASE WHEN sentiment_label = 'bearish' THEN 1 ELSE 0 END) as bearish,
                       SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral,
                       MIN(timestamp) as first_mention,
                       MAX(timestamp) as last_mention
                FROM stock_data 
                WHERE symbol = ? 
                GROUP BY symbol
            ''', (symbol.upper(),))
            
            basic_info = cursor.fetchone()
            
            if not basic_info:
                return jsonify({'error': f'Stock {symbol} not found'}), 404

            symbol, mentions, avg_sentiment, bullish, bearish, neutral, first_mention, last_mention = basic_info
            
            # Get recent mentions with details
            cursor.execute('''
                SELECT timestamp, sentiment, sentiment_label, source, post_url
                FROM stock_data 
                WHERE symbol = ?
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (symbol.upper(),))
            
            recent_mentions = cursor.fetchall()
            
            # Get hourly activity for chart
            cursor.execute('''
                SELECT strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                       COUNT(*) as mentions,
                       AVG(sentiment) as avg_sentiment
                FROM stock_data 
                WHERE symbol = ? 
                AND timestamp >= datetime('now', '-24 hours')
                GROUP BY hour
                ORDER BY hour
            ''', (symbol.upper(),))
            
            hourly_activity = cursor.fetchall()
            
            # Get top sources
            cursor.execute('''
                SELECT source, COUNT(*) as mentions,
                       AVG(sentiment) as avg_sentiment
                FROM stock_data 
                WHERE symbol = ?
                GROUP BY source
                ORDER BY mentions DESC
                LIMIT 5
            ''', (symbol.upper(),))
            
            top_sources = cursor.fetchall()
            
            # Determine overall sentiment
            if avg_sentiment > 0.1:
                overall_sentiment = 'bullish'
            elif avg_sentiment < -0.1:
                overall_sentiment = 'bearish'
            else:
                overall_sentiment = 'neutral'
            
            # Format response
            stock_details = {
                'symbol': symbol,
                'basic_info': {
                    'mentions': mentions,
                    'avg_sentiment': round(avg_sentiment, 3),
                    'overall_sentiment': overall_sentiment,
                    'bullish': bullish,
                    'bearish': bearish,
                    'neutral': neutral,
                    'first_mention': first_mention,
                    'last_mention': last_mention
                },
                'recent_mentions': [
                    {
                        'timestamp': mention[0],
                        'sentiment': round(mention[1], 3),
                        'sentiment_label': mention[2],
                        'source': mention[3],
                        'post_url': mention[4]
                    }
                    for mention in recent_mentions
                ],
                'hourly_activity': [
                    {
                        'hour': hour[0],
                        'mentions': hour[1],
                        'avg_sentiment': round(hour[2], 3) if hour[2] else 0
                    }
                    for hour in hourly_activity
                ],
                'top_sources': [
                    {
                        'source': source[0],
                        'mentions': source[1],
                        'avg_sentiment': round(source[2], 3)
                    }
                    for source in top_sources
                ]
            }
            
            return jsonify(stock_details)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/refresh')
def refresh():
    """Manually trigger stock data refresh"""
    try:
        # Import the monitor function and run it in background
        from .business_logic import monitor_stocks
        threading.Thread(target=monitor_stocks, daemon=True).start()
        return jsonify({'status': 'enhanced refresh started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/collect-real-data')
def collect_real_data():
    """Trigger manual data collection using background collector"""
    try:
        # Trigger immediate collection via background collector
        force_collection()
        
        # Run manual collection in background
        def quick_collection():
            collect_stock_data(duration_minutes=5, posts_per_subreddit=15)
        
        threading.Thread(target=quick_collection, daemon=True).start()
        return jsonify({
            'status': 'real data collection started',
            'duration': '5 minutes',
            'message': 'Check console for progress updates'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500