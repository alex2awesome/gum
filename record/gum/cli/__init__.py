"""Command-line interface utilities for the Gum recorder."""

from .background import BackgroundRecorder
from .main import main, parse_args

__all__ = ["BackgroundRecorder", "main", "parse_args"]
