"""
FinBERT Financial Sentiment Analyzer

Optimized implementation using ProsusAI/finbert for financial text analysis
with time decay weighting and proper normalization.

Features:
- Financial domain-specific sentiment analysis
- Time decay weighting for recent posts
- Batch processing capabilities
- Thread-safe design
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from datetime import datetime
import re
import logging
from typing import Dict, List, Tuple, Optional, Union

# Configure logging for errors only
logging.getLogger("transformers").setLevel(logging.ERROR)

class FinBERTSentimentAnalyzer:
    """
    Advanced financial sentiment analyzer using FinBERT model
    
    Attributes:
        model: Pre-trained FinBERT model
        tokenizer: FinBERT tokenizer
        decay_lambda: Time decay parameter (default: 0.1)
        max_length: Maximum token length for processing (default: 512)
    """
    
    def __init__(self, decay_lambda: float = 0.1, max_length: int = 512):
        """
        Initialize FinBERT analyzer
        
        Args:
            decay_lambda: Time decay rate parameter
            max_length: Maximum sequence length for tokenization
        """
        try:
            # Load ProsusAI/finbert model components
            self.tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finbert')
            self.model = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')
            self.model.eval()  # Set to evaluation mode
            
            # Configuration parameters
            self.decay_lambda = decay_lambda
            self.max_length = max_length
            
            # Stock symbol extraction pattern (1-5 uppercase letters)
            self.stock_pattern = re.compile(r'\b[A-Z]{1,5}\b')
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize FinBERT model: {e}")
    
    def analyze_text_sentiment(self, text: str) -> Tuple[float, Dict[str, float]]:
        """
        Analyze sentiment of input text using FinBERT
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (sentiment_score, probability_dict)
            sentiment_score: Float between -1 (bearish) and +1 (bullish)
            probability_dict: Dict with 'positive', 'neutral', 'negative' probabilities
        """
        try:
            # Tokenize input text
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                max_length=self.max_length,
                padding=True
            )
            
            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Extract probabilities (FinBERT order: [negative, neutral, positive])
            neg_prob, neu_prob, pos_prob = probabilities[0].numpy()
            
            # Calculate sentiment score: P(positive) - P(negative)
            sentiment_score = float(pos_prob - neg_prob)
            
            probability_dict = {
                "positive": float(pos_prob),
                "neutral": float(neu_prob),
                "negative": float(neg_prob)
            }
            
            return sentiment_score, probability_dict
            
        except Exception as e:
            # Return neutral sentiment on error
            return 0.0, {"positive": 0.33, "neutral": 0.34, "negative": 0.33}
    
    def extract_stock_symbols(self, text: str) -> List[str]:
        """
        Extract potential stock symbols from text
        
        Args:
            text: Input text to search
            
        Returns:
            List of unique uppercase stock symbols
        """
        matches = self.stock_pattern.findall(text.upper())
        return list(set(matches))  # Remove duplicates
    
    def calculate_time_weight(self, timestamp: Union[str, datetime], 
                            current_time: Optional[datetime] = None) -> float:
        """
        Calculate time decay weight using exponential decay formula
        
        Formula: w_t = e^(-λ * Δt)
        Where λ is decay_lambda and Δt is time difference in hours
        
        Args:
            timestamp: Post timestamp (string or datetime)
            current_time: Reference time (defaults to now)
            
        Returns:
            Time weight between 0 and 1
        """
        try:
            # Convert string timestamp to datetime if needed
            if isinstance(timestamp, str):
                # Handle ISO format with timezone
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)
            
            # Use current time as reference
            if current_time is None:
                current_time = datetime.now()
            
            # Calculate time difference in hours
            time_delta_hours = (current_time - timestamp).total_seconds() / 3600
            
            # Apply exponential decay: w_t = e^(-λ * Δt)
            weight = np.exp(-self.decay_lambda * max(0, time_delta_hours))
            
            return float(weight)
            
        except Exception:
            # Return neutral weight on error
            return 1.0
    
    def analyze_posts_batch(self, posts: List[Dict], source_weight: float = 1.0) -> Dict[str, Dict]:
        """
        Analyze sentiment for multiple posts with stock mentions
        
        Args:
            posts: List of post dictionaries with 'text', 'timestamp', and optional 'stocks'
            source_weight: Weight for source reliability (default: 1.0)
            
        Returns:
            Dictionary mapping stock symbols to sentiment data
        """
        stock_data = {}
        
        for post in posts:
            text = post.get('text', '')
            timestamp = post.get('timestamp')
            
            if not text:
                continue
            
            # Extract stock symbols if not provided
            stocks = post.get('stocks', self.extract_stock_symbols(text))
            
            if not stocks:
                continue
            
            # Analyze sentiment for this post
            sentiment_score, probabilities = self.analyze_text_sentiment(text)
            
            # Calculate time weight
            time_weight = self.calculate_time_weight(timestamp) if timestamp else 1.0
            
            # Combined weight
            total_weight = time_weight * source_weight
            
            # Store data for each mentioned stock
            for stock in stocks:
                if stock not in stock_data:
                    stock_data[stock] = {
                        'scores': [],
                        'weights': [],
                        'probabilities': []
                    }
                
                stock_data[stock]['scores'].append(sentiment_score)
                stock_data[stock]['weights'].append(total_weight)
                stock_data[stock]['probabilities'].append(probabilities)
        
        # Calculate final weighted sentiment for each stock
        return self._calculate_final_sentiments(stock_data)
    
    def _calculate_final_sentiments(self, stock_data: Dict) -> Dict[str, Dict]:
        """
        Calculate final weighted sentiment scores for stocks
        
        Args:
            stock_data: Raw stock data with scores and weights
            
        Returns:
            Dictionary with final sentiment analysis for each stock
        """
        final_results = {}
        
        for stock, data in stock_data.items():
            scores = np.array(data['scores'])
            weights = np.array(data['weights'])
            
            if len(scores) == 0:
                continue
            
            # Calculate weighted average sentiment
            weighted_sentiment = np.average(scores, weights=weights)
            
            # Normalize to [-1, 1] range
            normalized_sentiment = np.clip(weighted_sentiment, -1.0, 1.0)
            
            # Determine sentiment label
            if normalized_sentiment > 0.1:
                sentiment_label = 'bullish'
            elif normalized_sentiment < -0.1:
                sentiment_label = 'bearish'
            else:
                sentiment_label = 'neutral'
            
            # Calculate confidence based on weight sum and consistency
            total_weight = np.sum(weights)
            sentiment_variance = np.var(scores) if len(scores) > 1 else 0
            confidence = min(1.0, total_weight / len(scores)) * (1 - min(sentiment_variance, 0.5))
            
            final_results[stock] = {
                'sentiment_score': float(normalized_sentiment),
                'sentiment_label': sentiment_label,
                'mentions': len(scores),
                'confidence': float(confidence),
                'total_weight': float(total_weight)
            }
        
        return final_results

def analyze_single_post(text: str, timestamp: Optional[str] = None, 
                       analyzer: Optional[FinBERTSentimentAnalyzer] = None) -> Optional[Dict]:
    """
    Convenience function to analyze a single post
    
    Args:
        text: Post text to analyze
        timestamp: Post timestamp (optional)
        analyzer: Pre-initialized analyzer (optional, creates new if None)
        
    Returns:
        Dictionary with sentiment analysis results or None if no stocks found
    """
    if analyzer is None:
        analyzer = FinBERTSentimentAnalyzer()
    
    # Extract stock symbols
    stocks = analyzer.extract_stock_symbols(text)
    
    if not stocks:
        return None
    
    # Prepare post data
    post_data = [{
        'text': text,
        'timestamp': timestamp or datetime.now().isoformat(),
        'stocks': stocks
    }]
    
    # Analyze and return results
    return analyzer.analyze_posts_batch(post_data)