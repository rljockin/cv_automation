#!/usr/bin/env python3
"""
Centralized Logging Configuration
Provides consistent logging across all CV Automation components
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

def setup_logger(name: str, log_level: str = "INFO", log_to_file: bool = True) -> logging.Logger:
    """
    Setup centralized logger with file and console handlers
    
    Args:
        name: Logger name (usually __name__ from calling module)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file (default: True)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> from src.core.logger import setup_logger
        >>> logger = setup_logger(__name__)
        >>> logger.info("Processing started")
        >>> logger.error("Error occurred", exc_info=True)
    """
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Only configure if not already configured (avoid duplicate handlers)
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.propagate = False  # Don't propagate to root logger
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Console formatter (simpler for readability)
    console_formatter = logging.Formatter(
        '[%(levelname)s] [%(name)s] %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file:
        try:
            # Create logs directory
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Create log file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"cv_automation_{timestamp}.log"
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # File gets all messages
            
            # File formatter (detailed with timestamps and line numbers)
            file_formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)-8s] [%(name)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            # If file logging fails, just use console
            logger.warning(f"Failed to setup file logging: {e}")
    
    return logger


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    error: Exception,
    context: Optional[dict] = None
):
    """
    Log an error with full context and stack trace
    
    Args:
        logger: Logger instance
        message: Error message
        error: Exception object
        context: Additional context (dict of key-value pairs)
        
    Example:
        >>> log_error_with_context(
        ...     logger,
        ...     "Failed to process CV",
        ...     exception,
        ...     {'file': cv_path, 'attempt': 1}
        ... )
    """
    error_msg = f"{message}: {str(error)}"
    
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        error_msg = f"{error_msg} | Context: {context_str}"
    
    logger.error(error_msg, exc_info=True)


# Error categories for consistent error handling
ERROR_CATEGORIES = {
    'extraction_failed': 'Failed to extract text from file',
    'parsing_failed': 'Failed to parse CV structure',
    'generation_failed': 'Failed to generate resume',
    'api_error': 'OpenAI API error',
    'file_not_found': 'Input file not found',
    'validation_failed': 'Data validation failed',
    'ocr_failed': 'OCR processing failed',
    'conversion_failed': 'File format conversion failed',
    'database_error': 'Database operation failed',
    'permission_error': 'Permission denied accessing file',
}


def get_error_category(exception: Exception) -> str:
    """
    Categorize exception type for better error tracking
    
    Args:
        exception: Exception object
        
    Returns:
        Error category string
    """
    exception_type = type(exception).__name__
    
    # Map common exceptions to categories
    if 'FileNotFound' in exception_type or 'NotFoundError' in exception_type:
        return 'file_not_found'
    elif 'Permission' in exception_type:
        return 'permission_error'
    elif 'API' in exception_type or 'OpenAI' in exception_type:
        return 'api_error'
    elif 'Validation' in exception_type:
        return 'validation_failed'
    elif 'OCR' in exception_type:
        return 'ocr_failed'
    elif 'Database' in exception_type or 'SQL' in exception_type:
        return 'database_error'
    else:
        return 'unknown_error'


__all__ = [
    'setup_logger',
    'log_error_with_context',
    'ERROR_CATEGORIES',
    'get_error_category'
]

