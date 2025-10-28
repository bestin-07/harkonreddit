"""
Enhanced Sentiment Analyzer with FinBERT Integration
Drop-in replacement for existing sentiment analysis
"""

from .finbert_analyzer import FinBERTSentimentAnalyzer
from datetime import datetime
import re

class EnhancedSentimentAnalyzer:
    def __init__(self):
        try:
            self.finbert = FinBERTSentimentAnalyzer()
            self.use_finbert = True
            print("✅ FinBERT loaded successfully")
        except ImportError:
            self.use_finbert = False
            print("⚠️  FinBERT not available, using basic sentiment")
        
        # Stock pattern
        self.stock_pattern = re.compile(r'\b[A-Z]{1,5}\b')
    
    def analyze_sentiment(self, text, timestamp=None):
        """Analyze sentiment with FinBERT or fallback to basic"""
        if self.use_finbert:
            return self._finbert_sentiment(text, timestamp)
        else:
            return self._basic_sentiment(text)
    
    def _finbert_sentiment(self, text, timestamp=None):
        """FinBERT-based sentiment analysis"""
        sentiment_score, _ = self.finbert.get_sentence_sentiment(text)
        
        # Apply time decay if timestamp provided
        if timestamp:
            time_weight = self.finbert.time_decay_weight(timestamp)
            sentiment_score *= time_weight
        
        # Normalize
        return max(min(sentiment_score, 1.0), -1.0)
    
    def _basic_sentiment(self, text):
        """Fallback basic sentiment (simplified)"""
        positive_words = ['good', 'great', 'buy', 'bull', 'up', 'gain', 'profit']
        negative_words = ['bad', 'sell', 'bear', 'down', 'loss', 'drop', 'crash']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        sentiment = (pos_count - neg_count) / (pos_count + neg_count)
        return max(min(sentiment, 1.0), -1.0)
    
    def extract_stock_mentions(self, text):
        """Extract stock symbols"""
        return list(set(self.stock_pattern.findall(text.upper())))
    
    def analyze_post_with_stocks(self, text, timestamp=None):
        """Analyze post and return stock sentiments"""
        stocks = self.extract_stock_mentions(text)
        if not stocks:
            return {}
        
        sentiment = self.analyze_sentiment(text, timestamp)
        
        # Return sentiment for each stock mentioned
        return {stock: sentiment for stock in stocks}