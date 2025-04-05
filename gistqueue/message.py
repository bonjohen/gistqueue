"""
Message operations module for GistQueue.

This module provides functionality for creating, retrieving, updating, and deleting
messages in queues stored in GitHub Gists.
"""
import json
import uuid
import time
import datetime
import socket
import os
import logging
from typing import Optional, List, Dict, Any, Union
from gistqueue.direct_api import Gist

from gistqueue.queue import QueueManager
from gistqueue.config import CONFIG
from gistqueue.logging_config import logger

class MessageStatus:
    """Message status constants."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"

class MessageManager:
    """
    Manager for messages in queues stored in GitHub Gists.
    """

    def __init__(self, queue_manager: Optional[QueueManager] = None):
        """
        Initialize the MessageManager.

        Args:
            queue_manager (Optional[QueueManager]): A QueueManager instance. If None, a new one will be created.

        Raises:
            RuntimeError: If queue_manager initialization fails.
        """
        self.queue_manager = queue_manager or QueueManager()
        self.cleanup_threshold_days = CONFIG['CLEANUP_THRESHOLD_DAYS']

    def _generate_message_id(self) -> str:
        """
        Generate a unique message ID.

        Returns:
            str: A unique message ID.
        """
        return str(uuid.uuid4())

    def _get_process_identifier(self) -> str:
        """
        Get an identifier for the current process.

        Returns:
            str: An identifier for the current process.
        """
        hostname = socket.gethostname()
        pid = os.getpid()
        return f"{hostname}:{pid}"

    def _get_current_datetime(self) -> str:
        """
        Get the current datetime in ISO format.

        Returns:
            str: The current datetime in ISO format.
        """
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def create_message(self, queue: Union[str, Gist], content: Any, queue_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new message in a queue.

        Args:
            queue (Union[str, Gist]): Either a queue name, a Gist ID, or a Gist object.
            content (Any): The content of the message. Will be serialized to JSON.
            queue_name (Optional[str]): The name of the queue. Only used if queue is a Gist object.

        Returns:
            Optional[Dict[str, Any]]: The created message, or None if creation fails.
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
            logger.warning("Queue not found.")
            return None

        # Get the queue content
        queue_content = self.queue_manager.get_queue_content(gist, queue_name)
        if queue_content is None:
            logger.error("Failed to retrieve queue content.")
            return None

        # Create the message
        message = {
            "id": self._generate_message_id(),
            "content": content,
            "status": MessageStatus.PENDING,
            "status_datetime": self._get_current_datetime(),
            "process": None
        }

        # Add the message to the queue
        queue_content.append(message)

        # Update the queue
        filename = self.queue_manager._get_queue_filename(queue_name or self.queue_manager.default_queue)
        try:
            self.queue_manager.client.update_gist(gist, filename, json.dumps(queue_content, indent=2))
            logger.info(f"Message created with ID: {message['id']}")
            return message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            return None

    def list_messages(self, queue: Union[str, Gist], status: Optional[str] = None, queue_name: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        List messages in a queue, optionally filtered by status.

        Args:
            queue (Union[str, Gist]): Either a queue name, a Gist ID, or a Gist object.
            status (Optional[str]): Filter messages by status. If None, all messages are returned.
            queue_name (Optional[str]): The name of the queue. Only used if queue is a Gist object.

        Returns:
            Optional[List[Dict[str, Any]]]: The list of messages, or None if retrieval fails.
        """
        # Get the queue content
        queue_content = self.queue_manager.get_queue_content(queue, queue_name)
        if queue_content is None:
            logger.error("Failed to retrieve queue content.")
            return None

        # Filter by status if specified
        if status:
            return [msg for msg in queue_content if msg.get("status") == status]

        return queue_content

    def get_next_message(self, queue: Union[str, Gist], queue_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the next pending message from a queue and mark it as in progress.

        Args:
            queue (Union[str, Gist]): Either a queue name, a Gist ID, or a Gist object.
            queue_name (Optional[str]): The name of the queue. Only used if queue is a Gist object.

        Returns:
            Optional[Dict[str, Any]]: The next message, or None if no pending messages are available.
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
            logger.warning("Queue not found.")
            return None

        # Get the queue content
        queue_content = self.queue_manager.get_queue_content(gist, queue_name)
        if queue_content is None:
            logger.error("Failed to retrieve queue content.")
            return None

        # Find the first pending message
        for i, message in enumerate(queue_content):
            if message.get("status") == MessageStatus.PENDING:
                # Update the message status
                message["status"] = MessageStatus.IN_PROGRESS
                message["status_datetime"] = self._get_current_datetime()
                message["process"] = self._get_process_identifier()

                # Update the queue
                filename = self.queue_manager._get_queue_filename(queue_name or self.queue_manager.default_queue)
                try:
                    self.queue_manager.client.update_gist(gist, filename, json.dumps(queue_content, indent=2))
                    logger.info(f"Message {message['id']} marked as in progress.")
                    return message
                except Exception as e:
                    logger.error(f"Error updating message status: {e}")
                    return None

        logger.info("No pending messages found.")
        return None

    def update_message(self, queue: Union[str, Gist], message_id: str, content: Optional[Any] = None,
                      status: Optional[str] = None, queue_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Update a message in a queue.

        Args:
            queue (Union[str, Gist]): Either a queue name, a Gist ID, or a Gist object.
            message_id (str): The ID of the message to update.
            content (Optional[Any]): The new content of the message. If None, the content is not updated.
            status (Optional[str]): The new status of the message. If None, the status is not updated.
            queue_name (Optional[str]): The name of the queue. Only used if queue is a Gist object.

        Returns:
            Optional[Dict[str, Any]]: The updated message, or None if update fails.
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
            logger.warning("Queue not found.")
            return None

        # Get the queue content
        queue_content = self.queue_manager.get_queue_content(gist, queue_name)
        if queue_content is None:
            logger.error("Failed to retrieve queue content.")
            return None

        # Find the message
        for i, message in enumerate(queue_content):
            if message.get("id") == message_id:
                # Update the message
                if content is not None:
                    message["content"] = content

                if status is not None:
                    message["status"] = status
                    message["status_datetime"] = self._get_current_datetime()

                # Update the queue
                filename = self.queue_manager._get_queue_filename(queue_name or self.queue_manager.default_queue)
                try:
                    self.queue_manager.client.update_gist(gist, filename, json.dumps(queue_content, indent=2))
                    logger.info(f"Message {message_id} updated.")
                    return message
                except Exception as e:
                    logger.error(f"Error updating message: {e}")
                    return None

        logger.warning(f"Message {message_id} not found.")
        return None

    def delete_completed_messages(self, queue: Union[str, Gist], queue_name: Optional[str] = None) -> Optional[int]:
        """
        Delete completed messages that are older than the cleanup threshold.

        Args:
            queue (Union[str, Gist]): Either a queue name, a Gist ID, or a Gist object.
            queue_name (Optional[str]): The name of the queue. Only used if queue is a Gist object.

        Returns:
            Optional[int]: The number of deleted messages, or None if deletion fails.
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
            logger.warning("Queue not found.")
            return None

        # Get the queue content
        queue_content = self.queue_manager.get_queue_content(gist, queue_name)
        if queue_content is None:
            print("Failed to retrieve queue content.")
            return None

        # Calculate the threshold datetime
        threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=self.cleanup_threshold_days)
        threshold_str = threshold.isoformat()

        # Filter out completed messages older than the threshold
        original_count = len(queue_content)
        queue_content = [
            msg for msg in queue_content
            if not (
                msg.get("status") == MessageStatus.COMPLETE and
                msg.get("status_datetime", "") < threshold_str
            )
        ]
        deleted_count = original_count - len(queue_content)

        if deleted_count > 0:
            # Update the queue
            filename = self.queue_manager._get_queue_filename(queue_name or self.queue_manager.default_queue)
            try:
                self.queue_manager.client.update_gist(gist, filename, json.dumps(queue_content, indent=2))
                logger.info(f"Deleted {deleted_count} completed messages.")
                return deleted_count
            except Exception as e:
                logger.error(f"Error deleting messages: {e}")
                return None

        logger.info("No messages to delete.")
        return 0
