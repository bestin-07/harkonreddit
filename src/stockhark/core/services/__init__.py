"""
Services layer for StockHark application.

This module contains business logic and service orchestration.
"""

from .background_collector import (
    BackgroundDataCollector,
    start_background_collection,
    stop_background_collection
)
from .service_factory import (
    ServiceFactory,
    get_service_factory
)

__all__ = [
    'BackgroundDataCollector',
    'start_background_collection',
    'stop_background_collection',
    'ServiceFactory',
    'get_service_factory'
]