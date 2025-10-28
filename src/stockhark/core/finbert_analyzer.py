"""
FinBERT Financial Sentiment Analyzer
Minimalistic implementation with time decay and normalization
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from datetime import datetime, timedelta
import re

class FinBERTSentimentAnalyzer:
    def __init__(self):
        # Load ProsusAI/finbert model
        self.tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finbert')
        self.model = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')
        self.model.eval()
        
        # Stock symbol pattern
        self.stock_pattern = re.compile(r'\b[A-Z]{1,5}\b')
    
    def get_sentence_sentiment(self, text):
        """Get FinBERT sentiment probabilities for text"""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        # FinBERT outputs: [negative, neutral, positive]
        neg, neu, pos = probs[0].numpy()
        
        # Calculate sentiment score: P(positive) - P(negative)
        sentiment_score = pos - neg
        return sentiment_score, {"positive": pos, "neutral": neu, "negative": neg}
    
    def extract_stock_mentions(self, text):
        """Extract stock symbols from text"""
        return list(set(self.stock_pattern.findall(text.upper())))
    
    def time_decay_weight(self, timestamp, decay_lambda=0.1):
        """Calculate time decay weight: w_t = e^(-λ * Δt)"""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        delta_hours = (datetime.now() - timestamp).total_seconds() / 3600
        return np.exp(-decay_lambda * delta_hours)
    
    def analyze_stock_sentiment(self, posts_data, source_weight=1.0):
        """
        Analyze sentiment for stocks with time decay
        
        posts_data: list of {"text": str, "timestamp": str, "stocks": list}
        """
        stock_sentiments = {}
        
        for post in posts_data:
            # Get sentence sentiment
            sentiment_score, probs = self.get_sentence_sentiment(post["text"])
            
            # Calculate time weight
            time_weight = self.time_decay_weight(post["timestamp"])
            
            # Combined weight
            total_weight = time_weight * source_weight
            
            # Apply to each stock mentioned
            for stock in post.get("stocks", []):
                if stock not in stock_sentiments:
                    stock_sentiments[stock] = {"scores": [], "weights": []}
                
                stock_sentiments[stock]["scores"].append(sentiment_score)
                stock_sentiments[stock]["weights"].append(total_weight)
        
        # Calculate weighted average for each stock
        final_sentiments = {}
        for stock, data in stock_sentiments.items():
            scores = np.array(data["scores"])
            weights = np.array(data["weights"])
            
            # Weighted average
            weighted_avg = np.average(scores, weights=weights)
            
            # Normalize to [-1, 1]
            sentiment_score = max(min(weighted_avg, 1.0), -1.0)
            
            final_sentiments[stock] = {
                "sentiment": sentiment_score,
                "mentions": len(scores),
                "confidence": np.sum(weights)
            }
        
        return final_sentiments

# Simple usage example
def analyze_reddit_post(text, timestamp=None):
    """Simple function to analyze a single Reddit post"""
    analyzer = FinBERTSentimentAnalyzer()
    
    # Extract stocks
    stocks = analyzer.extract_stock_mentions(text)
    
    if not stocks:
        return None
    
    # Prepare data
    post_data = [{
        "text": text,
        "timestamp": timestamp or datetime.now().isoformat(),
        "stocks": stocks
    }]
    
    # Analyze
    sentiments = analyzer.analyze_stock_sentiment(post_data)
    
    return sentiments