"""Unit tests for human-friendly formatting helpers."""

from datetime import datetime

import pytest

from src.core.humanize import format_bytes, format_percentage, format_timestamp


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
