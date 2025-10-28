"""
Reddit Client Singleton

Centralized Reddit API client management to eliminate duplicate instantiations
and provide consistent configuration across the application.
"""

import praw
import os
import threading
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RedditClientSingleton:
    """
    Thread-safe singleton Reddit client with connection pooling and error handling
    
    Features:
    - Single Reddit instance across entire application
    - Thread-safe initialization
    - Configuration validation
    - Connection health checking
    - Graceful error handling
    """
    
    _instance: Optional['RedditClientSingleton'] = None
    _lock = threading.Lock()
    _reddit_client: Optional[praw.Reddit] = None
    
    def __new__(cls) -> 'RedditClientSingleton':
        """Ensure only one instance exists (thread-safe)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Reddit client if not already done"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._setup_client()
    
    def _setup_client(self) -> None:
        """Setup Reddit client with proper configuration"""
        try:
            # Get configuration from environment
            config = self._get_reddit_config()
            
            # Validate configuration
            self._validate_config(config)
            
            # Create Reddit client
            self._reddit_client = praw.Reddit(**config)
            
            # Test connection
            self._test_connection()
            
            logger.info("Reddit client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            self._reddit_client = None
            raise
    
    def _get_reddit_config(self) -> Dict[str, str]:
        """Get Reddit API configuration from environment"""
        return {
            'client_id': os.getenv('REDDIT_CLIENT_ID', ''),
            'client_secret': os.getenv('REDDIT_CLIENT_SECRET', ''),
            'user_agent': os.getenv('REDDIT_USER_AGENT', 'StockHark/1.0')
        }
    
    def _validate_config(self, config: Dict[str, str]) -> None:
        """Validate Reddit API configuration"""
        required_fields = ['client_id', 'client_secret', 'user_agent']
        
        for field in required_fields:
            if not config.get(field):
                raise ValueError(f"Missing required Reddit API configuration: {field}")
        
        # Check for placeholder values
        if config['client_id'] in ['your-client-id', 'your_actual_client_id']:
            raise ValueError("Reddit client_id contains placeholder value")
        
        if config['client_secret'] in ['your-client-secret', 'your_actual_client_secret']:
            raise ValueError("Reddit client_secret contains placeholder value")
    
    def _test_connection(self) -> None:
        """Test Reddit API connection"""
        if self._reddit_client is None:
            raise RuntimeError("Reddit client not initialized")
        
        try:
            # Simple test - access user info
            _ = self._reddit_client.user.me()
            logger.debug("Reddit API connection test successful")
        except Exception as e:
            logger.warning(f"Reddit API connection test failed: {e}")
            # Don't raise here as read-only access might still work
    
    @property
    def client(self) -> praw.Reddit:
        """Get the Reddit client instance"""
        if self._reddit_client is None:
            raise RuntimeError("Reddit client not properly initialized")
        return self._reddit_client
    
    def get_subreddit(self, name: str) -> praw.models.Subreddit:
        """Get a subreddit instance"""
        return self.client.subreddit(name)
    
    def is_healthy(self) -> bool:
        """Check if Reddit client is healthy and connected"""
        try:
            if self._reddit_client is None:
                return False
            
            # Quick health check
            _ = self._reddit_client.subreddit('test').display_name
            return True
            
        except Exception as e:
            logger.warning(f"Reddit client health check failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Reddit client statistics"""
        return {
            'initialized': self._reddit_client is not None,
            'healthy': self.is_healthy(),
            'user_agent': self._reddit_client.config.user_agent if self._reddit_client else None,
            'client_id': self._reddit_client.config.client_id if self._reddit_client else None
        }


# Global singleton instance
_reddit_singleton = None

def get_reddit_client() -> praw.Reddit:
    """
    Get the global Reddit client instance
    
    Returns:
        praw.Reddit: Configured Reddit client
        
    Raises:
        RuntimeError: If client cannot be initialized
    """
    global _reddit_singleton
    
    if _reddit_singleton is None:
        _reddit_singleton = RedditClientSingleton()
    
    return _reddit_singleton.client

def get_reddit_singleton() -> RedditClientSingleton:
    """
    Get the Reddit singleton instance for advanced operations
    
    Returns:
        RedditClientSingleton: The singleton instance
    """
    global _reddit_singleton
    
    if _reddit_singleton is None:
        _reddit_singleton = RedditClientSingleton()
    
    return _reddit_singleton

def is_reddit_configured() -> bool:
    """
    Check if Reddit API is properly configured
    
    Returns:
        bool: True if Reddit client can be initialized
    """
    try:
        client = get_reddit_client()
        return client is not None
    except Exception:
        return False