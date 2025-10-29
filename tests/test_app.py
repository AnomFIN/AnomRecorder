"""Tests for app-level functionality."""

from src.utils.zoom import ZoomState


def test_pan_camera():
    """Test panning updates the zoom state correctly."""
    state = ZoomState()
    # Initial pan position is 0.5, 0.5
    assert abs(state.pan_x - 0.5) < 0.001
    assert abs(state.pan_y - 0.5) < 0.001
    
    # Pan right and down
    state.pan(0.1, 0.1)
    assert abs(state.pan_x - 0.6) < 0.001
    assert abs(state.pan_y - 0.6) < 0.001
    
    # Pan left and up
    state.pan(-0.2, -0.2)
    assert abs(state.pan_x - 0.4) < 0.001
    assert abs(state.pan_y - 0.4) < 0.001


def test_zoom_out_below_one():
    """Test zooming out below 1.0 works."""
    state = ZoomState()
    state.zoom_out()
    assert state.factor == 0.75
    state.zoom_out()
    assert state.factor == 0.5
    # At minimum
    state.zoom_out()
    assert state.factor == 0.5

