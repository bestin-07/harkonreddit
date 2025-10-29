"""
StockHark Validators Module

This package contains various stock symbol validation components:
- stock_validator.py: Original regex-based validator
- ai_stock_validator.py: AI-powered NER-based validator  
- hybrid_validator.py: Combines both approaches

Usage:
    from stockhark.core.validators import StockValidator
    from stockhark.core.validators import AIStockValidator, HybridStockValidator
"""

# Import main validators for easy access
from .stock_validator import StockValidator, create_stock_validator, validate_stock_symbols, is_valid_stock_symbol

# Import AI validators (with graceful fallback if dependencies missing)
try:
    from .ai_stock_validator import AIStockValidator, create_ai_validator
    from .hybrid_validator import HybridStockValidator, create_hybrid_validator
    AI_VALIDATORS_AVAILABLE = True
except ImportError:
    # spaCy or other dependencies not available
    AIStockValidator = None
    HybridStockValidator = None
    create_ai_validator = None
    create_hybrid_validator = None
    AI_VALIDATORS_AVAILABLE = False

__all__ = [
    # Core validator (always available)
    'StockValidator',
    'create_stock_validator', 
    'validate_stock_symbols',
    'is_valid_stock_symbol',
    
    # AI validators (may be None if dependencies missing)
    'AIStockValidator',
    'HybridStockValidator', 
    'create_ai_validator',
    'create_hybrid_validator',
    
    # Availability flag
    'AI_VALIDATORS_AVAILABLE'
]