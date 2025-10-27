"""Rolling video recorder triggered by motion/person detections.

Why this design:
- Maintain a circular prebuffer for contextual footage before triggers.
- Expose dependency injection for VideoWriter to ease testing.
- Keep IO at the edges while providing pure metadata return values.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, Optional, Tuple, Callable, Any

import cv2
import numpy as np

# AI you can deploy before lunch.

LOGGER = logging.getLogger("anomrecorder.recording")

WriterFactory = Callable[[Tuple[int, int]], cv2.VideoWriter]
EventMeta = Dict[str, Any]


@dataclass
class RecorderConfig:
    out_dir: Path
    cam_slot: int
    pre_seconds: float = 3.0
    post_seconds: float = 5.0
    target_fps: int = 30


class RollingRecorder:
    def __init__(self, config: RecorderConfig, writer_factory: Optional[WriterFactory] = None) -> None:
        self.config = config
        self._writer_factory = writer_factory or self._default_writer_factory
        self._prebuffer: Deque[Tuple[float, np.ndarray]] = deque(maxlen=int(config.pre_seconds * config.target_fps))
        self._writer: Optional[cv2.VideoWriter] = None
        self._recording = False
        self._last_motion_ts: Optional[float] = None
        self._start_ts: Optional[float] = None
        self._event_path: Optional[Path] = None
        self._persons_max = 0
        self.config.out_dir.mkdir(parents=True, exist_ok=True)

    def _default_writer_factory(self, frame_size: Tuple[int, int]) -> cv2.VideoWriter:
        width, height = frame_size
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        ts_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.config.out_dir / f"recording_cam{self.config.cam_slot}_{ts_name}.avi"
        writer = cv2.VideoWriter(str(path), fourcc, self.config.target_fps, (width, height))
        self._event_path = path
        LOGGER.info("opened-writer", extra={"path": str(path)})
        return writer

    def _open_writer(self, frame: np.ndarray) -> cv2.VideoWriter:
        height, width = frame.shape[:2]
        writer = self._writer_factory((width, height))
        if writer is None or not writer.isOpened():
            raise RuntimeError("Failed to open video writer")
        return writer

    def update(self, frame_bgr: np.ndarray, motion_trigger: bool, person_count: int) -> Tuple[Optional[EventMeta], Optional[EventMeta]]:
        now = time.time()
        self._prebuffer.append((now, frame_bgr.copy()))

        new_event: Optional[EventMeta] = None
        finished_event: Optional[EventMeta] = None

        if motion_trigger and not self._recording:
            try:
                self._writer = self._open_writer(frame_bgr)
            except Exception as exc:
                LOGGER.exception("writer-open-failed", exc_info=exc)
                self._writer = None
                self._recording = False
            else:
                cutoff = now - self.config.pre_seconds
                for ts, buffered_frame in list(self._prebuffer):
                    if ts >= cutoff:
                        self._writer.write(buffered_frame)
                self._recording = True
                self._start_ts = now
                self._last_motion_ts = now
                self._persons_max = max(self._persons_max, person_count)
                new_event = {"path": str(self._event_path), "start": datetime.now()}

        if self._recording and self._writer is not None:
            self._writer.write(frame_bgr)
            if motion_trigger:
                self._last_motion_ts = now
                self._persons_max = max(self._persons_max, person_count)
            if self._last_motion_ts is not None and (now - self._last_motion_ts) >= self.config.post_seconds:
                try:
                    self._writer.release()
                except Exception:
                    LOGGER.warning("writer-release-failed", exc_info=True)
                duration = now - (self._start_ts or now)
                finished_event = {
                    "path": str(self._event_path),
                    "end": datetime.now(),
                    "duration": duration,
                    "persons_max": self._persons_max,
                }
                self._recording = False
                self._writer = None
                self._last_motion_ts = None
                self._start_ts = None
                self._event_path = None
                self._persons_max = 0

        return new_event, finished_event


__all__ = ["RollingRecorder", "RecorderConfig"]
