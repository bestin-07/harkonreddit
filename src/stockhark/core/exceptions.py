"""
StockHark Exception Classes

Centralized exception hierarchy for consistent error handling
across the StockHark application.
"""

from typing import Optional, Dict, Any


class StockHarkException(Exception):
    """
    Base exception class for all StockHark-specific errors
    
    Provides consistent error handling with optional context
    and error codes for different types of failures.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None, cause: Optional[Exception] = None):
        """
        Initialize StockHark exception
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            context: Additional context information
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()
        self.context = context or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'context': self.context,
            'cause': str(self.cause) if self.cause else None
        }
    
    def __str__(self) -> str:
        base_msg = f"{self.error_code}: {self.message}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg += f" (Context: {context_str})"
        if self.cause:
            base_msg += f" (Caused by: {self.cause})"
        return base_msg


class ConfigurationError(StockHarkException):
    """Raised when there are configuration-related errors"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, 
                 expected_value: Optional[str] = None, actual_value: Optional[str] = None):
        context = {}
        if config_key:
            context['config_key'] = config_key
        if expected_value:
            context['expected'] = expected_value
        if actual_value:
            context['actual'] = actual_value
        
        super().__init__(message, 'CONFIG_ERROR', context)


class RedditAPIError(StockHarkException):
    """Raised when Reddit API operations fail"""
    
    def __init__(self, message: str, api_endpoint: Optional[str] = None, 
                 status_code: Optional[int] = None, subreddit: Optional[str] = None):
        context = {}
        if api_endpoint:
            context['endpoint'] = api_endpoint
        if status_code:
            context['status_code'] = status_code
        if subreddit:
            context['subreddit'] = subreddit
        
        super().__init__(message, 'REDDIT_API_ERROR', context)


class DatabaseError(StockHarkException):
    """Raised when database operations fail"""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 table: Optional[str] = None, query: Optional[str] = None):
        context = {}
        if operation:
            context['operation'] = operation
        if table:
            context['table'] = table
        if query:
            context['query'] = query[:100] + "..." if query and len(query) > 100 else query
        
        super().__init__(message, 'DATABASE_ERROR', context)


class ValidationError(StockHarkException):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None, expected_type: Optional[str] = None):
        context = {}
        if field:
            context['field'] = field
        if value is not None:
            context['value'] = str(value)[:100]  # Truncate long values
        if expected_type:
            context['expected_type'] = expected_type
        
        super().__init__(message, 'VALIDATION_ERROR', context)


class SentimentAnalysisError(StockHarkException):
    """Raised when sentiment analysis fails"""
    
    def __init__(self, message: str, analyzer_type: Optional[str] = None, 
                 text_length: Optional[int] = None, model_name: Optional[str] = None):
        context = {}
        if analyzer_type:
            context['analyzer_type'] = analyzer_type
        if text_length:
            context['text_length'] = text_length
        if model_name:
            context['model_name'] = model_name
        
        super().__init__(message, 'SENTIMENT_ERROR', context)


# Removed unused: StockValidationError


class BackgroundServiceError(StockHarkException):
    """Raised when background services encounter errors"""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 operation: Optional[str] = None, collection_cycle: Optional[int] = None):
        context = {}
        if service_name:
            context['service_name'] = service_name
        if operation:
            context['operation'] = operation
        if collection_cycle:
            context['collection_cycle'] = collection_cycle
        
        super().__init__(message, 'BACKGROUND_SERVICE_ERROR', context)


# Removed unused: ServiceFactoryError, DataCollectionError


# Error severity levels
class ErrorSeverity:
    """Error severity levels for consistent error classification"""
    CRITICAL = "CRITICAL"    # System cannot continue
    ERROR = "ERROR"          # Operation failed but system can continue
    WARNING = "WARNING"      # Potential issue, system continues normally
    INFO = "INFO"           # Informational message


# Removed unused: ErrorMessages class, create_error_from_exception function