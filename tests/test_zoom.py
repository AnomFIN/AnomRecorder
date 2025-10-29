"""Tests for zoom state helpers."""

import numpy as np

from src.utils.zoom import ZoomState, crop_zoom


def test_zoom_state_bounds():
    state = ZoomState()
    # Test zoom in
    state.zoom_in()
    assert state.factor == 1.25
    state.zoom_out()
    assert state.factor == 1.0
    # Test zoom out below 1.0
    state.zoom_out()
    assert state.factor == 0.75
    state.zoom_out()
    assert state.factor == 0.5  # min_factor
    state.zoom_out()
    assert state.factor == 0.5  # should stay at min
    # Test zoom in to max
    for _ in range(20):
        state.zoom_in()
    assert state.factor == state.max_factor
    state.reset()
    assert state.factor == 1.0


def test_crop_zoom_center():
    frame = np.arange(100).reshape(10, 10).astype("uint8")
    # Test zoom in
    zoomed = crop_zoom(np.dstack([frame] * 3), 2.0)
    assert zoomed.shape[0] == 5
    assert zoomed.shape[1] == 5
    # Test zoom out
    zoomed_out = crop_zoom(np.dstack([frame] * 3), 0.5)
    assert zoomed_out.shape[0] == 20
    assert zoomed_out.shape[1] == 20
    # Test no zoom
    no_zoom = crop_zoom(np.dstack([frame] * 3), 1.0)
    assert no_zoom.shape[0] == 10
    assert no_zoom.shape[1] == 10
