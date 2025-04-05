"""
GitHub API client module for GistQueue.

This module provides a wrapper around the GitHub API for Gist operations.
"""
from typing import Optional, Dict, List, Any, Union
from gistqueue.direct_api import GithubException, Gist

from gistqueue.auth import get_github_client
from gistqueue.config import CONFIG

class GistClient:
    """
    Client for interacting with GitHub Gists.
    """

    def __init__(self):
        """
        Initialize the GistClient.

        Raises:
            RuntimeError: If authentication fails.
        """
        self.github = get_github_client()
        if not self.github:
            raise RuntimeError("Failed to initialize GitHub client. Check your authentication.")

        self.retry_count = CONFIG['API_RETRY_COUNT']
        self.retry_delay = CONFIG['API_RETRY_DELAY']

    def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: The function to execute.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            Any: The result of the function.

        Raises:
            GithubException: If the function fails after all retries.
        """
        # Simply delegate to the DirectGitHubClient's _execute_with_retry method
        return self.github._execute_with_retry(func, *args, **kwargs)

    def get_gist_by_description(self, description: str) -> Optional[Gist]:
        """
        Find a Gist by its description.

        Args:
            description (str): The description to search for.

        Returns:
            Optional[Gist]: The Gist if found, None otherwise.
        """
        return self.github.get_gist_by_description(description)

    def get_gist_by_id(self, gist_id: str) -> Optional[Gist]:
        """
        Get a Gist by its ID.

        Args:
            gist_id (str): The ID of the Gist.

        Returns:
            Optional[Gist]: The Gist if found, None otherwise.
        """
        try:
            return self.github.get_gist_by_id(gist_id)
        except GithubException:
            return None

    def create_gist(self, description: str, filename: str, content: str, public: bool = False) -> Gist:
        """
        Create a new Gist.

        Args:
            description (str): The description of the Gist.
            filename (str): The name of the file in the Gist.
            content (str): The content of the file.
            public (bool, optional): Whether the Gist should be public. Defaults to False.

        Returns:
            Gist: The created Gist.

        Raises:
            RuntimeError: If the Gist creation fails or returns an unexpected response.
        """
        try:
            return self.github.create_gist(description, filename, content, public)
        except Exception as e:
            # Re-raise with more context
            raise RuntimeError(f"Failed to create gist: {e}") from e

    def update_gist(self, gist: Gist, filename: str, content: str) -> Gist:
        """
        Update a Gist's file content.

        Args:
            gist (Gist): The Gist to update.
            filename (str): The name of the file to update.
            content (str): The new content of the file.

        Returns:
            Gist: The updated Gist.
        """
        return self.github.update_gist(gist, filename, content)

    def get_gist_content(self, gist: Gist, filename: str) -> Optional[str]:
        """
        Get the content of a file in a Gist.

        Args:
            gist (Gist): The Gist containing the file.
            filename (str): The name of the file.

        Returns:
            Optional[str]: The content of the file, or None if the file doesn't exist.
        """
        return self.github.get_gist_content(gist, filename)

    def parse_json_content(self, content: str) -> Union[Dict[str, Any], List[Any], None]:
        """
        Parse JSON content from a Gist file.

        Args:
            content (str): The JSON content to parse.

        Returns:
            Union[Dict[str, Any], List[Any], None]: The parsed JSON data, or None if parsing fails.
        """
        try:
            return self.github.parse_json_content(content)
        except ValueError:
            return None
