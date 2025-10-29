"""Tests for camera reconnection logic."""

import time
from src.utils.reconnect import ReconnectState


def test_reconnect_initial_state():
    """Test initial reconnection state."""
    state = ReconnectState()
    assert state.enabled is True
    assert state.attempt == 0
    # Initially with last_attempt_time=0, it will attempt (time difference is large)
    assert state.should_attempt() is True


def test_reconnect_attempt_tracking():
    """Test reconnection attempt tracking."""
    state = ReconnectState()
    state.last_attempt_time = time.time() - 10  # Fake old attempt
    
    assert state.should_attempt() is True
    state.record_attempt()
    assert state.attempt == 1
    
    # Should not attempt immediately after
    assert state.should_attempt() is False


def test_reconnect_exponential_backoff():
    """Test exponential backoff delays."""
    state = ReconnectState()
    state.base_delay = 1.0
    
    # First attempt should wait base_delay
    state.last_attempt_time = time.time() - 0.5
    assert state.should_attempt() is False
    
    state.last_attempt_time = time.time() - 1.5
    assert state.should_attempt() is True
    state.record_attempt()
    
    # Second attempt should wait 2 * base_delay
    state.last_attempt_time = time.time() - 1.5
    assert state.should_attempt() is False
    
    state.last_attempt_time = time.time() - 2.5
    assert state.should_attempt() is True


def test_reconnect_max_attempts():
    """Test maximum reconnection attempts."""
    state = ReconnectState(max_attempts=3)
    
    for _ in range(3):
        state.last_attempt_time = 0
        assert state.should_attempt() is True
        state.record_attempt()
    
    # Should not attempt after max attempts
    state.last_attempt_time = 0
    assert state.should_attempt() is False


def test_reconnect_reset():
    """Test reconnection state reset."""
    state = ReconnectState()
    state.attempt = 5
    state.last_attempt_time = time.time()
    
    state.reset()
    assert state.attempt == 0
    assert state.last_attempt_time == 0.0


def test_reconnect_disabled():
    """Test disabled reconnection."""
    state = ReconnectState(enabled=False)
    state.last_attempt_time = 0
    
    assert state.should_attempt() is False


def test_reconnect_status_text():
    """Test status text generation."""
    state = ReconnectState()
    text = state.get_status_text()
    assert "Yhdistetty" in text
    
    state.enabled = False
    text = state.get_status_text()
    assert "Pois päältä" in text
    
    state.enabled = True
    state.attempt = 2
    text = state.get_status_text()
    assert "yritys" in text
