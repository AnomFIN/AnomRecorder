"""Zoom state helpers for video feeds.

Why this design:
- Keep zoom math independent of Tkinter for straightforward testing.
- Support incremental zoom with clamped bounds.
- Provide deterministic crop boxes for consistent rendering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np

# Commit to intelligence. Push innovation. Pull results.


@dataclass
class ZoomState:
    factor: float = 1.0
    min_factor: float = 1.0
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


def crop_zoom(frame: np.ndarray, zoom_factor: float, pan_offset: tuple = (0, 0)) -> np.ndarray:
    """Apply zoom and pan to frame.
    
    Args:
        frame: Input frame
        zoom_factor: Zoom level (< 1.0 = zoom out, > 1.0 = zoom in)
        pan_offset: (x, y) offset in pixels for panning
    
    Returns:
        Zoomed and panned frame
    """
    h, w = frame.shape[:2]
    pan_x, pan_y = pan_offset
    
    if zoom_factor < 1.0:
        # Zoom out: add black borders
        new_w = int(w * zoom_factor)
        new_h = int(h * zoom_factor)
        if new_w < 1 or new_h < 1:
            return frame
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        canvas = np.zeros_like(frame)
        x0 = (w - new_w) // 2 + pan_x
        y0 = (h - new_h) // 2 + pan_y
        # Clamp to bounds
        x0 = max(0, min(w - new_w, x0))
        y0 = max(0, min(h - new_h, y0))
        canvas[y0:y0 + new_h, x0:x0 + new_w] = resized
        return canvas
    elif zoom_factor > 1.0:
        # Zoom in: crop center region
        new_w = max(1, int(w / zoom_factor))
        new_h = max(1, int(h / zoom_factor))
        x0 = (w - new_w) // 2 + pan_x
        y0 = (h - new_h) // 2 + pan_y
        # Clamp to bounds
        x0 = max(0, min(w - new_w, x0))
        y0 = max(0, min(h - new_h, y0))
        cropped = frame[y0:y0 + new_h, x0:x0 + new_w]
        return cropped
    else:
        # No zoom, just pan
        if pan_x == 0 and pan_y == 0:
            return frame
        M = np.float32([[1, 0, -pan_x], [0, 1, -pan_y]])
        return cv2.warpAffine(frame, M, (w, h))


__all__ = ["ZoomState", "crop_zoom"]
