"""
GistQueue - A message queue system using GitHub Gists.

This package provides a simple message queue system implemented using GitHub Gists
as the storage backend. It allows for creating, retrieving, and managing messages
in queues represented as Gist files.
"""

__version__ = '0.1.0'

# Import key modules for easier access
from gistqueue.auth import get_github_token, validate_token
from gistqueue.config import CONFIG
from gistqueue.github_client import GistClient
