"""Zoom and pan state helpers for video feeds.

Why this design:
- Keep zoom/pan math independent of Tkinter for straightforward testing.
- Support incremental zoom with clamped bounds (including zoom out).
- Support panning with boundary constraints.
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
    min_factor: float = 0.5  # Allow zoom out to 0.5x
    max_factor: float = 4.0
    step: float = 0.25
    pan_x: float = 0.0  # Pan offset as fraction of frame width (-1 to 1)
    pan_y: float = 0.0  # Pan offset as fraction of frame height (-1 to 1)

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
        return self.factor
    
    def pan(self, dx: float, dy: float) -> None:
        """Pan by dx, dy (as fraction of frame size). Constrained to bounds."""
        self.pan_x = max(-1.0, min(1.0, self.pan_x + dx))
        self.pan_y = max(-1.0, min(1.0, self.pan_y + dy))
    
    def pan_left(self, step: float = 0.1) -> None:
        self.pan(-step, 0.0)
    
    def pan_right(self, step: float = 0.1) -> None:
        self.pan(step, 0.0)
    
    def pan_up(self, step: float = 0.1) -> None:
        self.pan(0.0, -step)
    
    def pan_down(self, step: float = 0.1) -> None:
        self.pan(0.0, step)


def crop_zoom(frame: np.ndarray, zoom_factor: float, pan_x: float = 0.0, pan_y: float = 0.0) -> np.ndarray:
    """Crop and zoom frame with optional pan offset.
    
    Args:
        frame: Input frame (H, W, C)
        zoom_factor: Zoom factor (0.5 = zoom out, 1.0 = normal, 2.0 = zoom in)
        pan_x: Pan offset in x as fraction of frame width (-1 to 1)
        pan_y: Pan offset in y as fraction of frame height (-1 to 1)
    
    Returns:
        Cropped/zoomed frame
    """
    h, w = frame.shape[:2]
    
    # For zoom < 1.0, we need to add padding
    if zoom_factor < 1.0:
        # Calculate new dimensions
        new_h = int(h / zoom_factor)
        new_w = int(w / zoom_factor)
        
        # Create padded frame (black border)
        pad_top = (new_h - h) // 2
        pad_bottom = new_h - h - pad_top
        pad_left = (new_w - w) // 2
        pad_right = new_w - w - pad_left
        
        padded = np.pad(frame, ((pad_top, pad_bottom), (pad_left, pad_right), (0, 0)), mode='constant', constant_values=0)
        return padded
    
    # For zoom >= 1.0, crop the frame
    new_w = max(1, int(w / zoom_factor))
    new_h = max(1, int(h / zoom_factor))
    
    # Calculate center position with pan offset
    center_x = w // 2 + int(pan_x * w * 0.5)
    center_y = h // 2 + int(pan_y * h * 0.5)
    
    # Calculate crop box
    x0 = center_x - new_w // 2
    y0 = center_y - new_h // 2
    
    # Constrain to frame bounds
    x0 = max(0, min(w - new_w, x0))
    y0 = max(0, min(h - new_h, y0))
    
    cropped = frame[y0:y0 + new_h, x0:x0 + new_w]
    return cropped


__all__ = ["ZoomState", "crop_zoom"]
