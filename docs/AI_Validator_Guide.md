# AI Stock Validator Documentation

## Overview

The AI Stock Validator is a modular enhancement to StockHark that uses Natural Language Processing (NER - Named Entity Recognition) to extract company names and stock symbols from text. It's designed to work alongside the existing regex-based validator without breaking compatibility.

## Features

### 🧠 AI Stock Validator (`ai_stock_validator.py`)
- **Company Name Extraction**: Uses spaCy NER to find organizations and company names
- **Enhanced Symbol Detection**: Improved regex patterns with context-aware confidence scoring
- **Confidence Scoring**: Each match gets a confidence score based on context and validation rules
- **Modular Design**: Can be used independently or combined with existing validators

### 🔄 Hybrid Validator (`hybrid_validator.py`)
- **Best of Both Worlds**: Combines current regex validator + AI validator
- **Fallback Protection**: Always works, even if AI components are unavailable
- **Multiple Combination Modes**:
  - `union`: Include results from both validators (default)
  - `intersection`: Only symbols found by both validators
  - `ai_priority`: Prefer AI results but include current validator as fallback

### ⚙️ Service Factory Integration
- **Seamless Integration**: Automatically uses best available validator
- **Configuration-Driven**: Enable/disable via `FEATURE_FLAGS`
- **Backward Compatible**: Existing code continues to work unchanged

## Installation

### 1. Install Dependencies
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

### 2. Enable AI Validator
In `src/stockhark/core/constants.py`:
```python
FEATURE_FLAGS: Dict[str, bool] = {
    # ... other flags ...
    'ENABLE_AI_VALIDATOR': True,  # Change to True
}
```

### 3. Optional: Configure AI Settings
```python
AI_VALIDATOR_MODEL: str = "en_core_web_sm"  # spaCy model
AI_VALIDATOR_MIN_CONFIDENCE: float = 0.5    # Confidence threshold
AI_VALIDATOR_COMBINE_MODE: str = "union"    # Combination strategy
```

## Usage

### Basic Usage (Backward Compatible)
```python
from stockhark.core.services.service_factory import ServiceFactory

factory = ServiceFactory()
validator = factory.get_validator()  # Gets best available validator

# Works exactly like before
symbols = validator.extract_and_validate("I love $AAPL and Tesla Inc.")
print(symbols)  # ['AAPL', 'TSLA'] (if Tesla mapping exists)
```

### Advanced Usage (Hybrid Validator)
```python
from stockhark.core.validators.hybrid_validator import HybridStockValidator

validator = HybridStockValidator(ai_enabled=True)

# Get detailed results
result = validator.extract_and_validate_detailed(text)
print(f"Symbols: {result.symbols}")
print(f"Companies: {result.companies}")
print(f"Sources: {result.sources}")  # Shows which validator found each symbol
print(f"Confidence: {result.confidence_scores}")

# Get company names (new feature)
companies = validator.get_companies("Apple Inc. and Microsoft Corp are great")
print(companies)  # ['Apple Inc.', 'Microsoft Corp']
```

### AI-Only Usage
```python
from stockhark.core.validators.ai_stock_validator import AIStockValidator

validator = AIStockValidator()

if validator.is_ready():
    # Get all matches with confidence scores
    matches = validator.get_all_matches(text, min_confidence=0.4)
    
    for match in matches:
        if match.symbol:
            print(f"Symbol: ${match.symbol} (confidence: {match.confidence:.2f})")
        if match.company_name:
            print(f"Company: {match.company_name} (confidence: {match.confidence:.2f})")
```

## Configuration Options

### Feature Flags (`constants.py`)
```python
FEATURE_FLAGS = {
    'ENABLE_AI_VALIDATOR': False,  # Master switch for AI functionality
}

# AI Validator Configuration
AI_VALIDATOR_MODEL = "en_core_web_sm"           # spaCy model name
AI_VALIDATOR_MIN_CONFIDENCE = 0.5              # Minimum confidence threshold
AI_VALIDATOR_COMBINE_MODE = "union"            # How to combine results
```

### Combination Modes
- **`union`** (default): Include all symbols from both validators
- **`intersection`**: Only symbols found by both validators (high precision)
- **`ai_priority`**: Prefer high-confidence AI results, fall back to current validator

## Testing

Run the test suite to verify everything works:
```bash
python scripts/test_ai_validator.py
```

## Migration Strategy

### Phase 1: Installation (Optional)
- AI validator is **disabled by default**
- Install spaCy dependencies when ready
- No impact on existing functionality

### Phase 2: Testing
- Enable AI validator in development/testing
- Compare results with current validator
- Tune confidence thresholds and combination modes

### Phase 3: Production (Future)
- Enable AI validator in production
- Monitor performance and accuracy
- Gradually increase reliance on AI results

### Phase 4: Deprecation (Far Future)
- Eventually replace current validator with AI-only
- Remove regex-based validation
- Pure NLP-based extraction

## Technical Details

### Performance
- **AI Validator**: ~10-50ms per text (depends on length)
- **Current Validator**: ~1-5ms per text
- **Hybrid**: Combines both, total time = sum of individual times

### Memory Usage
- **spaCy Model**: ~50MB (en_core_web_sm)
- **Runtime**: Minimal additional memory overhead

### Accuracy Improvements
- **Company Names**: Can detect "Apple Inc.", "Tesla Motors", etc.
- **Context Awareness**: Considers surrounding text for confidence
- **False Positive Reduction**: Better filtering of non-stock acronyms

## Examples

### Input Text
```
"I'm very bullish on Apple Inc. ($AAPL) and Tesla Motors. 
Microsoft Corporation stock is also looking good. 
What do you think about AMD and NVIDIA Corp?"
```

### Current Validator Output
```
['AAPL', 'AMD']  # Misses companies without explicit symbols
```

### AI + Hybrid Validator Output
```
Symbols: ['AAPL', 'AMD', 'TSLA', 'MSFT', 'NVDA']
Companies: ['Apple Inc.', 'Tesla Motors', 'Microsoft Corporation', 'NVIDIA Corp']
Sources: {
    'AAPL': 'both',     # Found by both validators
    'AMD': 'current',   # Found by regex only
    'TSLA': 'ai',       # Found by AI (Tesla Motors -> TSLA mapping)
    'MSFT': 'ai',       # Found by AI (Microsoft Corporation -> MSFT)
    'NVDA': 'ai'        # Found by AI (NVIDIA Corp -> NVDA)
}
```

## Error Handling

The system is designed to be fault-tolerant:

1. **Missing spaCy**: Falls back to current validator
2. **Model Load Error**: Logs warning, continues with current validator
3. **Runtime Errors**: Catches exceptions, returns current validator results
4. **Import Errors**: Graceful degradation to current validator

## Future Enhancements

1. **Custom Financial Models**: Train spaCy on financial datasets
2. **Stock Symbol Mapping**: Build comprehensive company name -> symbol database
3. **Sentiment Context**: Use AI to better understand stock mention context
4. **Multi-Language Support**: Support non-English financial discussions
5. **Performance Optimization**: Cache results, optimize model loading