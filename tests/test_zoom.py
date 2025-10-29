"""Tests for zoom state helpers."""

import numpy as np

from src.utils.zoom import ZoomState, crop_zoom


def test_zoom_state_bounds():
    state = ZoomState()
    state.zoom_in()
    assert state.factor == 1.25
    state.zoom_out()
    assert state.factor == 1.0
    state.zoom_out()
    assert state.factor == 0.75  # Can zoom out below 1.0
    state.zoom_out()
    state.zoom_out()  # Try to go below min
    assert state.factor == state.min_factor  # Should clamp to min (0.5)
    for _ in range(20):
        state.zoom_in()
    assert state.factor == state.max_factor
    state.reset()
    assert state.factor == 1.0
    assert state.pan_x == 0.0
    assert state.pan_y == 0.0


def test_crop_zoom_center():
    frame = np.arange(100).reshape(10, 10).astype("uint8")
    zoomed = crop_zoom(np.dstack([frame] * 3), 2.0)
    assert zoomed.shape[0] == 5
    assert zoomed.shape[1] == 5


def test_zoom_out():
    """Test zoom out functionality."""
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
    zoomed = crop_zoom(frame, 0.5)
    # Zoomed out frame should have same dimensions but with padding
    assert zoomed.shape == frame.shape


def test_pan_bounds():
    """Test panning bounds."""
    state = ZoomState()
    state.pan(2.0, 2.0)  # Try to pan beyond bounds
    assert state.pan_x == 1.0  # Should clamp to max
    assert state.pan_y == 1.0
    
    state.pan(-4.0, -4.0)  # Try to pan beyond bounds
    assert state.pan_x == -1.0  # Should clamp to min
    assert state.pan_y == -1.0


def test_focus_point():
    """Test focus point setting."""
    state = ZoomState()
    state.set_focus(0.3, 0.7)
    assert state.focus_x == 0.3
    assert state.focus_y == 0.7
    
    # Test clamping
    state.set_focus(-0.5, 1.5)
    assert state.focus_x == 0.0
    assert state.focus_y == 1.0


def test_crop_zoom_with_pan():
    """Test crop zoom with panning."""
    frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
    # Should not crash with panning
    zoomed = crop_zoom(frame, 2.0, pan_x=0.5, pan_y=0.5)
    assert zoomed.shape[0] <= frame.shape[0]
    assert zoomed.shape[1] <= frame.shape[1]

