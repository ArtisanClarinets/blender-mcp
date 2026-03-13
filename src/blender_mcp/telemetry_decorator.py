"""Telemetry decorator for Blender MCP tools."""

from __future__ import annotations

import functools
import inspect
import logging
import time
from typing import Any, Callable

from .telemetry import TelemetryStatus, record_tool_usage

logger = logging.getLogger("blender-mcp-telemetry")



def telemetry_tool(tool_name: str):
    """Decorator to add telemetry tracking to MCP tools."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = False
            error: str | None = None
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as exc:
                error = str(exc)
                raise
            finally:
                duration_sec = time.time() - start_time
                try:
                    record_tool_usage(
                        tool_name,
                        TelemetryStatus.SUCCESS if success else TelemetryStatus.FAILURE,
                        duration_sec,
                        metadata={"error": error} if error else None,
                    )
                except Exception as log_error:  # pragma: no cover
                    logger.debug("Failed to record telemetry: %s", log_error)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            success = False
            error: str | None = None
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as exc:
                error = str(exc)
                raise
            finally:
                duration_sec = time.time() - start_time
                try:
                    record_tool_usage(
                        tool_name,
                        TelemetryStatus.SUCCESS if success else TelemetryStatus.FAILURE,
                        duration_sec,
                        metadata={"error": error} if error else None,
                    )
                except Exception as log_error:  # pragma: no cover
                    logger.debug("Failed to record telemetry: %s", log_error)

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
