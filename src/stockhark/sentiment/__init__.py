"""
Sentiment Analysis Module

Refactored sentiment analysis system with clear separation of concerns:
- Base analyzer interface
- FinBERT implementation
- Rule-based implementation  
- Factory pattern for analyzer creation
"""

from .base_analyzer import BaseSentimentAnalyzer
from .finbert_analyzer import FinBERTAnalyzer
from .rule_based_analyzer import RuleBasedAnalyzer
from .sentiment_factory import SentimentAnalyzerFactory, create_analyzer, create_enhanced_analyzer

__all__ = [
    'BaseSentimentAnalyzer',
    'FinBERTAnalyzer', 
    'RuleBasedAnalyzer',
    'SentimentAnalyzerFactory',
    'create_analyzer',
    'create_enhanced_analyzer'
]