"""Apple-specific application entrypoints and utilities for Gum."""

from .gum_apple_utils import AppleUIInspector, check_automation_permission_granted

__all__ = [
    "AppleUIInspector",
    "check_automation_permission_granted",
]
