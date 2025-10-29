"""
Stock Sentiment Aggregator Service
Implements the full 5-step sentiment methodology as specified in sentiment_methodology.html
"""

import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

from ..constants import (
    SENTIMENT_TIME_DECAY_LAMBDA,
    SOURCE_WEIGHTS,
    COMMON_WORD_SYMBOL_WEIGHTS,
    POST_COUNT_WEIGHT_MULTIPLIER,
    MIN_POST_COUNT_WEIGHT,
    MAX_POST_COUNT_WEIGHT,
    MIN_SENTIMENT_SCORE,
    MAX_SENTIMENT_SCORE
)


@dataclass
class SentimentMention:
    """Individual sentiment mention for aggregation"""
    symbol: str
    raw_sentiment: float
    timestamp: datetime
    source: str
    text: str
    post_url: Optional[str] = None
    
    def __post_init__(self):
        """Ensure timestamp is timezone-naive for consistent calculations"""
        if self.timestamp.tzinfo is not None:
            self.timestamp = self.timestamp.replace(tzinfo=None)


@dataclass 
class AggregatedSentiment:
    """Final aggregated sentiment result for a stock"""
    symbol: str
    final_sentiment: float
    sentiment_label: str
    confidence: float
    total_mentions: int
    methodology_version: str = "1.0"
    debug_info: Optional[Dict] = None


class StockSentimentAggregator:
    """
    Implements the full 5-step sentiment methodology:
    1. FinBERT Analysis (already done by analyzer)
    2. Time Decay Weighting  
    3. Source Reliability Weighting
    4. Stock-Level Aggregation 
    5. Final Normalization
    """
    
    def __init__(self, decay_lambda: float = SENTIMENT_TIME_DECAY_LAMBDA):
        """
        Initialize the aggregator
        
        Args:
            decay_lambda: Time decay parameter (default: 0.1 per methodology)
        """
        self.decay_lambda = decay_lambda
        self.source_weights = SOURCE_WEIGHTS.copy()
    
    def calculate_time_weight(self, timestamp: datetime, reference_time: Optional[datetime] = None) -> float:
        """
        Step 2: Calculate time decay weight
        Formula: w_t = e^(-λ × Δt)
        
        Args:
            timestamp: When the mention occurred
            reference_time: Reference time (default: now)
            
        Returns:
            Time weight between 0.0 and 1.0
        """
        if reference_time is None:
            reference_time = datetime.now()
        
        # Ensure both timestamps are timezone-naive
        if timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)
        if reference_time.tzinfo is not None:
            reference_time = reference_time.replace(tzinfo=None)
        
        # Calculate hours elapsed
        hours_elapsed = (reference_time - timestamp).total_seconds() / 3600
        hours_elapsed = max(0, hours_elapsed)  # No negative time
        
        # Apply exponential decay: w_t = e^(-λ × Δt)
        return float(math.exp(-self.decay_lambda * hours_elapsed))
    
    def get_source_weight(self, source: str) -> float:
        """
        Step 3: Get source reliability weight
        
        Args:
            source: Source identifier (e.g., 'reddit/r/investing')
            
        Returns:
            Source weight (1.0 for standard Reddit sources)
        """
        # Try exact match first
        if source in self.source_weights:
            return self.source_weights[source]
        
        # Try pattern matching for Reddit sources
        if source.startswith('reddit/r/'):
            subreddit = source.split('/')[-1].lower()
            for pattern in self.source_weights:
                if pattern.endswith(f'/r/{subreddit}'):
                    return self.source_weights[pattern]
        
        # Try generic reddit weight
        if source.startswith('reddit'):
            return self.source_weights.get('reddit', self.source_weights['default'])
        
        # Default weight
        return self.source_weights['default']
    
    def get_symbol_weight(self, symbol: str) -> float:
        """
        Get weight penalty for common English words that are also stock symbols
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Weight multiplier (1.0 = normal, <1.0 = reduced weight for common words)
        """
        return COMMON_WORD_SYMBOL_WEIGHTS.get(symbol.upper(), 
                                           COMMON_WORD_SYMBOL_WEIGHTS['default'])
    
    def get_post_count_weight(self, unique_posts: int) -> float:
        """
        Calculate weight boost based on number of unique posts mentioning the stock
        More posts = more widespread discussion = higher importance
        
        Formula: weight = 1.0 + (log(unique_posts) * multiplier)
        
        Args:
            unique_posts: Number of unique posts mentioning the stock
            
        Returns:
            Weight multiplier (>=1.0, higher for more posts)
        """
        if unique_posts <= 1:
            return MIN_POST_COUNT_WEIGHT
        
        # Logarithmic scaling to prevent excessive weighting
        log_posts = math.log(unique_posts)
        weight = MIN_POST_COUNT_WEIGHT + (log_posts * POST_COUNT_WEIGHT_MULTIPLIER)
        
        # Cap the maximum weight
        return min(weight, MAX_POST_COUNT_WEIGHT)
    
    def aggregate_stock_sentiment(self, mentions: List[SentimentMention], 
                                include_debug: bool = False) -> AggregatedSentiment:
        """
        Steps 4-5: Aggregate multiple mentions into final stock sentiment
        
        Formula: Stock Sentiment = Σ(score_i × w_t,i × w_s,i) / Σ(w_t,i × w_s,i)
        Then normalize to [-1, +1] range
        
        Args:
            mentions: List of sentiment mentions for the stock
            include_debug: Whether to include debug information
            
        Returns:
            Aggregated sentiment result
        """
        if not mentions:
            return AggregatedSentiment(
                symbol="UNKNOWN",
                final_sentiment=0.0,
                sentiment_label="neutral",
                confidence=0.0,
                total_mentions=0
            )
        
        symbol = mentions[0].symbol
        reference_time = datetime.now()
        
        # Calculate unique posts count for post count weighting
        unique_post_ids = set()
        for mention in mentions:
            if hasattr(mention, 'post_id') and mention.post_id:
                unique_post_ids.add(mention.post_id)
        unique_posts_count = len(unique_post_ids) if unique_post_ids else len(mentions)
        
        # Step 3.2: Post count weight - gives more importance to widely discussed stocks
        post_count_weight = self.get_post_count_weight(unique_posts_count)
        
        # Calculate weighted contributions
        weighted_numerator = 0.0
        weighted_denominator = 0.0
        debug_mentions = []
        
        for mention in mentions:
            # Step 2: Time decay weight
            time_weight = self.calculate_time_weight(mention.timestamp, reference_time)
            
            # Step 3: Source reliability weight  
            source_weight = self.get_source_weight(mention.source)
            
            # Step 3.1: Symbol weight penalty for common words
            symbol_weight = self.get_symbol_weight(symbol)
            
            # Combined weight including post count boost
            total_weight = time_weight * source_weight * symbol_weight * post_count_weight
            
            # Weighted contribution
            weighted_contribution = mention.raw_sentiment * total_weight
            
            weighted_numerator += weighted_contribution
            weighted_denominator += total_weight
            
            if include_debug:
                hours_elapsed = (reference_time - mention.timestamp).total_seconds() / 3600
                debug_mentions.append({
                    'text': mention.text[:100] + '...' if len(mention.text) > 100 else mention.text,
                    'raw_sentiment': mention.raw_sentiment,
                    'hours_elapsed': round(hours_elapsed, 1),
                    'time_weight': round(time_weight, 4),
                    'source': mention.source,
                    'source_weight': round(source_weight, 4),
                    'symbol_weight': round(symbol_weight, 4),
                    'post_count_weight': round(post_count_weight, 4),
                    'unique_posts': unique_posts_count,
                    'total_weight': round(total_weight, 4),
                    'weighted_contribution': round(weighted_contribution, 4)
                })
        
        # Step 4: Calculate weighted average
        if weighted_denominator > 0:
            weighted_avg = weighted_numerator / weighted_denominator
        else:
            weighted_avg = 0.0
        
        # Step 5: Final normalization (clamp to [-1, +1])
        final_sentiment = max(MIN_SENTIMENT_SCORE, min(MAX_SENTIMENT_SCORE, weighted_avg))
        
        # Determine sentiment label
        sentiment_label = self._determine_sentiment_label(final_sentiment)
        
        # Calculate confidence based on consensus and weight distribution
        confidence = self._calculate_confidence(mentions, weighted_denominator)
        
        # Prepare debug info
        debug_info = None
        if include_debug:
            debug_info = {
                'mentions': debug_mentions,
                'weighted_numerator': round(weighted_numerator, 4),
                'weighted_denominator': round(weighted_denominator, 4),
                'weighted_avg_before_clamp': round(weighted_avg, 4),
                'final_sentiment_after_clamp': round(final_sentiment, 4),
                'decay_lambda': self.decay_lambda
            }
        
        return AggregatedSentiment(
            symbol=symbol,
            final_sentiment=final_sentiment,
            sentiment_label=sentiment_label,
            confidence=confidence,
            total_mentions=len(mentions),
            debug_info=debug_info
        )
    
    def aggregate_multiple_stocks(self, all_mentions: List[SentimentMention],
                                include_debug: bool = False) -> Dict[str, AggregatedSentiment]:
        """
        Aggregate sentiment for multiple stocks from a collection of mentions
        
        Args:
            all_mentions: All sentiment mentions from data collection
            include_debug: Whether to include debug information
            
        Returns:
            Dictionary mapping stock symbols to aggregated sentiment
        """
        # Group mentions by stock symbol
        mentions_by_stock = defaultdict(list)
        for mention in all_mentions:
            mentions_by_stock[mention.symbol].append(mention)
        
        # Aggregate each stock
        results = {}
        for symbol, mentions in mentions_by_stock.items():
            results[symbol] = self.aggregate_stock_sentiment(mentions, include_debug)
        
        return results
    
    def _determine_sentiment_label(self, sentiment_score: float) -> str:
        """Determine sentiment label based on score (per methodology scale)"""
        if sentiment_score >= 0.3:
            return "Strong Bullish"
        elif sentiment_score >= 0.1:
            return "Weak Bullish"
        elif sentiment_score <= -0.3:
            return "Strong Bearish"
        elif sentiment_score <= -0.1:
            return "Weak Bearish"
        else:
            return "Neutral"
    
    def _calculate_confidence(self, mentions: List[SentimentMention], 
                            total_weight: float) -> float:
        """Calculate confidence based on mention consensus and weights"""
        if not mentions:
            return 0.0
        
        # Base confidence from total weight (more recent/reliable = higher confidence)
        weight_confidence = min(1.0, total_weight / len(mentions))
        
        # Consensus confidence (how much do mentions agree?)
        sentiments = [m.raw_sentiment for m in mentions]
        if len(sentiments) == 1:
            consensus_confidence = 0.8
        else:
            # Standard deviation of sentiments (lower = more consensus)
            mean_sentiment = sum(sentiments) / len(sentiments)
            variance = sum((s - mean_sentiment) ** 2 for s in sentiments) / len(sentiments)
            std_dev = math.sqrt(variance)
            # Convert to confidence (0.0 std_dev = 1.0 confidence, 2.0 std_dev = 0.0 confidence)
            consensus_confidence = max(0.0, 1.0 - (std_dev / 2.0))
        
        # Sample size confidence (more mentions = higher confidence)
        sample_confidence = min(1.0, len(mentions) / 5.0)  # Cap at 5 mentions
        
        # Combined confidence
        final_confidence = (weight_confidence * 0.4 + 
                          consensus_confidence * 0.4 + 
                          sample_confidence * 0.2)
        
        return max(0.0, min(1.0, final_confidence))


# Singleton instance for global use
_aggregator_instance: Optional[StockSentimentAggregator] = None

def get_sentiment_aggregator() -> StockSentimentAggregator:
    """Get the global sentiment aggregator instance"""
    global _aggregator_instance
    if _aggregator_instance is None:
        _aggregator_instance = StockSentimentAggregator()
    return _aggregator_instance