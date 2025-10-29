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
    assert state.factor == 0.75
    state.zoom_out()
    assert state.factor == 0.5  # Min factor
    state.zoom_out()
    assert state.factor == 0.5  # Stays at min
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


def test_zoom_out_adds_padding():
    frame = np.ones((100, 100, 3), dtype="uint8") * 255
    zoomed = crop_zoom(frame, 0.5)
    # Zoom out should add padding, making frame larger
    assert zoomed.shape[0] == 200
    assert zoomed.shape[1] == 200


def test_pan_constrains_bounds():
    state = ZoomState()
    state.pan(2.0, 2.0)  # Try to pan beyond bounds
    assert state.pan_x == 1.0  # Constrained to max
    assert state.pan_y == 1.0
    state.pan(-3.0, -3.0)
    assert state.pan_x == -1.0  # Constrained to min
    assert state.pan_y == -1.0


def test_pan_directions():
    state = ZoomState()
    state.pan_right()
    assert state.pan_x > 0
    state.pan_left()
    state.pan_left()
    assert state.pan_x < 0
    state.reset()
    state.pan_down()
    assert state.pan_y > 0
    state.pan_up()
    state.pan_up()
    assert state.pan_y < 0
