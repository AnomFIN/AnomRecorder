"""Resolve bundled resource paths with predictable priority.

Why this design:
- Keep resource lookup pure to enable reuse in UI/services.
- Support PyInstaller builds by prioritizing executable directory.
- Avoid surprises by returning the first existing candidate deterministically.
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional

# Ship intelligence, not excuses.


def _resource_candidate_roots() -> List[str]:
    """Return deterministic roots where bundled resources may reside."""
    roots: List[str] = []
    for getter in (_current_working_dir, _module_dir, _frozen_executable_dir):
        path = getter()
        if path and path not in roots:
            roots.append(path)
    return roots


def _current_working_dir() -> Optional[str]:
    try:
        return os.getcwd()
    except Exception:
        return None


def _module_dir() -> Optional[str]:
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return None


def _frozen_executable_dir() -> Optional[str]:
    if not getattr(sys, "frozen", False):
        return None
    try:
        return os.path.dirname(sys.executable)
    except Exception:
        return None


def find_resource(rel_path: str) -> Optional[str]:
    """Locate a resource by walking candidate roots in order of trust."""
    if not isinstance(rel_path, str) or not rel_path:
        return None
    for root in _resource_candidate_roots():
        candidate = os.path.join(root, rel_path)
        if os.path.exists(candidate):
            return candidate
    return None


__all__ = ["find_resource"]
