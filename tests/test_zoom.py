"""Tests for zoom and pan state helpers."""

import numpy as np

from src.utils.zoom import ZoomState, crop_zoom


def test_zoom_state_bounds():
    state = ZoomState()
    state.zoom_in()
    assert state.factor == 1.25
    state.zoom_out()
    assert state.factor == 1.0
    # Can now zoom out below 1.0
    state.zoom_out()
    assert state.factor == 0.75  # Now supports zoom out below 1.0
    state.zoom_out()
    assert state.factor == 0.5  # Min factor
    state.zoom_out()
    assert state.factor == 0.5  # Clamped at min
    for _ in range(20):
        state.zoom_in()
    assert state.factor == state.max_factor
    state.reset()
    assert state.factor == 1.0
    assert state.pan_x == 0.5
    assert state.pan_y == 0.5


def test_zoom_state_pan():
    state = ZoomState()
    state.pan(0.1, 0.0)
    assert abs(state.pan_x - 0.6) < 0.001
    state.pan(-0.2, 0.1)
    assert abs(state.pan_x - 0.4) < 0.001
    assert abs(state.pan_y - 0.6) < 0.001
    # Test bounds
    state.pan(1.0, 1.0)
    assert abs(state.pan_x - 1.0) < 0.001
    assert abs(state.pan_y - 1.0) < 0.001
    state.pan(-2.0, -2.0)
    assert abs(state.pan_x - 0.0) < 0.001
    assert abs(state.pan_y - 0.0) < 0.001


def test_crop_zoom_center():
    frame = np.arange(100).reshape(10, 10).astype("uint8")
    zoomed = crop_zoom(np.dstack([frame] * 3), 2.0)
    assert zoomed.shape[0] == 5
    assert zoomed.shape[1] == 5


def test_crop_zoom_out():
    frame = np.ones((10, 10, 3), dtype="uint8") * 255
    zoomed = crop_zoom(frame, 0.5)
    # Zoom out creates a larger frame with black border
    assert zoomed.shape[0] == 20
    assert zoomed.shape[1] == 20
    # Check that original is centered
    assert zoomed[5, 5, 0] == 255
    assert zoomed[0, 0, 0] == 0  # Border is black


def test_crop_zoom_pan():
    frame = np.arange(400).reshape(20, 20).astype("uint8")
    # Zoom in with pan to top-left
    zoomed = crop_zoom(np.dstack([frame] * 3), 2.0, pan_x=0.25, pan_y=0.25)
    assert zoomed.shape[0] == 10
    assert zoomed.shape[1] == 10
