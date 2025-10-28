from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_mail import Mail, Message
import sqlite3
import os
import threading
import time
from datetime import datetime, timedelta

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

from .monitoring.reddit_client import RedditMonitor
from .core.enhanced_sentiment import EnhancedSentimentAnalyzer
from .core.validator import StockValidator
from .core.database import init_db, add_subscriber, get_active_subscribers, add_stock_data, get_top_stocks
from .core.background_collector import start_background_collection, stop_background_collection, get_collection_status

app = Flask(__name__, 
           template_folder='web/templates',
           static_folder='web/static')

# Initialize extensions
mail = Mail(app)

# Initialize database
init_db()

# Initialize monitoring services
reddit_monitor = RedditMonitor()
sentiment_analyzer = EnhancedSentimentAnalyzer(enable_finbert=False)  # Start with rule-based, load FinBERT on demand
stock_validator = StockValidator(silent=True)  # Fast stock symbol validation

# Start background data collection
print("🔄 Starting background data collection...")
start_background_collection()
print("✅ Background data collection started")

# Template context processor to make datetime available in templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def index():
    """Main landing page showing top 10 hot stocks"""
    try:
        # Use 30-day window to capture historical data
        print(f"DEBUG: Calling get_top_stocks(limit=10, hours=720)")
        top_stocks = get_top_stocks(limit=10, hours=720)
        print(f"DEBUG: Got {len(top_stocks)} stocks for index")
        return render_template('index.html', stocks=top_stocks)
    except Exception as e:
        print(f"Error loading index: {e}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', stocks=[])

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    """Email subscription page"""
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            try:
                add_subscriber(email)
                flash('Successfully subscribed! You will receive alerts about hot stocks.', 'success')
                return redirect(url_for('subscribe'))
            except Exception as e:
                flash('Error subscribing. Please try again.', 'error')
        else:
            flash('Please enter a valid email address.', 'error')
    
    return render_template('subscribe.html')

@app.route('/methodology')
def methodology():
    """Sentiment analysis methodology explanation page"""
    return render_template('sentiment_methodology.html')

@app.route('/api/status')
def api_status():
    """API status and background collection status"""
    try:
        from .core.database import get_database_stats
        
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

@app.route('/api/test')
def api_test():
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

@app.route('/api/stocks')
def api_stocks():
    """API endpoint for stock data"""
    try:
        # Use 30-day window to capture historical data
        print(f"DEBUG: Calling get_top_stocks(limit=20, hours=720)")
        stocks = get_top_stocks(limit=20, hours=720)
        print(f"DEBUG: Got {len(stocks)} stocks")
        if len(stocks) == 0:
            print("DEBUG: No stocks returned - this is the problem!")
            # Try direct database query to debug
            from .core.database import get_database_stats
            stats = get_database_stats()
            print(f"DEBUG: Database stats: {stats}")
        return jsonify(stocks)
    except Exception as e:
        print(f"DEBUG: Error in api_stocks: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<symbol>')
def api_stock_details(symbol):
    """API endpoint for detailed stock information"""
    try:
        from .core.database import get_db_connection
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

            symbol, mentions, avg_sentiment, bullish, bearish, neutral, first_mention, last_mention = basic_info            # Get recent mentions with details
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

@app.route('/api/refresh')
def api_refresh():
    """Manually trigger stock data refresh"""
    try:
        # Run enhanced monitoring in background
        threading.Thread(target=monitor_stocks, daemon=True).start()
        return jsonify({'status': 'enhanced refresh started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/collect-real-data')
def api_collect_real_data():
    """Trigger manual data collection using background collector"""
    try:
        # Trigger immediate collection via background collector
        from .core.background_collector import force_collection
        force_collection()
        
        # Run manual collection in background
        def quick_collection():
            from .core.background_collector import collect_stock_data
            collect_stock_data(duration_minutes=5, posts_per_subreddit=15)
        
        threading.Thread(target=quick_collection, daemon=True).start()
        return jsonify({
            'status': 'real data collection started',
            'duration': '5 minutes',
            'message': 'Check console for progress updates'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def monitor_stocks():
    """Enhanced background task to monitor Reddit for stock mentions using global coverage"""
    try:
        print("🌍 Starting enhanced stock monitoring...")
        
        # Use enhanced monitoring with multiple categories
        categories = ['primary_us', 'european', 'trading', 'tech_focused']
        
        for category in categories:
            try:
                print(f"📊 Monitoring {category}...")
                
                # Get posts from this category using enhanced monitoring
                posts = reddit_monitor.get_enhanced_hot_posts(categories=[category], limit=20)
                
                posts_processed = 0
                stocks_found = 0
                
                # Analyze sentiment for each post
                for post in posts:
                    # Get full text including comments for better analysis
                    full_text = post['title'] + ' ' + post.get('content', '')
                    if post.get('comments'):
                        full_text += ' ' + ' '.join(post['comments'][:2])  # Add top 2 comments
                    
                    # Extract and validate stocks
                    stocks_mentioned = stock_validator.extract_and_validate(full_text)
                    
                    for stock in stocks_mentioned:
                        # Use comprehensive sentiment analysis
                        sentiment_result = sentiment_analyzer.analyze_post_comprehensive(
                            full_text, 
                            timestamp=post.get('created_utc')
                        )
                        
                        # Get sentiment for this specific stock
                        stock_sentiment = sentiment_result['stock_sentiments'].get(stock, 0.0)
                        sentiment_label = 'bullish' if stock_sentiment > 0.1 else 'bearish' if stock_sentiment < -0.1 else 'neutral'
                        
                        # Store in database with enhanced metadata
                        add_stock_data(
                            symbol=stock,
                            sentiment=stock_sentiment,
                            sentiment_label=sentiment_label,
                            confidence=sentiment_result['analysis']['confidence'],
                            mentions=1,
                            source=f"reddit/r/{post['subreddit']}",
                            post_url=post['url'],
                            timestamp=post.get('created_utc', datetime.now())
                        )
                        
                        stocks_found += 1
                    
                    posts_processed += 1
                
                print(f"✅ {category}: {posts_processed} posts → {stocks_found} stock mentions")
                
                # Small delay between categories to be respectful
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Error in {category}: {e}")
                continue
        
        # Check for alert conditions and send emails
        check_and_send_alerts()
        
        print("✅ Enhanced stock monitoring completed")
        
    except Exception as e:
        print(f"❌ Error in stock monitoring: {e}")

def check_and_send_alerts():
    """Check for stocks that meet alert criteria and send emails"""
    try:
        # Get stocks with high activity in last hour
        hot_stocks = get_top_stocks(limit=5, hours=1)
        
        # Filter stocks that meet alert criteria (high mentions + strong sentiment)
        alert_stocks = [stock for stock in hot_stocks 
                       if stock['mentions'] >= 10 and abs(stock['avg_sentiment']) >= 0.3]
        
        if alert_stocks:
            subscribers = get_active_subscribers()
            for subscriber in subscribers:
                send_alert_email(subscriber['email'], alert_stocks)
                
    except Exception as e:
        print(f"Error checking alerts: {e}")

def send_alert_email(email, stocks):
    """Send alert email to subscriber"""
    try:
        msg = Message(
            'Stock Alert: Hot Stocks Detected!',
            #sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email]
        )
        
        msg.html = render_template('email_alert.html', stocks=stocks)
        mail.send(msg)
        
    except Exception as e:
        print(f"Error sending email to {email}: {e}")

def run_periodic_monitoring():
    """Run enhanced monitoring every 20 minutes"""
    while True:
        try:
            print(f"🔄 Periodic monitoring at {datetime.now().strftime('%H:%M:%S')}")
            monitor_stocks()
            
            # Show current stats
            from .core.database import get_database_stats
            stats = get_database_stats()
            print(f"📊 Database: {stats['total_mentions']} mentions, {stats['unique_stocks']} unique stocks")
            
        except Exception as e:
            print(f"❌ Periodic monitoring error: {e}")
        
        time.sleep(1200)  # 20 minutes

def shutdown_background_services():
    """Shutdown background services gracefully"""
    print("🛑 Shutting down background services...")
    stop_background_collection()
    print("✅ Background services stopped")

def create_app():
    """Create and configure the Flask application"""
    print("🚀 Initializing StockHark with Background Data Collection")
    
    # Initialize database
    init_db()
    
    # Start background collection
    start_background_collection()
    
    # Show startup info
    from .core.database import get_database_stats
    stats = get_database_stats()
    print(f"📊 Database: {stats['total_mentions']} mentions, {stats['unique_stocks']} stocks")
    print(f"🔄 Background collection active (30min intervals)")
    
    return app

import atexit
atexit.register(shutdown_background_services)

if __name__ == '__main__':
    try:
        flask_app = create_app()
        print(f"🌐 Starting server at http://127.0.0.1:5000")
        flask_app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down StockHark...")
        shutdown_background_services()