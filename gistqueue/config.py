"""
Configuration module for GistQueue.

This module handles application configuration and settings.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Default configuration values
DEFAULT_CONFIG = {
    # Gist and queue settings
    'GIST_DESCRIPTION_PREFIX': 'Queue:',
    'DEFAULT_QUEUE_NAME': 'default',
    'DEFAULT_FILE_EXTENSION': 'json',

    # API settings
    'API_RETRY_COUNT': 3,
    'API_RETRY_DELAY': 1,  # seconds

    # Cleanup settings
    'CLEANUP_THRESHOLD_DAYS': 1,  # days
    'CLEANUP_INTERVAL_SECONDS': 3600,  # seconds (1 hour)
    'CLEANUP_AUTO_START': False,  # Whether to automatically start the cleanup thread

    # Concurrency settings
    'CONCURRENCY_MAX_RETRIES': 3,
    'CONCURRENCY_RETRY_DELAY_BASE': 1.0,  # seconds
    'CONCURRENCY_RETRY_DELAY_MAX': 5.0,  # seconds
    'CONCURRENCY_JITTER_FACTOR': 0.1,  # 10% jitter
}

def get_config() -> Dict[str, Any]:
    """
    Get the application configuration.

    This function loads configuration values from environment variables,
    falling back to default values if not specified.

    Returns:
        Dict[str, Any]: The application configuration.
    """
    config = DEFAULT_CONFIG.copy()

    # Override defaults with environment variables if they exist
    for key in config:
        env_value = os.environ.get(key)
        if env_value is not None:
            # Convert numeric values
            if isinstance(config[key], int):
                config[key] = int(env_value)
            elif isinstance(config[key], float):
                config[key] = float(env_value)
            else:
                config[key] = env_value

    return config

# Export the configuration
CONFIG = get_config()
