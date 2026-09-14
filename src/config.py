"""Compatibility import for the validated application settings.

New code should import from :mod:`src.core.config`. This module intentionally has
no import-time logging, model construction, or provider-specific configuration.
"""

from src.core.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
