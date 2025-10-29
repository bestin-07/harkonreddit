"""
Error Handler for StockHark

Centralized error handling, logging, and reporting system
for consistent error management across the application.
"""

import logging
import traceback
import sys
from datetime import datetime
from typing import Optional, Dict, Any, Callable, Union
from pathlib import Path

from .exceptions import (
    StockHarkException, ErrorSeverity, ConfigurationError, 
    RedditAPIError, DatabaseError, ValidationError
)
from .path_utils import get_logs_directory


class ErrorHandler:
    """
    Centralized error handler with logging, monitoring, and recovery
    
    Features:
    - Structured logging with different severity levels
    - Error context preservation
    - Automatic error recovery strategies
    - Error reporting and monitoring
    - Debug information collection
    """
    
    def __init__(self, logger_name: str = "StockHark", log_level: int = logging.INFO):
        """
        Initialize error handler
        
        Args:
            logger_name: Name for the logger instance
            log_level: Logging level (default: INFO)
        """
        self.logger_name = logger_name
        self.logger = self._setup_logger(log_level)
        self.error_count = 0
        self.warning_count = 0
        self.recovery_strategies: Dict[type, Callable] = {}
        
    def _setup_logger(self, log_level: int) -> logging.Logger:
        """Setup structured logging with file and console handlers"""
        logger = logging.getLogger(self.logger_name)
        
        # Don't add handlers if they already exist
        if logger.handlers:
            return logger
            
        logger.setLevel(log_level)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler for user-facing messages
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
        
        # File handler for detailed logs
        try:
            log_file = get_logs_directory() / f"{self.logger_name.lower()}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # If we can't create log file, continue without it
            logger.warning(f"Could not create log file: {e}")
        
        return logger
    
    def handle_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None,
                        severity: str = ErrorSeverity.ERROR, silent: bool = False) -> Optional[Any]:
        """
        Handle an exception with appropriate logging and recovery
        
        Args:
            exc: Exception to handle
            context: Additional context information
            severity: Error severity level
            silent: If True, suppress console output
            
        Returns:
            Any: Result of recovery strategy if available, None otherwise
        """
        # Convert to StockHark exception if needed
        if not isinstance(exc, StockHarkException):
            exc = self._convert_exception(exc, context)
        
        # Update counters
        if severity == ErrorSeverity.ERROR or severity == ErrorSeverity.CRITICAL:
            self.error_count += 1
        elif severity == ErrorSeverity.WARNING:
            self.warning_count += 1
        
        # Log the error
        self._log_error(exc, severity, silent)
        
        # Try recovery strategy
        recovery_result = self._attempt_recovery(exc)
        
        # For critical errors, we might want to exit
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical("Critical error occurred. System may be unstable.")
        
        return recovery_result
    
    def _convert_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None) -> StockHarkException:
        """Convert standard exception to StockHark exception"""
        exc_type = type(exc)
        message = str(exc)
        
        # Map common exception types to StockHark exceptions
        exception_mapping = {
            ConnectionError: RedditAPIError,
            ValueError: ValidationError,
            KeyError: ConfigurationError,
            FileNotFoundError: ConfigurationError,
            PermissionError: ConfigurationError,
        }
        
        stockhark_exc_type = exception_mapping.get(exc_type, StockHarkException)
        
        return stockhark_exc_type(
            message=message or f"{exc_type.__name__} occurred",
            context=context,
            cause=exc
        )
    
    def _log_error(self, exc: StockHarkException, severity: str, silent: bool):
        """Log error with appropriate level and detail"""
        error_msg = f"{exc.error_code}: {exc.message}"
        
        # Add context if available
        if exc.context:
            context_str = ", ".join(f"{k}={v}" for k, v in exc.context.items())
            error_msg += f" (Context: {context_str})"
        
        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(error_msg)
            if not silent:
                self.logger.critical("Stack trace:", exc_info=exc.cause)
        elif severity == ErrorSeverity.ERROR:
            self.logger.error(error_msg)
            if not silent and exc.cause:
                self.logger.debug("Stack trace:", exc_info=exc.cause)
        elif severity == ErrorSeverity.WARNING:
            self.logger.warning(error_msg)
        else:  # INFO
            self.logger.info(error_msg)
    
    def _attempt_recovery(self, exc: StockHarkException) -> Optional[Any]:
        """Attempt to recover from error using registered strategies"""
        exc_type = type(exc)
        
        if exc_type in self.recovery_strategies:
            try:
                self.logger.debug(f"Attempting recovery for {exc_type.__name__}")
                return self.recovery_strategies[exc_type](exc)
            except Exception as recovery_exc:
                self.logger.error(f"Recovery strategy failed: {recovery_exc}")
        
        return None
    
    def register_recovery_strategy(self, exception_type: type, strategy: Callable):
        """
        Register a recovery strategy for a specific exception type
        
        Args:
            exception_type: Type of exception to handle
            strategy: Function to call for recovery (takes exception as argument)
        """
        self.recovery_strategies[exception_type] = strategy
        self.logger.debug(f"Registered recovery strategy for {exception_type.__name__}")
    
    def handle_with_fallback(self, operation: Callable, fallback: Callable, 
                           context: Optional[Dict[str, Any]] = None,
                           operation_name: str = "operation") -> Any:
        """
        Execute operation with automatic fallback on error
        
        Args:
            operation: Primary operation to attempt
            fallback: Fallback operation if primary fails
            context: Context information for error handling
            operation_name: Name of operation for logging
            
        Returns:
            Any: Result of operation or fallback
        """
        try:
            self.logger.debug(f"Attempting {operation_name}")
            return operation()
        except Exception as exc:
            self.logger.warning(f"{operation_name} failed, using fallback")
            self.handle_exception(exc, context, ErrorSeverity.WARNING, silent=True)
            
            try:
                return fallback()
            except Exception as fallback_exc:
                self.handle_exception(
                    fallback_exc, 
                    {**context, 'fallback_operation': True} if context else {'fallback_operation': True},
                    ErrorSeverity.ERROR
                )
                raise
    
    def create_context_manager(self, operation_name: str, context: Optional[Dict[str, Any]] = None):
        """
        Create a context manager for error handling
        
        Args:
            operation_name: Name of the operation
            context: Additional context information
            
        Returns:
            ErrorContext: Context manager for error handling
        """
        return ErrorContext(self, operation_name, context)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors handled"""
        return {
            'total_errors': self.error_count,
            'total_warnings': self.warning_count,
            'recovery_strategies': len(self.recovery_strategies),
            'logger_name': self.logger_name
        }


class ErrorContext:
    """Context manager for structured error handling"""
    
    def __init__(self, error_handler: ErrorHandler, operation_name: str, 
                 context: Optional[Dict[str, Any]] = None):
        self.error_handler = error_handler
        self.operation_name = operation_name
        self.context = context or {}
        
    def __enter__(self):
        self.error_handler.logger.debug(f"Starting {self.operation_name}")
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self.error_handler.handle_exception(
                exc_value, 
                {**self.context, 'operation': self.operation_name},
                ErrorSeverity.ERROR
            )
            return False  # Don't suppress the exception
        else:
            self.error_handler.logger.debug(f"Completed {self.operation_name} successfully")
        return None


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
        
        # Register common recovery strategies
        _register_default_recovery_strategies(_global_error_handler)
    
    return _global_error_handler

def _register_default_recovery_strategies(handler: ErrorHandler):
    """Register default recovery strategies for common errors"""
    
    def reddit_api_recovery(exc: RedditAPIError):
        """Recovery strategy for Reddit API errors"""
        handler.logger.info("Reddit API error - implementing rate limiting delay")
        import time
        time.sleep(5)  # Wait 5 seconds before retrying
        return None
    
    def database_recovery(exc: DatabaseError):
        """Recovery strategy for database errors"""
        handler.logger.info("Database error - attempting to reinitialize connection")
        # Could implement database reconnection logic here
        return None
    
    handler.register_recovery_strategy(RedditAPIError, reddit_api_recovery)
    handler.register_recovery_strategy(DatabaseError, database_recovery)

# Convenience functions
def handle_error(exc: Exception, context: Optional[Dict[str, Any]] = None, 
                severity: str = ErrorSeverity.ERROR, silent: bool = False) -> Optional[Any]:
    """Convenience function to handle errors with global handler"""
    return get_error_handler().handle_exception(exc, context, severity, silent)

def with_error_handling(operation_name: str, context: Optional[Dict[str, Any]] = None):
    """Decorator for automatic error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            handler = get_error_handler()
            with handler.create_context_manager(operation_name, context):
                return func(*args, **kwargs)
        return wrapper
    return decorator