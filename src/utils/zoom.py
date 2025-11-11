"""Zoom and pan state helpers for video feeds.

Why this design:
- Keep zoom/pan math independent of Tkinter for straightforward testing.
- Support incremental zoom with clamped bounds (including zoom out).
- Provide deterministic crop boxes with explicit validation for safer pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple, Union

import numpy as np

# Commit to intelligence. Push innovation. Pull results.


@dataclass
class ZoomState:
    """Mutable zoom/pan tracker with guard rails for UI bindings."""

    factor: float = 1.0
    min_factor: float = 0.5
    max_factor: float = 4.0
    step: float = 0.25
    pan_x: float = 0.5
    pan_y: float = 0.5

    def zoom_in(self) -> float:
        """Increase zoom respecting the configured maximum."""
        self.factor = min(self.max_factor, self.factor + abs(self.step))
        return self.factor

    def zoom_out(self) -> float:
        """Decrease zoom respecting the configured minimum."""
        self.factor = max(self.min_factor, self.factor - abs(self.step))
        return self.factor

    def reset(self) -> float:
        """Reset zoom factor and pan center."""
        self.factor = 1.0
        self.pan_x = 0.5
        self.pan_y = 0.5
        return self.factor

    def pan(self, dx: float, dy: float) -> Tuple[float, float]:
        """Pan by delta, clamped between 0.0 and 1.0 for normalized coordinates."""
        self.pan_x = max(0.0, min(1.0, self.pan_x + dx))
        self.pan_y = max(0.0, min(1.0, self.pan_y + dy))
        return self.pan_x, self.pan_y


PanInput = Union[float, Tuple[float, float], Sequence[float]]


def _validate_frame(frame: np.ndarray) -> None:
    """Ensure input frames are valid numpy arrays."""
    if not isinstance(frame, np.ndarray):
        raise TypeError("frame must be a numpy.ndarray")
    if frame.ndim < 2:
        raise ValueError("frame must have at least two dimensions")


def _resize_nearest(frame: np.ndarray, new_h: int, new_w: int) -> np.ndarray:
    """Resize using nearest-neighbour sampling to avoid OpenCV dependency."""
    if new_h <= 0 or new_w <= 0:
        raise ValueError("new dimensions must be positive")

    h, w = frame.shape[:2]
    if new_h == h and new_w == w:
        return frame

    y_idx = np.clip(np.round(np.linspace(0, h - 1, new_h)).astype(int), 0, h - 1)
    x_idx = np.clip(np.round(np.linspace(0, w - 1, new_w)).astype(int), 0, w - 1)

    resized = frame[y_idx][:, x_idx]
    return resized


def _parse_pan(pan_x: PanInput, pan_y: float) -> Tuple[float, float, float, float, bool]:
    """Return normalized coords, pixel offsets, and mode flag."""
    if isinstance(pan_x, (tuple, list, np.ndarray)):
        if len(pan_x) != 2:
            raise ValueError("pan tuple must contain two elements")
        offset_x = float(pan_x[0])
        offset_y = float(pan_x[1])
        return 0.5, 0.5, offset_x, offset_y, True

    normalized_x = float(pan_x)
    normalized_y = float(pan_y)
    normalized_x = float(np.clip(normalized_x, 0.0, 1.0))
    normalized_y = float(np.clip(normalized_y, 0.0, 1.0))
    return normalized_x, normalized_y, 0.0, 0.0, False


def crop_zoom(frame: np.ndarray, zoom_factor: float, pan_x: PanInput = 0.5, pan_y: float = 0.5) -> np.ndarray:
    """Return a zoomed/panned copy of the frame with bounds checking."""
    _validate_frame(frame)

    if zoom_factor <= 0:
        raise ValueError("zoom_factor must be positive")

    normalized_x, normalized_y, offset_x, offset_y, is_pixel_mode = _parse_pan(pan_x, pan_y)

    if zoom_factor == 1.0 and not is_pixel_mode and normalized_x == 0.5 and normalized_y == 0.5:
        return frame

    h, w = frame.shape[:2]

    if zoom_factor < 1.0:
        # Zoom out: shrink frame and pad with zeros to keep original shape.
        shrink_w = max(1, int(round(w * zoom_factor)))
        shrink_h = max(1, int(round(h * zoom_factor)))
        scaled = _resize_nearest(frame, shrink_h, shrink_w)

        canvas = np.zeros_like(frame)
        max_x_offset = w - shrink_w
        max_y_offset = h - shrink_h

        if is_pixel_mode:
            x_offset = int(round((max_x_offset / 2.0) + offset_x))
            y_offset = int(round((max_y_offset / 2.0) + offset_y))
        else:
            x_offset = int(round(normalized_x * max_x_offset))
            y_offset = int(round(normalized_y * max_y_offset))

        x_offset = max(0, min(max_x_offset, x_offset))
        y_offset = max(0, min(max_y_offset, y_offset))

        if canvas.ndim == 3:
            canvas[y_offset:y_offset + shrink_h, x_offset:x_offset + shrink_w, :] = scaled
        else:
            canvas[y_offset:y_offset + shrink_h, x_offset:x_offset + shrink_w] = scaled
        return canvas

    # Zoom in: crop using pan center.
    new_w = max(1, int(round(w / zoom_factor)))
    new_h = max(1, int(round(h / zoom_factor)))

    if is_pixel_mode:
        center_x = int(round((w - 1) / 2.0 + offset_x))
        center_y = int(round((h - 1) / 2.0 + offset_y))
    else:
        center_x = int(round(normalized_x * (w - 1)))
        center_y = int(round(normalized_y * (h - 1)))

    x0 = max(0, min(w - new_w, center_x - new_w // 2))
    y0 = max(0, min(h - new_h, center_y - new_h // 2))

    return frame[y0:y0 + new_h, x0:x0 + new_w]


__all__ = ["ZoomState", "crop_zoom"]
