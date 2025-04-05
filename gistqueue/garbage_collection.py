"""
Garbage collection module for GistQueue.

This module provides functionality for cleaning up completed messages
that are older than a specified threshold.
"""
import time
import datetime
import logging
import threading
from typing import Optional, List, Dict, Any, Set

from gistqueue.queue import QueueManager
from gistqueue.message import MessageManager, MessageStatus
from gistqueue.concurrency import ConcurrencyManager
from gistqueue.config import CONFIG

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gistqueue.garbage_collection')

class GarbageCollector:
    """
    Garbage collector for cleaning up completed messages.
    """
    
    def __init__(self, queue_manager: Optional[QueueManager] = None,
                 message_manager: Optional[MessageManager] = None,
                 concurrency_manager: Optional[ConcurrencyManager] = None):
        """
        Initialize the GarbageCollector.
        
        Args:
            queue_manager (Optional[QueueManager]): A QueueManager instance. If None, a new one will be created.
            message_manager (Optional[MessageManager]): A MessageManager instance. If None, a new one will be created.
            concurrency_manager (Optional[ConcurrencyManager]): A ConcurrencyManager instance. If None, a new one will be created.
            
        Raises:
            RuntimeError: If initialization fails.
        """
        self.queue_manager = queue_manager or QueueManager()
        self.message_manager = message_manager or MessageManager(self.queue_manager)
        self.concurrency_manager = concurrency_manager or ConcurrencyManager(self.queue_manager, self.message_manager)
        self.cleanup_threshold_days = CONFIG.get('CLEANUP_THRESHOLD_DAYS', 1)
        self.cleanup_interval_seconds = CONFIG.get('CLEANUP_INTERVAL_SECONDS', 3600)  # Default: 1 hour
        self.cleanup_thread = None
        self.stop_event = threading.Event()
    
    def cleanup_queue(self, queue_name: str) -> int:
        """
        Clean up completed messages in a queue that are older than the threshold.
        
        Args:
            queue_name (str): The name of the queue to clean up.
            
        Returns:
            int: The number of messages deleted, or -1 if cleanup fails.
        """
        try:
            logger.info(f"Cleaning up queue: {queue_name}")
            deleted_count = self.message_manager.delete_completed_messages(queue_name)
            if deleted_count is not None:
                logger.info(f"Deleted {deleted_count} messages from queue: {queue_name}")
                return deleted_count
            else:
                logger.error(f"Failed to clean up queue: {queue_name}")
                return -1
        except Exception as e:
            logger.error(f"Error cleaning up queue {queue_name}: {e}")
            return -1
    
    def cleanup_all_queues(self) -> Dict[str, int]:
        """
        Clean up completed messages in all queues.
        
        Returns:
            Dict[str, int]: A dictionary mapping queue names to the number of messages deleted.
        """
        results = {}
        try:
            queues = self.queue_manager.list_queues()
            logger.info(f"Found {len(queues)} queues to clean up")
            
            for queue in queues:
                queue_name = queue.get('name')
                deleted_count = self.cleanup_queue(queue_name)
                results[queue_name] = deleted_count
            
            return results
        except Exception as e:
            logger.error(f"Error cleaning up all queues: {e}")
            return results
    
    def _cleanup_worker(self):
        """
        Worker function for the cleanup thread.
        """
        logger.info("Starting cleanup worker thread")
        
        while not self.stop_event.is_set():
            try:
                # Clean up all queues
                self.cleanup_all_queues()
                
                # Sleep until the next cleanup interval or until stopped
                logger.info(f"Sleeping for {self.cleanup_interval_seconds} seconds until next cleanup")
                self.stop_event.wait(self.cleanup_interval_seconds)
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                # Sleep for a short time to avoid tight loops in case of persistent errors
                time.sleep(10)
        
        logger.info("Cleanup worker thread stopped")
    
    def start_cleanup_thread(self):
        """
        Start the cleanup thread.
        
        Returns:
            bool: True if the thread was started, False otherwise.
        """
        if self.cleanup_thread is not None and self.cleanup_thread.is_alive():
            logger.warning("Cleanup thread is already running")
            return False
        
        self.stop_event.clear()
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        logger.info("Cleanup thread started")
        return True
    
    def stop_cleanup_thread(self, timeout: float = 5.0):
        """
        Stop the cleanup thread.
        
        Args:
            timeout (float): Maximum time to wait for the thread to stop, in seconds.
            
        Returns:
            bool: True if the thread was stopped, False otherwise.
        """
        if self.cleanup_thread is None or not self.cleanup_thread.is_alive():
            logger.warning("Cleanup thread is not running")
            return False
        
        logger.info("Stopping cleanup thread")
        self.stop_event.set()
        self.cleanup_thread.join(timeout)
        
        if self.cleanup_thread.is_alive():
            logger.warning(f"Cleanup thread did not stop within {timeout} seconds")
            return False
        
        logger.info("Cleanup thread stopped")
        return True
