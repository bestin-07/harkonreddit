"""
FinBERT Sentiment Analyzer

Wrapper around the existing FinBERT implementation to conform to the new interface.
Provides advanced financial sentiment analysis using transformer models.
"""

from typing import Dict, List, Optional
from .base_analyzer import BaseSentimentAnalyzer

class FinBERTAnalyzer(BaseSentimentAnalyzer):
    """
    FinBERT-based sentiment analyzer wrapper
    
    Integrates the existing FinBERT implementation with the new analyzer interface
    """
    
    def __init__(self):
        """Initialize FinBERT analyzer"""
        super().__init__()
        self.analyzer_type = "finbert"
        self.finbert_impl = None
        
        # Try to initialize the actual FinBERT implementation
        self._initialize_finbert()
    
    def _initialize_finbert(self) -> None:
        """Initialize the actual FinBERT implementation"""
        try:
            # Import the existing FinBERT analyzer
            from core.finbert_analyzer import FinBERTSentimentAnalyzer
            self.finbert_impl = FinBERTSentimentAnalyzer()
            
        except (ImportError, RuntimeError, Exception) as e:
            # FinBERT not available, this analyzer will fallback gracefully
            self.finbert_impl = None
            raise RuntimeError(f"FinBERT not available: {e}")
    
    def is_available(self) -> bool:
        """Check if FinBERT is available for analysis"""
        return self.finbert_impl is not None
    
    def analyze_sentiment(self, text: str, timestamp: Optional[str] = None,
                         apply_time_decay: bool = True) -> float:
        """
        Analyze sentiment using FinBERT
        
        Args:
            text: Text to analyze
            timestamp: Optional timestamp for time decay
            apply_time_decay: Whether to apply time decay weighting
            
        Returns:
            Sentiment score between -1.0 (bearish) and 1.0 (bullish)
        """
        if not self.is_available():
            raise RuntimeError("FinBERT analyzer not available")
        
        try:
            # Use existing FinBERT implementation
            sentiment_score, _ = self.finbert_impl.analyze_text_sentiment(text)
            
            # Apply time decay if requested
            if apply_time_decay and timestamp:
                time_weight = self.calculate_time_weight(timestamp)
                sentiment_score *= time_weight
            
            return self._clip_value(sentiment_score, -1.0, 1.0)
            
        except Exception as e:
            raise RuntimeError(f"FinBERT analysis failed: {e}")
    
    def analyze_post_comprehensive(self, text: str, timestamp: Optional[str] = None) -> Dict:
        """
        Comprehensive analysis using FinBERT
        
        Args:
            text: Post text to analyze
            timestamp: Optional post timestamp
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        if not self.is_available():
            raise RuntimeError("FinBERT analyzer not available")
        
        # Extract stock symbols
        stocks = self.extract_stock_symbols(text)
        
        if not stocks:
            return {
                'stocks': [],
                'analysis': {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'confidence': 0.0,
                    'method': 'finbert',
                    'text_length': len(text),
                    'stock_count': 0
                },
                'stock_sentiments': {}
            }
        
        try:
            # Analyze sentiment using FinBERT
            sentiment_score = self.analyze_sentiment(text, timestamp)
            
            # Get additional analysis if available
            additional_analysis = {}
            if hasattr(self.finbert_impl, 'analyze_text_comprehensive'):
                additional_analysis = self.finbert_impl.analyze_text_comprehensive(text)
            
            # Build comprehensive results
            analysis_results = {
                'sentiment_score': sentiment_score,
                'sentiment_label': self.determine_sentiment_label(sentiment_score),
                'confidence': self.calculate_confidence(sentiment_score, len(text), len(stocks)),
                'method': 'finbert',
                'text_length': len(text),
                'stock_count': len(stocks)
            }
            
            # Add FinBERT-specific analysis if available
            if additional_analysis:
                analysis_results.update(additional_analysis)
            
            return {
                'stocks': stocks,
                'analysis': analysis_results,
                'stock_sentiments': {stock: sentiment_score for stock in stocks}
            }
            
        except Exception as e:
            raise RuntimeError(f"FinBERT comprehensive analysis failed: {e}")
    
    def analyze_posts_batch(self, posts: List[Dict]) -> Dict[str, Dict]:
        """
        Batch analysis using FinBERT (if supported)
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary mapping stock symbols to aggregated sentiment data
        """
        if not self.is_available():
            raise RuntimeError("FinBERT analyzer not available")
        
        # Check if FinBERT implementation supports batch processing
        if hasattr(self.finbert_impl, 'analyze_posts_batch'):
            try:
                return self.finbert_impl.analyze_posts_batch(posts)
            except Exception:
                # Fall back to individual processing
                pass
        
        # Use base class batch processing as fallback
        return super().analyze_posts_batch(posts)