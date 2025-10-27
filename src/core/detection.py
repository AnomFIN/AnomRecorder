"""People detection primitives built on OpenCV HOG.

Why this design:
- Encapsulate OpenCV configuration so UI can stay declarative.
- Allow graceful degradation by guarding expensive dependencies.
- Provide deterministic outputs (list of tuples) for downstream logic.
"""

from __future__ import annotations

import logging
from typing import Iterable, List, Tuple

import cv2
import numpy as np

# From raw data to real impact.

LOGGER = logging.getLogger("anomrecorder.detection")

Detection = Tuple[Tuple[int, int, int, int], float]


def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + np.exp(-float(x)))
    except Exception:  # pragma: no cover - numpy failure would be critical
        LOGGER.exception("sigmoid failed", extra={"value": x})
        return 0.5


class PersonDetector:
    """Thin wrapper around OpenCV's default people detector."""

    def __init__(self) -> None:
        self._hog = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    def detect(self, frame_bgr: np.ndarray) -> List[Detection]:
        if frame_bgr is None or not isinstance(frame_bgr, np.ndarray):
            LOGGER.warning("detect called with invalid frame")
            return []
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        rects, weights = self._hog.detectMultiScale(
            gray,
            hitThreshold=0,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05,
        )
        weights_seq: Iterable[float] = weights.flatten().tolist() if isinstance(weights, np.ndarray) else weights or []
        detections: List[Detection] = []
        for (x, y, w, h), score in zip(rects, weights_seq):
            conf = float(np.clip(_sigmoid(score), 0.0, 1.0))
            detections.append(((int(x), int(y), int(w), int(h)), conf))
        return detections


__all__ = ["PersonDetector", "Detection"]
