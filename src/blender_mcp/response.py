"""
Response helpers for Blender MCP

Provides utility functions for creating consistent responses
"""

from typing import Any, Dict, Optional
from .protocol import ResponseEnvelope, TelemetryStatus


def ok(
    data: Any = None, meta: Optional[Dict[str, Any]] = None, request_id: str = None
) -> ResponseEnvelope:
    """Create a successful response envelope."""
    return ResponseEnvelope(
        ok=True, data=data, error=None, request_id=request_id, meta=meta
    )


def err(
    code: str, message: str, details: Any = None, request_id: str = None
) -> ResponseEnvelope:
    """Create an error response envelope."""
    return ResponseEnvelope(
        ok=False,
        data=None,
        error={"code": code, "message": message, "details": details},
        request_id=request_id,
        meta=None,
    )


def normalize_exception(e: Exception, request_id: str = None) -> ResponseEnvelope:
    """Normalize an exception into a response envelope."""
    return err(
        code="internal_error",
        message=str(e),
        details={
            "type": type(e).__name__,
            "traceback": None,  # Could add traceback if needed
        },
        request_id=request_id,
    )


def telemetry_event(
    tool_name: str,
    status: TelemetryStatus,
    duration: float,
    request_id: str,
    metadata: dict = None,
):
    """Record a telemetry event."""
    from .telemetry import record_tool_usage

    record_tool_usage(tool_name, status, duration, request_id, metadata)


class ResponseBuilder:
    """Builder for creating consistent responses."""

    def __init__(self, request_id: str = None):
        self.request_id = request_id
        self.start_time = None
        self.tool_name = None

    def start(self, tool_name: str):
        """Start timing a response."""
        self.tool_name = tool_name
        self.start_time = time.time()
        return self

    def success(
        self, data: Any = None, meta: Optional[Dict[str, Any]] = None
    ) -> ResponseEnvelope:
        """Create a successful response with timing."""
        duration = time.time() - self.start_time if self.start_time else 0.0
        telemetry_event(
            self.tool_name, TelemetryStatus.SUCCESS, duration, self.request_id, meta
        )
        return ok(data, meta, self.request_id)

    def error(self, code: str, message: str, details: Any = None) -> ResponseEnvelope:
        """Create an error response with timing."""
        duration = time.time() - self.start_time if self.start_time else 0.0
        telemetry_event(
            self.tool_name,
            TelemetryStatus.FAILURE,
            duration,
            self.request_id,
            {"error_code": code, "error_details": details},
        )
        return err(code, message, details, self.request_id)


# Import time for ResponseBuilder
try:
    import time
except ImportError:
    pass
