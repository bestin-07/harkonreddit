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
            # Try to import FinBERT dependencies
            from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
            import torch
            
            # Initialize FinBERT model and tokenizer
            model_name = "ProsusAI/finbert"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            
            # Create sentiment analysis pipeline
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1  # Use GPU if available
            )
            
            self.finbert_impl = True
            print(f"✅ FinBERT model loaded successfully ({'GPU' if torch.cuda.is_available() else 'CPU'})")
            
        except (ImportError, RuntimeError, Exception) as e:
            # FinBERT not available, this analyzer will fallback gracefully
            self.finbert_impl = None
            raise RuntimeError(f"FinBERT not available: {e}")
    
    def is_available(self) -> bool:
        """Check if FinBERT is available for analysis"""
        return self.finbert_impl is not None and hasattr(self, 'sentiment_pipeline')
    
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
            # Clean and prepare text
            text = text.strip()
            if not text:
                return 0.0
            
            # Truncate text if too long (FinBERT has token limits)
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]
            
            # Use FinBERT pipeline for sentiment analysis
            result = self.sentiment_pipeline(text)[0]
            
            # Convert FinBERT labels to numerical scores
            label = result['label'].lower()
            confidence = result['score']
            
            if label == 'positive':
                sentiment_score = confidence  # Bullish: 0 to 1
            elif label == 'negative':
                sentiment_score = -confidence  # Bearish: -1 to 0
            else:  # neutral
                sentiment_score = 0.0
            
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
            
            # Get FinBERT raw results for confidence
            finbert_result = self.sentiment_pipeline(text[:512])[0]
            finbert_confidence = finbert_result['score']
            
            # Build comprehensive results
            analysis_results = {
                'sentiment_score': sentiment_score,
                'sentiment_label': self.determine_sentiment_label(sentiment_score),
                'confidence': finbert_confidence,  # Use FinBERT's confidence directly
                'method': 'finbert',
                'text_length': len(text),
                'stock_count': len(stocks),
                'finbert_label': finbert_result['label'],
                'finbert_confidence': finbert_confidence
            }
            
            return {
                'stocks': stocks,
                'analysis': analysis_results,
                'stock_sentiments': {stock: sentiment_score for stock in stocks}
            }
            
        except Exception as e:
            raise RuntimeError(f"FinBERT comprehensive analysis failed: {e}")
    
    def analyze_posts_batch(self, posts: List[Dict]) -> Dict[str, Dict]:
        """
        Batch analysis using FinBERT
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary mapping stock symbols to aggregated sentiment data
        """
        if not self.is_available():
            raise RuntimeError("FinBERT analyzer not available")
        
        # Use base class batch processing (processes posts individually with FinBERT)
        return super().analyze_posts_batch(posts)