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
    min_factor: float = 0.5
    max_factor: float = 4.0
    step: float = 0.25
    # Pan offset in normalized coordinates (0.0 to 1.0)
    pan_x: float = 0.5
    pan_y: float = 0.5

    def zoom_in(self) -> float:
        self.factor = min(self.max_factor, self.factor + self.step)
        return self.factor

    def zoom_out(self) -> float:
        self.factor = max(self.min_factor, self.factor - self.step)
        return self.factor

    def reset(self) -> float:
        self.factor = 1.0
        self.pan_x = 0.5
        self.pan_y = 0.5
        return self.factor
    
    def pan(self, dx: float, dy: float) -> None:
        """Pan by normalized delta. Bounds enforced in crop_zoom."""
        self.pan_x = max(0.0, min(1.0, self.pan_x + dx))
        self.pan_y = max(0.0, min(1.0, self.pan_y + dy))

    def pan(self, dx: float, dy: float) -> None:
        """Pan by delta, clamped to bounds."""
        self.pan_x = max(-1.0, min(1.0, self.pan_x + dx))
        self.pan_y = max(-1.0, min(1.0, self.pan_y + dy))

def crop_zoom(frame: np.ndarray, zoom_factor: float, pan_x: float = 0.5, pan_y: float = 0.5) -> np.ndarray:
    """
    Crop frame based on zoom factor and pan position.
    
    Args:
        frame: Input frame (BGR or RGB)
        zoom_factor: Zoom level. >1.0 zooms in, <1.0 zooms out (adds border), 1.0 is original
        pan_x: Horizontal pan position (0.0=left, 0.5=center, 1.0=right)
        pan_y: Vertical pan position (0.0=top, 0.5=center, 1.0=bottom)
    
    Returns:
        Zoomed/panned frame
    """
    if zoom_factor == 1.0 and pan_x == 0.5 and pan_y == 0.5:
        return frame
    
    h, w = frame.shape[:2]
    
    if zoom_factor < 1.0:
        # Zoom out: add black border
        new_w = max(1, int(w / zoom_factor))
        new_h = max(1, int(h / zoom_factor))
        result = np.zeros((new_h, new_w, frame.shape[2]), dtype=frame.dtype)
        x_offset = (new_w - w) // 2
        y_offset = (new_h - h) // 2
        result[y_offset:y_offset + h, x_offset:x_offset + w] = frame
        return result
    
    # Zoom in: crop with pan
    new_w = max(1, int(w / zoom_factor))
    new_h = max(1, int(h / zoom_factor))
    
    # Calculate center position based on pan
    center_x = int(pan_x * w)
    center_y = int(pan_y * h)
    
    # Calculate crop boundaries
    x0 = center_x - new_w // 2
    y0 = center_y - new_h // 2
    
    # Bound to frame edges
    x0 = max(0, min(w - new_w, x0))
    y0 = max(0, min(h - new_h, y0))
    
    cropped = frame[y0:y0 + new_h, x0:x0 + new_w]
    return cropped


__all__ = ["ZoomState", "crop_zoom"]
