"""
Tests for the main module.
"""
import pytest
import os
import logging
from unittest.mock import patch, MagicMock
from gistqueue.main import main, check_environment, initialize_client

def test_check_environment_success():
    """Test that check_environment returns True when the token is valid."""
    with patch('gistqueue.main.get_github_token', return_value='test_token'):
        with patch('gistqueue.main.validate_token', return_value=True):
            assert check_environment() is True

def test_check_environment_failure():
    """Test that check_environment returns False when the token is invalid."""
    with patch('gistqueue.main.get_github_token', return_value='test_token'):
        with patch('gistqueue.main.validate_token', return_value=False):
            assert check_environment() is False

def test_initialize_client_success():
    """Test that initialize_client returns a GistClient instance when successful."""
    mock_client = MagicMock()
    with patch('gistqueue.main.GistClient', return_value=mock_client):
        client = initialize_client()
        assert client == mock_client

def test_initialize_client_failure():
    """Test that initialize_client returns None when initialization fails."""
    with patch('gistqueue.main.GistClient', side_effect=RuntimeError('Test error')):
        client = initialize_client()
        assert client is None

def test_main_with_environment_error():
    """Test that main returns 1 when the environment check fails."""
    with patch('gistqueue.main.check_environment', return_value=False):
        assert main() == 1

def test_main_with_client_error():
    """Test that main returns 1 when client initialization fails."""
    with patch('gistqueue.main.check_environment', return_value=True):
        with patch('gistqueue.main.initialize_client', return_value=None):
            assert main() == 1

def test_main_success(caplog):
    """Test that main returns 0 and logs the expected message when successful."""
    caplog.set_level(logging.INFO)
    mock_client = MagicMock()
    with patch('gistqueue.main.check_environment', return_value=True):
        with patch('gistqueue.main.initialize_client', return_value=mock_client):
            assert main() == 0
            assert "GistQueue initialized successfully" in caplog.text
