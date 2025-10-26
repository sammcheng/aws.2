"""
Logging utility for the home accessibility checker.
"""

import logging
import os
from typing import Optional

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name
        level: Log level (defaults to LOG_LEVEL env var or INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Set log level
        log_level = level or os.getenv('LOG_LEVEL', 'INFO')
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger
