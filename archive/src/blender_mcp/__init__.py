"""Blender integration through the Model Context Protocol."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__version__ = "1.5.5"

__all__ = ["__version__", "BlenderConnection", "get_blender_connection"]


def __getattr__(name: str) -> Any:
    if name in {"BlenderConnection", "get_blender_connection"}:
        server = import_module(".server", __name__)
        return getattr(server, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
