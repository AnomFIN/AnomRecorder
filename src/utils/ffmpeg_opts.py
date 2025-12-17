"""Helpers to tweak OpenCV's FFmpeg capture options for RTSP/HTTP streams.

OpenCV (FFmpeg backend) supports an environment variable
`OPENCV_FFMPEG_CAPTURE_OPTIONS` with a list of key/value pairs formatted as
``key;value|key;value|...``. Example:

  rtsp_transport;tcp|rtsp_flags;prefer_tcp|stimeout;10000000|rw_timeout;15000000

We apply sensible defaults to avoid long 30s timeouts and reduce latency.
"""

from __future__ import annotations

import os
from typing import Optional


def _merge_options(base: str, extra: str) -> str:
    """Merge two option strings (key;value pairs separated by '|').

    Later values override earlier ones.
    """
    def parse(s: str) -> dict[str, str]:
        pairs: dict[str, str] = {}
        if not s:
            return pairs
        # Split pairs by '|', then each pair as 'key;value'
        for token in s.split("|"):
            token = token.strip()
            if not token:
                continue
            if ";" not in token:
                # Ignore malformed entries
                continue
            k, v = token.split(";", 1)
            pairs[k] = v
        return pairs

    merged = parse(base)
    merged.update(parse(extra))
    # Flatten back into 'k;v|k;v'
    parts: list[str] = [f"{k};{v}" for k, v in merged.items()]
    return "|".join(parts)


def apply_rtsp_defaults(
    prefer_tcp: bool = True,
    stimeout_ms: int = 10000,
    rw_timeout_ms: int = 15000,
    max_delay_us: int = 500_000,
    buffer_size_bytes: int = 1_048_576,
    reorder_queue_size: int = 0,
) -> None:
    """Apply default FFmpeg capture options to lower latency and timeouts.

    Safe to call multiple times. Only affects the current process.
    """
    # Build as 'key;value' tokens and join with '|'
    tokens: list[str] = []
    if prefer_tcp:
        tokens += ["rtsp_transport;tcp", "rtsp_flags;prefer_tcp"]
    if stimeout_ms:
        tokens += [f"stimeout;{int(stimeout_ms) * 1000}"]  # microseconds
    if rw_timeout_ms:
        tokens += [f"rw_timeout;{int(rw_timeout_ms) * 1000}"]  # microseconds
    if max_delay_us:
        tokens += [f"max_delay;{int(max_delay_us)}"]
    if buffer_size_bytes:
        tokens += [f"buffer_size;{int(buffer_size_bytes)}"]
    if reorder_queue_size is not None:
        tokens += [f"reorder_queue_size;{int(reorder_queue_size)}"]
    extra = "|".join(tokens)
    current = os.environ.get("OPENCV_FFMPEG_CAPTURE_OPTIONS", "")
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = _merge_options(current, extra)


__all__ = ["apply_rtsp_defaults"]
