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
from .core.validator import OptimizedSentimentAnalyzer
from .core.database import init_db, add_subscriber, get_subscribers, add_stock_data, get_top_stocks

app = Flask(__name__, 
           template_folder='web/templates',
           static_folder='web/static')

# Initialize extensions
mail = Mail(app)

# Initialize database
init_db()

# Initialize monitoring services
reddit_monitor = RedditMonitor()
sentiment_analyzer = OptimizedSentimentAnalyzer()  # Ultra-fast validation with JSON files

# Template context processor to make datetime available in templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/')
def index():
    """Main landing page showing top 10 hot stocks"""
    try:
        top_stocks = get_top_stocks(limit=10)
        return render_template('index.html', stocks=top_stocks)
    except Exception as e:
        print(f"Error loading index: {e}")
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

@app.route('/api/stocks')
def api_stocks():
    """API endpoint for stock data"""
    try:
        stocks = get_top_stocks(limit=20)
        return jsonify(stocks)
    except Exception as e:
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
    """Trigger real data collection (5-minute quick collection)"""
    try:
        def quick_collection():
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
            from collect_data import collect_real_data
            collect_real_data(duration_minutes=5, max_posts_per_category=15)
        
        # Run collection in background
        threading.Thread(target=quick_collection, daemon=True).start()
        return jsonify({
            'status': 'real data collection started',
            'duration': '5 minutes',
            'message': 'Check console for progress updates'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """Show system status and configuration"""
    try:
        from .core.database import get_database_stats
        db_stats = get_database_stats()
        
        # Check if validation is enabled
        validation_enabled = hasattr(sentiment_analyzer, 'fast_validator') and sentiment_analyzer.fast_validator is not None
        
        # Get subreddit stats
        subreddit_stats = reddit_monitor.get_subreddit_stats()
        
        return jsonify({
            'stock_validation': {
                'enabled': validation_enabled,
                'validator_type': 'fast_json_validator' if validation_enabled else None,
                'symbols_loaded': len(sentiment_analyzer.fast_validator.all_symbols) if validation_enabled else 0,
                'speed': '0.00ms per symbol'
            },
            'database': db_stats,
            'monitoring': {
                'total_subreddits': subreddit_stats['total'],
                'categories': len(subreddit_stats) - 1,  # -1 for 'total' key
                'enhanced_monitoring': True
            },
            'timestamp': datetime.now().isoformat()
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
                    
                    # Extract stocks with enhanced detection
                    stocks_mentioned = sentiment_analyzer.extract_stock_symbols(full_text)
                    
                    for stock in stocks_mentioned:
                        # Use context-aware sentiment analysis
                        sentiment = sentiment_analyzer.get_stock_context_sentiment(full_text, stock)
                        
                        # Store in database with enhanced metadata
                        add_stock_data(
                            symbol=stock,
                            sentiment=sentiment['score'],
                            sentiment_label=sentiment['label'],
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
            subscribers = get_subscribers()
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

if __name__ == '__main__':
    # Start background monitoring
    monitoring_thread = threading.Thread(target=run_periodic_monitoring, daemon=True)
    monitoring_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)