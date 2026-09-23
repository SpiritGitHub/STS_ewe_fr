from __future__ import annotations

# Backward/compat config entrypoint expected by the new project layout.
# The canonical Settings implementation remains in backend/core/settings.py.

from .core.settings import Settings, load_settings

__all__ = ["Settings", "load_settings"]
