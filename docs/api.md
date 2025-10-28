# StockHark API Documentation

## Overview

StockHark provides REST API endpoints for accessing stock sentiment data from Reddit.

## Authentication

Currently, no authentication is required for API access.

## Endpoints

### GET /api/stocks

Returns a list of all tracked stocks with basic sentiment information.

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "mentions": 150,
    "sentiment": 0.25,
    "sentiment_label": "bullish",
    "last_updated": "2025-10-28T10:00:00Z"
  }
]
```

### GET /api/stock/{symbol}

Returns detailed information for a specific stock symbol.

**Parameters:**
- `symbol` (string): Stock ticker symbol (e.g., "AAPL")

**Response:**
```json
{
  "symbol": "AAPL",
  "mentions": 150,
  "avg_sentiment": 0.25,
  "bullish": 90,
  "bearish": 30,
  "neutral": 30,
  "recent_mentions": [
    {
      "timestamp": "2025-10-28T09:30:00Z",
      "sentiment": 0.8,
      "sentiment_label": "bullish",
      "source": "wallstreetbets",
      "post_url": "https://reddit.com/..."
    }
  ],
  "top_sources": [
    {"source": "wallstreetbets", "mentions": 75},
    {"source": "stocks", "mentions": 45}
  ]
}
```

### GET /api/status

Returns application status and health information.

**Response:**
```json
{
  "status": "healthy",
  "database": {
    "total_mentions": 15000,
    "unique_stocks": 150,
    "last_updated": "2025-10-28T10:00:00Z"
  },
  "reddit_monitor": {
    "status": "active",
    "subreddits": 67
  }
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful request
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a message field:
```json
{
  "error": "Stock symbol not found",
  "message": "The requested stock symbol 'INVALID' was not found in our database."
}
```