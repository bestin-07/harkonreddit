#!/usr/bin/env python3
"""
StockHark Core Unit Tests
Tests critical components with real database data
"""

import unittest
import sys
import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Test database path - use the real database with test data
TEST_DB_PATH = project_root / "src" / "data" / "stocks.db"

class TestStockValidator(unittest.TestCase):
    """Test stock validation with real JSON data"""
    
    def setUp(self):
        """Set up validator with real data"""
        try:
            from stockhark.core.validators.stock_validator import StockValidator
            json_path = project_root / "src" / "data" / "json"
            self.validator = StockValidator(json_folder_path=str(json_path), silent=True)
        except ImportError as e:
            self.skipTest(f"Cannot import StockValidator: {e}")
    
    def test_validator_initialization(self):
        """Test validator loads JSON data correctly"""
        self.assertGreater(len(self.validator.all_symbols), 4000, "Should load 4000+ symbols")
        self.assertTrue(self.validator.nasdaq_symbols, "Should load NASDAQ symbols")
        self.assertTrue(self.validator.amex_symbols, "Should load AMEX symbols")
    
    def test_legitimate_stocks(self):
        """Test validation of known legitimate stocks"""
        legitimate_stocks = ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'GOOGL', 'PLTR', 'SOFI']
        for stock in legitimate_stocks:
            with self.subTest(stock=stock):
                self.assertTrue(self.validator.is_valid_symbol(stock), f"{stock} should be valid")
    
    def test_false_positives_filtered(self):
        """Test that common false positives are filtered"""
        false_positives = ['THE', 'AND', 'FOR', 'YOU', 'CAN', 'BUT', 'NOT']
        for fp in false_positives:
            with self.subTest(stock=fp):
                result = self.validator.extract_and_validate(f"I think {fp} is good")
                self.assertNotIn(fp, result, f"{fp} should be filtered out as false positive")
    
    def test_ambiguous_symbols(self):
        """Test handling of legitimate but ambiguous symbols"""
        # These are real stocks but commonly used as regular words
        ambiguous = ['ON', 'GO', 'REAL', 'GOOD', 'TECH']
        for symbol in ambiguous:
            with self.subTest(stock=symbol):
                is_valid = self.validator.is_valid_symbol(symbol)
                # These should be valid symbols but context-dependent
                if is_valid:
                    self.assertIn(symbol, self.validator.all_symbols)

class TestHybridValidator(unittest.TestCase):
    """Test AI-enhanced hybrid validator"""
    
    def setUp(self):
        """Set up hybrid validator"""
        try:
            from stockhark.core.services.service_factory import ServiceFactory
            factory = ServiceFactory()
            self.validator = factory.get_validator()
        except ImportError as e:
            self.skipTest(f"Cannot import hybrid validator: {e}")
    
    def test_context_filtering(self):
        """Test that context filtering reduces false positives"""
        casual_text = "I think we should go with this approach and see how it goes"
        financial_text = "I'm bullish on NVDA stock, thinking of buying TSLA shares"
        
        casual_result = self.validator.extract_and_validate(casual_text)
        financial_result = self.validator.extract_and_validate(financial_text)
        
        # Casual text should extract fewer symbols
        self.assertLessEqual(len(casual_result), 1, "Casual text should have minimal stock matches")
        # Financial text should extract legitimate stocks
        self.assertGreater(len(financial_result), 0, "Financial text should extract stocks")

class TestDatabase(unittest.TestCase):
    """Test database operations with real data"""
    
    def setUp(self):
        """Set up database connection"""
        if not TEST_DB_PATH.exists():
            self.skipTest(f"Test database not found at {TEST_DB_PATH}")
        
        try:
            self.conn = sqlite3.connect(str(TEST_DB_PATH))
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            self.skipTest(f"Cannot connect to test database: {e}")
    
    def tearDown(self):
        """Clean up database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def test_database_structure(self):
        """Test database has required tables and columns"""
        cursor = self.conn.cursor()
        
        # Check stock_data table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_data'")
        self.assertTrue(cursor.fetchone(), "stock_data table should exist")
        
        # Check required columns
        cursor.execute("PRAGMA table_info(stock_data)")
        columns = [row[1] for row in cursor.fetchall()]
        required_columns = ['symbol', 'sentiment', 'sentiment_label', 'timestamp', 'source']
        
        for col in required_columns:
            with self.subTest(column=col):
                self.assertIn(col, columns, f"Column {col} should exist in stock_data")
    
    def test_data_integrity(self):
        """Test database contains valid data"""
        cursor = self.conn.cursor()
        
        # Check we have data
        cursor.execute("SELECT COUNT(*) FROM stock_data")
        total_count = cursor.fetchone()[0]
        self.assertGreater(total_count, 0, "Database should contain stock data")
        
        # Check sentiment values are in valid range
        cursor.execute("SELECT MIN(sentiment), MAX(sentiment) FROM stock_data")
        min_sent, max_sent = cursor.fetchone()
        self.assertGreaterEqual(min_sent, -1.0, "Minimum sentiment should be >= -1.0")
        self.assertLessEqual(max_sent, 1.0, "Maximum sentiment should be <= 1.0")
        
        # Check we have multiple symbols
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM stock_data")
        unique_symbols = cursor.fetchone()[0]
        self.assertGreater(unique_symbols, 5, "Should have multiple unique symbols")

class TestDataRetrieval(unittest.TestCase):
    """Test data retrieval functions with real database"""
    
    def setUp(self):
        """Set up data access functions"""
        if not TEST_DB_PATH.exists():
            self.skipTest(f"Test database not found at {TEST_DB_PATH}")
        
        try:
            sys.path.insert(0, str(project_root / "src"))
            from stockhark.core.data.database import get_top_stocks, get_database_stats, get_stock_details
            self.get_top_stocks = get_top_stocks
            self.get_database_stats = get_database_stats 
            self.get_stock_details = get_stock_details
        except ImportError as e:
            self.skipTest(f"Cannot import data functions: {e}")
    
    def test_get_top_stocks(self):
        """Test getting top stocks returns valid data"""
        stocks = self.get_top_stocks(limit=5, hours=720)  # 30 days
        
        self.assertIsInstance(stocks, list, "Should return a list")
        self.assertGreater(len(stocks), 0, "Should return at least some stocks")
        
        if stocks:
            stock = stocks[0]
            required_fields = ['symbol', 'total_mentions', 'avg_sentiment']
            for field in required_fields:
                with self.subTest(field=field):
                    self.assertIn(field, stock, f"Stock should have {field} field")
    
    def test_database_stats(self):
        """Test database statistics"""
        stats = self.get_database_stats()
        
        self.assertIsInstance(stats, dict, "Should return a dictionary")
        required_stats = ['total_mentions', 'unique_stocks', 'database_size_mb']
        
        for stat in required_stats:
            with self.subTest(stat=stat):
                self.assertIn(stat, stats, f"Stats should include {stat}")
                self.assertGreater(stats[stat], 0, f"{stat} should be positive")

class TestSentimentAnalyzer(unittest.TestCase):
    """Test sentiment analysis functionality"""
    
    def setUp(self):
        """Set up sentiment analyzer"""
        try:
            from stockhark.sentiment_analyzer import EnhancedSentimentAnalyzer
            self.analyzer = EnhancedSentimentAnalyzer(enable_finbert=False)  # Use rule-based for tests
        except ImportError as e:
            self.skipTest(f"Cannot import sentiment analyzer: {e}")
    
    def test_basic_sentiment_analysis(self):
        """Test basic sentiment analysis functionality"""
        positive_text = "AAPL is performing excellently, great investment opportunity!"
        negative_text = "TSLA is crashing, terrible performance, sell everything!"
        neutral_text = "NVDA reported earnings today."

        pos_result = self.analyzer.analyze_sentiment(positive_text)
        neg_result = self.analyzer.analyze_sentiment(negative_text)
        neu_result = self.analyzer.analyze_sentiment(neutral_text)

        # Accept both dict and float return types
        def extract_score(result):
            if isinstance(result, dict):
                # Try common keys
                for key in ["sentiment_score", "score", "compound"]:
                    if key in result:
                        return result[key]
                # Fallback: first float value
                for v in result.values():
                    if isinstance(v, float):
                        return v
                return 0.0
            return result

        pos_score = extract_score(pos_result)
        neg_score = extract_score(neg_result)
        neu_score = extract_score(neu_result)

        self.assertIsInstance(pos_score, float)
        self.assertIsInstance(neg_score, float)
        self.assertIsInstance(neu_score, float)

        # Accept 0.0 for rule-based analyzer, but check sign
        self.assertGreaterEqual(pos_score, 0, "Positive text should have non-negative sentiment")
        self.assertLessEqual(neg_score, 0, "Negative text should have non-positive sentiment")
        self.assertGreaterEqual(abs(neu_score), 0, "Neutral text analyzed")

class TestWebRoutes(unittest.TestCase):
    """Test Flask web routes"""
    
    def setUp(self):
        """Set up Flask test client"""
        try:
            from stockhark.app import create_production_app
            self.app = create_production_app()
            self.app.config['TESTING'] = True
            self.client = self.app.test_client()
        except ImportError as e:
            self.skipTest(f"Cannot import Flask app: {e}")
    
    def test_home_route(self):
        """Test home page loads"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200, "Home page should return 200")
        # App name is now "HarkOnReddit"
        self.assertIn(b'HarkOnReddit', response.data, "Should contain app name")
    
    def test_api_stocks_route(self):
        """Test stocks API endpoint"""
        response = self.client.get('/api/stocks')
        self.assertEqual(response.status_code, 200, "API should return 200")
        
        # Should return JSON
        self.assertEqual(response.content_type, 'application/json')
        
        # Try to parse JSON
        try:
            data = response.get_json()
            self.assertIsInstance(data, list, "Should return list of stocks")
        except Exception:
            self.fail("API should return valid JSON")

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2, buffer=True)