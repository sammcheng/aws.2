"""
Structured logging utilities for the Accessibility Checker API.
Provides contextual logging with request IDs, timestamps, and error types.
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone
from utils.exceptions import AccessibilityCheckerError


class StructuredLogger:
    """Structured logger with contextual information."""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, level.upper()))
        
        # Create JSON formatter
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def _create_log_entry(
        self,
        level: str,
        message: str,
        request_id: Optional[str] = None,
        function_name: Optional[str] = None,
        operation: Optional[str] = None,
        error_type: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create structured log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "message": message,
            "service": "accessibility-checker-api"
        }
        
        # Add contextual information
        if request_id:
            entry["request_id"] = request_id
        if function_name:
            entry["function_name"] = function_name
        if operation:
            entry["operation"] = operation
        if error_type:
            entry["error_type"] = error_type
        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 2)
        
        # Add any additional context
        entry.update(kwargs)
        
        return entry
    
    def info(
        self,
        message: str,
        request_id: Optional[str] = None,
        function_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Log info message with context."""
        entry = self._create_log_entry(
            "INFO", message, request_id, function_name, operation, **kwargs
        )
        self.logger.info(json.dumps(entry))
    
    def warning(
        self,
        message: str,
        request_id: Optional[str] = None,
        function_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Log warning message with context."""
        entry = self._create_log_entry(
            "WARNING", message, request_id, function_name, operation, **kwargs
        )
        self.logger.warning(json.dumps(entry))
    
    def error(
        self,
        message: str,
        request_id: Optional[str] = None,
        function_name: Optional[str] = None,
        operation: Optional[str] = None,
        error_type: Optional[str] = None,
        exception: Optional[Exception] = None,
        **kwargs
    ):
        """Log error message with context."""
        entry = self._create_log_entry(
            "ERROR", message, request_id, function_name, operation, error_type, **kwargs
        )
        
        # Add exception details if provided
        if exception:
            entry["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception)
            }
            
            # Add custom exception details
            if isinstance(exception, AccessibilityCheckerError):
                entry["error_code"] = exception.error_code
                entry["error_details"] = exception.details
        
        self.logger.error(json.dumps(entry))
    
    def debug(
        self,
        message: str,
        request_id: Optional[str] = None,
        function_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Log debug message with context."""
        entry = self._create_log_entry(
            "DEBUG", message, request_id, function_name, operation, **kwargs
        )
        self.logger.debug(json.dumps(entry))
    
    def performance(
        self,
        message: str,
        duration_ms: float,
        request_id: Optional[str] = None,
        function_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """Log performance metrics."""
        entry = self._create_log_entry(
            "INFO", message, request_id, function_name, operation, duration_ms=duration_ms, **kwargs
        )
        entry["metric_type"] = "performance"
        self.logger.info(json.dumps(entry))
    
    def business_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        request_id: Optional[str] = None,
        function_name: Optional[str] = None,
        **kwargs
    ):
        """Log business metrics."""
        entry = self._create_log_entry(
            "INFO", f"Business metric: {metric_name}", request_id, function_name, **kwargs
        )
        entry["metric_type"] = "business"
        entry["metric_name"] = metric_name
        entry["metric_value"] = value
        self.logger.info(json.dumps(entry))


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        if hasattr(record, 'getMessage'):
            return record.getMessage()
        return super().format(record)


class RequestContext:
    """Context manager for request-scoped logging."""
    
    def __init__(self, request_id: str, function_name: str, logger: StructuredLogger):
        self.request_id = request_id
        self.function_name = function_name
        self.logger = logger
        self.start_time = time.time()
    
    def __enter__(self):
        self.logger.info(
            "Request started",
            request_id=self.request_id,
            function_name=self.function_name,
            operation="request_start"
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        
        if exc_type:
            self.logger.error(
                f"Request failed: {exc_val}",
                request_id=self.request_id,
                function_name=self.function_name,
                operation="request_end",
                error_type=exc_type.__name__,
                exception=exc_val,
                duration_ms=duration_ms
            )
        else:
            self.logger.info(
                "Request completed successfully",
                request_id=self.request_id,
                function_name=self.function_name,
                operation="request_end",
                duration_ms=duration_ms
            )
    
    def log_operation(self, operation: str, message: str, **kwargs):
        """Log operation within request context."""
        self.logger.info(
            message,
            request_id=self.request_id,
            function_name=self.function_name,
            operation=operation,
            **kwargs
        )
    
    def log_error(self, operation: str, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error within request context."""
        self.logger.error(
            message,
            request_id=self.request_id,
            function_name=self.function_name,
            operation=operation,
            exception=exception,
            **kwargs
        )


def get_logger(name: str, level: Optional[str] = None) -> StructuredLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        level: Log level (defaults to LOG_LEVEL env var or INFO)
        
    Returns:
        StructuredLogger instance
    """
    log_level = level or os.getenv('LOG_LEVEL', 'INFO')
    return StructuredLogger(name, log_level)


def create_request_context(request_id: str, function_name: str) -> RequestContext:
    """
    Create a request context for scoped logging.
    
    Args:
        request_id: Unique request identifier
        function_name: Name of the Lambda function
        
    Returns:
        RequestContext instance
    """
    logger = get_logger(function_name)
    return RequestContext(request_id, function_name, logger)
