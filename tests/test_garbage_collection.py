"""
Tests for the garbage collection module.
"""
import pytest
import threading
import time
from unittest.mock import patch, MagicMock, call

from gistqueue.garbage_collection import GarbageCollector

class TestGarbageCollector:
    """Test cases for the GarbageCollector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_queue_manager = MagicMock()
        self.mock_message_manager = MagicMock()
        self.mock_concurrency_manager = MagicMock()
        self.garbage_collector = GarbageCollector(
            self.mock_queue_manager,
            self.mock_message_manager,
            self.mock_concurrency_manager
        )
        # Set a shorter cleanup interval for testing
        self.garbage_collector.cleanup_interval_seconds = 0.1

    def test_cleanup_queue_success(self):
        """Test that cleanup_queue successfully cleans up a queue."""
        # Mock the message_manager.delete_completed_messages method
        self.mock_message_manager.delete_completed_messages.return_value = 5

        # Call cleanup_queue
        result = self.garbage_collector.cleanup_queue("test_queue")

        # Verify the result
        assert result == 5

        # Verify that delete_completed_messages was called with the correct arguments
        self.mock_message_manager.delete_completed_messages.assert_called_once_with("test_queue")

    def test_cleanup_queue_failure(self):
        """Test that cleanup_queue returns -1 when cleanup fails."""
        # Mock the message_manager.delete_completed_messages method to return None
        self.mock_message_manager.delete_completed_messages.return_value = None

        # Call cleanup_queue
        result = self.garbage_collector.cleanup_queue("test_queue")

        # Verify the result
        assert result == -1

        # Verify that delete_completed_messages was called with the correct arguments
        self.mock_message_manager.delete_completed_messages.assert_called_once_with("test_queue")

    def test_cleanup_queue_exception(self):
        """Test that cleanup_queue returns -1 when an exception is raised."""
        # Mock the message_manager.delete_completed_messages method to raise an exception
        self.mock_message_manager.delete_completed_messages.side_effect = Exception("Test error")

        # Call cleanup_queue
        result = self.garbage_collector.cleanup_queue("test_queue")

        # Verify the result
        assert result == -1

        # Verify that delete_completed_messages was called with the correct arguments
        self.mock_message_manager.delete_completed_messages.assert_called_once_with("test_queue")

    def test_cleanup_all_queues_success(self):
        """Test that cleanup_all_queues successfully cleans up all queues."""
        # Mock the queue_manager.list_queues method
        mock_queues = [
            {"name": "queue1", "id": "id1"},
            {"name": "queue2", "id": "id2"}
        ]
        self.mock_queue_manager.list_queues.return_value = mock_queues

        # Mock the cleanup_queue method
        with patch.object(self.garbage_collector, 'cleanup_queue') as mock_cleanup_queue:
            mock_cleanup_queue.side_effect = [3, 2]

            # Call cleanup_all_queues
            results = self.garbage_collector.cleanup_all_queues()

            # Verify the results
            assert results == {"queue1": 3, "queue2": 2}

            # Verify that cleanup_queue was called with the correct arguments
            mock_cleanup_queue.assert_has_calls([
                call("queue1"),
                call("queue2")
            ])

    def test_cleanup_all_queues_empty(self):
        """Test that cleanup_all_queues returns an empty dict when no queues are found."""
        # Mock the queue_manager.list_queues method to return an empty list
        self.mock_queue_manager.list_queues.return_value = []

        # Call cleanup_all_queues
        results = self.garbage_collector.cleanup_all_queues()

        # Verify the results
        assert results == {}

        # We can't easily verify that cleanup_queue was not called since it's a method, not a mock

    def test_cleanup_all_queues_exception(self):
        """Test that cleanup_all_queues returns an empty dict when an exception is raised."""
        # Mock the queue_manager.list_queues method to raise an exception
        self.mock_queue_manager.list_queues.side_effect = Exception("Test error")

        # Call cleanup_all_queues
        results = self.garbage_collector.cleanup_all_queues()

        # Verify the results
        assert results == {}

    def test_start_cleanup_thread(self):
        """Test that start_cleanup_thread starts a new thread."""
        # Call start_cleanup_thread
        result = self.garbage_collector.start_cleanup_thread()

        # Verify the result
        assert result is True

        # Verify that the thread was started
        assert self.garbage_collector.cleanup_thread is not None
        assert self.garbage_collector.cleanup_thread.is_alive()

        # Clean up
        self.garbage_collector.stop_event.set()
        self.garbage_collector.cleanup_thread.join(1.0)

    def test_start_cleanup_thread_already_running(self):
        """Test that start_cleanup_thread returns False when a thread is already running."""
        # Start a thread
        self.garbage_collector.start_cleanup_thread()

        # Call start_cleanup_thread again
        result = self.garbage_collector.start_cleanup_thread()

        # Verify the result
        assert result is False

        # Clean up
        self.garbage_collector.stop_event.set()
        self.garbage_collector.cleanup_thread.join(1.0)

    def test_stop_cleanup_thread(self):
        """Test that stop_cleanup_thread stops a running thread."""
        # Start a thread
        self.garbage_collector.start_cleanup_thread()

        # Call stop_cleanup_thread
        result = self.garbage_collector.stop_cleanup_thread()

        # Verify the result
        assert result is True

        # Verify that the thread was stopped
        assert not self.garbage_collector.cleanup_thread.is_alive()

    def test_stop_cleanup_thread_not_running(self):
        """Test that stop_cleanup_thread returns False when no thread is running."""
        # Call stop_cleanup_thread
        result = self.garbage_collector.stop_cleanup_thread()

        # Verify the result
        assert result is False

    def test_cleanup_worker(self):
        """Test that _cleanup_worker calls cleanup_all_queues periodically."""
        # Mock the cleanup_all_queues method
        with patch.object(self.garbage_collector, 'cleanup_all_queues') as mock_cleanup_all_queues:
            # Set up the stop event to stop the thread after a short time
            def stop_thread():
                time.sleep(0.3)  # Let the thread run for a short time
                self.garbage_collector.stop_event.set()

            # Start a thread to stop the worker thread
            stop_thread = threading.Thread(target=stop_thread)
            stop_thread.daemon = True
            stop_thread.start()

            # Call _cleanup_worker
            self.garbage_collector._cleanup_worker()

            # Verify that cleanup_all_queues was called at least once
            mock_cleanup_all_queues.assert_called()
