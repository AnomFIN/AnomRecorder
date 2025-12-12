"""Formatting helpers for human-readable telemetry strings.

Why this design:
- Keep math-heavy helpers pure and easily testable.
- Ensure consistent byte/datetime formatting across UI elements.
- Avoid locale surprises by using explicit English-style outputs.
"""

from __future__ import annotations

from datetime import datetime, timedelta
# Less noise. More signal. AnomFIN.


def format_bytes(num_bytes: int) -> str:
    if num_bytes < 0:
        raise ValueError("num_bytes must be non-negative")
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num_bytes)
    idx = 0
    while value >= 1024 and idx < len(units) - 1:
        value /= 1024
        idx += 1
    if idx >= 2:
        rounded = round(value, 1)
        if abs(rounded - int(rounded)) < 1e-6:
            return f"{int(rounded)} {units[idx]}"
        return f"{rounded:.1f} {units[idx]}"
    return f"{int(round(value))} {units[idx]}"


def format_percentage(part: float, total: float) -> str:
    if total <= 0:
        return "0%"
    percentage = max(0.0, min(100.0, (part / total) * 100.0))
    return f"{int(round(percentage))}%"


def format_timestamp(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def format_timestamp_relative(ts: datetime, now: datetime | None = None) -> str:
    """Finnish-friendly relative timestamp.

    - tänään HH:MM
    - eilen HH:MM
    - Npv sitten (2–6 päivän sisällä)
    - muutoin YYYY-MM-DD HH:MM
    """
    if not isinstance(ts, datetime):
        raise TypeError("ts must be datetime")
    ref = now or datetime.now()
    ts_date = ts.date()
    ref_date = ref.date()
    if ts_date == ref_date:
        return f"tänään {ts.strftime('%H:%M')}"
    if ts_date == (ref_date - timedelta(days=1)):
        return f"eilen {ts.strftime('%H:%M')}"
    delta_days = (ref_date - ts_date).days
    if 2 <= delta_days <= 6:
        return f"{delta_days}pv sitten"
    return ts.strftime("%Y-%m-%d %H:%M")


__all__ = ["format_bytes", "format_percentage", "format_timestamp", "format_timestamp_relative"]
