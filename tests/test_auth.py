"""
Tests for the authentication module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from gistqueue.direct_api import GithubException

from gistqueue.auth import get_github_token, validate_token, get_github_client

class TestAuth:
    """Test cases for the authentication module."""

    def test_get_github_token_success(self):
        """Test that get_github_token returns the token when it's set."""
        with patch.dict(os.environ, {'GIST_TOKEN': 'test_token'}):
            token = get_github_token()
            assert token == 'test_token'

    def test_get_github_token_missing(self):
        """Test that get_github_token raises ValueError when token is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                get_github_token()

    def test_validate_token_success(self):
        """Test that validate_token returns True for a valid token."""
        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_client.get_user.return_value = mock_user

        with patch('gistqueue.auth.DirectGitHubClient', return_value=mock_client):
            result = validate_token('test_token')
            assert result is True

    def test_validate_token_failure(self):
        """Test that validate_token returns False for an invalid token."""
        mock_client = MagicMock()
        mock_client.get_user.side_effect = GithubException(401, {'message': 'Bad credentials'})

        with patch('gistqueue.auth.DirectGitHubClient', return_value=mock_client):
            result = validate_token('invalid_token')
            assert result is False

    def test_get_github_client_success(self):
        """Test that get_github_client returns a DirectGitHubClient instance when authentication succeeds."""
        mock_client = MagicMock()

        with patch('gistqueue.auth.get_github_token', return_value='test_token'):
            with patch('gistqueue.auth.validate_token', return_value=True):
                with patch('gistqueue.auth.DirectGitHubClient', return_value=mock_client):
                    client = get_github_client()
                    assert client == mock_client

    def test_get_github_client_validation_failure(self):
        """Test that get_github_client returns None when token validation fails."""
        with patch('gistqueue.auth.get_github_token', return_value='test_token'):
            with patch('gistqueue.auth.validate_token', return_value=False):
                client = get_github_client()
                assert client is None

    def test_get_github_client_missing_token(self):
        """Test that get_github_client returns None when token is missing."""
        with patch('gistqueue.auth.get_github_token', side_effect=ValueError('Token missing')):
            client = get_github_client()
            assert client is None
