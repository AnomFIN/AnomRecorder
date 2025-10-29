"""Tests for recording persistence and deletion."""

import pytest


def test_send2trash_available():
    """Test that send2trash is available for safe deletion."""
    try:
        from send2trash import send2trash
        assert send2trash is not None
    except ImportError:
        pytest.fail("send2trash not available")


def test_recordings_directory_logic():
    """Test that the recordings directory path logic works correctly."""
    from pathlib import Path
    import os
    
    # Test that we can create a recordings directory path
    record_dir = Path(os.getcwd()) / "recordings"
    assert record_dir.name == "recordings"
    
    # Verify that Path.mkdir with parents=True and exist_ok=True works
    # (This is what the app uses to ensure the directory exists)
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "recordings"
        test_dir.mkdir(parents=True, exist_ok=True)
        assert test_dir.exists()
        assert test_dir.is_dir()
        
        # Calling again should not raise an error
        test_dir.mkdir(parents=True, exist_ok=True)
        assert test_dir.exists()

