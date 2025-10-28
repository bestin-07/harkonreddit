"""
Enhanced Sentiment Analyzer

Intelligent sentiment analysis system with FinBERT integration and graceful fallback.
Provides drop-in replacement for basic sentiment analysis while leveraging
advanced financial domain knowledge when available.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

# Suppress transformer warnings
logging.getLogger("transformers").setLevel(logging.ERROR)

class EnhancedSentimentAnalyzer:
    """
    Hybrid sentiment analyzer with FinBERT primary and rule-based fallback
    
    Features:
    - Automatic FinBERT integration when available
    - Graceful fallback to rule-based analysis
    - Consistent API regardless of backend
    - Time-aware sentiment weighting
    """
    
    def __init__(self, enable_finbert: bool = True):
        """
        Initialize enhanced sentiment analyzer
        
        Args:
            enable_finbert: Whether to attempt FinBERT loading (default: True)
        """
        self.finbert_analyzer = None
        self.use_finbert = False
        
        # Stock symbol pattern (1-5 uppercase letters)  
        self.stock_pattern = re.compile(r'\b[A-Z]{1,5}\b')
        
        # Initialize FinBERT if requested and available
        if enable_finbert:
            self._initialize_finbert()
        
        # Financial lexicon for fallback analysis
        self.financial_lexicon = self._build_financial_lexicon()
    
    def _initialize_finbert(self) -> None:
        """Attempt to initialize FinBERT analyzer"""
        try:
            from .finbert_analyzer import FinBERTSentimentAnalyzer
            self.finbert_analyzer = FinBERTSentimentAnalyzer()
            self.use_finbert = True
            
        except (ImportError, RuntimeError, Exception):
            # Silently fall back to rule-based analysis
            self.use_finbert = False
    
    def _build_financial_lexicon(self) -> Dict[str, List[str]]:
        """Build financial sentiment lexicon for fallback analysis"""
        return {
            'bullish': [
                # Strong positive
                'moon', 'rocket', 'surge', 'breakout', 'rally', 'pump',
                'diamond hands', 'hodl', 'to the moon', 'bull run',
                
                # Moderate positive  
                'buy', 'long', 'bull', 'bullish', 'strong', 'positive',
                'growth', 'gain', 'rise', 'up', 'green', 'calls',
                'hold', 'support', 'bounce', 'recovery',
                
                # Financial positives
                'beat earnings', 'exceed expectations', 'strong revenue',
                'good news', 'upgrade', 'outperform', 'overweight'
            ],
            
            'bearish': [
                # Strong negative
                'crash', 'dump', 'panic sell', 'paper hands', 'rug pull',
                'dead cat bounce', 'bear trap', 'capitulation',
                
                # Moderate negative
                'sell', 'short', 'bear', 'bearish', 'weak', 'negative', 
                'loss', 'drop', 'fall', 'decline', 'down', 'red', 'puts',
                'resistance', 'breakdown', 'correction',
                
                # Financial negatives  
                'miss earnings', 'below expectations', 'weak revenue',
                'bad news', 'downgrade', 'underperform', 'underweight'
            ]
        }
    
    def analyze_sentiment(self, text: str, timestamp: Optional[str] = None,
                         apply_time_decay: bool = True) -> float:
        """
        Analyze sentiment of text using best available method
        
        Args:
            text: Text to analyze
            timestamp: Optional timestamp for time decay
            apply_time_decay: Whether to apply time decay weighting
            
        Returns:
            Sentiment score between -1.0 (bearish) and 1.0 (bullish)
        """
        if self.use_finbert and self.finbert_analyzer:
            return self._finbert_sentiment(text, timestamp, apply_time_decay)
        else:
            return self._rule_based_sentiment(text, timestamp, apply_time_decay)
    
    def _finbert_sentiment(self, text: str, timestamp: Optional[str] = None,
                          apply_time_decay: bool = True) -> float:
        """FinBERT-based sentiment analysis with optional time decay"""
        try:
            # Get base sentiment from FinBERT
            sentiment_score, _ = self.finbert_analyzer.analyze_text_sentiment(text)
            
            # Apply time decay if requested and timestamp available
            if apply_time_decay and timestamp:
                time_weight = self.finbert_analyzer.calculate_time_weight(timestamp)
                sentiment_score *= time_weight
            
            return float(np.clip(sentiment_score, -1.0, 1.0))
            
        except Exception:
            # Fall back to rule-based on any error
            return self._rule_based_sentiment(text, timestamp, apply_time_decay)
    
    def _rule_based_sentiment(self, text: str, timestamp: Optional[str] = None,
                             apply_time_decay: bool = True) -> float:
        """Rule-based sentiment analysis using financial lexicon"""
        text_lower = text.lower()
        
        # Count sentiment indicators
        bullish_score = 0
        bearish_score = 0
        
        # Score based on keyword presence and strength
        for word in self.financial_lexicon['bullish']:
            if word in text_lower:
                # Weight stronger sentiment words more heavily
                weight = 2.0 if len(word.split()) > 1 else 1.0
                bullish_score += weight
        
        for word in self.financial_lexicon['bearish']:
            if word in text_lower:
                # Weight stronger sentiment words more heavily  
                weight = 2.0 if len(word.split()) > 1 else 1.0
                bearish_score += weight
        
        # Calculate sentiment score
        total_score = bullish_score + bearish_score
        if total_score == 0:
            sentiment = 0.0
        else:
            sentiment = (bullish_score - bearish_score) / total_score
        
        # Apply time decay if requested
        if apply_time_decay and timestamp:
            time_weight = self._calculate_time_weight(timestamp)
            sentiment *= time_weight
        
        return float(np.clip(sentiment, -1.0, 1.0))
    
    def _calculate_time_weight(self, timestamp: str, decay_lambda: float = 0.1) -> float:
        """Calculate time decay weight for rule-based analysis"""
        try:
            # Parse timestamp
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)
            
            # Calculate hours elapsed
            hours_elapsed = (datetime.now() - timestamp).total_seconds() / 3600
            
            # Apply exponential decay
            import numpy as np
            return float(np.exp(-decay_lambda * max(0, hours_elapsed)))
            
        except Exception:
            return 1.0  # No decay on error
    
    def extract_stock_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text"""
        matches = self.stock_pattern.findall(text.upper())
        return list(set(matches))  # Remove duplicates
    
    def analyze_post_comprehensive(self, text: str, timestamp: Optional[str] = None) -> Dict:
        """
        Comprehensive post analysis returning detailed results
        
        Args:
            text: Post text to analyze
            timestamp: Optional post timestamp
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        # Extract stock symbols
        stocks = self.extract_stock_symbols(text)
        
        if not stocks:
            return {'stocks': [], 'analysis': {}}
        
        # Analyze sentiment
        sentiment_score = self.analyze_sentiment(text, timestamp)
        
        # Determine sentiment label
        if sentiment_score > 0.1:
            sentiment_label = 'bullish'
        elif sentiment_score < -0.1:
            sentiment_label = 'bearish'
        else:
            sentiment_label = 'neutral'
        
        # Build comprehensive results
        analysis_results = {
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'confidence': min(1.0, abs(sentiment_score) * 2),  # Simple confidence
            'method': 'finbert' if self.use_finbert else 'rule_based',
            'text_length': len(text),
            'stock_count': len(stocks)
        }
        
        return {
            'stocks': stocks,
            'analysis': analysis_results,
            'stock_sentiments': {stock: sentiment_score for stock in stocks}
        }
    
    def analyze_posts_batch(self, posts: List[Dict]) -> Dict[str, Dict]:
        """
        Analyze multiple posts efficiently
        
        Args:
            posts: List of post dictionaries with 'text' and optional 'timestamp'
            
        Returns:
            Dictionary mapping stock symbols to aggregated sentiment data
        """
        if self.use_finbert and self.finbert_analyzer:
            # Use FinBERT batch processing if available
            return self.finbert_analyzer.analyze_posts_batch(posts)
        
        # Fallback to individual processing
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
                'sentiment_score': float(np.clip(avg_sentiment, -1.0, 1.0)),
                'sentiment_label': 'bullish' if avg_sentiment > 0.1 else 'bearish' if avg_sentiment < -0.1 else 'neutral',
                'mentions': data['mentions'],
                'confidence': min(1.0, abs(avg_sentiment) * (len(scores) / 10)),  # Scale by mention count
                'method': 'rule_based_batch'
            }
        
        return final_results

# Import numpy here to avoid issues if not available at module level
try:
    import numpy as np
except ImportError:
    # Create minimal numpy-like functionality for clipping
    class MockNumpy:
        @staticmethod
        def clip(value, min_val, max_val):
            return max(min_val, min(max_val, value))
        
        @staticmethod  
        def exp(value):
            import math
            return math.exp(value)
    
    np = MockNumpy()