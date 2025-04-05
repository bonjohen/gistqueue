"""
Concurrency and conflict handling module for GistQueue.

This module provides functionality for handling concurrent access to queues
and resolving conflicts that may arise when multiple processes access the same queue.
"""
import time
import json
import random
import hashlib
from typing import Optional, Dict, Any, Callable, TypeVar, List, Union
from github.Gist import Gist
from github import GithubException

from gistqueue.queue import QueueManager
from gistqueue.message import MessageManager, MessageStatus
from gistqueue.config import CONFIG

# Type variable for generic functions
T = TypeVar('T')

class ConflictError(Exception):
    """Exception raised when a conflict is detected during a queue operation."""
    pass

class ConcurrencyManager:
    """
    Manager for handling concurrent access to queues and resolving conflicts.
    """

    def __init__(self, queue_manager: Optional[QueueManager] = None,
                 message_manager: Optional[MessageManager] = None):
        """
        Initialize the ConcurrencyManager.

        Args:
            queue_manager (Optional[QueueManager]): A QueueManager instance. If None, a new one will be created.
            message_manager (Optional[MessageManager]): A MessageManager instance. If None, a new one will be created.

        Raises:
            RuntimeError: If queue_manager or message_manager initialization fails.
        """
        self.queue_manager = queue_manager or QueueManager()
        self.message_manager = message_manager or MessageManager(self.queue_manager)
        self.max_retries = CONFIG.get('CONCURRENCY_MAX_RETRIES', 3)
        self.retry_delay_base = CONFIG.get('CONCURRENCY_RETRY_DELAY_BASE', 1.0)
        self.retry_delay_max = CONFIG.get('CONCURRENCY_RETRY_DELAY_MAX', 5.0)
        self.jitter_factor = CONFIG.get('CONCURRENCY_JITTER_FACTOR', 0.1)

    def _calculate_etag(self, content: str) -> str:
        """
        Calculate an ETag for the content.

        Args:
            content (str): The content to calculate the ETag for.

        Returns:
            str: The calculated ETag.
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate the delay before retrying an operation.

        Uses exponential backoff with jitter to avoid thundering herd problem.

        Args:
            attempt (int): The current attempt number (0-based).

        Returns:
            float: The delay in seconds.
        """
        # Exponential backoff
        delay = min(self.retry_delay_base * (2 ** attempt), self.retry_delay_max)

        # Add jitter
        jitter = random.uniform(-self.jitter_factor * delay, self.jitter_factor * delay)
        delay += jitter

        return max(0.1, delay)  # Ensure minimum delay of 0.1 seconds

    def with_retry(self, operation: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute an operation with retry logic.

        Args:
            operation (Callable): The operation to execute.
            *args: Positional arguments to pass to the operation.
            **kwargs: Keyword arguments to pass to the operation.

        Returns:
            T: The result of the operation.

        Raises:
            ConflictError: If the operation fails after all retries.
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except (ConflictError, GithubException) as e:
                last_exception = e

                # If this is the last attempt, don't wait
                if attempt == self.max_retries - 1:
                    break

                # Calculate delay and wait
                delay = self._calculate_retry_delay(attempt)
                print(f"Retry attempt {attempt + 1}/{self.max_retries} after {delay:.2f} seconds...")
                time.sleep(delay)

        # If we get here, all retries failed
        raise ConflictError(f"Operation failed after {self.max_retries} attempts: {last_exception}")

    def atomic_update(self, queue: Union[str, Gist], update_func: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]],
                     queue_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Atomically update a queue by applying an update function.

        Args:
            queue (Union[str, Gist]): Either a queue name, a Gist ID, or a Gist object.
            update_func (Callable): A function that takes the current queue content and returns the updated content.
            queue_name (Optional[str]): The name of the queue. Only used if queue is a Gist object.

        Returns:
            List[Dict[str, Any]]: The updated queue content.

        Raises:
            ConflictError: If the update fails due to a conflict.
        """
        # Get the queue
        gist = None
        if isinstance(queue, str):
            # Check if the string is a Gist ID (alphanumeric)
            if queue.isalnum():
                gist = self.queue_manager.get_queue_by_id(queue)
            else:
                # Assume it's a queue name
                gist = self.queue_manager.get_queue(queue)
                queue_name = queue
        else:
            # Assume it's a Gist object
            gist = queue

        if not gist:
            raise ValueError("Queue not found.")

        # Get the queue filename
        filename = self.queue_manager._get_queue_filename(queue_name or self.queue_manager.default_queue)

        # Get the current content and calculate ETag
        current_content_str = self.queue_manager.client.get_gist_content(gist, filename)
        if current_content_str is None:
            raise ValueError("Failed to retrieve queue content.")

        current_etag = self._calculate_etag(current_content_str)

        # Parse the current content
        try:
            current_content = json.loads(current_content_str)
        except json.JSONDecodeError:
            raise ValueError("Failed to parse queue content as JSON.")

        # Apply the update function
        updated_content = update_func(current_content)

        # Convert the updated content to JSON
        updated_content_str = json.dumps(updated_content, indent=2)

        # Update the queue
        try:
            updated_gist = self.queue_manager.client.update_gist(gist, filename, updated_content_str)

            # Verify that the update was successful by checking the ETag
            new_content_str = self.queue_manager.client.get_gist_content(updated_gist, filename)
            if new_content_str is None:
                raise ConflictError("Failed to retrieve updated queue content.")

            new_etag = self._calculate_etag(new_content_str)

            # Calculate the expected ETag for the updated content
            expected_etag = self._calculate_etag(updated_content_str)

            # If the new ETag matches the expected ETag, the update was successful
            if new_etag == expected_etag:
                return updated_content
            else:
                # The content was modified by another process
                raise ConflictError("Queue was modified by another process during update.")
        except GithubException as e:
            raise ConflictError(f"Failed to update queue: {e}")

    def atomic_get_next_message(self, queue: Union[str, Gist], queue_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Atomically get the next pending message from a queue and mark it as in progress.

        Args:
            queue (Union[str, Gist]): Either a queue name, a Gist ID, or a Gist object.
            queue_name (Optional[str]): The name of the queue. Only used if queue is a Gist object.

        Returns:
            Optional[Dict[str, Any]]: The next message, or None if no pending messages are available.

        Raises:
            ConflictError: If the operation fails due to a conflict.
        """
        def update_func(content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Update function for atomic_update."""
            # Find the first pending message
            for i, message in enumerate(content):
                if message.get("status") == MessageStatus.PENDING:
                    # Update the message status
                    message["status"] = MessageStatus.IN_PROGRESS
                    message["status_datetime"] = self.message_manager._get_current_datetime()
                    message["process"] = self.message_manager._get_process_identifier()

                    # Return the updated content
                    return content

            # No pending messages found
            return content

        # Get the current queue content
        try:
            current_content = self.queue_manager.get_queue_content(queue, queue_name)
            if current_content is None:
                print("Failed to retrieve queue content.")
                return None

            # Check if there are any pending messages
            pending_messages = [msg for msg in current_content if msg.get("status") == MessageStatus.PENDING]
            if not pending_messages:
                print("No pending messages found.")
                return None

            # Update the queue atomically
            updated_content = self.with_retry(self.atomic_update, queue, update_func, queue_name)

            # Find the message that was updated
            for message in updated_content:
                if (message.get("status") == MessageStatus.IN_PROGRESS and
                    message.get("process") == self.message_manager._get_process_identifier()):
                    print(f"Message {message['id']} marked as in progress.")
                    return message

            # No message was updated
            print("No message was updated.")
            return None
        except (ValueError, ConflictError) as e:
            print(f"Error getting next message: {e}")
            return None

    def atomic_update_message(self, queue: Union[str, Gist], message_id: str, content: Optional[Any] = None,
                             status: Optional[str] = None, queue_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Atomically update a message in a queue.

        Args:
            queue (Union[str, Gist]): Either a queue name, a Gist ID, or a Gist object.
            message_id (str): The ID of the message to update.
            content (Optional[Any]): The new content of the message. If None, the content is not updated.
            status (Optional[str]): The new status of the message. If None, the status is not updated.
            queue_name (Optional[str]): The name of the queue. Only used if queue is a Gist object.

        Returns:
            Optional[Dict[str, Any]]: The updated message, or None if update fails.

        Raises:
            ConflictError: If the update fails due to a conflict.
        """
        def update_func(queue_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Update function for atomic_update."""
            # Find the message
            for i, message in enumerate(queue_content):
                if message.get("id") == message_id:
                    # Update the message
                    if content is not None:
                        message["content"] = content

                    if status is not None:
                        message["status"] = status
                        message["status_datetime"] = self.message_manager._get_current_datetime()

                    # Return the updated content
                    return queue_content

            # Message not found
            raise ValueError(f"Message {message_id} not found.")

        # Update the queue atomically
        try:
            updated_content = self.with_retry(self.atomic_update, queue, update_func, queue_name)

            # Find the updated message
            for message in updated_content:
                if message.get("id") == message_id:
                    print(f"Message {message_id} updated.")
                    return message

            # Message not found
            print(f"Message {message_id} not found.")
            return None
        except (ValueError, ConflictError) as e:
            print(f"Error updating message: {e}")
            return None
