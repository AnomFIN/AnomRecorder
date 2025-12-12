"""Unit tests for human-friendly formatting helpers."""

from datetime import datetime

import pytest

from src.core.humanize import format_bytes, format_percentage, format_timestamp, format_timestamp_relative


def test_format_bytes_scaling():
    assert format_bytes(0) == "0 B"
    assert format_bytes(1023) == "1023 B"
    assert format_bytes(1024) == "1 KB"
    assert format_bytes(1024 ** 2) == "1 MB"
    assert format_bytes(5 * 1024 ** 3) == "5 GB"


def test_format_bytes_negative():
    with pytest.raises(ValueError):
        format_bytes(-1)


def test_format_percentage():
    assert format_percentage(0, 100) == "0%"
    assert format_percentage(50, 100) == "50%"
    assert format_percentage(150, 100) == "100%"
    assert format_percentage(1, 0) == "0%"


def test_format_timestamp():
    ts = datetime(2024, 2, 29, 12, 30, 45)
    assert format_timestamp(ts) == "2024-02-29 12:30:45"


def test_format_timestamp_relative_today_and_yesterday():
    now = datetime(2025, 12, 10, 15, 0, 0)
    ts_today = datetime(2025, 12, 10, 9, 5, 0)
    ts_yesterday = datetime(2025, 12, 9, 22, 0, 0)
    assert format_timestamp_relative(ts_today, now=now).startswith("tänään ")
    assert format_timestamp_relative(ts_yesterday, now=now).startswith("eilen ")


def test_format_timestamp_relative_days():
    now = datetime(2025, 12, 10, 15, 0, 0)
    ts_4d = datetime(2025, 12, 6, 10, 0, 0)
    assert format_timestamp_relative(ts_4d, now=now) == "4pv sitten"
