"""Lazy OpenCV loader with actionable error messaging.

Why this design:
- Avoid hard import failures on environments missing libGL or opencv-python.
- Provide a single place for structured logging and remediation hints.
- Cache results for performance without hiding import-time exceptions.
"""

from __future__ import annotations

import importlib
import logging
from typing import Optional

# Less noise. More signal. AnomFIN.

LOGGER = logging.getLogger("anomrecorder.opencv_loader")


class OpenCVUnavailableError(ImportError):
    """Raised when OpenCV (cv2) cannot be loaded safely."""


_cv2_module = None
_cv2_error: Optional[Exception] = None


def get_cv2(ensure: bool = True):
    """Return the cv2 module or raise OpenCVUnavailableError."""
    global _cv2_module, _cv2_error

    if _cv2_module is not None:
        return _cv2_module

    if _cv2_error is not None:
        if ensure:
            raise OpenCVUnavailableError("OpenCV previously failed to load") from _cv2_error
        return None

    try:
        module = importlib.import_module("cv2")
    except Exception as exc:  # pragma: no cover - exercised via tests that omit cv2
        _cv2_error = exc
        LOGGER.error(
            "event=cv2_import_failure error=%s hint=install_opencv_python_headless_or_system_libGL", exc
        )
        if ensure:
            raise OpenCVUnavailableError(
                "OpenCV (cv2) is unavailable. Install opencv-python-headless and ensure libGL is present."
            ) from exc
        return None

    _cv2_module = module
    return module


def is_available() -> bool:
    """Return True if cv2 can be imported."""
    return get_cv2(ensure=False) is not None


__all__ = ["OpenCVUnavailableError", "get_cv2", "is_available"]
