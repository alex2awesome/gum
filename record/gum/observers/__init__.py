"""Observer package orchestrating platform-specific implementations."""

from __future__ import annotations

import sys
from typing import Type

from .base import Observer

Screen: Type[Observer] | None = None
AppleUIInspector = None

if sys.platform == "darwin":
    try:
        from .macos import Screen as _MacScreen  # type: ignore F401
        from .macos import AppleUIInspector as _MacAppleUIInspector  # type: ignore F401
    except Exception:  # pragma: no cover - best effort import guard
        Screen = None
        AppleUIInspector = None
    else:
        Screen = _MacScreen
        AppleUIInspector = _MacAppleUIInspector
else:
    Screen = None
    AppleUIInspector = None

__all__ = ["Observer", "Screen", "AppleUIInspector"]
