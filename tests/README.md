# StockHark Testing Guide

## Overview
Comprehensive testing suite for StockHark with real database integration and Railway deployment readiness checks.

## Test Structure

### 1. Core Functionality Tests (`test_core.py`)
- **Stock Validator Tests**: JSON data loading, symbol validation, false positive filtering
- **Hybrid Validator Tests**: AI-enhanced context filtering with spaCy NER
- **Database Tests**: Schema validation, data integrity, query performance
- **Data Retrieval Tests**: `get_top_stocks()`, `get_database_stats()` functionality
- **Sentiment Analyzer Tests**: Basic sentiment analysis validation
- **Web Routes Tests**: Flask application and API endpoint testing

### 2. Performance & System Tests (`test_performance.py`)
- **Performance Metrics**: Memory usage monitoring (Railway 512MB limit)
- **Database Performance**: Query execution time benchmarks
- **Validator Performance**: Stock validation speed tests
- **Railway Compatibility**: Environment variables, static files, database paths
- **System Integration**: Bootstrap script, service factory, JSON data integrity
- **Data Consistency**: Cross-validation between JSON files and database

## Running Tests

### Quick Test Run
```bash
# Run all tests with the test runner
python run_tests.py
```

### Detailed Test Runs
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run specific test files
python -m pytest tests/test_core.py -v
python -m pytest tests/test_performance.py -v

# Run with coverage
python -m pytest --cov=src tests/ --cov-report=html

# Run integration tests only
python -m pytest -m integration -v

# Run fast tests (skip slow ones)
python -m pytest -m "not slow" -v
```

### GitHub Actions Testing
The `.github/workflows/test-and-deploy.yml` workflow automatically:
1. Sets up Python 3.11 environment
2. Installs dependencies and system requirements
3. Downloads spaCy language model
4. Verifies database and JSON data files
5. Runs comprehensive test suite
6. Tests Flask application routes
7. Deploys to Railway on success

## Database Testing

### Real Database Integration
Tests use the actual `src/data/stocks.db` with **8,333+ stock mentions**:
- ✅ Tests run against real production data
- ✅ Validates actual stock validator performance
- ✅ Checks sentiment analysis quality
- ✅ Verifies query performance with real volume

### Database Verification Commands
```bash
# Check database stats
sqlite3 src/data/stocks.db "SELECT COUNT(*) as total_records FROM stock_data;"
sqlite3 src/data/stocks.db "SELECT COUNT(DISTINCT symbol) as unique_stocks FROM stock_data;"

# View top stocks
sqlite3 src/data/stocks.db "
SELECT symbol, COUNT(*) as mentions, AVG(sentiment) as avg_sentiment 
FROM stock_data 
GROUP BY symbol 
HAVING mentions > 3
ORDER BY mentions DESC 
LIMIT 10;"
```

## Test Categories

### ✅ **Passing Tests**
- Stock validator JSON loading (4000+ symbols)
- Database schema and data integrity
- Flask application creation and routes
- API endpoint functionality
- Basic sentiment analysis

### ⚠️ **Conditional Tests**
- AI-enhanced validation (requires spaCy model)
- Performance tests (requires psutil)
- Database-dependent tests (requires stocks.db)

### 🔄 **Continuous Integration**
- Automatic testing on push/PR
- Railway deployment on success
- Test result summaries in GitHub

## Railway Deployment Testing

### Pre-deployment Checks
- ✅ Memory usage < 400MB (Railway 512MB limit)
- ✅ Database queries < 2 seconds
- ✅ Flask app startup successful
- ✅ Static file handling
- ✅ Environment variable processing

### Post-deployment Verification
- ✅ Bootstrap script functionality
- ✅ Database persistence via git inclusion
- ✅ API endpoints return data
- ✅ Stock validation system operational

## Test Data Quality

### Stock Validation Quality
- **JSON Symbols**: 4000+ legitimate stock symbols
- **Database Records**: 8,333+ sentiment-analyzed mentions
- **Validation Accuracy**: AI-enhanced context filtering
- **False Positive Handling**: Advanced NER-based filtering

### Performance Benchmarks
- **Validator Init**: < 10 seconds
- **Stock Validation**: < 1 second per text
- **Database Queries**: < 2 seconds for complex aggregations
- **Memory Usage**: < 400MB peak

## Troubleshooting

### Common Issues
1. **Missing Database**: Tests will skip database-dependent checks
2. **Missing spaCy Model**: AI validation tests will be skipped
3. **Import Errors**: Check PYTHONPATH includes `src/` directory
4. **Performance Issues**: Install `psutil` for detailed system monitoring

### Environment Setup
```bash
# Ensure proper project structure
src/
├── data/
│   ├── stocks.db          # Main database
│   └── json/              # Stock symbol JSON files
├── stockhark/             # Main application code
└── ...

tests/
├── test_core.py          # Core functionality tests
├── test_performance.py   # Performance & system tests
└── test_integration.py   # Existing integration tests
```

## Test Results Interpretation

### Success Indicators
- ✅ All core tests pass
- ✅ Database contains expected data volume
- ✅ API returns stock data
- ✅ Memory usage within Railway limits
- ✅ Flask application starts successfully

### Warning Indicators
- ⚠️ Some tests skipped due to missing dependencies
- ⚠️ Performance tests show high resource usage
- ⚠️ Database inconsistencies detected

### Failure Indicators
- ❌ Core functionality broken
- ❌ Database corruption or missing
- ❌ API endpoints non-functional
- ❌ Memory usage exceeds Railway limits

## GitHub Secrets Setup

For Railway deployment, set these secrets in your GitHub repository:

1. Go to Repository Settings → Secrets and Variables → Actions
2. Add: `RAILWAY_TOKEN` with your Railway API token
3. Get token from: https://railway.app/account/tokens

The workflow will automatically deploy on successful test completion.