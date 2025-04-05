"""
Tests for the main module.
"""
import pytest
from gistqueue.main import main

def test_main(capsys):
    """Test that the main function runs without errors and prints the expected message."""
    main()
    captured = capsys.readouterr()
    assert "GistQueue application initialized" in captured.out
