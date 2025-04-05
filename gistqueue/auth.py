"""
Authentication module for GistQueue.

This module handles GitHub authentication and token management.
"""
import os
import sys
from typing import Optional
from dotenv import load_dotenv
from github import Github, GithubException

# Load environment variables from .env file if it exists
load_dotenv()

def get_github_token() -> str:
    """
    Get the GitHub token from environment variables.
    
    Returns:
        str: The GitHub token.
        
    Raises:
        ValueError: If the token is not found or invalid.
    """
    token = os.environ.get('GIST_TOKEN')
    
    if not token:
        raise ValueError(
            "GitHub token not found. Please set the GIST_TOKEN environment variable."
        )
    
    return token

def validate_token(token: str) -> bool:
    """
    Validate the GitHub token by making a test API call.
    
    Args:
        token (str): The GitHub token to validate.
        
    Returns:
        bool: True if the token is valid, False otherwise.
    """
    try:
        # Create a GitHub instance with the token
        github = Github(token)
        # Make a simple API call to validate the token
        user = github.get_user()
        # If we get here, the token is valid
        return True
    except GithubException as e:
        print(f"Error validating GitHub token: {e}", file=sys.stderr)
        return False

def get_github_client() -> Optional[Github]:
    """
    Get an authenticated GitHub client.
    
    Returns:
        Github: An authenticated GitHub client instance.
        None: If authentication fails.
    """
    try:
        token = get_github_token()
        if validate_token(token):
            return Github(token)
        return None
    except ValueError as e:
        print(f"Authentication error: {e}", file=sys.stderr)
        return None
