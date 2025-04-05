"""
Queue management module for GistQueue.

This module provides functionality for creating and managing message queues
using GitHub Gists as the storage backend.
"""
import json
import time
from typing import Optional, List, Dict, Any, Union
from github.Gist import Gist

from gistqueue.github_client import GistClient
from gistqueue.config import CONFIG

class QueueManager:
    """
    Manager for message queues stored in GitHub Gists.
    """
    
    def __init__(self, client: Optional[GistClient] = None):
        """
        Initialize the QueueManager.
        
        Args:
            client (Optional[GistClient]): A GistClient instance. If None, a new one will be created.
            
        Raises:
            RuntimeError: If client initialization fails.
        """
        self.client = client or GistClient()
        self.prefix = CONFIG['GIST_DESCRIPTION_PREFIX']
        self.default_queue = CONFIG['DEFAULT_QUEUE_NAME']
        self.file_extension = CONFIG['DEFAULT_FILE_EXTENSION']
    
    def _get_queue_description(self, queue_name: str) -> str:
        """
        Get the description for a queue.
        
        Args:
            queue_name (str): The name of the queue.
            
        Returns:
            str: The queue description.
        """
        return f"{self.prefix} {queue_name}"
    
    def _get_queue_filename(self, queue_name: str) -> str:
        """
        Get the filename for a queue.
        
        Args:
            queue_name (str): The name of the queue.
            
        Returns:
            str: The queue filename.
        """
        return f"{queue_name}_queue.{self.file_extension}"
    
    def create_queue(self, queue_name: Optional[str] = None, public: bool = False) -> Optional[Gist]:
        """
        Create a new message queue.
        
        Args:
            queue_name (Optional[str]): The name of the queue. If None, the default queue name will be used.
            public (bool): Whether the queue should be public. Defaults to False.
            
        Returns:
            Optional[Gist]: The created Gist, or None if creation fails.
        """
        queue_name = queue_name or self.default_queue
        description = self._get_queue_description(queue_name)
        filename = self._get_queue_filename(queue_name)
        
        # Check if the queue already exists
        existing_queue = self.get_queue(queue_name)
        if existing_queue:
            print(f"Queue '{queue_name}' already exists.")
            return existing_queue
        
        # Create a new queue with an empty array
        try:
            gist = self.client.create_gist(
                description=description,
                filename=filename,
                content="[]",
                public=public
            )
            print(f"Queue '{queue_name}' created successfully.")
            return gist
        except Exception as e:
            print(f"Error creating queue '{queue_name}': {e}")
            return None
    
    def get_queue(self, queue_name: Optional[str] = None) -> Optional[Gist]:
        """
        Get a queue by name.
        
        Args:
            queue_name (Optional[str]): The name of the queue. If None, the default queue name will be used.
            
        Returns:
            Optional[Gist]: The queue Gist, or None if not found.
        """
        queue_name = queue_name or self.default_queue
        description = self._get_queue_description(queue_name)
        
        try:
            return self.client.get_gist_by_description(description)
        except Exception as e:
            print(f"Error retrieving queue '{queue_name}': {e}")
            return None
    
    def get_queue_by_id(self, gist_id: str) -> Optional[Gist]:
        """
        Get a queue by its Gist ID.
        
        Args:
            gist_id (str): The ID of the Gist.
            
        Returns:
            Optional[Gist]: The queue Gist, or None if not found.
        """
        try:
            return self.client.get_gist_by_id(gist_id)
        except Exception as e:
            print(f"Error retrieving queue with ID '{gist_id}': {e}")
            return None
    
    def list_queues(self) -> List[Dict[str, str]]:
        """
        List all available queues.
        
        Returns:
            List[Dict[str, str]]: A list of dictionaries containing queue information.
        """
        user = self.client.github.get_user()
        gists = user.get_gists()
        
        queues = []
        for gist in gists:
            if gist.description and gist.description.startswith(self.prefix):
                queue_name = gist.description[len(self.prefix):].strip()
                queues.append({
                    'id': gist.id,
                    'name': queue_name,
                    'description': gist.description,
                    'url': gist.html_url,
                    'created_at': gist.created_at.isoformat(),
                    'updated_at': gist.updated_at.isoformat()
                })
        
        return queues
    
    def get_queue_content(self, queue: Union[str, Gist], queue_name: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Get the content of a queue.
        
        Args:
            queue (Union[str, Gist]): Either a queue name, a Gist ID, or a Gist object.
            queue_name (Optional[str]): The name of the queue. Only used if queue is a Gist object.
            
        Returns:
            Optional[List[Dict[str, Any]]]: The queue content, or None if retrieval fails.
        """
        gist = None
        filename = None
        
        if isinstance(queue, str):
            # Check if the string is a Gist ID (alphanumeric)
            if queue.isalnum():
                gist = self.get_queue_by_id(queue)
                # Try to find the queue filename
                if gist:
                    for file in gist.files.values():
                        if file.filename.endswith(f"_queue.{self.file_extension}"):
                            filename = file.filename
                            break
            else:
                # Assume it's a queue name
                gist = self.get_queue(queue)
                filename = self._get_queue_filename(queue)
        else:
            # Assume it's a Gist object
            gist = queue
            queue_name = queue_name or self.default_queue
            filename = self._get_queue_filename(queue_name)
        
        if not gist:
            print("Queue not found.")
            return None
        
        if not filename or filename not in gist.files:
            print(f"Queue file not found in Gist.")
            return None
        
        content = self.client.get_gist_content(gist, filename)
        if not content:
            print("Failed to retrieve queue content.")
            return None
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print("Failed to parse queue content as JSON.")
            return None
