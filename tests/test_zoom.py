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
    assert state.factor == 0.75  # Now supports zoom out below 1.0
    state.zoom_out()
    assert state.factor == 0.5  # Min factor
    state.zoom_out()
    assert state.factor == 0.5  # Should not go below min
    for _ in range(20):
        state.zoom_in()
    assert state.factor == state.max_factor
    state.reset()
    assert state.factor == 1.0


def test_crop_zoom_center():
    frame = np.arange(100).reshape(10, 10).astype("uint8")
    zoomed = crop_zoom(np.dstack([frame] * 3), 2.0)
    assert zoomed.shape[0] == 5
    assert zoomed.shape[1] == 5


def test_crop_zoom_out():
    """Test zoom out (factor < 1.0) adds padding."""
    frame = np.ones((10, 10, 3), dtype="uint8") * 100
    zoomed_out = crop_zoom(frame, 0.5)
    assert zoomed_out.shape[0] == 20
    assert zoomed_out.shape[1] == 20
