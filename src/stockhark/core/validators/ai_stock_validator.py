#!/usr/bin/env python3
"""
AI-Powered Stock Validator using spaCy NER
Extracts company names and stock symbols using Natural Language Processing

This is a modular addition to the existing validation system.
Can be used independently or in combination with the current StockValidator.
"""

import re
import logging
from typing import List, Set, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

@dataclass
class CompanyEntity:
    """Represents a detected company/organization entity"""
    text: str
    label: str  # ORG, PERSON, etc.
    start: int
    end: int
    confidence: float = 0.0

@dataclass 
class StockMatch:
    """Represents a matched stock symbol or company"""
    symbol: Optional[str] = None
    company_name: Optional[str] = None
    confidence: float = 0.0
    source: str = "unknown"  # "ner", "regex", "combined"
    entity: Optional[CompanyEntity] = None

class AIStockValidator:
    """
    AI-powered stock and company name validator using spaCy NER
    
    Features:
    - Company name extraction using NER
    - Stock symbol detection via regex
    - Confidence scoring with JSON validation
    - Modular design for easy integration
    """
    
    def __init__(self, model_name: str = "en_core_web_sm", json_folder_path: Optional[str] = None):
        """
        Initialize AI Stock Validator
        
        Args:
            model_name: spaCy model to use (default: en_core_web_sm)
            json_folder_path: Path to JSON validation files (optional)
        """
        self.logger = logging.getLogger('StockHark.AIStockValidator')
        self.model_name = model_name
        self.nlp = None
        self.is_available = SPACY_AVAILABLE
        
        # Initialize JSON-based validation
        self.json_validator = None
        self.json_folder_path = json_folder_path
        self._initialize_json_validator()
        
        # Stock symbol patterns with context awareness
        self.stock_patterns = [
            # High confidence patterns
            r'\$([A-Z]{2,5})\b',           # $AAPL format (strong indicator)
            r'\b([A-Z]{2,5})\$',           # AAPL$ format
            
            # Medium confidence patterns (need more validation)
            r'\b([A-Z]{2,5})\s+(?:stock|shares?|ticker|symbol)',  # AAPL stock
            r'(?:buy|sell|hold|long|short)\s+([A-Z]{2,5})\b',     # buy AAPL
            r'\b([A-Z]{2,5})\s+(?:price|earnings|dividend)',      # AAPL price
            r'\b([A-Z]{2,5})\s+(?:vs|and|or)\s+[A-Z]{2,5}',      # AAPL vs MSFT
            r'\b([A-Z]{2,5})(?=\s*[,;]|\s+and\s|\s+or\s)',       # AAPL, MSFT
            
            # Lower confidence - standalone (need strong context validation)
            r'\b([A-Z]{2,5})\b(?=\s|$|[.,!?])',  # Standalone symbols (validate heavily)
        ]
        
        # Common false positives to filter out (enhanced list)
        self.false_positives = {
            # Common English words
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE',
            'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD',
            'SEE', 'TWO', 'WHO', 'BOY', 'DID', 'ITS', 'LET', 'OWN', 'SAY', 'SHE', 'TOO', 'USE',
            'WAY', 'WHY', 'YET', 'YES', 'WIN', 'WON', 'TOP', 'TRY', 'PUT', 'RUN', 'SET', 'SIT',
            
            # Financial/Trading terminology (not stock symbols)
            'CEO', 'CFO', 'CTO', 'IPO', 'SEC', 'FDA', 'USA', 'NYC', 'LA', 'UK', 'EU', 'GDP',
            'EDIT', 'TLDR', 'ELI', 'FOMO', 'YOLO', 'DD', 'TA', 'FA', 'WSB', 'IMO', 'IMHO',
            
            # Action words commonly misidentified as symbols
            'BUY', 'SELL', 'HOLD', 'PUMP', 'DUMP', 'MOON', 'CRASH', 'DIP', 'RISE', 'FALL',
            'BOOM', 'BUST', 'PEAK', 'LOW', 'HIGH', 'LONG', 'SHORT', 'CALL', 'PUT', 'OPTION',
            
            # Common words that appear in caps
            'STOCK', 'STOCKS', 'MARKET', 'TRADE', 'TRADING', 'INVEST', 'INVESTING', 'MONEY',
            'PRICE', 'VALUE', 'PROFIT', 'LOSS', 'GAIN', 'BULL', 'BEAR', 'CASH', 'DEBT',
            'BIG', 'HUGE', 'MASSIVE', 'FIRE', 'HOT', 'COLD', 'COOL', 'BEST', 'WORST', 'GROW',
            
            # Prepositions and conjunctions
            'ON', 'IN', 'AT', 'TO', 'OF', 'BY', 'OR', 'AS', 'IF', 'SO', 'UP', 'GO', 'NO',
            'IS', 'IT', 'BE', 'WE', 'MY', 'ME', 'HE', 'US', 'DO', 'AN', 'AM', 'VS', 'AI'
        }
        
        # Finance-specific organization indicators
        self.finance_indicators = {
            'inc', 'corp', 'ltd', 'llc', 'company', 'group', 'holdings', 'capital',
            'partners', 'associates', 'ventures', 'fund', 'trust', 'bank', 'financial',
            'securities', 'investment', 'asset', 'management', 'advisors'
        }
        
        # Context keywords that indicate financial discussion
        self.financial_context_keywords = {
            # Stock-specific terms
            'stock', 'stocks', 'share', 'shares', 'ticker', 'symbol', 'equity', 'securities',
            
            # Trading terms
            'buy', 'sell', 'trade', 'trading', 'invest', 'investing', 'portfolio', 'position',
            'long', 'short', 'calls', 'puts', 'options', 'futures', 'dividend', 'earnings',
            
            # Market terms
            'market', 'nasdaq', 'nyse', 'exchange', 'bull', 'bear', 'bullish', 'bearish',
            'rally', 'correction', 'volatility', 'volume', 'price', 'valuation', 'pe',
            
            # Financial metrics
            'revenue', 'profit', 'eps', 'ebitda', 'roi', 'growth', 'margin', 'debt',
            'cash', 'flow', 'balance', 'sheet', 'quarterly', 'annual', 'guidance',
            
            # Reddit/social trading terms
            'yolo', 'diamond', 'hands', 'paper', 'moon', 'rocket', 'tendies', 'apes',
            'hodl', 'btfd', 'stonks', 'dd', 'due', 'diligence'
        }
        
        # JSON validator will provide comprehensive symbol validation
        # Keep a small hardcoded list as fallback if JSON validation fails
        self.fallback_known_symbols = {
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 'INTC',
            'NFLX','BABA', 'TSM', 'JPM', 'JNJ', 'WMT', 'PG', 'UNH',
            'MA', 'BAC', 'XOM', 'ABBV', 'PFE', 'KO', 'AVGO', 'PEP', 'TMO', 'NVS',
            'CVX', 'ADBE', 'ABT', 'ACN', 'MRK', 'ORCL', 'CRM', 'LLY', 'TXN', 'QCOM',
            'GME', 'AMC', 'NOK', 'PLTR', 'NIO', 'LCID', 'RIVN'
        }
        
        self._initialize_model()
    
    def _initialize_json_validator(self):
        """Initialize JSON-based stock validator for comprehensive symbol validation"""
        try:
            from .stock_validator import StockValidator
            
            if self.json_folder_path:
                self.json_validator = StockValidator(
                    json_folder_path=self.json_folder_path,
                    silent=True  # Don't spam logs
                )
            else:
                # Use default path
                self.json_validator = StockValidator(silent=True)
            
            symbol_count = len(self.json_validator.all_symbols) if hasattr(self.json_validator, 'all_symbols') else 0
            self.logger.info(f"JSON validator initialized with {symbol_count} stock symbols")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize JSON validator: {e}")
            self.json_validator = None
    
    def _initialize_model(self):
        """Initialize spaCy model with error handling"""
        if not SPACY_AVAILABLE:
            self.logger.warning("spaCy not available. AI validator will be disabled.")
            return
        
        try:
            self.nlp = spacy.load(self.model_name)
            self.logger.info(f"AI Stock Validator initialized with {self.model_name}")
        except OSError:
            self.logger.warning(f"spaCy model '{self.model_name}' not found. Download with: python -m spacy download {self.model_name}")
            self.is_available = False
        except Exception as e:
            self.logger.error(f"Failed to initialize AI validator: {e}")
            self.is_available = False
    
    def is_ready(self) -> bool:
        """Check if AI validator is ready to use"""
        return self.is_available and self.nlp is not None
    
    def is_valid_stock_symbol(self, symbol: str) -> bool:
        """
        Check if a symbol is a valid stock symbol using JSON validation
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            True if valid stock symbol, False otherwise
        """
        if self.json_validator:
            try:
                # Use JSON validator's comprehensive validation
                return self.json_validator.is_valid_stock_symbol(symbol)
            except Exception as e:
                self.logger.debug(f"JSON validation failed for {symbol}: {e}")
        
        # Fallback to hardcoded list
        return symbol in self.fallback_known_symbols
    
    def get_valid_symbols_from_text(self, text: str) -> List[str]:
        """
        Extract symbols using AI and validate against JSON database
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of valid stock symbols only (deduplicated)
        """
        # Get AI-detected symbols
        symbols = self.get_stock_symbols_only(text, min_confidence=0.3)  # Lower threshold for JSON filtering
        
        # Filter through JSON validation and deduplicate
        valid_symbols = []
        seen_symbols = set()
        
        for symbol in symbols:
            if symbol not in seen_symbols and self.is_valid_stock_symbol(symbol):
                valid_symbols.append(symbol)
                seen_symbols.add(symbol)
            elif symbol not in seen_symbols:
                self.logger.debug(f"Symbol '{symbol}' filtered out by JSON validation")
                seen_symbols.add(symbol)  # Still track to avoid duplicate logging
        
        return valid_symbols
    
    def extract_companies_ner(self, text: str) -> List[CompanyEntity]:
        """
        Extract company/organization entities using NER
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of detected company entities
        """
        if not self.is_ready():
            return []
        
        try:
            doc = self.nlp(text)
            companies = []
            
            for ent in doc.ents:
                # Focus on organizations and some persons (for company founders/CEOs)
                if ent.label_ in ['ORG', 'PERSON']:
                    # Calculate confidence based on context
                    confidence = self._calculate_entity_confidence(ent, doc)
                    
                    companies.append(CompanyEntity(
                        text=ent.text.strip(),
                        label=ent.label_,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=confidence
                    ))
            
            return companies
            
        except Exception as e:
            self.logger.error(f"Error in NER extraction: {e}")
            return []
    
    def _calculate_entity_confidence(self, entity, doc) -> float:
        """
        Calculate confidence score for an entity based on context
        
        Args:
            entity: spaCy entity
            doc: spaCy document
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        entity_text = entity.text.lower()
        
        # Boost confidence for finance-related context
        for token in doc:
            if token.text.lower() in self.finance_indicators:
                confidence += 0.2
                break
        
        # Boost for company suffixes
        if any(suffix in entity_text for suffix in self.finance_indicators):
            confidence += 0.3
        
        # Reduce for very short entities (likely false positives)
        if len(entity.text) <= 2:
            confidence -= 0.3
        
        # Reduce for all caps (likely acronyms that aren't companies)
        if entity.text.isupper() and len(entity.text) <= 4:
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def extract_stock_symbols_regex(self, text: str) -> List[StockMatch]:
        """
        Extract stock symbols using regex patterns
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of stock symbol matches
        """
        symbols = []
        
        for pattern in self.stock_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                symbol = match.group(1) if match.groups() else match.group(0)
                symbol = symbol.strip('$').upper()
                
                # Filter false positives
                if (len(symbol) >= 2 and 
                    symbol not in self.false_positives and 
                    not symbol.isdigit()):
                    
                    confidence = self._calculate_symbol_confidence(symbol, text, match.start())
                    
                    symbols.append(StockMatch(
                        symbol=symbol,
                        confidence=confidence,
                        source="regex"
                    ))
        
        return symbols
    
    def _calculate_symbol_confidence(self, symbol: str, text: str, position: int) -> float:
        """Calculate confidence for a stock symbol match with enhanced context awareness"""
        confidence = 0.3  # Lower base confidence - make symbols prove themselves
        
        # Major boost for known legitimate stock symbols
        if self.is_valid_stock_symbol(symbol):
            confidence += 0.6  # Increased for known symbols
        
        # Boost for dollar sign prefix (strong indicator)
        if position > 0 and text[position-1] == '$':
            confidence += 0.4  # Increased - dollar sign is very strong indicator
        
        # Boost for typical stock symbol length
        if 2 <= len(symbol) <= 4:
            confidence += 0.2
        elif len(symbol) == 5:
            confidence += 0.1
        else:
            confidence -= 0.3  # Penalize unusual lengths more heavily
        
        # Heavy penalty for false positives (unless has strong indicators like $)
        if symbol in self.false_positives:
            penalty = 0.7  # Heavy penalty
            # Reduce penalty if has dollar sign (strong indicator overrides false positive)
            if position > 0 and text[position-1] == '$':
                penalty = 0.3  # Reduced penalty for $ symbols
            confidence -= penalty
        
        # Context analysis with larger window
        context_window = 100  # Increased context window
        start = max(0, position - context_window)
        end = min(len(text), position + len(symbol) + context_window)
        context = text[start:end].lower()
        
        # Check for financial context keywords
        financial_context_count = sum(1 for keyword in self.financial_context_keywords if keyword in context)
        if financial_context_count > 0:
            confidence += min(0.3, financial_context_count * 0.05)  # Up to 0.3 boost
        
        # Check for explicit stock-related phrases
        stock_phrases = [
            'stock', 'ticker', 'symbol', 'share', 'equity',
            'buy', 'sell', 'trade', 'invest', 'portfolio'
        ]
        phrase_matches = sum(1 for phrase in stock_phrases if phrase in context)
        if phrase_matches > 0:
            confidence += min(0.2, phrase_matches * 0.05)  # Up to 0.2 boost
        
        # Penalty for appearing in non-financial context
        non_financial_indicators = [
            'said', 'says', 'told', 'called', 'named', 'word', 'letter', 'sentence',
            'paragraph', 'article', 'book', 'page', 'chapter', 'title', 'heading'
        ]
        if any(indicator in context for indicator in non_financial_indicators):
            confidence -= 0.2
        
        # Pattern-based boosts
        if self._has_stock_pattern_context(text, position, symbol):
            confidence += 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _has_stock_pattern_context(self, text: str, position: int, symbol: str) -> bool:
        """Check for specific patterns that indicate stock discussion"""
        # Extract text around the symbol
        start = max(0, position - 30)
        end = min(len(text), position + len(symbol) + 30)
        context = text[start:end].lower()
        
        # Look for common stock mention patterns
        patterns = [
            f'${symbol.lower()}',  # Dollar sign prefix
            f'{symbol.lower()} stock',  # Explicit "stock" after symbol
            f'{symbol.lower()} shares',  # "shares" after symbol
            f'buy {symbol.lower()}',  # Action words before symbol
            f'sell {symbol.lower()}',
            f'hold {symbol.lower()}',
            f'{symbol.lower()} price',  # Price discussion
            f'{symbol.lower()} earnings',  # Earnings discussion
            f'{symbol.lower()} vs',  # Comparison
            f'vs {symbol.lower()}',
            f'{symbol.lower()} and',  # Listed with other symbols
            f'and {symbol.lower()}'
        ]
        
        return any(pattern in context for pattern in patterns)
    
    def extract_all_entities(self, text: str) -> Tuple[List[CompanyEntity], List[StockMatch]]:
        """
        Extract both companies and stock symbols from text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (companies, stock_symbols)
        """
        companies = self.extract_companies_ner(text)
        symbols = self.extract_stock_symbols_regex(text)
        
        return companies, symbols
    
    def get_all_matches(self, text: str, min_confidence: float = 0.4) -> List[StockMatch]:
        """
        Get all stock-related matches (companies + symbols) above confidence threshold
        
        Args:
            text: Input text to analyze  
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of all matches above threshold
        """
        companies, symbols = self.extract_all_entities(text)
        
        all_matches = []
        
        # Add company entities as matches
        for company in companies:
            if company.confidence >= min_confidence:
                all_matches.append(StockMatch(
                    company_name=company.text,
                    confidence=company.confidence,
                    source="ner",
                    entity=company
                ))
        
        # Add symbol matches
        for symbol in symbols:
            if symbol.confidence >= min_confidence:
                all_matches.append(symbol)
        
        # Sort by confidence (highest first)
        all_matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return all_matches
    
    def get_stock_symbols_only(self, text: str, min_confidence: float = 0.5) -> List[str]:
        """
        Get only stock symbols (compatible with current validator interface)
        
        Args:
            text: Input text to analyze
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of stock symbol strings
        """
        symbols = self.extract_stock_symbols_regex(text)
        return [s.symbol for s in symbols if s.symbol and s.confidence >= min_confidence]
    
    def analyze_text_debug(self, text: str) -> Dict:
        """
        Debug method to see detailed analysis results
        
        Args:
            text: Input text to analyze
            
        Returns:
            Detailed analysis results for debugging
        """
        if not self.is_ready():
            return {"error": "AI validator not available", "available": False}
        
        companies, symbols = self.extract_all_entities(text)
        
        return {
            "available": True,
            "text": text,
            "companies": [
                {
                    "text": c.text,
                    "label": c.label, 
                    "confidence": c.confidence,
                    "position": f"{c.start}-{c.end}"
                } for c in companies
            ],
            "symbols": [
                {
                    "symbol": s.symbol,
                    "confidence": s.confidence,
                    "source": s.source
                } for s in symbols
            ],
            "model": self.model_name
        }

# Convenience function for easy integration
def create_ai_validator(model_name: str = "en_core_web_sm") -> AIStockValidator:
    """Create an AI stock validator instance"""
    return AIStockValidator(model_name)

# Example usage and testing
if __name__ == "__main__":
    # Test the AI validator
    validator = AIStockValidator()
    
    if validator.is_ready():
        test_text = "I'm bullish on Apple Inc. and think $TSLA will moon. Microsoft Corporation is also a good buy."
        
        print("AI Stock Validator Test")
        print("=" * 40)
        print(f"Text: {test_text}")
        print()
        
        # Get debug analysis
        analysis = validator.analyze_text_debug(test_text)
        
        print("Companies found:")
        for company in analysis['companies']:
            print(f"  - {company['text']} ({company['confidence']:.2f} confidence)")
        
        print("\nSymbols found:")
        for symbol in analysis['symbols']:
            print(f"  - ${symbol['symbol']} ({symbol['confidence']:.2f} confidence)")
        
        print(f"\nStock symbols only: {validator.get_stock_symbols_only(test_text)}")
        
    else:
        print("AI validator not available. Install spaCy with:")
        print("pip install spacy")
        print("python -m spacy download en_core_web_sm")