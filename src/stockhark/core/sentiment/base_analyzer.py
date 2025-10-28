"""
Base Sentiment Analyzer Interface

Defines the contract that all sentiment analyzers must implement
for consistent behavior across different analysis methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from datetime import datetime

class BaseSentimentAnalyzer(ABC):
    """
    Abstract base class for sentiment analyzers
    
    Provides consistent interface for all sentiment analysis implementations
    """
    
    def __init__(self):
        """Initialize the base analyzer"""
        self.analyzer_type = "base"
    
    @abstractmethod
    def analyze_sentiment(self, text: str, timestamp: Optional[str] = None,
                         apply_time_decay: bool = True) -> float:
        """
        Analyze sentiment of text
        
        Args:
            text: Text to analyze
            timestamp: Optional timestamp for time decay
            apply_time_decay: Whether to apply time decay weighting
            
        Returns:
            Sentiment score between -1.0 (bearish) and 1.0 (bullish)
        """
        pass
    
    @abstractmethod
    def analyze_post_comprehensive(self, text: str, timestamp: Optional[str] = None) -> Dict:
        """
        Comprehensive post analysis returning detailed results
        
        Args:
            text: Post text to analyze
            timestamp: Optional post timestamp
            
        Returns:
            Dictionary with comprehensive analysis results including:
            - stocks: List of detected stock symbols
            - analysis: Analysis metadata (score, label, confidence, method)
            - stock_sentiments: Per-stock sentiment mapping
        """
        pass
    
    def extract_stock_symbols(self, text: str) -> List[str]:
        """
        Extract stock symbols from text
        Default implementation using regex pattern
        
        Args:
            text: Text to search for stock symbols
            
        Returns:
            List of unique stock symbols found
        """
        import re
        stock_pattern = re.compile(r'\\b[A-Z]{1,5}\\b')
        matches = stock_pattern.findall(text.upper())
        return list(set(matches))  # Remove duplicates
    
    def determine_sentiment_label(self, sentiment_score: float) -> str:
        """
        Convert sentiment score to categorical label
        
        Args:
            sentiment_score: Numerical sentiment score
            
        Returns:
            String label: 'bullish', 'bearish', or 'neutral'
        """
        if sentiment_score > 0.1:
            return 'bullish'
        elif sentiment_score < -0.1:
            return 'bearish'
        else:
            return 'neutral'
    
    def calculate_confidence(self, sentiment_score: float, text_length: int = 0,
                           stock_count: int = 1) -> float:
        """
        Calculate confidence score for sentiment analysis
        
        Args:
            sentiment_score: Numerical sentiment score
            text_length: Length of analyzed text
            stock_count: Number of stocks mentioned
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence from absolute sentiment strength
        base_confidence = min(1.0, abs(sentiment_score) * 2)
        
        # Boost confidence for longer texts (more context)
        length_boost = min(0.2, text_length / 1000) if text_length > 0 else 0
        
        # Slightly reduce confidence for multiple stocks (diluted focus)
        stock_penalty = max(0, (stock_count - 1) * 0.05) if stock_count > 1 else 0
        
        final_confidence = base_confidence + length_boost - stock_penalty
        return max(0.0, min(1.0, final_confidence))
    
    def analyze_posts_batch(self, posts: List[Dict]) -> Dict[str, Dict]:
        """
        Default batch processing implementation
        Subclasses can override for more efficient batch processing
        
        Args:
            posts: List of post dictionaries with 'text' and optional 'timestamp'
            
        Returns:
            Dictionary mapping stock symbols to aggregated sentiment data
        """
        stock_data = {}
        
        for post in posts:
            text = post.get('text', '')
            timestamp = post.get('timestamp')
            
            if not text:
                continue
                
            result = self.analyze_post_comprehensive(text, timestamp)
            
            for stock in result['stocks']:
                if stock not in stock_data:
                    stock_data[stock] = {
                        'sentiment_scores': [],
                        'mentions': 0
                    }
                
                stock_data[stock]['sentiment_scores'].append(result['analysis']['sentiment_score'])
                stock_data[stock]['mentions'] += 1
        
        # Calculate final aggregated results
        final_results = {}
        for stock, data in stock_data.items():
            scores = data['sentiment_scores']
            avg_sentiment = sum(scores) / len(scores) if scores else 0.0
            
            final_results[stock] = {
                'sentiment_score': self._clip_value(avg_sentiment, -1.0, 1.0),
                'sentiment_label': self.determine_sentiment_label(avg_sentiment),
                'mentions': data['mentions'],
                'confidence': self.calculate_confidence(avg_sentiment, 0, len(scores)),
                'method': f'{self.analyzer_type}_batch'
            }
        
        return final_results
    
    def _clip_value(self, value: float, min_val: float, max_val: float) -> float:
        """Utility method to clip values to range"""
        return max(min_val, min(max_val, value))
    
    def calculate_time_weight(self, timestamp: Union[str, datetime], 
                            decay_lambda: float = 0.1) -> float:
        """
        Calculate time decay weight for sentiment analysis
        
        Args:
            timestamp: Timestamp string or datetime object
            decay_lambda: Decay rate (higher = faster decay)
            
        Returns:
            Time weight between 0.0 and 1.0
        """
        try:
            # Parse timestamp if string
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)
            
            # Calculate hours elapsed
            hours_elapsed = (datetime.now() - timestamp).total_seconds() / 3600
            
            # Apply exponential decay
            import math
            return float(math.exp(-decay_lambda * max(0, hours_elapsed)))
            
        except Exception:
            return 1.0  # No decay on error