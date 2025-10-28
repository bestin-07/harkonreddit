"""
Rule-Based Sentiment Analyzer

Implements sentiment analysis using financial lexicon and keyword matching.
Provides fast, reliable sentiment analysis without external model dependencies.
"""

from typing import Dict, List, Optional
from .base_analyzer import BaseSentimentAnalyzer

class RuleBasedAnalyzer(BaseSentimentAnalyzer):
    """
    Rule-based sentiment analyzer using financial keyword lexicon
    
    Features:
    - Financial domain-specific keywords
    - Multi-phrase sentiment detection
    - Weighted scoring based on keyword strength
    - No external dependencies
    """
    
    def __init__(self):
        """Initialize rule-based analyzer with financial lexicon"""
        super().__init__()
        self.analyzer_type = "rule_based"
        self.financial_lexicon = self._build_financial_lexicon()
    
    def _build_financial_lexicon(self) -> Dict[str, List[str]]:
        """Build comprehensive financial sentiment lexicon"""
        return {
            'bullish': [
                # Strong positive indicators
                'moon', 'rocket', 'surge', 'breakout', 'rally', 'pump',
                'diamond hands', 'hodl', 'to the moon', 'bull run',
                'lambo', 'tendies', 'stonks only go up',
                
                # Moderate positive indicators
                'buy', 'long', 'bull', 'bullish', 'strong', 'positive',
                'growth', 'gain', 'rise', 'up', 'green', 'calls',
                'hold', 'support', 'bounce', 'recovery', 'uptrend',
                'momentum', 'reversal', 'catalyst', 'breakthrough',
                
                # Financial positives
                'beat earnings', 'exceed expectations', 'strong revenue',
                'good news', 'upgrade', 'outperform', 'overweight',
                'analyst upgrade', 'price target increase', 'dividend increase',
                'strong fundamentals', 'solid quarter', 'impressive results',
                
                # Technical analysis positive
                'golden cross', 'cup and handle', 'ascending triangle',
                'higher highs', 'bullish flag', 'volume surge'
            ],
            
            'bearish': [
                # Strong negative indicators
                'crash', 'dump', 'panic sell', 'paper hands', 'rug pull',
                'dead cat bounce', 'bear trap', 'capitulation', 'bloodbath',
                'free fall', 'cliff dive', 'bag holder', 'rekt',
                
                # Moderate negative indicators
                'sell', 'short', 'bear', 'bearish', 'weak', 'negative', 
                'loss', 'drop', 'fall', 'decline', 'down', 'red', 'puts',
                'resistance', 'breakdown', 'correction', 'downtrend',
                'profit taking', 'selling pressure', 'margin call',
                
                # Financial negatives
                'miss earnings', 'below expectations', 'weak revenue',
                'bad news', 'downgrade', 'underperform', 'underweight',
                'analyst downgrade', 'price target cut', 'dividend cut',
                'weak fundamentals', 'disappointing quarter', 'poor results',
                'guidance cut', 'warning', 'investigation', 'lawsuit',
                
                # Technical analysis negative
                'death cross', 'head and shoulders', 'descending triangle',
                'lower lows', 'bearish flag', 'volume drop', 'support break'
            ],
            
            'intensifiers': [
                # Words that amplify sentiment
                'very', 'extremely', 'highly', 'massive', 'huge', 'enormous',
                'incredible', 'amazing', 'terrible', 'awful', 'fantastic',
                'outstanding', 'exceptional', 'phenomenal', 'disastrous'
            ]
        }
    
    def analyze_sentiment(self, text: str, timestamp: Optional[str] = None,
                         apply_time_decay: bool = True) -> float:
        """
        Analyze sentiment using rule-based lexicon matching
        
        Args:
            text: Text to analyze
            timestamp: Optional timestamp for time decay
            apply_time_decay: Whether to apply time decay weighting
            
        Returns:
            Sentiment score between -1.0 (bearish) and 1.0 (bullish)
        """
        text_lower = text.lower()
        
        # Initialize scores
        bullish_score = 0.0
        bearish_score = 0.0
        
        # Check for intensifiers first
        intensifier_multiplier = self._calculate_intensifier_boost(text_lower)
        
        # Score bullish keywords
        for keyword in self.financial_lexicon['bullish']:
            if keyword.lower() in text_lower:
                # Multi-word phrases get higher weight
                weight = 2.0 if len(keyword.split()) > 1 else 1.0
                # Apply intensifier boost
                weight *= intensifier_multiplier
                bullish_score += weight
        
        # Score bearish keywords
        for keyword in self.financial_lexicon['bearish']:
            if keyword.lower() in text_lower:
                # Multi-word phrases get higher weight
                weight = 2.0 if len(keyword.split()) > 1 else 1.0
                # Apply intensifier boost
                weight *= intensifier_multiplier
                bearish_score += weight
        
        # Calculate final sentiment
        total_score = bullish_score + bearish_score
        if total_score == 0:
            sentiment = 0.0
        else:
            sentiment = (bullish_score - bearish_score) / total_score
        
        # Apply time decay if requested
        if apply_time_decay and timestamp:
            time_weight = self.calculate_time_weight(timestamp)
            sentiment *= time_weight
        
        return self._clip_value(sentiment, -1.0, 1.0)
    
    def _calculate_intensifier_boost(self, text_lower: str) -> float:
        """Calculate boost from intensifier words"""
        intensifier_count = 0
        for intensifier in self.financial_lexicon['intensifiers']:
            if intensifier.lower() in text_lower:
                intensifier_count += 1
        
        # Cap the boost to avoid extreme scores
        return min(2.0, 1.0 + (intensifier_count * 0.2))
    
    def analyze_post_comprehensive(self, text: str, timestamp: Optional[str] = None) -> Dict:
        """
        Comprehensive analysis with rule-based method
        
        Args:
            text: Post text to analyze
            timestamp: Optional post timestamp
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        # Extract stock symbols
        stocks = self.extract_stock_symbols(text)
        
        if not stocks:
            return {
                'stocks': [],
                'analysis': {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'confidence': 0.0,
                    'method': 'rule_based',
                    'text_length': len(text),
                    'stock_count': 0
                },
                'stock_sentiments': {}
            }
        
        # Analyze sentiment
        sentiment_score = self.analyze_sentiment(text, timestamp)
        
        # Build comprehensive results
        analysis_results = {
            'sentiment_score': sentiment_score,
            'sentiment_label': self.determine_sentiment_label(sentiment_score),
            'confidence': self.calculate_confidence(sentiment_score, len(text), len(stocks)),
            'method': 'rule_based',
            'text_length': len(text),
            'stock_count': len(stocks),
            'keyword_analysis': self._analyze_keywords(text.lower())
        }
        
        return {
            'stocks': stocks,
            'analysis': analysis_results,
            'stock_sentiments': {stock: sentiment_score for stock in stocks}
        }
    
    def _analyze_keywords(self, text_lower: str) -> Dict:
        """Analyze which keywords contributed to the sentiment"""
        found_keywords = {
            'bullish': [],
            'bearish': [],
            'intensifiers': []
        }
        
        for category, keywords in self.financial_lexicon.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_keywords[category].append(keyword)
        
        return {
            'bullish_count': len(found_keywords['bullish']),
            'bearish_count': len(found_keywords['bearish']),
            'intensifier_count': len(found_keywords['intensifiers']),
            'found_keywords': found_keywords
        }