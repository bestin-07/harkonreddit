#!/usr/bin/env python3
"""
Real Data Collection for StockHark
Populate database with actual Reddit data using enhanced monitoring
"""

import os
import sys
from datetime import datetime, timedelta
import time
import threading

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from reddit_monitor import RedditMonitor
from fast_stock_validator import OptimizedSentimentAnalyzer
from database import init_db, add_stock_data, get_top_stocks, get_database_stats

def show_spinner(message, stop_event):
    """Show a spinner while processing"""
    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    while not stop_event.is_set():
        print(f'\r{spinner_chars[i % len(spinner_chars)]} {message}', end='', flush=True)
        time.sleep(0.1)
        i += 1
    print('\r' + ' ' * (len(message) + 2) + '\r', end='', flush=True)  # Clear the line

def collect_real_data(duration_minutes=30, max_posts_per_category=50):
    """
    Collect real Reddit data for specified duration
    
    Args:
        duration_minutes: How long to collect data
        max_posts_per_category: Max posts to collect per subreddit category
    """
    print("🚀 StockHark Real Data Collection")
    print("=" * 60)
    
    # Show initialization progress
    print("⏳ Initializing components...")
    print("   🔧 Setting up database connection...")
    time.sleep(0.5)  # Brief pause for visibility
    
    # Initialize components with progress indicators
    init_db()
    print("   ✅ Database initialized")
    
    # Reddit monitor with spinner
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_spinner, args=("Connecting to Reddit API...", stop_event))
    spinner_thread.start()
    
    reddit_monitor = RedditMonitor()
    
    stop_event.set()
    spinner_thread.join()
    print("   ✅ Reddit monitor ready")
    
    # Sentiment analyzer with spinner
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_spinner, args=("Loading sentiment analyzer & stock validator...", stop_event))
    spinner_thread.start()
    
    sentiment_analyzer = OptimizedSentimentAnalyzer()  # Ultra-fast validation with JSON files
    
    stop_event.set()
    spinner_thread.join()
    print("   ✅ Sentiment analyzer with fast stock validation ready")
    
    # Show configuration
    print(f"\n📋 Collection Configuration:")
    print(f"   ⏱️  Duration: {duration_minutes} minutes")
    print(f"   📊 Max Posts per Category: {max_posts_per_category}")
    
    # Show subreddit stats
    print("   🔍 Loading subreddit configuration...")
    stats = reddit_monitor.get_subreddit_stats()
    print(f"   📡 Monitoring {stats['total']} subreddits across {len(stats)-1} categories")
    
    print(f"\n🌍 Starting real data collection...")
    print(f"⚠️  This will use your Reddit API quota - be mindful of rate limits")
    print("💡 You can press Ctrl+C anytime to stop collection gracefully")
    print("🔄 Progress will be shown in real-time...")
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    total_posts_processed = 0
    total_stocks_found = 0
    category_stats = {}
    
    # Define categories to collect from
    categories = [
        ('primary_us', 'US Markets'),
        ('european', 'European Markets'),
        ('trading', 'Trading & Options'),
        ('tech_focused', 'Technology Stocks'),
        ('commodities', 'Commodities & Energy')
    ]
    
    try:
        for category_key, category_name in categories:
            if datetime.now() >= end_time:
                print(f"\n⏰ Collection time limit reached")
                break
                
            print(f"\n📈 Collecting from {category_name}...")
            print(f"   🔍 Fetching up to {max_posts_per_category} posts...")
            
            try:
                # Get posts from this category
                posts = reddit_monitor.get_enhanced_hot_posts(
                    categories=[category_key],
                    limit=max_posts_per_category
                )
                print(f"   ✅ Retrieved {len(posts)} posts from {category_name}")
                
                posts_processed = 0
                stocks_found = 0
                
                print(f"   🔬 Analyzing posts for stock mentions...")
                
                for i, post in enumerate(posts[:max_posts_per_category], 1):
                    # Extract full text for analysis
                    full_text = post['title'] + ' ' + post.get('content', '')
                    
                    # Add top comments for better context
                    if post.get('comments'):
                        comment_text = ' '.join(post['comments'][:3])  # Top 3 comments
                        full_text += ' ' + comment_text
                    
                    # Extract stock symbols
                    stocks = sentiment_analyzer.extract_and_validate_symbols(full_text)
                    
                    # Show progress every 10 posts
                    if i % 10 == 0:
                        print(f"   📊 Progress: {i}/{len(posts)} posts analyzed, {stocks_found} stocks found so far")
                    
                    if stocks:
                        print(f"   🎯 r/{post['subreddit']}: Found {len(stocks)} stocks → {', '.join(stocks)}")
                        print(f"      📰 '{post['title'][:60]}...' ({post['score']} ⬆️)")
                        
                        for stock in stocks:
                            # Get context-aware sentiment
                            sentiment = sentiment_analyzer.get_stock_context_sentiment(full_text, stock)
                            
                            # Store in database
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
                            
                            # Show individual stock saves for important ones
                            if stock in ['BYND', 'TSLA', 'NVDA', 'META', 'AAPL']:
                                print(f"      💎 Saved ${stock} mention: {sentiment['label']} ({sentiment['score']:+.3f})")
                        
                        # Small delay to be respectful to Reddit API
                        time.sleep(0.1)
                    
                    posts_processed += 1
                    
                    # Check time limit
                    if datetime.now() >= end_time:
                        break
                
                category_stats[category_name] = {
                    'posts': posts_processed,
                    'stocks': stocks_found
                }
                
                total_posts_processed += posts_processed
                total_stocks_found += stocks_found
                
                print(f"   ✅ {category_name} COMPLETE: {posts_processed} posts → {stocks_found} stock mentions")
                print(f"   📊 Running Total: {total_posts_processed} posts, {total_stocks_found} stock mentions")
                
                # Brief pause between categories
                print(f"   ⏳ Pausing 3 seconds before next category...")
                time.sleep(3)
                
            except Exception as e:
                print(f"   ❌ Error in {category_name}: {e}")
                continue
    
    except KeyboardInterrupt:
        print(f"\n⏹️  Collection stopped by user")
        print(f"📊 Partial results: {total_posts_processed} posts, {total_stocks_found} stocks found")
    
    # Final results
    actual_duration = (datetime.now() - start_time).total_seconds() / 60
    print(f"\n" + "=" * 60)
    print(f"📊 Real Data Collection Results:")
    print(f"   Duration: {actual_duration:.1f} minutes")
    print(f"   Posts processed: {total_posts_processed}")
    print(f"   Stock mentions collected: {total_stocks_found}")
    
    print(f"\n📈 Category Breakdown:")
    for category, stats in category_stats.items():
        print(f"   {category}: {stats['posts']} posts → {stats['stocks']} mentions")
    
    # Show database statistics
    db_stats = get_database_stats()
    print(f"\n💾 Database Status:")
    print(f"   Total mentions: {db_stats['total_mentions']}")
    print(f"   Unique stocks: {db_stats['unique_stocks']}")
    print(f"   Active subscribers: {db_stats['active_subscribers']}")
    
    # Show current top stocks
    print(f"\n🔥 Current Top 10 Stocks:")
    top_stocks = get_top_stocks(limit=10, hours=24)
    
    if top_stocks:
        for i, stock in enumerate(top_stocks, 1):
            emoji = "🟢" if stock['overall_sentiment'] == 'bullish' else "🔴" if stock['overall_sentiment'] == 'bearish' else "⚪"
            print(f"   {i:2}. ${stock['symbol']:<8} {emoji} {stock['mentions']:3} mentions | {stock['avg_sentiment']:+.3f}")
    else:
        print("   No stocks found (this is normal for first run)")
    
    print(f"\n✅ Real data collection completed!")
    print(f"🌐 Visit http://localhost:5000 to see your live data")
    
    return total_stocks_found > 0

def quick_real_data_test():
    """Quick test with real Reddit data (5 minutes)"""
    print("⚡ Quick Real Data Test")
    print("=" * 40)
    
    return collect_real_data(duration_minutes=5, max_posts_per_category=10)

def full_real_data_collection():
    """Full data collection (30 minutes)"""
    print("🌍 Full Real Data Collection")
    print("=" * 40)
    
    return collect_real_data(duration_minutes=30, max_posts_per_category=50)

def continuous_monitoring():
    """Continuous monitoring (runs until stopped)"""
    print("🔄 Continuous Real Data Monitoring")
    print("=" * 40)
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            print(f"📅 Collection cycle starting at {datetime.now().strftime('%H:%M:%S')}")
            collect_real_data(duration_minutes=15, max_posts_per_category=25)
            
            print(f"\n⏳ Waiting 10 minutes before next cycle...")
            time.sleep(600)  # Wait 10 minutes
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Continuous monitoring stopped")

if __name__ == "__main__":
    print("🌍 StockHark Real Data Collection")
    print("=" * 60)
    
    # Check environment setup
    if not os.getenv('REDDIT_CLIENT_ID') or os.getenv('REDDIT_CLIENT_ID') == 'your-client-id':
        print("❌ Reddit API credentials not configured!")
        print("📝 Please add your credentials to the .env file:")
        print("   REDDIT_CLIENT_ID=your_actual_client_id")
        print("   REDDIT_CLIENT_SECRET=your_actual_client_secret")
        print("   REDDIT_USER_AGENT=StockHark/1.0 by YourUsername")
        sys.exit(1)
    
    print("\nReal Data Collection Options:")
    print("1. Quick test (5 minutes, 10 posts per category)")
    print("2. Full collection (30 minutes, 50 posts per category)")  
    print("3. Continuous monitoring (runs until stopped)")
    print("4. Custom duration")
    
    try:
        choice = input("\nEnter choice (1-4, default 1): ").strip() or "1"
        
        if choice == "1":
            success = quick_real_data_test()
        elif choice == "2":
            success = full_real_data_collection()
        elif choice == "3":
            continuous_monitoring()
            success = True
        elif choice == "4":
            duration = int(input("Enter duration in minutes (default 15): ") or "15")
            max_posts = int(input("Enter max posts per category (default 25): ") or "25")
            success = collect_real_data(duration, max_posts)
        else:
            print("Invalid choice")
            sys.exit(1)
        
        if success:
            print(f"\n🎉 Success! Your StockHark now has real Reddit data!")
            print(f"🚀 Start your webapp with: python app.py")
        else:
            print(f"\n⚠️  No data collected. Check your Reddit API setup.")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Collection stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()