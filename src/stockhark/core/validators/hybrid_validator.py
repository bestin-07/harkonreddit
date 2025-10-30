#!/usr/bin/env python3
"""
Hybrid Stock Validator
Combines the existing StockValidator with the new AI-powered validator

This provides a seamless upgrade path:
- Falls back to current validator if AI is unavailable
- Combines results from both approaches
- Maintains full backward compatibility
- Can be gradually tuned and improved
"""

import logging
from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass

from .stock_validator import StockValidator
from .ai_stock_validator import AIStockValidator, StockMatch, CompanyEntity

@dataclass
class ValidationResult:
    """Combined validation result with provenance tracking"""
    symbols: List[str]
    companies: List[str]
    confidence_scores: Dict[str, float]
    sources: Dict[str, str]  # symbol/company -> source ("current", "ai", "both")
    ai_available: bool = False

class HybridStockValidator:
    """
    Hybrid validator combining current regex-based approach with AI NER
    
    Strategy:
    1. Always use current validator (reliable fallback)
    2. Enhance with AI validator if available
    3. Combine and deduplicate results
    4. Track confidence and provenance
    """
    
    def __init__(self, 
                 ai_model: str = "en_core_web_sm",
                 ai_enabled: bool = True,
                 ai_min_confidence: float = 0.5,
                 combine_mode: str = "union"):
        """
        Initialize hybrid validator
        
        Args:
            ai_model: spaCy model name for AI validator
            ai_enabled: Whether to enable AI validator
            ai_min_confidence: Minimum confidence for AI results
            combine_mode: How to combine results ("union", "intersection", "ai_priority")
        """
        self.logger = logging.getLogger('StockHark.HybridValidator')
        
        # Always initialize current validator (reliable fallback)
        self.current_validator = StockValidator()
        self.logger.info("Current validator initialized")
        
        # Initialize AI validator if enabled
        self.ai_validator = None
        self.ai_available = False
        
        if ai_enabled:
            try:
                self.ai_validator = AIStockValidator(ai_model)
                self.ai_available = self.ai_validator.is_ready()
                if self.ai_available:
                    self.logger.info("AI validator initialized successfully")
                else:
                    self.logger.warning("AI validator initialized but not ready (missing spaCy model)")
            except Exception as e:
                self.logger.warning(f"AI validator initialization failed: {e}")
        
        self.ai_min_confidence = ai_min_confidence
        self.combine_mode = combine_mode
        
        self.logger.info(f"Hybrid validator ready (AI: {'enabled' if self.ai_available else 'disabled'})")
    
    def extract_and_validate(self, text: str) -> List[str]:
        """
        Extract and validate stock symbols (backward compatible interface)
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of validated stock symbols
        """
        result = self.extract_and_validate_detailed(text)
        return result.symbols
    
    def extract_and_validate_detailed(self, text: str) -> ValidationResult:
        """
        Extract and validate with detailed results
        
        Args:
            text: Input text to analyze
            
        Returns:
            Detailed validation result
        """
        # Always get current validator results (reliable baseline)
        current_symbols = set(self.current_validator.extract_and_validate(text))
        
        symbols = current_symbols.copy()
        companies = set()
        confidence_scores = {}
        sources = {}
        
        # Mark current validator results
        for symbol in current_symbols:
            sources[symbol] = "current"
            confidence_scores[symbol] = 0.8  # Assign decent confidence to current validator
        
        # Enhance with AI validator if available
        if self.ai_available and self.ai_validator:
            try:
                ai_matches = self.ai_validator.get_all_matches(text, self.ai_min_confidence)
                
                for match in ai_matches:
                    if match.symbol:
                        # Handle stock symbols from AI
                        if match.symbol in symbols:
                            # Symbol found by both - mark as combined and boost confidence
                            sources[match.symbol] = "both"
                            confidence_scores[match.symbol] = max(
                                confidence_scores.get(match.symbol, 0),
                                match.confidence
                            )
                        else:
                            # New symbol from AI only
                            if self.combine_mode in ["union", "ai_priority"]:
                                symbols.add(match.symbol)
                                sources[match.symbol] = "ai"
                                confidence_scores[match.symbol] = match.confidence
                    
                    if match.company_name:
                        # Handle company names from AI
                        companies.add(match.company_name)
                        sources[match.company_name] = "ai"
                        confidence_scores[match.company_name] = match.confidence
                
                self.logger.debug(f"AI validator found {len(ai_matches)} matches")
                
            except Exception as e:
                self.logger.warning(f"AI validation failed, using current validator only: {e}")
        
        # Apply combination strategy
        final_symbols = self._apply_combination_strategy(symbols, sources, confidence_scores)
    

        valid_symbols = {k: v for k, v in self.current_validator.all_symbols if k in final_symbols}


        self.current_validator.all_symbols

        return ValidationResult(
            symbols=sorted(valid_symbols),
            companies=sorted(list(companies)),
            confidence_scores=confidence_scores,
            sources=sources,
            ai_available=self.ai_available
        )
    
    def _apply_combination_strategy(self, 
                                   symbols: Set[str], 
                                   sources: Dict[str, str], 
                                   confidence_scores: Dict[str, float]) -> Set[str]:
        """Apply the configured combination strategy"""
        
        if self.combine_mode == "union":
            # Include all symbols from both validators
            return symbols
        
        elif self.combine_mode == "intersection":
            # Only include symbols found by both validators
            return {s for s in symbols if sources.get(s) == "both"}
        
        elif self.combine_mode == "ai_priority":
            # Prefer AI results, but include current validator as fallback
            high_confidence_ai = {s for s, score in confidence_scores.items() 
                                if sources.get(s) in ["ai", "both"] and score >= self.ai_min_confidence}
            current_only = {s for s in symbols if sources.get(s) == "current"}
            
            # If AI found high-confidence results, use those + any current validator results
            # If AI found nothing confident, fall back to current validator
            if high_confidence_ai:
                return high_confidence_ai | current_only
            else:
                return current_only
        
        else:
            # Default to union
            return symbols
    
    def get_companies(self, text: str, min_confidence: float = 0.5) -> List[str]:
        """
        Extract company names (new functionality from AI validator)
        
        Args:
            text: Input text to analyze
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of company names
        """
        if not self.ai_available:
            return []
        
        try:
            companies, _ = self.ai_validator.extract_all_entities(text)
            return [c.text for c in companies if c.confidence >= min_confidence]
        except Exception as e:
            self.logger.warning(f"Company extraction failed: {e}")
            return []
    
    def analyze_text_debug(self, text: str) -> Dict:
        """
        Comprehensive debug analysis showing both validators
        
        Args:
            text: Input text to analyze
            
        Returns:
            Detailed analysis from both validators
        """
        debug_info = {
            "text": text,
            "hybrid_config": {
                "ai_available": self.ai_available,
                "combine_mode": self.combine_mode,
                "ai_min_confidence": self.ai_min_confidence
            }
        }
        
        # Current validator results
        current_symbols = self.current_validator.extract_and_validate(text)
        debug_info["current_validator"] = {
            "symbols": current_symbols,
            "count": len(current_symbols)
        }
        
        # AI validator results
        if self.ai_available:
            ai_debug = self.ai_validator.analyze_text_debug(text)
            debug_info["ai_validator"] = ai_debug
        else:
            debug_info["ai_validator"] = {"available": False, "reason": "Not initialized or missing dependencies"}
        
        # Combined results
        detailed_result = self.extract_and_validate_detailed(text)
        debug_info["combined_result"] = {
            "symbols": detailed_result.symbols,
            "companies": detailed_result.companies,
            "confidence_scores": detailed_result.confidence_scores,
            "sources": detailed_result.sources,
            "total_symbols": len(detailed_result.symbols),
            "total_companies": len(detailed_result.companies)
        }
        
        return debug_info
    
    def get_validator_status(self) -> Dict[str, bool]:
        """Get status of both validators"""
        return {
            "current_validator": True,  # Always available
            "ai_validator": self.ai_available,
            "hybrid_ready": True  # Hybrid always works (falls back to current)
        }
    
    def set_ai_enabled(self, enabled: bool) -> bool:
        """
        Enable/disable AI validator at runtime
        
        Args:
            enabled: Whether to enable AI validator
            
        Returns:
            True if successful, False otherwise
        """
        if enabled and not self.ai_validator:
            try:
                self.ai_validator = AIStockValidator()
                self.ai_available = self.ai_validator.is_ready()
                self.logger.info(f"AI validator {'enabled' if self.ai_available else 'initialization failed'}")
                return self.ai_available
            except Exception as e:
                self.logger.warning(f"Failed to enable AI validator: {e}")
                return False
        elif not enabled:
            self.ai_available = False
            self.logger.info("AI validator disabled")
            return True
        
        return self.ai_available

# Convenience function for creating hybrid validator
def create_hybrid_validator(ai_enabled: bool = True, **kwargs) -> HybridStockValidator:
    """Create a hybrid validator with optional AI enhancement"""
    return HybridStockValidator(ai_enabled=ai_enabled, **kwargs)

# Example usage and testing
if __name__ == "__main__":
    # Test the hybrid validator
    validator = HybridStockValidator()
    
    test_text = "I'm very bullish on Apple Inc. ($AAPL) and Tesla Motors. $MSFT is also looking good. What do you think about AMD stock?"
    
    print("Hybrid Stock Validator Test")
    print("=" * 50)
    print(f"Text: {test_text}")
    print()
    
    # Get status
    status = validator.get_validator_status()
    print("Validator Status:")
    for name, available in status.items():
        print(f"  - {name}: {'✅' if available else '❌'}")
    print()
    
    # Simple extraction (backward compatible)
    symbols = validator.extract_and_validate(test_text)
    print(f"Stock symbols found: {symbols}")
    
    # Detailed extraction
    detailed = validator.extract_and_validate_detailed(test_text)
    print(f"\nDetailed Results:")
    print(f"  Symbols: {detailed.symbols}")
    print(f"  Companies: {detailed.companies}")
    print(f"  Sources: {detailed.sources}")
    print(f"  Confidence: {detailed.confidence_scores}")
    
    # Debug analysis
    debug = validator.analyze_text_debug(test_text)
    print(f"\nDebug Analysis:")
    print(f"  Current validator found: {debug['current_validator']['count']} symbols")
    if debug['ai_validator'].get('available'):
        print(f"  AI validator found: {len(debug['ai_validator']['symbols'])} symbols, {len(debug['ai_validator']['companies'])} companies")
    print(f"  Combined result: {debug['combined_result']['total_symbols']} symbols, {debug['combined_result']['total_companies']} companies")