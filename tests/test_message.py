"""
Tests for the message module.
"""
import pytest
import json
import datetime
from unittest.mock import patch, MagicMock
from github.Gist import Gist

from gistqueue.message import MessageManager, MessageStatus

class TestMessageManager:
    """Test cases for the MessageManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_queue_manager = MagicMock()
        self.message_manager = MessageManager(self.mock_queue_manager)

    def test_generate_message_id(self):
        """Test that _generate_message_id returns a string."""
        message_id = self.message_manager._generate_message_id()
        assert isinstance(message_id, str)
        assert len(message_id) > 0

    def test_get_process_identifier(self):
        """Test that _get_process_identifier returns a string."""
        process_id = self.message_manager._get_process_identifier()
        assert isinstance(process_id, str)
        assert len(process_id) > 0

    def test_get_current_datetime(self):
        """Test that _get_current_datetime returns a string in ISO format."""
        datetime_str = self.message_manager._get_current_datetime()
        assert isinstance(datetime_str, str)
        # Verify that it's a valid ISO format datetime
        try:
            datetime.datetime.fromisoformat(datetime_str)
        except ValueError:
            pytest.fail("_get_current_datetime did not return a valid ISO format datetime")

    def test_create_message_success(self):
        """Test that create_message creates a new message when successful."""
        # Mock the queue_manager.get_queue method
        mock_gist = MagicMock()
        self.mock_queue_manager.get_queue.return_value = mock_gist
        self.mock_queue_manager.get_queue_by_id.return_value = mock_gist

        # Mock the queue_manager.get_queue_content method
        self.mock_queue_manager.get_queue_content.return_value = []

        # Mock the queue_manager._get_queue_filename method
        self.mock_queue_manager._get_queue_filename.return_value = "test_queue.json"

        # Mock the queue_manager.client.update_gist method
        self.mock_queue_manager.client.update_gist.return_value = mock_gist

        # Mock the _generate_message_id method
        with patch.object(self.message_manager, '_generate_message_id', return_value="test_id"):
            # Mock the _get_current_datetime method
            with patch.object(self.message_manager, '_get_current_datetime', return_value="2021-01-01T00:00:00+00:00"):
                # Call create_message
                result = self.message_manager.create_message("test", "test_content")

                # Verify the result
                assert result is not None
                assert result["id"] == "test_id"
                assert result["content"] == "test_content"
                assert result["status"] == MessageStatus.PENDING
                assert result["status_datetime"] == "2021-01-01T00:00:00+00:00"
                assert result["process"] is None

                # Verify that update_gist was called with the correct arguments
                self.mock_queue_manager.client.update_gist.assert_called_once()
                args, kwargs = self.mock_queue_manager.client.update_gist.call_args
                assert args[0] == mock_gist
                assert args[1] == "test_queue.json"
                # Verify that the content is valid JSON
                try:
                    content = json.loads(args[2])
                    assert isinstance(content, list)
                    assert len(content) == 1
                    assert content[0]["id"] == "test_id"
                    assert content[0]["content"] == "test_content"
                    assert content[0]["status"] == MessageStatus.PENDING
                except json.JSONDecodeError:
                    pytest.fail("update_gist was not called with valid JSON content")

    def test_create_message_queue_not_found(self):
        """Test that create_message returns None when the queue is not found."""
        # Mock the queue_manager.get_queue method to return None
        self.mock_queue_manager.get_queue.return_value = None

        # Call create_message
        result = self.message_manager.create_message("test", "test_content")

        # Verify the result
        assert result is None

        # Verify that update_gist was not called
        self.mock_queue_manager.client.update_gist.assert_not_called()

    def test_list_messages_success(self):
        """Test that list_messages returns a list of messages when successful."""
        # Mock the queue_manager.get_queue_content method
        mock_messages = [
            {
                "id": "msg1",
                "content": "test1",
                "status": MessageStatus.PENDING,
                "status_datetime": "2021-01-01T00:00:00+00:00",
                "process": None
            },
            {
                "id": "msg2",
                "content": "test2",
                "status": MessageStatus.IN_PROGRESS,
                "status_datetime": "2021-01-02T00:00:00+00:00",
                "process": "host:123"
            }
        ]
        self.mock_queue_manager.get_queue_content.return_value = mock_messages

        # Call list_messages
        result = self.message_manager.list_messages("test")

        # Verify the result
        assert result == mock_messages

        # Call list_messages with status filter
        result = self.message_manager.list_messages("test", MessageStatus.PENDING)

        # Verify the result
        assert len(result) == 1
        assert result[0]["id"] == "msg1"

    def test_list_messages_queue_not_found(self):
        """Test that list_messages returns None when the queue is not found."""
        # Mock the queue_manager.get_queue_content method to return None
        self.mock_queue_manager.get_queue_content.return_value = None

        # Call list_messages
        result = self.message_manager.list_messages("test")

        # Verify the result
        assert result is None

    def test_get_next_message_success(self):
        """Test that get_next_message returns the next pending message when successful."""
        # Mock the queue_manager.get_queue method
        mock_gist = MagicMock()
        self.mock_queue_manager.get_queue.return_value = mock_gist
        self.mock_queue_manager.get_queue_by_id.return_value = mock_gist

        # Mock the queue_manager.get_queue_content method
        mock_messages = [
            {
                "id": "msg1",
                "content": "test1",
                "status": MessageStatus.PENDING,
                "status_datetime": "2021-01-01T00:00:00+00:00",
                "process": None
            },
            {
                "id": "msg2",
                "content": "test2",
                "status": MessageStatus.PENDING,
                "status_datetime": "2021-01-02T00:00:00+00:00",
                "process": None
            }
        ]
        self.mock_queue_manager.get_queue_content.return_value = mock_messages

        # Mock the queue_manager._get_queue_filename method
        self.mock_queue_manager._get_queue_filename.return_value = "test_queue.json"

        # Mock the queue_manager.client.update_gist method
        self.mock_queue_manager.client.update_gist.return_value = mock_gist

        # Mock the _get_current_datetime method
        with patch.object(self.message_manager, '_get_current_datetime', return_value="2021-01-03T00:00:00+00:00"):
            # Mock the _get_process_identifier method
            with patch.object(self.message_manager, '_get_process_identifier', return_value="host:123"):
                # Call get_next_message
                result = self.message_manager.get_next_message("test")

                # Verify the result
                assert result is not None
                assert result["id"] == "msg1"
                assert result["content"] == "test1"
                assert result["status"] == MessageStatus.IN_PROGRESS
                assert result["status_datetime"] == "2021-01-03T00:00:00+00:00"
                assert result["process"] == "host:123"

                # Verify that update_gist was called with the correct arguments
                self.mock_queue_manager.client.update_gist.assert_called_once()
                args, kwargs = self.mock_queue_manager.client.update_gist.call_args
                assert args[0] == mock_gist
                assert args[1] == "test_queue.json"
                # Verify that the content is valid JSON
                try:
                    content = json.loads(args[2])
                    assert isinstance(content, list)
                    assert len(content) == 2
                    assert content[0]["id"] == "msg1"
                    assert content[0]["status"] == MessageStatus.IN_PROGRESS
                    assert content[0]["status_datetime"] == "2021-01-03T00:00:00+00:00"
                    assert content[0]["process"] == "host:123"
                except json.JSONDecodeError:
                    pytest.fail("update_gist was not called with valid JSON content")

    def test_get_next_message_no_pending(self):
        """Test that get_next_message returns None when there are no pending messages."""
        # Mock the queue_manager.get_queue method
        mock_gist = MagicMock()
        self.mock_queue_manager.get_queue.return_value = mock_gist

        # Mock the queue_manager.get_queue_content method
        mock_messages = [
            {
                "id": "msg1",
                "content": "test1",
                "status": MessageStatus.IN_PROGRESS,
                "status_datetime": "2021-01-01T00:00:00+00:00",
                "process": "host:123"
            },
            {
                "id": "msg2",
                "content": "test2",
                "status": MessageStatus.COMPLETE,
                "status_datetime": "2021-01-02T00:00:00+00:00",
                "process": "host:123"
            }
        ]
        self.mock_queue_manager.get_queue_content.return_value = mock_messages

        # Call get_next_message
        result = self.message_manager.get_next_message("test")

        # Verify the result
        assert result is None

        # Verify that update_gist was not called
        self.mock_queue_manager.client.update_gist.assert_not_called()

    def test_update_message_success(self):
        """Test that update_message updates a message when successful."""
        # Mock the queue_manager.get_queue method
        mock_gist = MagicMock()
        self.mock_queue_manager.get_queue.return_value = mock_gist
        self.mock_queue_manager.get_queue_by_id.return_value = mock_gist

        # Mock the queue_manager.get_queue_content method
        mock_messages = [
            {
                "id": "msg1",
                "content": "test1",
                "status": MessageStatus.IN_PROGRESS,
                "status_datetime": "2021-01-01T00:00:00+00:00",
                "process": "host:123"
            },
            {
                "id": "msg2",
                "content": "test2",
                "status": MessageStatus.PENDING,
                "status_datetime": "2021-01-02T00:00:00+00:00",
                "process": None
            }
        ]
        self.mock_queue_manager.get_queue_content.return_value = mock_messages

        # Mock the queue_manager._get_queue_filename method
        self.mock_queue_manager._get_queue_filename.return_value = "test_queue.json"

        # Mock the queue_manager.client.update_gist method
        self.mock_queue_manager.client.update_gist.return_value = mock_gist

        # Mock the _get_current_datetime method
        with patch.object(self.message_manager, '_get_current_datetime', return_value="2021-01-03T00:00:00+00:00"):
            # Call update_message
            result = self.message_manager.update_message("test", "msg1", "updated_content", MessageStatus.COMPLETE)

            # Verify the result
            assert result is not None
            assert result["id"] == "msg1"
            assert result["content"] == "updated_content"
            assert result["status"] == MessageStatus.COMPLETE
            assert result["status_datetime"] == "2021-01-03T00:00:00+00:00"
            assert result["process"] == "host:123"

            # Verify that update_gist was called with the correct arguments
            self.mock_queue_manager.client.update_gist.assert_called_once()
            args, kwargs = self.mock_queue_manager.client.update_gist.call_args
            assert args[0] == mock_gist
            assert args[1] == "test_queue.json"
            # Verify that the content is valid JSON
            try:
                content = json.loads(args[2])
                assert isinstance(content, list)
                assert len(content) == 2
                assert content[0]["id"] == "msg1"
                assert content[0]["content"] == "updated_content"
                assert content[0]["status"] == MessageStatus.COMPLETE
                assert content[0]["status_datetime"] == "2021-01-03T00:00:00+00:00"
            except json.JSONDecodeError:
                pytest.fail("update_gist was not called with valid JSON content")

    def test_update_message_not_found(self):
        """Test that update_message returns None when the message is not found."""
        # Mock the queue_manager.get_queue method
        mock_gist = MagicMock()
        self.mock_queue_manager.get_queue.return_value = mock_gist

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

        # Call update_message with a non-existent message ID
        result = self.message_manager.update_message("test", "msg2", "updated_content", MessageStatus.COMPLETE)

        # Verify the result
        assert result is None

        # Verify that update_gist was not called
        self.mock_queue_manager.client.update_gist.assert_not_called()

    def test_delete_completed_messages_success(self):
        """Test that delete_completed_messages deletes completed messages when successful."""
        # Mock the queue_manager.get_queue method
        mock_gist = MagicMock()
        self.mock_queue_manager.get_queue.return_value = mock_gist
        self.mock_queue_manager.get_queue_by_id.return_value = mock_gist

        # Mock the queue_manager.get_queue_content method
        mock_messages = [
            {
                "id": "msg1",
                "content": "test1",
                "status": MessageStatus.COMPLETE,
                "status_datetime": "2020-01-01T00:00:00+00:00",  # Old message
                "process": "host:123"
            },
            {
                "id": "msg2",
                "content": "test2",
                "status": MessageStatus.COMPLETE,
                "status_datetime": datetime.datetime.now(datetime.timezone.utc).isoformat(),  # Recent message
                "process": "host:123"
            },
            {
                "id": "msg3",
                "content": "test3",
                "status": MessageStatus.PENDING,
                "status_datetime": "2020-01-01T00:00:00+00:00",  # Old but not complete
                "process": None
            }
        ]
        self.mock_queue_manager.get_queue_content.return_value = mock_messages

        # Mock the queue_manager._get_queue_filename method
        self.mock_queue_manager._get_queue_filename.return_value = "test_queue.json"

        # Mock the queue_manager.client.update_gist method
        self.mock_queue_manager.client.update_gist.return_value = mock_gist

        # Call delete_completed_messages
        result = self.message_manager.delete_completed_messages("test")

        # Verify the result
        assert result == 1  # One message should be deleted

        # Verify that update_gist was called with the correct arguments
        self.mock_queue_manager.client.update_gist.assert_called_once()
        args, kwargs = self.mock_queue_manager.client.update_gist.call_args
        assert args[0] == mock_gist
        assert args[1] == "test_queue.json"
        # Verify that the content is valid JSON
        try:
            content = json.loads(args[2])
            assert isinstance(content, list)
            assert len(content) == 2
            assert content[0]["id"] == "msg2"  # Recent complete message
            assert content[1]["id"] == "msg3"  # Pending message
        except json.JSONDecodeError:
            pytest.fail("update_gist was not called with valid JSON content")

    def test_delete_completed_messages_none_to_delete(self):
        """Test that delete_completed_messages returns 0 when there are no messages to delete."""
        # Mock the queue_manager.get_queue method
        mock_gist = MagicMock()
        self.mock_queue_manager.get_queue.return_value = mock_gist
        self.mock_queue_manager.get_queue_by_id.return_value = mock_gist

        # Mock the queue_manager.get_queue_content method
        mock_messages = [
            {
                "id": "msg1",
                "content": "test1",
                "status": MessageStatus.PENDING,
                "status_datetime": "2021-01-01T00:00:00+00:00",
                "process": None
            },
            {
                "id": "msg2",
                "content": "test2",
                "status": MessageStatus.IN_PROGRESS,
                "status_datetime": "2021-01-02T00:00:00+00:00",
                "process": "host:123"
            }
        ]
        self.mock_queue_manager.get_queue_content.return_value = mock_messages

        # Call delete_completed_messages
        result = self.message_manager.delete_completed_messages("test")

        # Verify the result
        assert result == 0

        # Verify that update_gist was not called
        self.mock_queue_manager.client.update_gist.assert_not_called()
