"""Camera auto-reconnect with exponential backoff.

Why this design:
- Handle camera disconnects gracefully without blocking UI.
- Use exponential backoff to avoid hammering the system.
- Provide user notifications of reconnect attempts.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

# Scale solutions. Not frustrations.

LOGGER = logging.getLogger("anomrecorder.reconnect")


@dataclass
class ReconnectState:
    """State for camera reconnection logic."""
    enabled: bool = True
    max_attempts: int = 5
    base_delay: float = 1.0
    max_delay: float = 30.0
    
    attempt: int = 0
    last_attempt_time: float = 0.0
    
    def should_attempt(self) -> bool:
        """Check if we should attempt reconnection."""
        if not self.enabled:
            return False
        if self.attempt >= self.max_attempts:
            return False
        
        now = time.time()
        delay = min(self.base_delay * (2 ** self.attempt), self.max_delay)
        
        if now - self.last_attempt_time >= delay:
            return True
        return False
    
    def record_attempt(self) -> None:
        """Record a reconnection attempt."""
        self.attempt += 1
        self.last_attempt_time = time.time()
        LOGGER.info("reconnect-attempt", extra={"attempt": self.attempt})
    
    def reset(self) -> None:
        """Reset reconnection state after successful connection."""
        self.attempt = 0
        self.last_attempt_time = 0.0
    
    def get_status_text(self) -> str:
        """Get Finnish status text."""
        if not self.enabled:
            return "Automaattinen uudelleenyhdistäminen: Pois päältä"
        if self.attempt == 0:
            return "Yhdistetty"
        if self.attempt >= self.max_attempts:
            return f"Yhdistäminen epäonnistui {self.max_attempts} yrityksen jälkeen"
        return f"Yritetään uudelleenyhdistää... (yritys {self.attempt}/{self.max_attempts})"


__all__ = ["ReconnectState"]
