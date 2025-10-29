"""
Data access layer for StockHark application.

This module contains database operations and data models.
"""

from .database import (
    init_db,
    get_db_connection,
    add_subscriber,
    get_active_subscribers,
    update_subscriber_notification,
    add_stock_data_batch,
    add_stock_data,
    get_top_stocks,
    get_stock_details,
    get_recent_activity,
    get_database_stats
)

__all__ = [
    'init_db',
    'get_db_connection',
    'add_subscriber',
    'get_active_subscribers', 
    'update_subscriber_notification',
    'add_stock_data_batch',
    'add_stock_data',
    'get_top_stocks',
    'get_stock_details',
    'get_recent_activity',
    'get_database_stats'
]