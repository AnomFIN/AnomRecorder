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
    min_factor: float = 0.5  # Allow zoom out
    max_factor: float = 4.0
    step: float = 0.25
    pan_x: float = 0.0  # Pan offset in normalized coords (-1 to 1)
    pan_y: float = 0.0
    focus_x: float = 0.5  # Focus point for zoom (0 to 1)
    focus_y: float = 0.5

    def zoom_in(self) -> float:
        self.factor = min(self.max_factor, self.factor + self.step)
        return self.factor

    def zoom_out(self) -> float:
        self.factor = max(self.min_factor, self.factor - self.step)
        return self.factor

    def reset(self) -> float:
        self.factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.focus_x = 0.5
        self.focus_y = 0.5
        return self.factor

    def pan(self, dx: float, dy: float) -> None:
        """Pan by delta, clamped to bounds."""
        self.pan_x = max(-1.0, min(1.0, self.pan_x + dx))
        self.pan_y = max(-1.0, min(1.0, self.pan_y + dy))

    def set_focus(self, x: float, y: float) -> None:
        """Set focus point for centered zoom (normalized 0-1)."""
        self.focus_x = max(0.0, min(1.0, x))
        self.focus_y = max(0.0, min(1.0, y))


def crop_zoom(frame: np.ndarray, zoom_factor: float, pan_x: float = 0.0, pan_y: float = 0.0, 
              focus_x: float = 0.5, focus_y: float = 0.5) -> np.ndarray:
    """
    Crop and zoom frame with panning support.
    
    Args:
        frame: Input frame
        zoom_factor: Zoom factor (< 1.0 for zoom out, > 1.0 for zoom in)
        pan_x: Pan offset in X direction (-1 to 1)
        pan_y: Pan offset in Y direction (-1 to 1)
        focus_x: Focus point X for zoom (0 to 1)
        focus_y: Focus point Y for zoom (0 to 1)
    """
    h, w = frame.shape[:2]
    
    # For zoom out, add padding and scale down
    if zoom_factor < 1.0:
        new_h = int(h * zoom_factor)
        new_w = int(w * zoom_factor)
        if new_h < 1 or new_w < 1:
            return frame
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        # Create padded frame
        result = np.zeros_like(frame)
        y_offset = (h - new_h) // 2
        x_offset = (w - new_w) // 2
        result[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
        return result
    
    # For zoom in, crop with focus and pan
    new_w = max(1, int(w / zoom_factor))
    new_h = max(1, int(h / zoom_factor))
    
    # Calculate center based on focus point
    center_x = int(w * focus_x)
    center_y = int(h * focus_y)
    
    # Apply pan offset
    pan_offset_x = int(pan_x * w * 0.3)  # 30% of width max pan
    pan_offset_y = int(pan_y * h * 0.3)  # 30% of height max pan
    
    center_x += pan_offset_x
    center_y += pan_offset_y
    
    # Calculate crop bounds
    x0 = center_x - new_w // 2
    y0 = center_y - new_h // 2
    
    # Clamp to frame bounds
    x0 = max(0, min(w - new_w, x0))
    y0 = max(0, min(h - new_h, y0))
    
    cropped = frame[y0:y0 + new_h, x0:x0 + new_w]
    return cropped


__all__ = ["ZoomState", "crop_zoom"]
