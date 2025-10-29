"""
Service Factory for StockHark

Centralized factory pattern to eliminate component initialization duplication
and provide consistent service configuration across the application.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Import feature flags from constants
from ..constants import FEATURE_FLAGS

logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for StockHark services"""
    # Database configuration
    database_path: str = "data/stocks.db"
    database_timeout: float = 30.0
    
    # Sentiment analysis configuration
    enable_finbert: bool = FEATURE_FLAGS.get('ENABLE_FINBERT', False)
    sentiment_cache_size: int = 1000
    
    # Stock validation configuration
    json_folder_path: str = "data/json"
    validator_silent: bool = True
    
    # Background collection configuration
    collection_interval_minutes: int = 30
    posts_per_subreddit: int = 20
    
    # Reddit API configuration
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "StockHark/1.0"
    
    @classmethod
    def from_environment(cls) -> 'ServiceConfig':
        """Create configuration from environment variables"""
        return cls(
            reddit_client_id=os.getenv('REDDIT_CLIENT_ID', ''),
            reddit_client_secret=os.getenv('REDDIT_CLIENT_SECRET', ''),
            reddit_user_agent=os.getenv('REDDIT_USER_AGENT', 'StockHark/1.0'),
        )


class ServiceFactory:
    """
    Centralized factory for creating and managing StockHark services
    
    Features:
    - Singleton pattern for shared services
    - Lazy initialization
    - Configuration management
    - Dependency injection
    - Service health monitoring
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        """
        Initialize service factory
        
        Args:
            config: Service configuration (defaults to environment-based config)
        """
        self.config = config or ServiceConfig.from_environment()
        self._services: Dict[str, Any] = {}
        self._initialized: Dict[str, bool] = {}
        
        # Setup logging
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup factory logger"""
        logger = logging.getLogger('StockHark.ServiceFactory')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_reddit_client(self):
        """Get Reddit client singleton"""
        if 'reddit_client' not in self._services:
            from ..clients.reddit_client import get_reddit_client
            self._services['reddit_client'] = get_reddit_client()
            self.logger.debug("Reddit client initialized")
        return self._services['reddit_client']
    
    def get_sentiment_analyzer(self, enable_finbert: Optional[bool] = None):
        """Get sentiment analyzer with caching"""
        key = f'sentiment_analyzer_{enable_finbert or self.config.enable_finbert}'
        
        if key not in self._services:
            from ...sentiment_analyzer import EnhancedSentimentAnalyzer
            
            finbert_enabled = enable_finbert if enable_finbert is not None else self.config.enable_finbert
            self._services[key] = EnhancedSentimentAnalyzer(enable_finbert=finbert_enabled)
            self.logger.debug(f"Sentiment analyzer initialized (FinBERT: {finbert_enabled})")
        
        return self._services[key]
    
    def get_stock_validator(self, json_folder_path: Optional[str] = None, silent: Optional[bool] = None):
        """Get stock validator with caching"""
        folder_path = json_folder_path or self.config.json_folder_path
        is_silent = silent if silent is not None else self.config.validator_silent
        
        key = f'stock_validator_{folder_path}_{is_silent}'
        
        if key not in self._services:
            from ..validators.stock_validator import StockValidator
            
            # Resolve relative paths
            if not os.path.isabs(folder_path):
                # Path from service_factory.py: src/stockhark/core/services/service_factory.py
                # parent.parent.parent gives us src/stockhark/, parent.parent.parent.parent gives us src/
                # We want src/data/json, so need to go up 4 levels from current file
                src_dir = Path(__file__).parent.parent.parent.parent
                resolved_path = src_dir / folder_path
                folder_path = str(resolved_path)
            
            self._services[key] = StockValidator(
                json_folder_path=folder_path,
                silent=is_silent
            )
            self.logger.debug(f"Stock validator initialized with {len(self._services[key].all_symbols)} symbols (path: {folder_path})")
        
        return self._services[key]
    
    def get_hybrid_validator(self, json_folder_path: Optional[str] = None, silent: Optional[bool] = None):
        """
        Get hybrid validator (combines current + AI validators)
        Falls back to current validator if AI is disabled or unavailable
        """
        from ..constants import FEATURE_FLAGS, AI_VALIDATOR_MODEL, AI_VALIDATOR_MIN_CONFIDENCE, AI_VALIDATOR_COMBINE_MODE
        
        ai_enabled = FEATURE_FLAGS.get('ENABLE_AI_VALIDATOR', False)
        
        # Create cache key
        folder_path = json_folder_path or self.config.json_folder_path
        is_silent = silent if silent is not None else self.config.validator_silent
        key = f'hybrid_validator_{folder_path}_{is_silent}_{ai_enabled}'
        
        if key not in self._services:
            if ai_enabled:
                try:
                    from ..validators.hybrid_validator import HybridStockValidator
                    
                    # Initialize hybrid validator with AI capabilities
                    self._services[key] = HybridStockValidator(
                        ai_model=AI_VALIDATOR_MODEL,
                        ai_enabled=True,
                        ai_min_confidence=AI_VALIDATOR_MIN_CONFIDENCE,
                        combine_mode=AI_VALIDATOR_COMBINE_MODE
                    )
                    
                    validator_type = "hybrid (AI + current)"
                    if not self._services[key].ai_available:
                        validator_type = "hybrid (current only - AI unavailable)"
                    
                    self.logger.info(f"Hybrid validator initialized: {validator_type}")
                    
                except ImportError as e:
                    # Fallback to current validator if hybrid is not available
                    self.logger.warning(f"Hybrid validator unavailable, using current validator: {e}")
                    self._services[key] = self.get_stock_validator(json_folder_path, silent)
                    
            else:
                # AI disabled - use current validator
                self._services[key] = self.get_stock_validator(json_folder_path, silent)
                self.logger.debug("AI validator disabled, using current validator")
        
        return self._services[key]
    
    def get_validator(self, json_folder_path: Optional[str] = None, silent: Optional[bool] = None):
        """
        Get the best available validator (hybrid if AI enabled, current otherwise)
        This is the recommended method for getting a validator
        """
        from ..constants import FEATURE_FLAGS
        
        if FEATURE_FLAGS.get('ENABLE_AI_VALIDATOR', False):
            return self.get_hybrid_validator(json_folder_path, silent)
        else:
            return self.get_stock_validator(json_folder_path, silent)
    
    def get_database_connection(self):
        """Get database connection (not cached - creates new connections)"""
        from ..data.database import get_db_connection
        return get_db_connection()
    
    def initialize_database(self):
        """Initialize database (idempotent)"""
        if not self._initialized.get('database', False):
            from ..data.database import init_db
            init_db()
            self._initialized['database'] = True
            self.logger.info("Database initialized")
    
    def get_background_collector(self, interval_minutes: Optional[int] = None):
        """Get background collector singleton"""
        if 'background_collector' not in self._services:
            from .background_collector import BackgroundDataCollector
            
            interval = interval_minutes or self.config.collection_interval_minutes
            self._services['background_collector'] = BackgroundDataCollector(
                collection_interval_minutes=interval
            )
            self.logger.debug(f"Background collector initialized (interval: {interval}min)")
        
        return self._services['background_collector']
    
    def get_reddit_monitor(self):
        """Get Reddit monitor"""
        if 'reddit_monitor' not in self._services:
            from ...monitoring.reddit_monitor import RedditMonitor
            self._services['reddit_monitor'] = RedditMonitor()
            self.logger.debug("Reddit monitor initialized")
        
        return self._services['reddit_monitor']
    
    def create_standard_components(self, enable_finbert: Optional[bool] = None):
        """
        Create standard component set used across the application
        
        Args:
            enable_finbert: Whether to enable FinBERT sentiment analysis (defaults to configuration)
            
        Returns:
            tuple: (reddit_client, sentiment_analyzer, stock_validator)
        """
        self.logger.info("Creating standard component set")
        
        # Initialize database first
        self.initialize_database()
        
        # Use configuration default if not explicitly provided
        finbert_enabled = enable_finbert if enable_finbert is not None else self.config.enable_finbert
        
        # Create components
        reddit_client = self.get_reddit_client()
        sentiment_analyzer = self.get_sentiment_analyzer(enable_finbert=finbert_enabled)
        stock_validator = self.get_validator()  # Use best available validator (hybrid if AI enabled)
        
        self.logger.info("Standard components created successfully")
        
        return reddit_client, sentiment_analyzer, stock_validator
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all initialized services"""
        health = {
            'factory_initialized': True,
            'services_count': len(self._services),
            'services': {},
            'configuration': {
                'enable_finbert': self.config.enable_finbert,
                'collection_interval': self.config.collection_interval_minutes,
                'database_path': self.config.database_path
            }
        }
        
        # Check individual service health
        for service_name, service in self._services.items():
            try:
                if hasattr(service, 'is_healthy'):
                    health['services'][service_name] = service.is_healthy()
                elif hasattr(service, 'get_stats'):
                    health['services'][service_name] = service.get_stats()
                else:
                    health['services'][service_name] = 'initialized'
            except Exception as e:
                health['services'][service_name] = f'error: {str(e)}'
        
        return health
    
    def shutdown_services(self):
        """Gracefully shutdown all services"""
        self.logger.info("Shutting down services")
        
        for service_name, service in self._services.items():
            try:
                if hasattr(service, 'stop'):
                    service.stop()
                elif hasattr(service, 'close'):
                    service.close()
                self.logger.debug(f"Service {service_name} shut down")
            except Exception as e:
                self.logger.error(f"Error shutting down {service_name}: {e}")
        
        self._services.clear()
        self._initialized.clear()
        self.logger.info("All services shut down")


# Global factory instance
_service_factory: Optional[ServiceFactory] = None

def get_service_factory(config: Optional[ServiceConfig] = None) -> ServiceFactory:
    """
    Get the global service factory instance
    
    Args:
        config: Optional configuration (only used on first call)
        
    Returns:
        ServiceFactory: The global factory instance
    """
    global _service_factory
    
    if _service_factory is None:
        _service_factory = ServiceFactory(config)
    
    return _service_factory

def create_standard_components(enable_finbert: Optional[bool] = None):
    """
    Convenience function to create standard component set
    
    Args:
        enable_finbert: Whether to enable FinBERT sentiment analysis (defaults to configuration)
        
    Returns:
        tuple: (reddit_client, sentiment_analyzer, stock_validator)
    """
    factory = get_service_factory()
    # Use configuration default if not explicitly provided
    finbert_enabled = enable_finbert if enable_finbert is not None else FEATURE_FLAGS.get('ENABLE_FINBERT', False)
    return factory.create_standard_components(enable_finbert=finbert_enabled)

def shutdown_all_services():
    """Shutdown all services in the global factory"""
    global _service_factory
    if _service_factory:
        _service_factory.shutdown_services()
        _service_factory = None