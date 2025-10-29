"""Zoom state helpers for video feeds.

Why this design:
- Keep zoom math independent of Tkinter for straightforward testing.
- Support incremental zoom with clamped bounds.
- Provide deterministic crop boxes for consistent rendering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

# Commit to intelligence. Push innovation. Pull results.


@dataclass
class ZoomState:
    factor: float = 1.0
    min_factor: float = 0.5
    max_factor: float = 4.0
    step: float = 0.25

    def zoom_in(self) -> float:
        self.factor = min(self.max_factor, self.factor + self.step)
        return self.factor

    def zoom_out(self) -> float:
        self.factor = max(self.min_factor, self.factor - self.step)
        return self.factor

    def reset(self) -> float:
        self.factor = 1.0
        return self.factor


def crop_zoom(frame: np.ndarray, zoom_factor: float, pan_x: int = 0, pan_y: int = 0) -> np.ndarray:
    """Crop and zoom frame with optional panning.
    
    Args:
        frame: Input frame
        zoom_factor: Zoom factor (>1.0 zooms in, <1.0 zooms out, 1.0 no change)
        pan_x: Pan offset in X direction (pixels)
        pan_y: Pan offset in Y direction (pixels)
    """
    if zoom_factor == 1.0 and pan_x == 0 and pan_y == 0:
        return frame
    
    h, w = frame.shape[:2]
    
    if zoom_factor > 1.0:
        # Zoom in: crop center region
        new_w = max(1, int(w / zoom_factor))
        new_h = max(1, int(h / zoom_factor))
        x0 = max(0, min(w - new_w, (w - new_w) // 2 + pan_x))
        y0 = max(0, min(h - new_h, (h - new_h) // 2 + pan_y))
        cropped = frame[y0:y0 + new_h, x0:x0 + new_w]
        return cropped
    elif zoom_factor < 1.0:
        # Zoom out: add padding
        new_w = int(w / zoom_factor)
        new_h = int(h / zoom_factor)
        pad_x = (new_w - w) // 2
        pad_y = (new_h - h) // 2
        padded = np.zeros((new_h, new_w, frame.shape[2]), dtype=frame.dtype)
        padded[pad_y:pad_y + h, pad_x:pad_x + w] = frame
        return padded
    else:
        return frame


__all__ = ["ZoomState", "crop_zoom"]
