"""
Tests for the concurrency module.
"""
import pytest
import json
import hashlib
from unittest.mock import patch, MagicMock, call
from github import GithubException

from gistqueue.concurrency import ConcurrencyManager, ConflictError
from gistqueue.message import MessageStatus

class TestConcurrencyManager:
    """Test cases for the ConcurrencyManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_queue_manager = MagicMock()
        self.mock_message_manager = MagicMock()
        self.concurrency_manager = ConcurrencyManager(
            self.mock_queue_manager,
            self.mock_message_manager
        )

    def test_calculate_etag(self):
        """Test that _calculate_etag returns the correct hash."""
        content = "test content"
        expected_etag = hashlib.md5(content.encode('utf-8')).hexdigest()

        etag = self.concurrency_manager._calculate_etag(content)

        assert etag == expected_etag

    def test_calculate_retry_delay(self):
        """Test that _calculate_retry_delay returns a value within the expected range."""
        # First attempt
        delay = self.concurrency_manager._calculate_retry_delay(0)
        assert delay >= 0.9 and delay <= 1.1  # Base delay with jitter

        # Second attempt
        delay = self.concurrency_manager._calculate_retry_delay(1)
        assert delay >= 1.8 and delay <= 2.2  # 2x base delay with jitter

        # Third attempt
        delay = self.concurrency_manager._calculate_retry_delay(2)
        assert delay >= 3.6 and delay <= 4.4  # 4x base delay with jitter

        # Fourth attempt (should be capped at max delay)
        delay = self.concurrency_manager._calculate_retry_delay(3)
        assert delay >= 4.5 and delay <= 5.5  # Max delay with jitter

    def test_with_retry_success_first_attempt(self):
        """Test that with_retry returns the result of the operation on the first attempt."""
        mock_operation = MagicMock(return_value="success")

        result = self.concurrency_manager.with_retry(mock_operation, "arg1", kwarg1="value1")

        assert result == "success"
        mock_operation.assert_called_once_with("arg1", kwarg1="value1")

    def test_with_retry_success_after_retries(self):
        """Test that with_retry retries the operation and returns the result on success."""
        mock_operation = MagicMock(side_effect=[
            ConflictError("Conflict 1"),
            ConflictError("Conflict 2"),
            "success"
        ])

        with patch('time.sleep') as mock_sleep:
            result = self.concurrency_manager.with_retry(mock_operation)

        assert result == "success"
        assert mock_operation.call_count == 3
        assert mock_sleep.call_count == 2

    def test_with_retry_failure_after_max_retries(self):
        """Test that with_retry raises ConflictError after max retries."""
        mock_operation = MagicMock(side_effect=ConflictError("Persistent conflict"))

        with patch('time.sleep'), pytest.raises(ConflictError) as excinfo:
            self.concurrency_manager.with_retry(mock_operation)

        assert "Persistent conflict" in str(excinfo.value)
        assert mock_operation.call_count == self.concurrency_manager.max_retries

    def test_atomic_update_success(self):
        """Test that atomic_update successfully updates a queue."""
        # Mock the queue_manager.get_queue method
        mock_gist = MagicMock()
        self.mock_queue_manager.get_queue.return_value = mock_gist
        self.mock_queue_manager.get_queue_by_id.return_value = mock_gist

        # Mock the queue_manager._get_queue_filename method
        self.mock_queue_manager._get_queue_filename.return_value = "test_queue.json"

        # Mock the queue_manager.client.get_gist_content method
        current_content = [{"id": "msg1", "content": "test1"}]
        current_content_str = json.dumps(current_content)
        # Create the updated content string with the same formatting as json.dumps(content, indent=2)
        updated_content_str = json.dumps([{"id": "msg1", "content": "updated"}], indent=2)
        self.mock_queue_manager.client.get_gist_content.side_effect = [
            current_content_str,  # First call to get current content
            updated_content_str  # Second call to verify update
        ]

        # Mock the queue_manager.client.update_gist method
        self.mock_queue_manager.client.update_gist.return_value = mock_gist

        # Define the update function
        def update_func(content):
            content[0]["content"] = "updated"
            return content

        # Call atomic_update
        result = self.concurrency_manager.atomic_update("test", update_func)

        # Verify the result
        assert result == [{"id": "msg1", "content": "updated"}]

        # Verify that update_gist was called with the correct arguments
        self.mock_queue_manager.client.update_gist.assert_called_once()
        args, kwargs = self.mock_queue_manager.client.update_gist.call_args
        assert args[0] == mock_gist
        assert args[1] == "test_queue.json"
        assert "updated" in args[2]

    def test_atomic_update_conflict(self):
        """Test that atomic_update raises ConflictError when the content is modified during update."""
        # Mock the queue_manager.get_queue method
        mock_gist = MagicMock()
        self.mock_queue_manager.get_queue.return_value = mock_gist

        # Mock the queue_manager._get_queue_filename method
        self.mock_queue_manager._get_queue_filename.return_value = "test_queue.json"

        # Mock the queue_manager.client.get_gist_content method
        current_content = [{"id": "msg1", "content": "test1"}]
        current_content_str = json.dumps(current_content)
        modified_content_str = json.dumps([{"id": "msg1", "content": "modified by another process"}])
        self.mock_queue_manager.client.get_gist_content.side_effect = [
            current_content_str,  # First call to get current content
            modified_content_str  # Second call to verify update (content has been modified)
        ]

        # Mock the queue_manager.client.update_gist method
        self.mock_queue_manager.client.update_gist.return_value = mock_gist

        # Define the update function
        def update_func(content):
            content[0]["content"] = "updated"
            return content

        # Call atomic_update
        with pytest.raises(ConflictError) as excinfo:
            self.concurrency_manager.atomic_update("test", update_func)

        assert "modified by another process" in str(excinfo.value)

    def test_atomic_get_next_message_success(self):
        """Test that atomic_get_next_message successfully gets the next message."""
        # Mock the queue_manager.get_queue_content method
        mock_messages = [
            {
                "id": "msg1",
                "content": "test1",
                "status": MessageStatus.PENDING,
                "status_datetime": "2021-01-01T00:00:00+00:00",
                "process": None
            }
        ]
        self.mock_queue_manager.get_queue_content.return_value = mock_messages

        # Mock the atomic_update method
        updated_messages = [
            {
                "id": "msg1",
                "content": "test1",
                "status": MessageStatus.IN_PROGRESS,
                "status_datetime": "2021-01-02T00:00:00+00:00",
                "process": "host:123"
            }
        ]
        self.concurrency_manager.atomic_update = MagicMock(return_value=updated_messages)

        # Mock the message_manager._get_process_identifier method
        self.mock_message_manager._get_process_identifier.return_value = "host:123"

        # Call atomic_get_next_message
        result = self.concurrency_manager.atomic_get_next_message("test")

        # Verify the result
        assert result == updated_messages[0]

        # Verify that atomic_update was called
        self.concurrency_manager.atomic_update.assert_called_once()

    def test_atomic_get_next_message_no_pending(self):
        """Test that atomic_get_next_message returns None when there are no pending messages."""
        # Mock the queue_manager.get_queue_content method
        mock_messages = [
            {
                "id": "msg1",
                "content": "test1",
                "status": MessageStatus.IN_PROGRESS,
                "status_datetime": "2021-01-01T00:00:00+00:00",
                "process": "host:123"
            }
        ]
        self.mock_queue_manager.get_queue_content.return_value = mock_messages

        # Call atomic_get_next_message
        result = self.concurrency_manager.atomic_get_next_message("test")

        # Verify the result
        assert result is None

        # We can't easily verify that atomic_update was not called since it's a method, not a mock

    def test_atomic_update_message_success(self):
        """Test that atomic_update_message successfully updates a message."""
        # Mock the with_retry method
        updated_messages = [
            {
                "id": "msg1",
                "content": "updated",
                "status": MessageStatus.COMPLETE,
                "status_datetime": "2021-01-02T00:00:00+00:00",
                "process": "host:123"
            }
        ]
        self.concurrency_manager.with_retry = MagicMock(return_value=updated_messages)

        # Call atomic_update_message
        result = self.concurrency_manager.atomic_update_message("test", "msg1", "updated", MessageStatus.COMPLETE)

        # Verify the result
        assert result == updated_messages[0]

        # Verify that with_retry was called
        self.concurrency_manager.with_retry.assert_called_once()

    def test_atomic_update_message_not_found(self):
        """Test that atomic_update_message returns None when the message is not found."""
        # Mock the with_retry method to raise ValueError
        self.concurrency_manager.with_retry = MagicMock(side_effect=ValueError("Message not found"))

        # Call atomic_update_message
        result = self.concurrency_manager.atomic_update_message("test", "msg2", "updated", MessageStatus.COMPLETE)

        # Verify the result
        assert result is None

        # Verify that with_retry was called
        self.concurrency_manager.with_retry.assert_called_once()
