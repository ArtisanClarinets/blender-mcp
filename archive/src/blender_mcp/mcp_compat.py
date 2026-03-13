"""Compatibility imports for FastMCP.

Falls back to minimal stubs in unit-test or constrained environments where the
external mcp package cannot be imported cleanly.
"""

from __future__ import annotations

from typing import Any, Callable

try:  # pragma: no cover - exercised indirectly when dependency is available
    from mcp.server.fastmcp import Context, FastMCP, Image
except Exception:  # pragma: no cover - used in tests when mcp import is unstable
    class Context:  # type: ignore[override]
        pass

    class Image:  # type: ignore[override]
        def __init__(self, data: bytes | None = None, format: str | None = None):
            self.data = data
            self.format = format

    class FastMCP:  # type: ignore[override]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

        @staticmethod
        def tool() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            return lambda func: func
