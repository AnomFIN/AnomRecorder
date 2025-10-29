"""Hotkey management and bindings.

Why this design:
- Centralize hotkey configuration for easy customization.
- Support persistence to settings.
- Provide clear mapping of actions to keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

# Deploy fast. Scale faster.


@dataclass
class HotkeyConfig:
    """Configuration for application hotkeys."""
    start_stop_recording: str = "space"
    refresh_live: str = "r"
    zoom_in: str = "plus"
    zoom_out: str = "minus"
    cancel: str = "Escape"
    pan_up: str = "Up"
    pan_down: str = "Down"
    pan_left: str = "Left"
    pan_right: str = "Right"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for persistence."""
        return {
            "start_stop_recording": self.start_stop_recording,
            "refresh_live": self.refresh_live,
            "zoom_in": self.zoom_in,
            "zoom_out": self.zoom_out,
            "cancel": self.cancel,
            "pan_up": self.pan_up,
            "pan_down": self.pan_down,
            "pan_left": self.pan_left,
            "pan_right": self.pan_right,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> HotkeyConfig:
        """Create from dictionary."""
        return cls(
            start_stop_recording=data.get("start_stop_recording", "space"),
            refresh_live=data.get("refresh_live", "r"),
            zoom_in=data.get("zoom_in", "plus"),
            zoom_out=data.get("zoom_out", "minus"),
            cancel=data.get("cancel", "Escape"),
            pan_up=data.get("pan_up", "Up"),
            pan_down=data.get("pan_down", "Down"),
            pan_left=data.get("pan_left", "Left"),
            pan_right=data.get("pan_right", "Right"),
        )
    
    def get_display_text(self) -> str:
        """Get Finnish display text for hotkeys."""
        return f"""Pikanäppäimet:
  Välilyönti: Aloita/lopeta tallennus
  R: Päivitä Live-näkymä
  +/-: Zoomaa sisään/ulos
  Nuolinäppäimet: Panoroi
  Esc: Peruuta/lopeta
  Ctrl+Hiiren rulla: Zoomaa"""


__all__ = ["HotkeyConfig"]
