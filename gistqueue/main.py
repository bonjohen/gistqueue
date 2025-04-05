"""
Main module for the GistQueue application.

This module provides the main entry point for the GistQueue application,
which implements a message queue system using GitHub Gists.
"""
import sys
import logging
from gistqueue.auth import get_github_client, validate_token, get_github_token
from gistqueue.config import CONFIG
from gistqueue.github_client import GistClient
from gistqueue.queue import QueueManager
from gistqueue.message import MessageManager
from gistqueue.concurrency import ConcurrencyManager
from gistqueue.garbage_collection import GarbageCollector
from gistqueue.logging_config import logger

def check_environment():
    """
    Check that the environment is properly configured.

    Returns:
        bool: True if the environment is properly configured, False otherwise.
    """
    try:
        # Check for GitHub token
        token = get_github_token()
        if not validate_token(token):
            logger.error("Invalid GitHub token. Please check your GIST_TOKEN environment variable.")
            return False

        logger.info("Environment check passed. GitHub authentication successful.")
        return True
    except ValueError as e:
        logger.error(f"{e}")
        return False

def initialize_client():
    """
    Initialize the GitHub Gist client.

    Returns:
        GistClient: An initialized GistClient instance, or None if initialization fails.
    """
    try:
        return GistClient()
    except RuntimeError as e:
        logger.error(f"{e}")
        return None

def initialize_garbage_collector(client):
    """
    Initialize the garbage collector.

    Args:
        client (GistClient): An initialized GistClient instance.

    Returns:
        GarbageCollector: An initialized GarbageCollector instance, or None if initialization fails.
    """
    try:
        queue_manager = QueueManager(client)
        message_manager = MessageManager(queue_manager)
        concurrency_manager = ConcurrencyManager(queue_manager, message_manager)
        return GarbageCollector(queue_manager, message_manager, concurrency_manager)
    except Exception as e:
        logger.error(f"Failed to initialize garbage collector: {e}")
        return None

def main():
    """
    Main entry point for the application.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    logger.info("Initializing GistQueue...")

    # Check environment configuration
    if not check_environment():
        return 1

    # Initialize GitHub client
    client = initialize_client()
    if not client:
        return 1

    # Initialize garbage collector
    garbage_collector = initialize_garbage_collector(client)
    if not garbage_collector:
        logger.warning("Garbage collector initialization failed. Automatic cleanup will not be available.")
    elif CONFIG.get('CLEANUP_AUTO_START', False):
        logger.info("Starting automatic garbage collection...")
        if garbage_collector.start_cleanup_thread():
            logger.info(f"Garbage collection thread started. Cleanup interval: {CONFIG['CLEANUP_INTERVAL_SECONDS']} seconds")
        else:
            logger.warning("Failed to start garbage collection thread.")

    logger.info("GistQueue initialized successfully.")
    # Log only non-sensitive configuration parameters
    non_sensitive_config = {key: value for key, value in CONFIG.items() if key not in ["sensitive_key1", "sensitive_key2"]}
    logger.info(f"Using configuration: {non_sensitive_config}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
