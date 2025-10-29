"""Tests for hotkey configuration."""

from src.utils.hotkeys import HotkeyConfig


def test_hotkey_defaults():
    """Test default hotkey configuration."""
    config = HotkeyConfig()
    assert config.start_stop_recording == "space"
    assert config.refresh_live == "r"
    assert config.zoom_in == "plus"
    assert config.zoom_out == "minus"
    assert config.cancel == "Escape"


def test_hotkey_to_dict():
    """Test serialization to dict."""
    config = HotkeyConfig()
    data = config.to_dict()
    assert isinstance(data, dict)
    assert data["start_stop_recording"] == "space"
    assert data["refresh_live"] == "r"


def test_hotkey_from_dict():
    """Test deserialization from dict."""
    data = {
        "start_stop_recording": "s",
        "refresh_live": "f5",
        "zoom_in": "equal",
        "zoom_out": "underscore",
        "cancel": "q",
    }
    config = HotkeyConfig.from_dict(data)
    assert config.start_stop_recording == "s"
    assert config.refresh_live == "f5"
    assert config.zoom_in == "equal"


def test_hotkey_display_text():
    """Test display text generation."""
    config = HotkeyConfig()
    text = config.get_display_text()
    assert "Välilyönti" in text
    assert "Zoomaa" in text
    assert "Panoroi" in text
