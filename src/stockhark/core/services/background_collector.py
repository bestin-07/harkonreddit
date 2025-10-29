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
    
    def __init__(self, collection_interval_minutes: int = 30):
        """
        Initialize background data collector
        
        Args:
            collection_interval_minutes: Minutes between collection cycles
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
        """Collect fresh data from Reddit"""
        try:
            # Import here to avoid circular imports
            from ...sentiment_analyzer import EnhancedSentimentAnalyzer
            from ..validator import StockValidator
            from ..clients.reddit_client import get_reddit_client
            from ..data.database import add_stock_data
            from ...config import DATA_DIR
            
            self.logger.info("Starting data collection cycle")
            
            # Initialize components using ServiceFactory
            from .service_factory import create_standard_components
            reddit, sentiment_analyzer, stock_validator = create_standard_components()
            
            # Focus on most active subreddits
            subreddits = ['wallstreetbets', 'stocks', 'investing', 'pennystocks', 'options']
            posts_per_subreddit = 10
            stocks_found = 0
            
            for subreddit_name in subreddits:
                if not self.running:
                    break
                    
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    posts = list(subreddit.hot(limit=posts_per_subreddit))
                    
                    for post in posts:
                        if not self.running:
                            break
                            
                        if post.stickied:
                            continue
                        
                        # Create full text
                        full_text = post.title
                        if hasattr(post, 'selftext') and post.selftext:
                            full_text += ' ' + post.selftext
                        
                        # Extract and validate symbols
                        valid_symbols = stock_validator.extract_and_validate(full_text)
                        
                        for symbol in valid_symbols:
                            if not self.running:
                                break
                                
                            # Analyze sentiment
                            sentiment_score = sentiment_analyzer.analyze_sentiment(full_text)
                            
                            # Convert to label
                            if sentiment_score > 0.1:
                                sentiment_label = 'bullish'
                            elif sentiment_score < -0.1:
                                sentiment_label = 'bearish'
                            else:
                                sentiment_label = 'neutral'
                            
                            # Add to database
                            try:
                                add_stock_data(
                                    symbol=symbol,
                                    sentiment=sentiment_score,
                                    sentiment_label=sentiment_label,
                                    confidence=0.7,
                                    mentions=1,
                                    source=f"reddit/r/{subreddit_name}",
                                    post_url=f"https://reddit.com{post.permalink}",
                                    timestamp=datetime.fromtimestamp(post.created_utc)
                                )
                                
                                stocks_found += 1
                                
                            except Exception as e:
                                self.logger.error(f"Error saving {symbol}: {e}")
                        
                        # Small delay between posts
                        time.sleep(0.1)
                    
                    # Delay between subreddits
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"Error processing r/{subreddit_name}: {e}")
                    continue
            
            self.total_stocks_collected += stocks_found
            self.logger.info(f"Collection completed: {stocks_found} new stock mentions added")
            
        except Exception as e:
            self.logger.error(f"Error in data collection: {e}")
            raise
    
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
        _collector = BackgroundDataCollector(collection_interval_minutes=30)
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

def collect_stock_data(duration_minutes: int = 5, posts_per_subreddit: int = 15):
    """Manual data collection function"""
    collector = get_collector()
    # Force a collection cycle
    collector._collect_data()