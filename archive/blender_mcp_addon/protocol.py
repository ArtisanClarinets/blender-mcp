"""
Protocol definitions for Blender MCP Addon

Mirrors the protocol definitions from Python server side.
"""

import json
from typing import Any, Dict, Optional


def encode_command(command: Dict[str, Any]) -> bytes:
    """
    Encode a command to bytes using newline-delimited JSON.

    Args:
        command: Command dictionary

    Returns:
        Encoded bytes
    """
    json_str = json.dumps(command) + "\n"
    return json_str.encode("utf-8")


def decode_response(data: bytes) -> Optional[Dict[str, Any]]:
    """
    Decode a response from bytes.

    Args:
        data: Response bytes

    Returns:
        Decoded response dictionary or None if invalid
    """
    try:
        json_str = data.decode("utf-8").strip()
        return json.loads(json_str)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def create_response(
    ok: bool,
    data: Any = None,
    error: Optional[Dict[str, Any]] = None,
    request_id: str = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized response envelope.

    Args:
        ok: Success status
        data: Response data
        error: Error information
        request_id: Request ID for correlation
        meta: Metadata

    Returns:
        Response dictionary
    """
    response = {"ok": ok, "request_id": request_id}

    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    if meta is not None:
        response["meta"] = meta

    return response


def create_success_response(
    data: Any, request_id: str = None, meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a success response."""
    return create_response(ok=True, data=data, request_id=request_id, meta=meta)


def create_error_response(
    code: str, message: str, details: Any = None, request_id: str = None
) -> Dict[str, Any]:
    """Create an error response."""
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return create_response(ok=False, error=error, request_id=request_id)


def parse_command(data: bytes) -> Optional[Dict[str, Any]]:
    """
    Parse a command from bytes.

    Args:
        data: Command bytes

    Returns:
        Parsed command dictionary or None if invalid
    """
    try:
        json_str = data.decode("utf-8").strip()
        command = json.loads(json_str)

        # Validate required fields
        if "type" not in command:
            return None
        if "request_id" not in command:
            return None

        return command
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def get_command_type(command: Dict[str, Any]) -> str:
    """Get the command type."""
    return command.get("type", "")


def get_command_params(command: Dict[str, Any]) -> Dict[str, Any]:
    """Get the command parameters."""
    return command.get("params", {})


def get_request_id(command: Dict[str, Any]) -> str:
    """Get the request ID."""
    return command.get("request_id", "")


def get_idempotency_key(command: Dict[str, Any]) -> Optional[str]:
    """Get the idempotency key if present."""
    return command.get("idempotency_key")
