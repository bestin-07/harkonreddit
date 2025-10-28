#!/usr/bin/env python3
"""
Fast Stock Symbol Validator using Local JSON Files
Efficient search algorithms for stock symbol validation
"""

import json
import os
from typing import Set, List, Dict, Optional
import time
from collections import defaultdict

class FastStockValidator:
    """Ultra-fast stock validator using local JSON files with optimized search"""
    
    def __init__(self, json_folder_path="JSON"):
        self.json_folder = json_folder_path
        self.nasdaq_symbols: Set[str] = set()
        self.amex_symbols: Set[str] = set()
        self.all_symbols: Set[str] = set()
        
        # For fuzzy matching and analysis
        self.symbols_by_length: Dict[int, Set[str]] = defaultdict(set)
        self.symbols_by_first_letter: Dict[str, Set[str]] = defaultdict(set)
        
        # Load symbols
        self._load_symbols()
        self._build_indexes()
        
        print(f"📊 Fast Stock Validator initialized:")
        print(f"   NASDAQ symbols: {len(self.nasdaq_symbols):,}")
        print(f"   AMEX symbols: {len(self.amex_symbols):,}")
        print(f"   Total symbols: {len(self.all_symbols):,}")
    
    def _load_symbols(self):
        """Load symbols from JSON files"""
        try:
            # Load NASDAQ symbols
            nasdaq_file = os.path.join(self.json_folder, "nasdaq_tickers.json")
            if os.path.exists(nasdaq_file):
                with open(nasdaq_file, 'r') as f:
                    nasdaq_data = json.load(f)
                    self.nasdaq_symbols = set(nasdaq_data)
                    print(f"✅ Loaded {len(self.nasdaq_symbols):,} NASDAQ symbols")
            else:
                print(f"⚠️  NASDAQ file not found: {nasdaq_file}")
            
            # Load AMEX symbols
            amex_file = os.path.join(self.json_folder, "amex_tickers.json")
            if os.path.exists(amex_file):
                with open(amex_file, 'r') as f:
                    amex_data = json.load(f)
                    self.amex_symbols = set(amex_data)
                    print(f"✅ Loaded {len(self.amex_symbols):,} AMEX symbols")
            else:
                print(f"⚠️  AMEX file not found: {amex_file}")
            
            # Combine all symbols
            self.all_symbols = self.nasdaq_symbols | self.amex_symbols
            
        except Exception as e:
            print(f"❌ Error loading symbols: {e}")
            self.all_symbols = set()
    
    def _build_indexes(self):
        """Build optimized indexes for fast searching"""
        for symbol in self.all_symbols:
            # Index by length
            self.symbols_by_length[len(symbol)].add(symbol)
            
            # Index by first letter
            if symbol:
                self.symbols_by_first_letter[symbol[0]].add(symbol)
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """
        Ultra-fast symbol validation using set lookup - O(1) average case
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            bool: True if symbol is valid
        """
        return symbol.upper() in self.all_symbols
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """
        Get detailed information about a symbol
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            dict: Symbol information
        """
        symbol_upper = symbol.upper()
        
        if symbol_upper in self.all_symbols:
            # Determine exchange
            exchange = "NASDAQ" if symbol_upper in self.nasdaq_symbols else "AMEX"
            
            return {
                'symbol': symbol_upper,
                'valid': True,
                'exchange': exchange,
                'length': len(symbol_upper),
                'validation_method': 'local_json'
            }
        else:
            return {
                'symbol': symbol_upper,
                'valid': False,
                'reason': 'not_found_in_exchanges'
            }
    
    def batch_validate(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Validate multiple symbols efficiently
        
        Args:
            symbols: List of symbols to validate
            
        Returns:
            dict: Validation results for each symbol
        """
        results = {}
        
        for symbol in symbols:
            results[symbol] = self.get_symbol_info(symbol)
        
        return results
    
    def find_similar_symbols(self, symbol: str, max_results: int = 5) -> List[str]:
        """
        Find symbols similar to the input (for typo correction)
        
        Args:
            symbol: Symbol to find similar matches for
            max_results: Maximum number of results
            
        Returns:
            list: List of similar symbols
        """
        symbol_upper = symbol.upper()
        
        # First try exact match
        if symbol_upper in self.all_symbols:
            return [symbol_upper]
        
        similar = []
        
        # Try symbols of same length starting with same letter
        if symbol_upper:
            same_length_symbols = self.symbols_by_length.get(len(symbol_upper), set())
            same_first_letter = self.symbols_by_first_letter.get(symbol_upper[0], set())
            
            # Intersection for most likely matches
            likely_matches = same_length_symbols & same_first_letter
            
            for candidate in likely_matches:
                if self._calculate_similarity(symbol_upper, candidate) > 0.7:
                    similar.append(candidate)
                    if len(similar) >= max_results:
                        break
        
        return similar
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Simple similarity calculation"""
        if len(s1) != len(s2):
            return 0.0
        
        matches = sum(1 for a, b in zip(s1, s2) if a == b)
        return matches / len(s1)
    
    def validate_extracted_symbols(self, symbols: List[str]) -> List[str]:
        """
        Validate a list of extracted symbols and return only valid ones
        
        Args:
            symbols: List of potential symbols
            
        Returns:
            list: List of validated symbols
        """
        valid_symbols = []
        
        for symbol in symbols:
            if self.is_valid_symbol(symbol):
                valid_symbols.append(symbol.upper())
        
        return valid_symbols
    
    def get_statistics(self) -> Dict:
        """Get validator statistics"""
        return {
            'total_symbols': len(self.all_symbols),
            'nasdaq_symbols': len(self.nasdaq_symbols),
            'amex_symbols': len(self.amex_symbols),
            'symbols_by_length': {k: len(v) for k, v in self.symbols_by_length.items()},
            'most_common_lengths': sorted(self.symbols_by_length.keys(), 
                                        key=lambda x: len(self.symbols_by_length[x]), 
                                        reverse=True)[:5]
        }

class OptimizedSentimentAnalyzer:
    """Enhanced sentiment analyzer using fast local validation"""
    
    def __init__(self, json_folder_path="JSON"):
        # Initialize the fast validator 
        self.fast_validator = FastStockValidator(json_folder_path)
        
        # Common stock ticker patterns (more restrictive)
        import re
        self.stock_pattern = re.compile(r'\b[A-Z]{1,5}\b')
        
        # Enhanced false positives list (common English words)
        self.false_positives = {
            # Common English words that might be detected as symbols
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 
            'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW',
            'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID',
            'ILL', 'LET', 'MAN', 'NEW', 'NOW', 'OLD', 'PUT', 'SAY', 'SHE', 'TOO',
            'USE', 'WAY', 'WIN', 'YES', 'YET', 'YOU', 'BAD', 'BIG', 'BOX', 'CUP',
            'END', 'FAN', 'FUN', 'GOT', 'HAD', 'HIT', 'HOT', 'LOT', 'MOM', 'POP',
            'RUN', 'SIT', 'TOP', 'TRY', 'WIN', 'YES', 'ZIP',
            
            # Reddit/Social media specific
            'LOL', 'OMG', 'WTF', 'TBH', 'IMO', 'YOLO', 'HODL', 'WSB', 'DD',
            'TLDR', 'ELI', 'AMA', 'TIL', 'DAE', 'PSA', 'LPT', 'TIFU',
            
            # Common words that might appear in caps
            'LIKE', 'WILL', 'WITH', 'HAVE', 'FROM', 'THEY', 'BEEN', 'MORE',
            'ABOUT', 'YOUR', 'YEARS', 'JUST', 'ALSO', 'VERY', 'WELL', 'GOOD',
            'MAKE', 'WORK', 'TIME', 'KNOW', 'WANT', 'NEED', 'EVEN', 'BACK',
            'ONLY', 'COME', 'STILL', 'THINK', 'TAKE', 'GIVE', 'LOOK', 'FEEL',
            'SEEM', 'FIND', 'KEEP', 'CALL', 'TALK', 'TURN', 'MOVE', 'LIVE',
            'SHOW', 'HEAR', 'PLAY', 'READ', 'WRITE', 'TELL', 'HELP', 'LOVE',
            
            # Financial terms that aren't stocks
            'BUY', 'SELL', 'HOLD', 'LONG', 'SHORT', 'CALL', 'PUT', 'MOON',
            'BEAR', 'BULL', 'DCA', 'ATH', 'ATL', 'RSI', 'MACD', 'SMA', 'EMA'
        }
    
    def extract_and_validate_symbols(self, text: str) -> List[str]:
        """
        Extract and validate stock symbols from text using optimized approach
        
        Args:
            text: Text to analyze
            
        Returns:
            list: List of validated stock symbols
        """
        # Convert to uppercase for analysis
        text_upper = text.upper()
        
        # Find potential symbols
        potential_symbols = self.stock_pattern.findall(text_upper)
        
        # Filter out obvious false positives first (fast)
        filtered_symbols = []
        for symbol in potential_symbols:
            if (len(symbol) >= 1 and len(symbol) <= 5 and  # Reasonable length
                symbol not in self.false_positives and      # Not a common word
                symbol.isalpha()):                          # Only letters
                filtered_symbols.append(symbol)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_symbols = []
        for symbol in filtered_symbols:
            if symbol not in seen:
                seen.add(symbol)
                unique_symbols.append(symbol)
        
        # Validate against actual stock symbols (ultra-fast O(1) lookup)
        validated_symbols = self.fast_validator.validate_extracted_symbols(unique_symbols)
        
        return validated_symbols[:10]  # Return top 10
    
    def get_stock_context_sentiment(self, text, stock_symbol):
        """
        Get context-aware sentiment for a specific stock symbol
        
        Args:
            text: Text to analyze
            stock_symbol: The stock symbol to analyze sentiment for
            
        Returns:
            dict: Contains 'score', 'label', and 'confidence'
        """
        from textblob import TextBlob
        
        # Convert to uppercase for consistency
        stock_symbol = stock_symbol.upper()
        text_upper = text.upper()
        
        # Check if stock is mentioned in text
        if stock_symbol not in text_upper:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}
        
        # Extract sentences containing the stock symbol
        sentences = text.split('.')
        relevant_sentences = [s for s in sentences if stock_symbol in s.upper()]
        
        if not relevant_sentences:
            # Fallback to full text analysis
            relevant_text = text
        else:
            relevant_text = '. '.join(relevant_sentences)
        
        # Use TextBlob for basic sentiment
        blob = TextBlob(relevant_text)
        base_sentiment = blob.sentiment.polarity
        
        # Enhance with keyword analysis
        text_lower = relevant_text.lower()
        
        # Bullish keywords
        bullish_keywords = [
            'buy', 'long', 'bull', 'bullish', 'moon', 'rocket', 'pump', 'rally',
            'surge', 'breakout', 'strong', 'positive', 'growth', 'gain', 'rise',
            'up', 'green', 'calls', 'diamond hands', 'hold', 'hodl', 'to the moon'
        ]
        
        # Bearish keywords
        bearish_keywords = [
            'sell', 'short', 'bear', 'bearish', 'crash', 'dump', 'fall', 'drop',
            'decline', 'weak', 'negative', 'loss', 'down', 'red', 'puts',
            'paper hands', 'panic sell'
        ]
        
        bullish_count = sum(1 for word in bullish_keywords if word in text_lower)
        bearish_count = sum(1 for word in bearish_keywords if word in text_lower)
        
        # Adjust sentiment based on keywords
        keyword_adjustment = (bullish_count - bearish_count) * 0.1
        final_sentiment = base_sentiment + keyword_adjustment
        
        # Clamp to [-1, 1] range
        final_sentiment = max(-1.0, min(1.0, final_sentiment))
        
        # Determine label
        if final_sentiment > 0.1:
            label = 'bullish'
        elif final_sentiment < -0.1:
            label = 'bearish'
        else:
            label = 'neutral'
        
        # Calculate confidence based on keyword strength and text length
        confidence = min(1.0, (abs(final_sentiment) + (bullish_count + bearish_count) * 0.1))
        
        return {
            'score': round(final_sentiment, 3),
            'label': label,
            'confidence': round(confidence, 3)
        }

def test_fast_validator():
    """Test the fast validator performance and accuracy"""
    print("🚀 Testing Fast Stock Validator")
    print("=" * 60)
    
    # Initialize validator
    validator = FastStockValidator()
    
    if len(validator.all_symbols) == 0:
        print("❌ No symbols loaded. Make sure JSON files are in the JSON folder.")
        return
    
    # Test cases
    test_symbols = [
        # Valid symbols
        'AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'META', 'NVDA',
        # Invalid symbols (common words)
        'WILL', 'HAVE', 'WITH', 'ALSO', 'LIKE', 'GOOD', 'VERY',
        # Invalid symbols (random)
        'XYZ123', 'FAKE', 'NOTREAL', 'DUMMY'
    ]
    
    print("⚡ Performance Test:")
    start_time = time.time()
    
    results = validator.batch_validate(test_symbols)
    
    end_time = time.time()
    print(f"   Validated {len(test_symbols)} symbols in {(end_time - start_time)*1000:.2f}ms")
    print(f"   Average: {(end_time - start_time)*1000/len(test_symbols):.2f}ms per symbol")
    
    print(f"\n📊 Validation Results:")
    valid_count = 0
    invalid_count = 0
    
    for symbol, info in results.items():
        status = "✅ VALID" if info['valid'] else "❌ INVALID"
        exchange = f"({info.get('exchange', 'N/A')})" if info['valid'] else ""
        print(f"   {symbol:<8} {status} {exchange}")
        
        if info['valid']:
            valid_count += 1
        else:
            invalid_count += 1
    
    print(f"\n📈 Summary:")
    print(f"   Valid symbols: {valid_count}")
    print(f"   Invalid symbols: {invalid_count}")
    print(f"   Accuracy: {(valid_count + invalid_count > 0 and valid_count / (valid_count + invalid_count) * 100) or 0:.1f}%")
    
    # Test with text extraction
    print(f"\n🧪 Text Extraction Test:")
    analyzer = OptimizedSentimentAnalyzer()
    
    test_texts = [
        "AAPL earnings great! Also MSFT and WILL be watching GOOGL. HAVE good feelings about TSLA.",
        "Buying AMZN calls, NVDA strong, WITH META also LIKE the outlook. VERY bullish.",
        "Portfolio: SPY, QQQ, FAKE123, NOTREAL, and some AAPL GOOD stock picks."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n   Test {i}: '{text[:50]}...'")
        extracted = analyzer.extract_and_validate_symbols(text)
        print(f"   Extracted: {', '.join(extracted) if extracted else 'None'}")
    
    # Show statistics
    stats = validator.get_statistics()
    print(f"\n📊 Validator Statistics:")
    print(f"   Total symbols: {stats['total_symbols']:,}")
    print(f"   NASDAQ: {stats['nasdaq_symbols']:,}")
    print(f"   AMEX: {stats['amex_symbols']:,}")
    print(f"   Most common lengths: {stats['most_common_lengths']}")

if __name__ == "__main__":
    test_fast_validator()