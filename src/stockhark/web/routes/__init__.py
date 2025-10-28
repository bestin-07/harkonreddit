"""
StockHark Web Routes Module

Provides organized route blueprints for the Flask application.
"""

from .web_routes import web_bp
from .api_routes import api_bp

__all__ = ['web_bp', 'api_bp']