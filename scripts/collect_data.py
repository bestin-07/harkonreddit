#!/usr/bin/env python3
"""
StockHark Data Collection Script
Combines database cleanup and fresh Reddit data collection with enhanced sentiment methodology
"""

import os
import sys
import time
import praw
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

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
from stockhark.core.validators.stock_validator import StockValidator
from stockhark.core.data import init_db, add_stock_data, get_top_stocks, get_database_stats
from stockhark.core.services.sentiment_aggregator import get_sentiment_aggregator, SentimentMention
from stockhark.core.services.service_factory import create_standard_components
from stockhark.config import DATABASE_PATH

def cleanup_database():
    """Clean the database by removing old entries and invalid stock symbols"""
    print("🧹 Starting database cleanup...")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get initial stats
        cursor.execute("SELECT COUNT(*) FROM stock_data")
        initial_count = cursor.fetchone()[0]
        
        # Remove entries older than 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        cursor.execute("DELETE FROM stock_data WHERE timestamp < ?", (cutoff_date,))
        old_entries_removed = cursor.rowcount
        
        # Remove entries with very low confidence (< 0.3)
        cursor.execute("DELETE FROM stock_data WHERE confidence < 0.3")
        low_confidence_removed = cursor.rowcount
        
        # Remove single-character symbols (likely false positives)
        cursor.execute("DELETE FROM stock_data WHERE LENGTH(symbol) = 1")
        single_char_removed = cursor.rowcount
        
        # Vacuum to reclaim space
        cursor.execute("VACUUM")
        
        conn.commit()
        conn.close()
        
        total_removed = old_entries_removed + low_confidence_removed + single_char_removed
        print(f"   ✅ Cleanup complete:")
        print(f"   📊 Initial entries: {initial_count}")
        print(f"   🗑️  Old entries removed: {old_entries_removed}")
        print(f"   🗑️  Low confidence removed: {low_confidence_removed}")
        print(f"   🗑️  Single-char symbols removed: {single_char_removed}")
        print(f"   📊 Total entries removed: {total_removed}")
        print(f"   📊 Remaining entries: {initial_count - total_removed}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Cleanup error: {e}")
        return False

def collect_fresh_data(duration_minutes: int = 10, posts_per_subreddit: int = 15):
    """Collect fresh Reddit data using enhanced sentiment methodology"""
    print(f"🔍 Starting fresh data collection...")
    print(f"   Duration: {duration_minutes} minutes")
    print(f"   Posts per subreddit: {posts_per_subreddit}")
    
    try:
        # Initialize components
        print("⏳ Initializing components...")
        reddit, sentiment_analyzer, stock_validator = create_standard_components()
        print("   ✅ All components ready")
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False
    
    # Show current database stats
    initial_stats = get_database_stats()
    print(f"\n📊 Current Database Status:")
    print(f"   Total mentions: {initial_stats['total_mentions']}")
    print(f"   Unique stocks: {initial_stats['unique_stocks']}")
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    total_posts_processed = 0
    total_stocks_found = 0
    new_mentions_added = 0
    
    # Initialize enhanced sentiment aggregation system
    aggregator = get_sentiment_aggregator()
    all_mentions = []  # Collect all mentions for batch aggregation
    
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
                        
                        # Get raw sentiment score (Step 1: FinBERT Analysis) 
                        underlying_analyzer = sentiment_analyzer._analyzer
                        raw_sentiment = underlying_analyzer.analyze_sentiment(
                            full_text, 
                            timestamp=None,  # We'll pass timestamp separately
                            apply_time_decay=False  # We handle time decay in aggregation
                        )
                        
                        # Create mentions for each symbol in this post (for aggregation)
                        post_timestamp = datetime.fromtimestamp(post.created_utc)
                        post_source = f"reddit/r/{subreddit_name}"
                        post_url = f"https://reddit.com{post.permalink}"
                        
                        for symbol in valid_symbols:
                            mention = SentimentMention(
                                symbol=symbol,
                                raw_sentiment=raw_sentiment,
                                timestamp=post_timestamp,
                                source=post_source,
                                text=full_text,
                                post_url=post_url
                            )
                            all_mentions.append(mention)
                            subreddit_stocks += 1
                            
                            # Show important stock mentions (preview with raw sentiment)
                            if symbol in ['TSLA', 'AAPL', 'NVDA', 'META', 'GOOGL', 'MSFT', 'GME', 'AMC', 'PLTR', 'NIO']:
                                sentiment_emoji = "🟢" if raw_sentiment > 0.1 else "🔴" if raw_sentiment < -0.1 else "⚪"
                                print(f"      💎 ${symbol} {sentiment_emoji} raw sentiment ({raw_sentiment:+.3f})")
                    
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
    
    # Apply Steps 2-5: Time Decay, Source Weighting, Symbol Penalties, Post Count Boost, Normalization
    if all_mentions:
        print(f"\n🧠 Applying enhanced sentiment methodology to {len(all_mentions)} mentions...")
        
        # Group mentions by stock symbol for aggregation
        stock_mentions = defaultdict(list)
        for mention in all_mentions:
            stock_mentions[mention.symbol].append(mention)
        
        print(f"   📊 Found {len(stock_mentions)} unique stocks for aggregation")
        
        # Create descriptive source string from subreddits processed
        processed_subreddits = sorted(set(priority_subreddits))
        source_description = f"reddit/r/{'+'.join(processed_subreddits)}"
        
        # Process each stock with full methodology
        for symbol, mentions in stock_mentions.items():
            try:
                # Apply full 5-step methodology with all enhancements
                aggregated_result = aggregator.aggregate_stock_sentiment(mentions)
                
                # Add aggregated result to database with descriptive source
                add_stock_data(
                    symbol=symbol,
                    sentiment=aggregated_result.final_sentiment,
                    sentiment_label=aggregated_result.sentiment_label,
                    confidence=aggregated_result.confidence,
                    mentions=aggregated_result.total_mentions,
                    source=source_description,  # Shows which subreddits were analyzed
                    post_url=None,  # Aggregated data doesn't have single URL
                    timestamp=datetime.now()
                )
                
                new_mentions_added += aggregated_result.total_mentions
                
                # Show enhanced results for important stocks
                if symbol in ['TSLA', 'AAPL', 'NVDA', 'META', 'GOOGL', 'MSFT', 'GME', 'AMC', 'PLTR', 'NIO']:
                    emoji = "🟢" if aggregated_result.sentiment_label == 'bullish' else "🔴" if aggregated_result.sentiment_label == 'bearish' else "⚪"
                    print(f"   💎 ${symbol:6} {emoji} {aggregated_result.sentiment_label} ({aggregated_result.final_sentiment:+.3f}) | {len(mentions)} mentions across {len(set(m.post_url for m in mentions))} posts")
                    
            except Exception as e:
                print(f"   ❌ Error aggregating {symbol}: {e}")
        
        print(f"   ✅ Enhanced methodology applied to all stocks")
    
    # Final results
    actual_duration = (datetime.now() - start_time).total_seconds() / 60
    print(f"\n" + "=" * 50)
    print(f"📊 Collection Results with Enhanced Methodology:")
    print(f"   Duration: {actual_duration:.1f} minutes")
    print(f"   Posts processed: {total_posts_processed}")
    print(f"   Stock mentions found: {total_stocks_found}")
    print(f"   Enhanced aggregations added: {new_mentions_added}")
    
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
    
    print(f"\n✅ Data collection completed!")
    print(f"🌐 Your StockHark app now has the latest data!")
    
    return new_mentions_added > 0

def main():
    """Main function - runs cleanup then data collection"""
    print("🚀 StockHark - Data Collection Tool")
    print("=" * 50)
    
    # Check Reddit API setup
    if not os.getenv('REDDIT_CLIENT_ID') or os.getenv('REDDIT_CLIENT_ID') == 'your-client-id':
        print("❌ Reddit API not configured!")
        print("📝 Please set up your Reddit API credentials in .env file")
        sys.exit(1)
    
    # Initialize database
    init_db()
    
    # Step 1: Cleanup database
    cleanup_success = cleanup_database()
    if not cleanup_success:
        print("⚠️  Database cleanup failed, but continuing with data collection...")
    
    print("\n" + "=" * 50)
    
    # Step 2: Collect fresh data
    collection_success = collect_fresh_data(duration_minutes=10, posts_per_subreddit=15)
    
    if collection_success:
        print(f"\n🎉 Success! Reddit data collected and processed!")
        print(f"   💡 Run your Flask app to see the latest trends")
    else:
        print(f"\n❌ Data collection failed")
        sys.exit(1)

if __name__ == "__main__":
    main()