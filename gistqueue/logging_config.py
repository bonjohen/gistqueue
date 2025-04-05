"""
Logging configuration for GistQueue.

This module provides a centralized logging configuration for the entire application.
"""
import logging
import sys
from typing import Optional

# Default logging format
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Create a logger for the gistqueue package
logger = logging.getLogger('gistqueue')

def configure_logging(level: int = logging.INFO, 
                     format_str: Optional[str] = None,
                     log_file: Optional[str] = None) -> None:
    """
    Configure logging for the GistQueue application.
    
    Args:
        level (int): The logging level (default: logging.INFO)
        format_str (Optional[str]): The log format string (default: DEFAULT_FORMAT)
        log_file (Optional[str]): Path to a log file (default: None, logs to stderr only)
    """
    # Set the logging level
    logger.setLevel(level)
    
    # Use the default format if none is provided
    if format_str is None:
        format_str = DEFAULT_FORMAT
    
    # Create a formatter
    formatter = logging.Formatter(format_str)
    
    # Create a console handler and set its formatter
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    
    # Add the console handler to the logger
    logger.addHandler(console_handler)
    
    # If a log file is specified, add a file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

# Configure logging with default settings
configure_logging()
