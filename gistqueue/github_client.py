"""
GitHub API client module for GistQueue.

This module provides a wrapper around the GitHub API for Gist operations.
"""
import time
import json
from typing import Optional, Dict, List, Any, Union
from github import Github, GithubException
from github.Gist import Gist

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
        last_exception = None
        
        for attempt in range(self.retry_count):
            try:
                return func(*args, **kwargs)
            except GithubException as e:
                last_exception = e
                
                # If rate limited, wait and retry
                if e.status == 403 and 'rate limit' in str(e).lower():
                    reset_time = int(e.headers.get('X-RateLimit-Reset', 0))
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
            raise last_exception
        
        # This should never happen, but just in case
        raise RuntimeError("All retries failed with unknown error")
    
    def get_gist_by_description(self, description: str) -> Optional[Gist]:
        """
        Find a Gist by its description.
        
        Args:
            description (str): The description to search for.
            
        Returns:
            Optional[Gist]: The Gist if found, None otherwise.
        """
        user = self.github.get_user()
        gists = self._execute_with_retry(user.get_gists)
        
        for gist in gists:
            if gist.description == description:
                return gist
        
        return None
    
    def get_gist_by_id(self, gist_id: str) -> Optional[Gist]:
        """
        Get a Gist by its ID.
        
        Args:
            gist_id (str): The ID of the Gist.
            
        Returns:
            Optional[Gist]: The Gist if found, None otherwise.
        """
        try:
            return self._execute_with_retry(self.github.get_gist, gist_id)
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
        """
        files = {filename: {"content": content}}
        return self._execute_with_retry(
            self.github.get_user().create_gist,
            public=public,
            description=description,
            files=files
        )
    
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
        files = {filename: {"content": content}}
        return self._execute_with_retry(gist.edit, files=files)
    
    def get_gist_content(self, gist: Gist, filename: str) -> Optional[str]:
        """
        Get the content of a file in a Gist.
        
        Args:
            gist (Gist): The Gist containing the file.
            filename (str): The name of the file.
            
        Returns:
            Optional[str]: The content of the file, or None if the file doesn't exist.
        """
        if filename in gist.files:
            return gist.files[filename].content
        return None
    
    def parse_json_content(self, content: str) -> Union[Dict[str, Any], List[Any], None]:
        """
        Parse JSON content from a Gist file.
        
        Args:
            content (str): The JSON content to parse.
            
        Returns:
            Union[Dict[str, Any], List[Any], None]: The parsed JSON data, or None if parsing fails.
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
