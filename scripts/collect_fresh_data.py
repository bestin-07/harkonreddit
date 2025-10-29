#!/usr/bin/env python3
"""
Simple Direct Reddit Data Collection
Uses PRAW directly to avoid inheritance issues
"""

import os
import sys
import time
import praw
from datetime import datetime, timedelta
from pathlib import Path

# Setup script environment using centralized utility  
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from stockhark.core.path_utils import setup_script_environment
setup_script_environment()

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from stockhark.sentiment_analyzer import EnhancedSentimentAnalyzer
from stockhark.core.validator import StockValidator
from stockhark.core.data import init_db, add_stock_data, get_top_stocks, get_database_stats

def collect_fresh_data(duration_minutes=10, posts_per_subreddit=15):
    """
    Collect fresh Reddit data using direct PRAW connection
    """
    print("🚀 StockHark - Direct Reddit Data Collection")
    print("=" * 50)
    
    # Initialize components
    print("⏳ Initializing components...")
    
    try:
        # Initialize database
        init_db()
        print("   ✅ Database ready")
        
        # Initialize components using ServiceFactory
        from stockhark.core.services.service_factory import create_standard_components
        reddit, sentiment_analyzer, stock_validator = create_standard_components(enable_finbert=False)
        print("   ✅ All components ready")
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False
    
    # Show current database stats
    initial_stats = get_database_stats()
    print(f"\n📊 Current Database Status:")
    print(f"   Total mentions: {initial_stats['total_mentions']}")
    print(f"   Unique stocks: {initial_stats['unique_stocks']}")
    
    print(f"\n🔍 Starting fresh data collection...")
    print(f"   Duration: {duration_minutes} minutes")
    print(f"   Posts per subreddit: {posts_per_subreddit}")
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    total_posts_processed = 0
    total_stocks_found = 0
    new_mentions_added = 0
    
    # Focus on most active financial subreddits
    priority_subreddits = [
        'wallstreetbets', 'stocks', 'investing', 'pennystocks',
        'options', 'thetagang', 'StockMarket', 'daytrading'
    ]
    
    try:
        for subreddit_name in priority_subreddits:
            if datetime.now() >= end_time:
                print(f"⏰ Time limit reached")
                break
                
            print(f"\n📈 Processing r/{subreddit_name}...")
            
            try:
                # Get posts directly with PRAW
                subreddit = reddit.subreddit(subreddit_name)
                posts = list(subreddit.hot(limit=posts_per_subreddit))
                
                print(f"   📥 Retrieved {len(posts)} posts")
                
                subreddit_stocks = 0
                
                for i, post in enumerate(posts, 1):
                    # Skip stickied posts
                    if post.stickied:
                        continue
                    
                    # Create full text for analysis
                    full_text = post.title
                    if hasattr(post, 'selftext') and post.selftext:
                        full_text += ' ' + post.selftext
                    
                    # Extract and validate stock symbols
                    valid_symbols = stock_validator.extract_and_validate(full_text)
                    
                    if valid_symbols:
                        print(f"   🎯 Post {i}: Found {len(valid_symbols)} stocks → {', '.join(valid_symbols)}")
                        print(f"      📰 '{post.title[:50]}...' ({post.score} ⬆️)")
                        
                        for symbol in valid_symbols:
                            # Analyze sentiment for this stock
                            sentiment_score = sentiment_analyzer.analyze_sentiment(full_text)
                            
                            # Convert float score to dictionary format
                            if sentiment_score > 0.1:
                                sentiment_label = 'bullish'
                            elif sentiment_score < -0.1:
                                sentiment_label = 'bearish'
                            else:
                                sentiment_label = 'neutral'
                            
                            sentiment_result = {
                                'score': sentiment_score,
                                'label': sentiment_label,
                                'confidence': 0.7
                            }
                            
                            # Add to database
                            try:
                                add_stock_data(
                                    symbol=symbol,
                                    sentiment=sentiment_result['score'],
                                    sentiment_label=sentiment_result['label'],
                                    confidence=sentiment_result.get('confidence', 0.5),
                                    mentions=1,
                                    source=f"reddit/r/{subreddit_name}",
                                    post_url=f"https://reddit.com{post.permalink}",
                                    timestamp=datetime.fromtimestamp(post.created_utc)
                                )
                                
                                new_mentions_added += 1
                                subreddit_stocks += 1
                                
                                # Show important stock mentions
                                if symbol in ['TSLA', 'AAPL', 'NVDA', 'META', 'GOOGL', 'MSFT', 'GME', 'AMC', 'PLTR', 'NIO']:
                                    sentiment_emoji = "🟢" if sentiment_result['label'] == 'bullish' else "🔴" if sentiment_result['label'] == 'bearish' else "⚪"
                                    print(f"      💎 ${symbol} {sentiment_emoji} {sentiment_result['label']} ({sentiment_result['score']:+.3f})")
                                
                            except Exception as e:
                                print(f"      ❌ Error saving {symbol}: {e}")
                    
                    total_posts_processed += 1
                    
                    # Show progress every 5 posts
                    if i % 5 == 0:
                        print(f"   📊 Progress: {i}/{len(posts)} posts, {subreddit_stocks} stocks found")
                    
                    # Check time limit
                    if datetime.now() >= end_time:
                        break
                        
                    # Small delay to be respectful to Reddit
                    time.sleep(0.2)
                
                total_stocks_found += subreddit_stocks
                print(f"   ✅ r/{subreddit_name} complete: {len(posts)} posts → {subreddit_stocks} stock mentions")
                
                # Pause between subreddits
                time.sleep(3)
                
            except Exception as e:
                print(f"   ❌ Error processing r/{subreddit_name}: {e}")
                continue
    
    except KeyboardInterrupt:
        print(f"\n⏹️  Collection stopped by user")
    
    # Final results
    actual_duration = (datetime.now() - start_time).total_seconds() / 60
    print(f"\n" + "=" * 50)
    print(f"📊 Collection Results:")
    print(f"   Duration: {actual_duration:.1f} minutes")
    print(f"   Posts processed: {total_posts_processed}")
    print(f"   Stock mentions found: {total_stocks_found}")
    print(f"   New mentions added: {new_mentions_added}")
    
    # Show updated database stats
    final_stats = get_database_stats()
    mentions_added = final_stats['total_mentions'] - initial_stats['total_mentions']
    print(f"\n💾 Updated Database Status:")
    print(f"   Total mentions: {final_stats['total_mentions']} (+{mentions_added})")  
    print(f"   Unique stocks: {final_stats['unique_stocks']}")
    print(f"   Database size: {final_stats['database_size_mb']:.2f} MB")
    
    # Show current top stocks
    print(f"\n🔥 Current Top 10 Trending Stocks:")
    top_stocks = get_top_stocks(limit=10, hours=24)
    
    if top_stocks:
        for i, stock in enumerate(top_stocks, 1):
            sentiment_emoji = "🟢" if stock['overall_sentiment'] == 'bullish' else "🔴" if stock['overall_sentiment'] == 'bearish' else "⚪"
            print(f"   {i:2}. ${stock['symbol']:<6} {sentiment_emoji} {stock['total_mentions']:3} mentions | {stock['avg_sentiment']:+.3f} sentiment")
    else:
        print("   No recent stock mentions found")
    
    print(f"\n✅ Fresh data collection completed!")
    print(f"🌐 Your StockHark app at http://127.0.0.1:5000 now has the latest data!")
    
    return new_mentions_added > 0

if __name__ == "__main__":
    print("🚀 StockHark - Fresh Data Collection")
    print("=" * 50)
    
    # Check Reddit API setup
    if not os.getenv('REDDIT_CLIENT_ID') or os.getenv('REDDIT_CLIENT_ID') == 'your-client-id':
        print("❌ Reddit API not configured!")
        print("📝 Please set up your Reddit API credentials in .env file")
        sys.exit(1)
    
    try:
        success = collect_fresh_data(duration_minutes=10, posts_per_subreddit=15)
        
        if success:
            print(f"\n🎉 Success! Fresh Reddit data collected!")
            print(f"   💡 Your Flask app will show the latest trends")
        else:
            print(f"\n⚠️  No new data collected")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Collection stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()