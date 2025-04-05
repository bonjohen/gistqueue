"""
Main module for the GistQueue application.

This module provides the main entry point for the GistQueue application,
which implements a message queue system using GitHub Gists.
"""
import sys
from gistqueue.auth import get_github_client, validate_token, get_github_token
from gistqueue.config import CONFIG
from gistqueue.github_client import GistClient

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
            print("ERROR: Invalid GitHub token. Please check your GIST_TOKEN environment variable.", file=sys.stderr)
            return False

        print("Environment check passed. GitHub authentication successful.")
        return True
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
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
        print(f"ERROR: {e}", file=sys.stderr)
        return None

def main():
    """
    Main entry point for the application.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    print("Initializing GistQueue...")

    # Check environment configuration
    if not check_environment():
        return 1

    # Initialize GitHub client
    client = initialize_client()
    if not client:
        return 1

    print("GistQueue initialized successfully.")
    # Log only non-sensitive configuration parameters
    non_sensitive_config = {key: value for key, value in CONFIG.items() if key not in ["sensitive_key1", "sensitive_key2"]}
    print(f"Using configuration: {non_sensitive_config}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
