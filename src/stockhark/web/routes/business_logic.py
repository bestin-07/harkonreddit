"""
Business Logic Module
Contains business operations and background processing logic
separated from route handlers for better organization
"""

import time
import threading
from datetime import datetime
from flask import render_template
from flask_mail import Message

from ...core.data import add_stock_data, get_top_stocks, get_active_subscribers
from ...core.services.service_factory import get_service_factory

# Get service factory instance
factory = get_service_factory()

def _get_posts_from_subreddits(reddit_client, subreddit_names, limit=20):
    """Get posts from multiple subreddits using core Reddit client"""
    posts = []
    
    for subreddit_name in subreddit_names:
        try:
            subreddit = reddit_client.subreddit(subreddit_name)
            
            for post in subreddit.hot(limit=limit):
                if post.stickied:
                    continue
                
                # Get post content
                content = post.selftext if hasattr(post, 'selftext') else ''
                
                # Get top comments
                post.comments.replace_more(limit=5)
                top_comments = []
                for comment in post.comments[:10]:
                    if hasattr(comment, 'body'):
                        top_comments.append(comment.body)
                
                posts.append({
                    'id': post.id,
                    'title': post.title,
                    'content': content,
                    'comments': top_comments,
                    'score': post.score,
                    'upvote_ratio': post.upvote_ratio,
                    'num_comments': post.num_comments,
                    'created_utc': datetime.fromtimestamp(post.created_utc),
                    'url': f"https://reddit.com{post.permalink}",
                    'subreddit': subreddit_name,
                    'author': str(post.author) if post.author else '[deleted]'
                })
                
        except Exception as e:
            print(f"Error fetching posts from r/{subreddit_name}: {e}")
            continue
    
    return posts

def monitor_stocks():
    """Enhanced background task to monitor Reddit for stock mentions using global coverage"""
    try:
        print("🌍 Starting enhanced stock monitoring...")
        
        # Get services from factory
        reddit_client = factory.get_reddit_client()
        sentiment_analyzer = factory.get_sentiment_analyzer(enable_finbert=False)
        stock_validator = factory.get_stock_validator()
        
        # Define subreddit categories directly (no need for monitoring wrapper)
        subreddit_categories = {
            'primary_us': ['wallstreetbets', 'stocks', 'investing'],
            'european': ['EuropeFIRE', 'UKInvesting', 'eupersonalfinance'],
            'trading': ['options', 'thetagang', 'daytrading', 'pennystocks'],
            'tech_focused': ['technology', 'artificial', 'startups']
        }
        
        for category, subreddits in subreddit_categories.items():
            try:
                print(f"📊 Monitoring {category}...")
                
                # Get posts directly from Reddit client
                posts = _get_posts_from_subreddits(reddit_client, subreddits, limit=20)
                
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

def send_alert_email(email, stocks, mail_instance=None):
    """Send alert email to subscriber"""
    try:
        if mail_instance is None:
            # This will be passed from the main app when called
            print(f"Would send alert email to {email} for {len(stocks)} stocks")
            return
            
        msg = Message(
            'Stock Alert: Hot Stocks Detected!',
            recipients=[email]
        )
        
        msg.html = render_template('email_alert.html', stocks=stocks)
        mail_instance.send(msg)
        
    except Exception as e:
        print(f"Error sending email to {email}: {e}")

def run_periodic_monitoring():
    """Run enhanced monitoring every 20 minutes"""
    while True:
        try:
            print(f"🔄 Periodic monitoring at {datetime.now().strftime('%H:%M:%S')}")
            monitor_stocks()
            
            # Show current stats
            from ...core.data import get_database_stats
            stats = get_database_stats()
            print(f"📊 Database: {stats['total_mentions']} mentions, {stats['unique_stocks']} unique stocks")
            
        except Exception as e:
            print(f"❌ Periodic monitoring error: {e}")
        
        time.sleep(1200)  # 20 minutes