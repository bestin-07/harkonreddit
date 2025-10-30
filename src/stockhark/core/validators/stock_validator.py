"""
Stock Symbol Validator

Efficient stock symbol validation using local JSON files with optimized lookups.
Provides fast O(1) validation and intelligent filtering of potential symbols.
"""

import json
import os
import re
from typing import Set, List, Dict, Optional, Tuple
from collections import defaultdict

class StockValidator:
    """
    High-performance stock symbol validator with intelligent filtering
    
    Features:
    - O(1) symbol validation using hash sets
    - False positive filtering for common English words
    - Batch validation support
    - Exchange identification (NASDAQ/AMEX)
    """
    
    def __init__(self, json_folder_path: str = "JSON", silent: bool = True):
        """
        Initialize stock validator
        
        Args:
            json_folder_path: Path to folder containing ticker JSON files
            silent: If True, suppress initialization output
        """
        self.json_folder = json_folder_path
        self.silent = silent
        
        # Symbol storage
        self.nasdaq_symbols: Set[str] = set()
        self.amex_symbols: Set[str] = set()
        self.all_symbols: Set[str] = set()
        
        # Load and index symbols
        self._load_symbol_data()
        
        # Initialize filters
        self.false_positive_filter = self._build_false_positive_filter()
        self.stock_pattern = re.compile(r'\b[A-Z]{1,5}\b')
        
        if not self.silent and self.all_symbols:
            print(f"Stock Validator: {len(self.all_symbols):,} symbols loaded")
    
    def _load_symbol_data(self) -> None:
        """Load stock symbols from JSON files"""
        try:
            # Load NASDAQ symbols
            nasdaq_file = os.path.join(self.json_folder, "nasdaq_tickers.json")
            if os.path.exists(nasdaq_file):
                with open(nasdaq_file, 'r') as f:
                    self.nasdaq_symbols = set(json.load(f))
            
            # Load AMEX symbols  
            amex_file = os.path.join(self.json_folder, "amex_tickers.json")
            if os.path.exists(amex_file):
                with open(amex_file, 'r') as f:
                    self.amex_symbols = set(json.load(f))
            
            # Combine all symbols
            self.all_symbols = self.nasdaq_symbols | self.amex_symbols
            
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            if not self.silent:
                print(f"Warning: Could not load ticker data - {e}")
            # Continue with empty symbol set for graceful degradation
            self.all_symbols = set()
    
    def _build_false_positive_filter(self) -> Set[str]:
        """Build comprehensive filter for common false positives"""
        return {
            # Common English words that appear in all caps
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 
            'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW',
            'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID',
            'ILL', 'LET', 'MAN', 'PUT', 'SAY', 'SHE', 'TOO', 'USE', 'WAY', 'WIN',
            'YES', 'YET', 'BAD', 'BIG', 'BOX', 'CUP', 'END', 'FAN', 'FUN', 'GOT',
            'HAD', 'HIT', 'HOT', 'LOT', 'MOM', 'POP', 'RUN', 'SIT', 'TOP', 'TRY',
            'ZIP', 'WILL', 'WITH', 'HAVE', 'FROM', 'BEEN', 'MORE', 'VERY', 'WELL',
            
            # Reddit/Social media abbreviations  
            'LOL', 'OMG', 'WTF', 'TBH', 'IMO', 'YOLO', 'WSB', 'TLDR', 'ELI', 
            'AMA', 'TIL', 'DAE', 'PSA', 'LPT', 'TIFU', 'HODL',
            
            # Financial terms that aren't stock symbols
            'BUY', 'SELL', 'HOLD', 'LONG', 'SHORT', 'CALL', 'PUT', 'MOON',
            'BEAR', 'BULL', 'YOLO', 'FOMO', 'ATH', 'ATL', 'RSI', 'MACD',
            
            # Days/months/times
            'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN',
            'JAN', 'FEB', 'MAR', 'APR', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'
        }
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Fast O(1) symbol validation
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            bool: True if symbol is a valid stock ticker
        """
        return symbol.upper() in self.all_symbols
    
    def get_exchange(self, symbol: str) -> Optional[str]:
        """
        Get exchange for valid symbol
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            Exchange name ('NASDAQ', 'AMEX') or None if invalid
        """
        symbol_upper = symbol.upper()
        
        if symbol_upper in self.nasdaq_symbols:
            return "NASDAQ"
        elif symbol_upper in self.amex_symbols:
            return "AMEX"
        else:
            return None

    def is_valid_stock_symbol(self, symbol: str) -> bool:
        return self.is_valid_symbol(symbol)
    
    def validate_symbols(self, symbols: List[str]) -> List[str]:
        """
        Filter list to only valid stock symbols
        
        Args:
            symbols: List of potential symbols
            
        Returns:
            List of validated uppercase symbols
        """
        return [s.upper() for s in symbols if self.is_valid_symbol(s)]
    
    def extract_and_validate(self, text: str, max_symbols: int = 10) -> List[str]:
        """
        Optimized extraction and validation with single-pass processing
        
        Args:
            text: Text to search for stock symbols
            max_symbols: Maximum number of symbols to return
            
        Returns:
            List of validated stock symbols
        """
        # Single-pass optimized approach
        filtered_symbols = []
        seen = set()
        
        # Use regex iterator for early termination and memory efficiency
        text_upper = text.upper()
        
        for match in self.stock_pattern.finditer(text_upper):
            symbol = match.group()
            
            # Skip if already processed or max reached
            if symbol in seen or len(filtered_symbols) >= max_symbols:
                continue
            seen.add(symbol)
            
            # Combined validation in single check - avoids multiple lookups
            if (1 <= len(symbol) <= 5 and  # Valid length
                symbol.isalpha() and  # Only letters
                symbol not in self.false_positive_filter and  # Not common word
                symbol in self.all_symbols):  # Valid stock symbol (O(1) hash lookup)
                
                filtered_symbols.append(symbol)
        
        return filtered_symbols

    # Removed unused methods: extract_and_validate_batch, get_validator_stats

# Convenience functions for backwards compatibility

def create_stock_validator(json_folder: str = "JSON", silent: bool = True) -> StockValidator:
    """
    Factory function to create a stock validator instance
    
    Args:
        json_folder: Path to ticker JSON files
        silent: Whether to suppress initialization output
        
    Returns:
        Configured StockValidator instance
    """
    return StockValidator(json_folder, silent)

def validate_stock_symbols(text: str, validator: Optional[StockValidator] = None) -> List[str]:
    """
    Quick function to extract and validate stock symbols from text
    
    Args:
        text: Text to analyze
        validator: Optional pre-initialized validator
        
    Returns:
        List of valid stock symbols
    """
    if validator is None:
        validator = StockValidator(silent=True)
    
    return validator.extract_and_validate(text)

def is_valid_stock_symbol(symbol: str, validator: Optional[StockValidator] = None) -> bool:
    """
    Quick function to check if a symbol is valid
    
    Args:
        symbol: Stock symbol to check
        validator: Optional pre-initialized validator
        
    Returns:
        True if symbol is valid
    """
    if validator is None:
        validator = StockValidator(silent=True)
    
    return validator.is_valid_symbol(symbol)