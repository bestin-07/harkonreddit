"""
Enhanced Sentiment Analysis - Refactored Version

This is the new enhanced sentiment module that uses the modular sentiment analysis
system. It maintains backward compatibility while providing cleaner architecture.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
import time

from .sentiment import create_enhanced_analyzer, BaseSentimentAnalyzer
from .core.services.service_factory import ServiceFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedSentimentAnalyzer:
    """
    Enhanced sentiment analyzer that combines multiple analysis approaches
    
    This is the refactored version that uses the modular sentiment system
    while maintaining full backward compatibility with existing code.
    """
    
    def __init__(self, enable_finbert: bool = True):
        """
        Initialize the enhanced sentiment analyzer
        
        Args:
            enable_finbert: Whether to enable FinBERT analysis
        """
        self.enable_finbert = enable_finbert
        self._analyzer = None
        self._service_factory = None
        self._initialization_time = None
        
        # Initialize analyzer
        self._initialize_analyzer()
    
    def _initialize_analyzer(self):
        """Initialize the sentiment analyzer with timing"""
        start_time = time.time()
        
        try:
            self._analyzer = create_enhanced_analyzer(enable_finbert=self.enable_finbert)
            self._initialization_time = time.time() - start_time
            
            analyzer_type = type(self._analyzer).__name__
            logger.info(f"[SUCCESS] Enhanced sentiment analyzer initialized with {analyzer_type} "
                       f"in {self._initialization_time:.2f}s")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize sentiment analyzer: {e}")
            raise
    
    @property
    def service_factory(self) -> ServiceFactory:
        """Get service factory instance"""
        if self._service_factory is None:
            self._service_factory = ServiceFactory()
        return self._service_factory
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not self._analyzer:
            raise RuntimeError("Sentiment analyzer not initialized")
        
        return self._analyzer.analyze_sentiment(text)
    
    def analyze_post_comprehensive(self, 
                                 post_data: Dict[str, Any],
                                 include_comments: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a Reddit post
        
        Args:
            post_data: Reddit post data dictionary
            include_comments: Whether to include comment analysis
            
        Returns:
            Comprehensive analysis results
        """
        if not self._analyzer:
            raise RuntimeError("Sentiment analyzer not initialized")
        
        return self._analyzer.analyze_post_comprehensive(post_data, include_comments)
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        results = []
        for text in texts:
            try:
                result = self.analyze_sentiment(text)
                results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing text batch item: {e}")
                results.append({
                    'sentiment': 'neutral',
                    'confidence': 0.0,
                    'compound': 0.0,
                    'error': str(e)
                })
        
        return results
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """
        Get information about the current analyzer
        
        Returns:
            Dictionary with analyzer information
        """
        if not self._analyzer:
            return {'status': 'not_initialized'}
        
        analyzer_type = type(self._analyzer).__name__
        
        info = {
            'analyzer_type': analyzer_type,
            'initialization_time': self._initialization_time,
            'finbert_enabled': self.enable_finbert,
            'status': 'initialized'
        }
        
        # Add analyzer-specific info
        if hasattr(self._analyzer, 'is_available'):
            info['analyzer_available'] = self._analyzer.is_available()
        
        if hasattr(self._analyzer, 'get_info'):
            info.update(self._analyzer.get_info())
        
        return info
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the analyzer
        
        Returns:
            Health status information
        """
        try:
            # Test with sample text
            test_result = self.analyze_sentiment("This is a test message for health check.")
            
            health_status = {
                'status': 'healthy',
                'analyzer_info': self.get_analyzer_info(),
                'test_result': test_result,
                'timestamp': time.time()
            }
            
        except Exception as e:
            health_status = {
                'status': 'unhealthy',
                'error': str(e),
                'analyzer_info': self.get_analyzer_info(),
                'timestamp': time.time()
            }
        
        return health_status

# Singleton instance for backward compatibility
_global_analyzer = None

def get_enhanced_analyzer(enable_finbert: bool = True) -> EnhancedSentimentAnalyzer:
    """
    Get global enhanced sentiment analyzer instance
    
    Args:
        enable_finbert: Whether to enable FinBERT
        
    Returns:
        Enhanced sentiment analyzer instance
    """
    global _global_analyzer
    
    if _global_analyzer is None:
        _global_analyzer = EnhancedSentimentAnalyzer(enable_finbert=enable_finbert)
    
    return _global_analyzer

def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Convenience function for sentiment analysis (backward compatibility)
    
    Args:
        text: Text to analyze
        
    Returns:
        Sentiment analysis results
    """
    analyzer = get_enhanced_analyzer()
    return analyzer.analyze_sentiment(text)

def analyze_post_comprehensive(post_data: Dict[str, Any], 
                             include_comments: bool = True) -> Dict[str, Any]:
    """
    Convenience function for comprehensive post analysis (backward compatibility)
    
    Args:
        post_data: Reddit post data
        include_comments: Whether to include comments
        
    Returns:
        Comprehensive analysis results
    """
    analyzer = get_enhanced_analyzer()
    return analyzer.analyze_post_comprehensive(post_data, include_comments)

# Legacy compatibility functions
def get_sentiment_analyzer():
    """Legacy function for getting analyzer"""
    return get_enhanced_analyzer()

def initialize_sentiment_analyzer(enable_finbert: bool = True):
    """Legacy function for initializing analyzer"""
    global _global_analyzer
    _global_analyzer = EnhancedSentimentAnalyzer(enable_finbert=enable_finbert)
    return _global_analyzer