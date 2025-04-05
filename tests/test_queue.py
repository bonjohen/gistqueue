"""
Tests for the queue module.
"""
import pytest
from unittest.mock import patch, MagicMock
from github.Gist import Gist

from gistqueue.queue import QueueManager
from gistqueue.config import CONFIG

class TestQueueManager:
    """Test cases for the QueueManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.queue_manager = QueueManager(self.mock_client)
    
    def test_get_queue_description(self):
        """Test that _get_queue_description returns the correct description."""
        description = self.queue_manager._get_queue_description("test")
        assert description == f"{CONFIG['GIST_DESCRIPTION_PREFIX']} test"
    
    def test_get_queue_filename(self):
        """Test that _get_queue_filename returns the correct filename."""
        filename = self.queue_manager._get_queue_filename("test")
        assert filename == f"test_queue.{CONFIG['DEFAULT_FILE_EXTENSION']}"
    
    def test_create_queue_success(self):
        """Test that create_queue creates a new queue when it doesn't exist."""
        # Mock the get_queue method to return None (queue doesn't exist)
        self.queue_manager.get_queue = MagicMock(return_value=None)
        
        # Mock the client.create_gist method
        mock_gist = MagicMock()
        self.mock_client.create_gist.return_value = mock_gist
        
        # Call create_queue
        result = self.queue_manager.create_queue("test")
        
        # Verify the result
        assert result == mock_gist
        
        # Verify that create_gist was called with the correct arguments
        self.mock_client.create_gist.assert_called_once_with(
            description=self.queue_manager._get_queue_description("test"),
            filename=self.queue_manager._get_queue_filename("test"),
            content="[]",
            public=False
        )
    
    def test_create_queue_already_exists(self):
        """Test that create_queue returns the existing queue when it already exists."""
        # Mock the get_queue method to return a mock gist (queue exists)
        mock_gist = MagicMock()
        self.queue_manager.get_queue = MagicMock(return_value=mock_gist)
        
        # Call create_queue
        result = self.queue_manager.create_queue("test")
        
        # Verify the result
        assert result == mock_gist
        
        # Verify that create_gist was not called
        self.mock_client.create_gist.assert_not_called()
    
    def test_get_queue_by_name(self):
        """Test that get_queue retrieves a queue by name."""
        # Mock the client.get_gist_by_description method
        mock_gist = MagicMock()
        self.mock_client.get_gist_by_description.return_value = mock_gist
        
        # Call get_queue
        result = self.queue_manager.get_queue("test")
        
        # Verify the result
        assert result == mock_gist
        
        # Verify that get_gist_by_description was called with the correct arguments
        self.mock_client.get_gist_by_description.assert_called_once_with(
            self.queue_manager._get_queue_description("test")
        )
    
    def test_get_queue_by_id(self):
        """Test that get_queue_by_id retrieves a queue by ID."""
        # Mock the client.get_gist_by_id method
        mock_gist = MagicMock()
        self.mock_client.get_gist_by_id.return_value = mock_gist
        
        # Call get_queue_by_id
        result = self.queue_manager.get_queue_by_id("test_id")
        
        # Verify the result
        assert result == mock_gist
        
        # Verify that get_gist_by_id was called with the correct arguments
        self.mock_client.get_gist_by_id.assert_called_once_with("test_id")
    
    def test_list_queues(self):
        """Test that list_queues returns a list of queues."""
        # Mock the client.github.get_user().get_gists() method
        mock_user = MagicMock()
        self.mock_client.github.get_user.return_value = mock_user
        
        # Create mock gists
        mock_gist1 = MagicMock()
        mock_gist1.id = "gist1"
        mock_gist1.description = f"{CONFIG['GIST_DESCRIPTION_PREFIX']} test1"
        mock_gist1.html_url = "https://gist.github.com/user/gist1"
        mock_gist1.created_at.isoformat.return_value = "2021-01-01T00:00:00"
        mock_gist1.updated_at.isoformat.return_value = "2021-01-02T00:00:00"
        
        mock_gist2 = MagicMock()
        mock_gist2.id = "gist2"
        mock_gist2.description = f"{CONFIG['GIST_DESCRIPTION_PREFIX']} test2"
        mock_gist2.html_url = "https://gist.github.com/user/gist2"
        mock_gist2.created_at.isoformat.return_value = "2021-01-03T00:00:00"
        mock_gist2.updated_at.isoformat.return_value = "2021-01-04T00:00:00"
        
        # Mock gist that is not a queue
        mock_gist3 = MagicMock()
        mock_gist3.description = "Not a queue"
        
        mock_user.get_gists.return_value = [mock_gist1, mock_gist2, mock_gist3]
        
        # Call list_queues
        result = self.queue_manager.list_queues()
        
        # Verify the result
        assert len(result) == 2
        assert result[0]["id"] == "gist1"
        assert result[0]["name"] == "test1"
        assert result[1]["id"] == "gist2"
        assert result[1]["name"] == "test2"
    
    def test_get_queue_content(self):
        """Test that get_queue_content retrieves and parses queue content."""
        # Mock the client.get_gist_content method
        self.mock_client.get_gist_content.return_value = '[{"id": "msg1", "content": "test"}]'
        
        # Mock the client.parse_json_content method
        expected_content = [{"id": "msg1", "content": "test"}]
        self.mock_client.parse_json_content.return_value = expected_content
        
        # Create a mock gist
        mock_gist = MagicMock()
        mock_gist.files = {"test_queue.json": MagicMock()}
        
        # Call get_queue_content
        result = self.queue_manager.get_queue_content(mock_gist, "test")
        
        # Verify the result
        assert result == expected_content
        
        # Verify that get_gist_content was called with the correct arguments
        self.mock_client.get_gist_content.assert_called_once_with(
            mock_gist, self.queue_manager._get_queue_filename("test")
        )
