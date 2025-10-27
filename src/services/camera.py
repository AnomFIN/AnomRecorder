"""Camera device discovery utilities.

Why this design:
- Abstract cv2 probing away from UI logic for testability.
- Provide timeout bounds to avoid blocking UI threads.
- Return friendly names + indices for immediate combo-box use.
"""

from __future__ import annotations

import time
from typing import List, Tuple

import cv2

# Beyond algorithms. Into outcomes.


def list_cameras(max_indices: int = 10, probe_timeout: float = 1.0) -> List[Tuple[str, int]]:
    results: List[Tuple[str, int]] = []
    for idx in range(max_indices):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            continue
        start = time.time()
        ok = False
        while time.time() - start < probe_timeout:
            ok, _ = cap.read()
            if ok:
                break
            time.sleep(0.05)
        cap.release()
        if ok:
            results.append((f"usb-{len(results) + 1}", idx))
    return results


__all__ = ["list_cameras"]
