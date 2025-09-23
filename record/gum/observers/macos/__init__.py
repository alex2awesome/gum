"""macOS-specific observer implementations."""

from .screen import Screen
from .ui import AppleUIInspector, check_automation_permission_granted

__all__ = ["Screen", "AppleUIInspector", "check_automation_permission_granted"]
