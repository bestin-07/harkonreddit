#!/bin/bash
# Railway deployment script - runs during build phase

# Download spaCy language model
python -m spacy download en_core_web_sm

# Initialize NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon')"

echo "✅ Railway build completed successfully"