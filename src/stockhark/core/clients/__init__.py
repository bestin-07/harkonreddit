"""
External API clients for StockHark application.

This module contains clients for integrating with external services.
"""

from .reddit_client import get_reddit_client

__all__ = [
    'get_reddit_client'
]