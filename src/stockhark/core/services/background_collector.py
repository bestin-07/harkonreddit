#!/usr/bin/env python3
"""
Background Data Collector for StockHark
Runs data collection in a separate thread while Flask app serves requests
"""

import threading
import time
import praw
from datetime import datetime, timedelta
from typing import Optional
import os
import logging

class BackgroundDataCollector:
    """Background data collection service for StockHark"""
    
    def __init__(self, collection_interval_minutes: int = 5):
        """
        Initialize background data collector
        
        Args:
            collection_interval_minutes: Minutes between collection cycles (default: 5 for development)
        """
        self.collection_interval = collection_interval_minutes * 60  # Convert to seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.logger = self._setup_logger()
        
        # Statistics
        self.last_collection_time: Optional[datetime] = None
        self.total_collections = 0
        self.total_stocks_collected = 0
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for background collector"""
        logger = logging.getLogger('StockHark.BackgroundCollector')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def start(self):
        """Start background data collection"""
        if self.running:
            self.logger.warning("Background collector is already running")
            return
        
        self.logger.info(f"Starting background data collection (every {self.collection_interval//60} minutes)")
        self.running = True
        self.thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop background data collection"""
        if not self.running:
            return
        
        self.logger.info("Stopping background data collection")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
    
    def _collection_loop(self):
        """Main collection loop running in background thread"""
        while self.running:
            try:
                # Run data collection
                self._collect_data()
                
                # Update statistics
                self.last_collection_time = datetime.now()
                self.total_collections += 1
                
                self.logger.info(f"Collection cycle {self.total_collections} completed")
                
                # Sleep until next collection
                for _ in range(self.collection_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Error in collection loop: {e}")
                # Wait 60 seconds before retrying on error
                time.sleep(60)
    
    def _collect_data(self):
        """Collect fresh data from Reddit using the full 5-step sentiment methodology"""
        try:
            self.logger.info("Starting data collection cycle")
            
            # Initialize components 
            components = self._initialize_components()
            reddit, sentiment_analyzer, stock_validator, aggregator = components
            
            # Collect mentions from subreddits
            all_mentions = self._collect_mentions_from_subreddits(reddit, sentiment_analyzer, stock_validator)
            
            # Process and store aggregated results
            stocks_found = self._process_and_store_mentions(all_mentions, aggregator)
            
            self.total_stocks_collected += stocks_found
            self.logger.info(f"Collection completed: {stocks_found} new stock mentions added")
            
        except Exception as e:
            self.logger.error(f"Error in data collection: {e}")
            raise

    def _initialize_components(self):
        """Initialize all required components for data collection"""
        # Import here to avoid circular imports
        from .service_factory import create_standard_components
        from .sentiment_aggregator import get_sentiment_aggregator
        
        reddit, sentiment_analyzer, stock_validator = create_standard_components()
        aggregator = get_sentiment_aggregator()
        
        return reddit, sentiment_analyzer, stock_validator, aggregator

    def _collect_mentions_from_subreddits(self, reddit, sentiment_analyzer, stock_validator):
        """Collect mentions from all configured subreddits"""
        from .sentiment_aggregator import SentimentMention
        
        subreddits = ['wallstreetbets', 'stocks', 'investing', 'pennystocks', 'options']
        posts_per_subreddit = 10
        all_mentions = []
        
        for subreddit_name in subreddits:
            if not self.running:
                break
                
            mentions = self._collect_mentions_from_subreddit(
                reddit, sentiment_analyzer, stock_validator, subreddit_name, posts_per_subreddit
            )
            all_mentions.extend(mentions)
        
        return all_mentions

    def _collect_mentions_from_subreddit(self, reddit, sentiment_analyzer, stock_validator, subreddit_name, limit):
        """Collect mentions from a single subreddit"""
        from .sentiment_aggregator import SentimentMention
        mentions = []
        
        try:
            subreddit = reddit.subreddit(subreddit_name)
            posts = list(subreddit.hot(limit=limit))
            
            for post in posts:
                if not self.running:
                    break
                    
                if post.stickied:
                    continue
                
                # Skip posts older than 24 hours (per methodology time window)
                post_age_hours = (datetime.now().timestamp() - post.created_utc) / 3600
                if post_age_hours > 24:
                    continue
                
                post_mentions = self._process_single_post(post, sentiment_analyzer, stock_validator, subreddit_name)
                mentions.extend(post_mentions)
                
        except Exception as e:
            self.logger.error(f"Error collecting from r/{subreddit_name}: {e}")
        
        return mentions

    def _process_single_post(self, post, sentiment_analyzer, stock_validator, subreddit_name):
        """Process a single Reddit post and extract stock mentions"""
        from .sentiment_aggregator import SentimentMention
        
        # Create full text
        full_text = post.title
        if hasattr(post, 'selftext') and post.selftext:
            full_text += ' ' + post.selftext
        
        # Extract and validate symbols
        valid_symbols = stock_validator.extract_and_validate(full_text)
        
        mentions = []
        if valid_symbols:  # Only analyze sentiment if we found stocks
            # Get raw sentiment score (Step 1: FinBERT Analysis)
            underlying_analyzer = sentiment_analyzer._analyzer
            raw_sentiment = underlying_analyzer.analyze_sentiment(
                full_text, 
                timestamp=None,  # We'll pass timestamp separately
                apply_time_decay=False  # We handle time decay in aggregation
            )
            
            # Create mentions for each symbol in this post
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
                mentions.append(mention)
        
        return mentions

    def _process_and_store_mentions(self, all_mentions, aggregator):
        """Process mentions through aggregation and store in database"""
        from ..data.database import add_stock_data
        
        if not all_mentions:
            return 0
        
        self.logger.info(f"Collected {len(all_mentions)} mentions, aggregating by stock using full methodology...")
        
        # Apply Steps 2-5: Time Decay, Source Weighting, Aggregation, Normalization
        aggregated_results = aggregator.aggregate_multiple_stocks(all_mentions)
        
        # Create descriptive source string from subreddits processed
        subreddits = ['wallstreetbets', 'stocks', 'investing', 'pennystocks', 'options']
        processed_subreddits = sorted(set(subreddits))
        source_description = f"reddit/r/{'+'.join(processed_subreddits)}"
        
        # Store aggregated results in database
        stocks_found = 0
        for symbol, result in aggregated_results.items():
            try:
                add_stock_data(
                    symbol=symbol,
                    sentiment=result.final_sentiment,
                    sentiment_label=result.sentiment_label.lower().replace(' ', '_'),
                    confidence=result.confidence,
                    mentions=result.total_mentions,
                    source=source_description,
                    post_url=None,
                    timestamp=datetime.now()
                )
                stocks_found += 1
                        
            except Exception as e:
                self.logger.error(f"Failed to add aggregated data for {symbol}: {e}")
                continue
        
        return stocks_found
    
    def get_status(self) -> dict:
        """Get current status of background collector"""
        return {
            'running': self.running,
            'last_collection': self.last_collection_time.isoformat() if self.last_collection_time else None,
            'total_collections': self.total_collections,
            'total_stocks_collected': self.total_stocks_collected,
            'collection_interval_minutes': self.collection_interval // 60
        }

# Global collector instance
_collector: Optional[BackgroundDataCollector] = None

def get_collector() -> BackgroundDataCollector:
    """Get the global collector instance"""
    global _collector
    if _collector is None:
        # Use environment variable or default to 5 minutes for development
        interval_minutes = int(os.getenv('STOCKHARK_COLLECTION_INTERVAL', '5'))
        _collector = BackgroundDataCollector(collection_interval_minutes=interval_minutes)
    return _collector

def start_background_collection():
    """Start background data collection"""
    collector = get_collector()
    collector.start()

def stop_background_collection():
    """Stop background data collection"""
    collector = get_collector()
    collector.stop()

def get_collection_status() -> dict:
    """Get status of background collection"""
    collector = get_collector()
    return collector.get_status()

def force_collection():
    """Force an immediate data collection"""
    collector = get_collector()
    collector._collect_data()

def collect_stock_data(posts_per_subreddit: int = 15):
    """Manual data collection function"""
    collector = get_collector()
    # Force a collection cycle with specified parameters
    collector._collect_data()