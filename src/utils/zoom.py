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


def crop_zoom(frame: np.ndarray, zoom_factor: float) -> np.ndarray:
    """Apply zoom to frame. Values >1.0 zoom in (crop), <1.0 zoom out (add border)."""
    if zoom_factor == 1.0:
        return frame
    
    h, w = frame.shape[:2]
    
    if zoom_factor > 1.0:
        # Zoom in: crop the frame
        new_w = max(1, int(w / zoom_factor))
        new_h = max(1, int(h / zoom_factor))
        x0 = max(0, (w - new_w) // 2)
        y0 = max(0, (h - new_h) // 2)
        cropped = frame[y0:y0 + new_h, x0:x0 + new_w]
        return cropped
    else:
        # Zoom out: add border around the frame
        new_w = int(w / zoom_factor)
        new_h = int(h / zoom_factor)
        # Create black background
        result = np.zeros((new_h, new_w, frame.shape[2] if len(frame.shape) == 3 else 1), dtype=frame.dtype)
        # Center the original frame
        x0 = (new_w - w) // 2
        y0 = (new_h - h) // 2
        result[y0:y0 + h, x0:x0 + w] = frame
        return result


__all__ = ["ZoomState", "crop_zoom"]
