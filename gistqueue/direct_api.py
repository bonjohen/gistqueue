"""
Direct GitHub API client for GistQueue.

This module provides direct access to the GitHub API without relying on external libraries.
It implements all the GitHub API functionality needed for GistQueue.
"""
import requests
import json
import time
import datetime
import logging
from typing import Optional, Dict, Any, List, Union, Callable, TypeVar
from gistqueue.logging_config import logger

# Type variable for generic functions
T = TypeVar('T')

class GithubException(Exception):
    """
    Exception raised when a GitHub API request fails.
    """
    def __init__(self, status: int, data: Dict[str, Any], headers: Dict[str, str] = None):
        self.status = status
        self.data = data
        self.headers = headers or {}
        message = f"{status} {data}"
        super().__init__(message)

class Gist:
    """
    Class representing a GitHub Gist.
    """
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a Gist object from API response data.

        Args:
            data (Dict[str, Any]): The Gist data from the GitHub API.
        """
        self.id = data.get('id', '')
        self.description = data.get('description', '')
        self.html_url = data.get('html_url', '')
        self.created_at = datetime.datetime.fromisoformat(data.get('created_at', '').replace('Z', '+00:00'))
        self.updated_at = datetime.datetime.fromisoformat(data.get('updated_at', '').replace('Z', '+00:00'))
        self.files = {}

        # Process files
        for filename, file_data in data.get('files', {}).items():
            self.files[filename] = GistFile(filename, file_data)

class GistFile:
    """
    Class representing a file in a GitHub Gist.
    """
    def __init__(self, filename: str, data: Dict[str, Any]):
        """
        Initialize a GistFile object.

        Args:
            filename (str): The name of the file.
            data (Dict[str, Any]): The file data from the GitHub API.
        """
        self.filename = filename
        self.content = data.get('content', '')
        self.raw_url = data.get('raw_url', '')
        self.size = data.get('size', 0)

class User:
    """
    Class representing a GitHub user.
    """
    def __init__(self, client: 'DirectGitHubClient', data: Dict[str, Any]):
        """
        Initialize a User object.

        Args:
            client (DirectGitHubClient): The GitHub client.
            data (Dict[str, Any]): The user data from the GitHub API.
        """
        self.client = client
        self.login = data.get('login', '')
        self.id = data.get('id', 0)
        self.name = data.get('name', '')
        self.email = data.get('email', '')
        self.avatar_url = data.get('avatar_url', '')
        self.html_url = data.get('html_url', '')

    def get_gists(self) -> List[Gist]:
        """
        Get all gists for this user.

        Returns:
            List[Gist]: A list of Gist objects.
        """
        return self.client.get_gists()

    def create_gist(self, public: bool, description: str, files: Dict[str, Dict[str, str]]) -> Gist:
        """
        Create a new Gist.

        Args:
            public (bool): Whether the Gist should be public.
            description (str): The description of the Gist.
            files (Dict[str, Dict[str, str]]): The files to include in the Gist.

        Returns:
            Gist: The created Gist.
        """
        return self.client.create_gist(description, list(files.keys())[0], list(files.values())[0]['content'], public)

class DirectGitHubClient:
    """
    Direct GitHub API client that uses requests to interact with the GitHub API.
    """

    def __init__(self, token: str):
        """
        Initialize the DirectGitHubClient.

        Args:
            token (str): The GitHub token to use for authentication.
        """
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.retry_count = 3
        self.retry_delay = 1

    def _execute_with_retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function with retry logic.

        Args:
            func (Callable): The function to execute.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            T: The result of the function.

        Raises:
            GithubException: If the function fails after all retries.
        """
        last_exception = None

        for attempt in range(self.retry_count):
            try:
                return func(*args, **kwargs)
            except requests.RequestException as e:
                last_exception = e

                # If rate limited, wait and retry
                if e.response and e.response.status_code == 403 and 'rate limit' in str(e).lower():
                    headers = e.response.headers
                    reset_time = int(headers.get('X-RateLimit-Reset', 0))
                    if reset_time > 0:
                        wait_time = max(reset_time - time.time(), 0) + 1
                        print(f"Rate limited. Waiting {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
                    else:
                        time.sleep(self.retry_delay * (attempt + 1))
                else:
                    # For other errors, use exponential backoff
                    time.sleep(self.retry_delay * (attempt + 1))

        # If we get here, all retries failed
        if last_exception:
            if hasattr(last_exception, 'response'):
                response = last_exception.response
                raise GithubException(
                    status=response.status_code,
                    data=response.json() if response.content else {},
                    headers=dict(response.headers)
                )
            else:
                raise GithubException(status=500, data={"message": str(last_exception)})

    def get_user(self) -> User:
        """
        Get the authenticated user.

        Returns:
            User: The authenticated user.

        Raises:
            GithubException: If the request fails.
        """
        def _get_user():
            url = f"{self.base_url}/user"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        data = self._execute_with_retry(_get_user)
        return User(self, data)

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
            GithubException: If the request fails.
        """
        # First, check if a gist with this description already exists
        existing_gists = self.get_gists()
        for gist in existing_gists:
            if gist.description == description:
                logger.info(f"Found existing gist with description: {description}")
                return gist

        # If no existing gist is found, create a new one
        def _create_gist():
            url = f"{self.base_url}/gists"
            data = {
                "description": description,
                "public": public,
                "files": {
                    filename: {
                        "content": content
                    }
                }
            }
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()

        data = self._execute_with_retry(_create_gist)
        return Gist(data)

    def get_gists(self) -> List[Gist]:
        """
        Get all gists for the authenticated user.

        Returns:
            List[Gist]: A list of Gist objects.

        Raises:
            GithubException: If the request fails.
        """
        def _get_gists():
            url = f"{self.base_url}/gists"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        data = self._execute_with_retry(_get_gists)
        return [Gist(item) for item in data]

    def get_gist_by_id(self, gist_id: str) -> Gist:
        """
        Get a gist by its ID.

        Args:
            gist_id (str): The ID of the gist.

        Returns:
            Gist: The gist.

        Raises:
            GithubException: If the request fails.
        """
        def _get_gist_by_id():
            url = f"{self.base_url}/gists/{gist_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

        data = self._execute_with_retry(_get_gist_by_id)
        return Gist(data)

    def get_gist_by_description(self, description: str) -> Optional[Gist]:
        """
        Get a gist by its description.

        Args:
            description (str): The description of the gist.

        Returns:
            Optional[Gist]: The gist, or None if not found.
        """
        gists = self.get_gists()
        for gist in gists:
            if gist.description == description:
                return gist
        return None

    def update_gist(self, gist: Gist, filename: str, content: str) -> Gist:
        """
        Update a gist.

        Args:
            gist (Gist): The gist to update.
            filename (str): The name of the file to update.
            content (str): The new content of the file.

        Returns:
            Gist: The updated gist.

        Raises:
            GithubException: If the request fails.
        """
        def _update_gist():
            url = f"{self.base_url}/gists/{gist.id}"
            data = {
                "files": {
                    filename: {
                        "content": content
                    }
                }
            }
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()

        data = self._execute_with_retry(_update_gist)
        return Gist(data)

    def get_gist_content(self, gist: Gist, filename: str) -> Optional[str]:
        """
        Get the content of a file in a gist.

        Args:
            gist (Gist): The gist.
            filename (str): The name of the file.

        Returns:
            Optional[str]: The content of the file, or None if the file is not found.
        """
        if filename in gist.files:
            # First try to get the content from the gist object
            content = gist.files[filename].content
            if content is not None:
                return content

            # If that fails, try to fetch the raw content from the raw_url
            raw_url = gist.files[filename].raw_url
            if raw_url:
                try:
                    logger.debug(f"Fetching raw content from {raw_url}")
                    response = requests.get(raw_url, headers=self.headers)
                    response.raise_for_status()
                    return response.text
                except Exception as e:
                    logger.error(f"Failed to fetch raw content: {e}")
        return None

    def parse_json_content(self, content: str) -> Any:
        """
        Parse JSON content.

        Args:
            content (str): The JSON content to parse.

        Returns:
            Any: The parsed JSON data.

        Raises:
            ValueError: If the content is not valid JSON.
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content: {e}")
