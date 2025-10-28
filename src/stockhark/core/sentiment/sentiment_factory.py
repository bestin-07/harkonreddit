"""
Sentiment Analyzer Factory

Factory pattern for creating appropriate sentiment analyzers based on availability
and configuration. Provides intelligent fallback and analyzer selection.
"""

from typing import Optional, Union
from .base_analyzer import BaseSentimentAnalyzer
from .rule_based_analyzer import RuleBasedAnalyzer
from .finbert_analyzer import FinBERTAnalyzer

class SentimentAnalyzerFactory:
    """
    Factory for creating sentiment analyzers with intelligent selection
    
    Features:
    - Automatic FinBERT availability detection
    - Graceful fallback to rule-based analysis
    - Configuration-based analyzer selection
    - Singleton pattern for efficiency
    """
    
    _instances = {}
    
    @classmethod
    def create_analyzer(cls, 
                       analyzer_type: str = "auto",
                       enable_finbert: bool = True,
                       fallback_to_rules: bool = True) -> BaseSentimentAnalyzer:
        """
        Create sentiment analyzer based on type and availability
        
        Args:
            analyzer_type: Type of analyzer ("auto", "finbert", "rule_based")
            enable_finbert: Whether to attempt FinBERT initialization
            fallback_to_rules: Whether to fallback to rule-based if FinBERT fails
            
        Returns:
            Configured sentiment analyzer instance
        """
        # Create cache key for singleton behavior
        cache_key = f"{analyzer_type}_{enable_finbert}_{fallback_to_rules}"
        
        if cache_key in cls._instances:
            return cls._instances[cache_key]
        
        analyzer = None
        
        if analyzer_type == "rule_based":
            # Explicitly requested rule-based analyzer
            analyzer = RuleBasedAnalyzer()
            
        elif analyzer_type == "finbert":
            # Explicitly requested FinBERT analyzer
            try:
                analyzer = FinBERTAnalyzer()
                if not analyzer.is_available():
                    raise RuntimeError("FinBERT not available")
            except Exception as e:
                if fallback_to_rules:
                    print(f"FinBERT failed, falling back to rule-based: {e}")
                    analyzer = RuleBasedAnalyzer()
                else:
                    raise RuntimeError(f"FinBERT analyzer creation failed: {e}")
                    
        elif analyzer_type == "auto":
            # Auto-select best available analyzer
            if enable_finbert:
                try:
                    analyzer = FinBERTAnalyzer()
                    if analyzer.is_available():
                        print("✅ Using FinBERT sentiment analyzer")
                    else:
                        raise RuntimeError("FinBERT not properly initialized")
                except Exception as e:
                    if fallback_to_rules:
                        print(f"⚠️ FinBERT unavailable, using rule-based analyzer: {e}")
                        analyzer = RuleBasedAnalyzer()
                    else:
                        raise RuntimeError(f"Auto-selection failed: {e}")
            else:
                analyzer = RuleBasedAnalyzer()
                print("✅ Using rule-based sentiment analyzer")
        
        else:
            raise ValueError(f"Unknown analyzer type: {analyzer_type}")
        
        if analyzer is None:
            raise RuntimeError("Failed to create any sentiment analyzer")
        
        # Cache the instance
        cls._instances[cache_key] = analyzer
        
        return analyzer
    
    @classmethod
    def get_available_analyzers(cls) -> dict:
        """
        Get information about available analyzers
        
        Returns:
            Dictionary with analyzer availability information
        """
        availability = {
            'rule_based': True,  # Always available
            'finbert': False
        }
        
        # Check FinBERT availability
        try:
            finbert_analyzer = FinBERTAnalyzer()
            availability['finbert'] = finbert_analyzer.is_available()
        except Exception:
            availability['finbert'] = False
        
        return availability
    
    @classmethod
    def clear_cache(cls):
        """Clear the analyzer instance cache"""
        cls._instances.clear()

def create_analyzer(analyzer_type: str = "auto",
                   enable_finbert: bool = True,
                   fallback_to_rules: bool = True) -> BaseSentimentAnalyzer:
    """
    Convenience function for creating sentiment analyzers
    
    Args:
        analyzer_type: Type of analyzer ("auto", "finbert", "rule_based")
        enable_finbert: Whether to attempt FinBERT initialization
        fallback_to_rules: Whether to fallback to rule-based if FinBERT fails
        
    Returns:
        Configured sentiment analyzer instance
    """
    return SentimentAnalyzerFactory.create_analyzer(
        analyzer_type=analyzer_type,
        enable_finbert=enable_finbert,
        fallback_to_rules=fallback_to_rules
    )

def create_enhanced_analyzer(enable_finbert: bool = True) -> BaseSentimentAnalyzer:
    """
    Create analyzer with enhanced capabilities (backwards compatibility)
    
    Args:
        enable_finbert: Whether to enable FinBERT (with fallback)
        
    Returns:
        Enhanced sentiment analyzer (FinBERT preferred, rule-based fallback)
    """
    return create_analyzer(
        analyzer_type="auto",
        enable_finbert=enable_finbert,
        fallback_to_rules=True
    )