"""Manages the connection to the Blender MCP addon."""

import socket
import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from ..exceptions import BlenderMCPError, ConnectionError, CommandError
from ..logging_config import LogContext, get_logger
from ..resilience import CircuitBreaker, CircuitBreakerOpen, build_retry
from ..schemas import has_command_schema, validate_command_payload, ValidationError

logger = get_logger(__name__)

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
CIRCUIT_BREAKER_OPEN_MESSAGE = (
    "Connection to Blender temporarily unavailable after repeated failures"
)

def _looks_like_base64_payload(value: str) -> bool:
    """Checks if a string looks like a base64 payload."""
    if len(value) < 128 or len(value) % 4 != 0:
        return False

    allowed = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r"
    )
    return all(char in allowed for char in value)

def _summarize_log_value(value: Any, *, key: Optional[str] = None) -> Any:
    """Summarizes a value for logging purposes."""
    if isinstance(value, dict):
        return {
            str(item_key): _summarize_log_value(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }

    if isinstance(value, list):
        if len(value) > 10:
            return {"type": "list", "count": len(value)}
        return [_summarize_log_value(item, key=key) for item in value]

    if isinstance(value, tuple):
        if len(value) > 10:
            return {"type": "tuple", "count": len(value)}
        return tuple(_summarize_log_value(item, key=key) for item in value)

    if isinstance(value, bytes):
        return {"type": "bytes", "size": len(value)}

    if not isinstance(value, str):
        return value

    normalized_key = (key or "").lower()
    if normalized_key == "code":
        return {"type": "code", "length": len(value)}

    if "path" in normalized_key or normalized_key.endswith("file"):
        return {"type": "path", "name": os.path.basename(value)}

    if _looks_like_base64_payload(value):
        return {"type": "base64", "length": len(value)}

    if len(value) > 200:
        return {"type": "text", "length": len(value)}

    return value

def _summarize_command_params_for_logging(params: Dict[str, Any]) -> Dict[str, Any]:
    """Summarizes command parameters for logging."""
    return {
        key: _summarize_log_value(value, key=key)
        for key, value in (params or {}).items()
    }

@dataclass
class BlenderConnection:
    """A resilient connection to the Blender MCP addon.

    Args:
        host: The host to connect to.
        port: The port to connect to.
        connect_timeout: The timeout for establishing a connection.
        response_timeout: The timeout for receiving a response.
        sock: The socket object.
        circuit_breaker: The circuit breaker for handling connection failures.
    """

    host: str
    port: int
    connect_timeout: float = 10.0
    response_timeout: float = 180.0
    sock: Optional[socket.socket] = None
    circuit_breaker: CircuitBreaker = field(
        default_factory=lambda: CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5.0,
            expected_exceptions=(
                ConnectionError,
                TimeoutError,
                socket.timeout,
                BrokenPipeError,
                ConnectionResetError,
                OSError,
            ),
        )
    )

    def _invalidate_socket(self) -> None:
        """Closes and invalidates the current socket."""
        if self.sock is None:
            return

        try:
            self.sock.close()
        except Exception as error:
            logger.warning("Failed to close Blender socket", error=str(error))
        finally:
            self.sock = None

    def _retry_strategy(self) -> Any:
        """Returns a retry strategy for connecting to Blender."""
        return build_retry(
            attempts=2,
            min_wait=0.1,
            max_wait=0.5,
            retry_exceptions=(
                ConnectionError,
                TimeoutError,
                socket.timeout,
                BrokenPipeError,
                ConnectionResetError,
                OSError,
            ),
        )

    def _ensure_connected(self) -> None:
        """Ensures that a connection to Blender is established."""
        if self.sock:
            return

        if self.connect():
            return

        if not self.circuit_breaker.allow_request():
            raise ConnectionError(CIRCUIT_BREAKER_OPEN_MESSAGE)

        raise ConnectionError("Not connected to Blender")

    def _connect_once(self) -> None:
        """Establishes a single connection to Blender."""
        self._invalidate_socket()
        candidate = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        candidate.settimeout(self.connect_timeout)

        try:
            candidate.connect((self.host, self.port))
        except OSError as error:
            candidate.close()
            raise ConnectionError(str(error)) from error

        self.sock = candidate

    def connect(self) -> bool:
        """Connects to the Blender addon socket server.

        Returns:
            True if the connection was successful, False otherwise.
        """
        if self.sock:
            return True

        if not self.circuit_breaker.allow_request():
            logger.warning(
                "Blender connection blocked by open circuit",
                host=self.host,
                port=self.port,
            )
            return False

        try:
            self._retry_strategy()(self._connect_once)
            self.circuit_breaker.record_success()
            logger.info("Connected to Blender", host=self.host, port=self.port)
            return True
        except Exception as error:
            self.circuit_breaker.record_failure(error)
            self._invalidate_socket()
            logger.error(
                "Failed to connect to Blender",
                host=self.host,
                port=self.port,
                error=str(error),
            )
            return False

    def disconnect(self) -> None:
        """Disconnects from the Blender addon."""
        self._invalidate_socket()

    def receive_full_response(self, sock: socket.socket, buffer_size: int = 8192) -> bytes:
        """Receives a newline-delimited JSON response from the socket."""
        buffer = bytearray()
        sock.settimeout(self.response_timeout)

        try:
            while True:
                chunk = sock.recv(buffer_size)
                if not chunk:
                    if not buffer:
                        raise ConnectionError(
                            "Connection closed before receiving any data"
                        )
                    break

                buffer.extend(chunk)
                if b"\n" in buffer:
                    line, _, _ = bytes(buffer).partition(b"\n")
                    logger.info("Received complete response", bytes=len(line))
                    return line
        except socket.timeout as e:
            logger.warning("Socket timeout during line receive")
            raise ConnectionError("Timeout waiting for Blender response") from e
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error("Socket connection error during receive", error=str(e))
            raise ConnectionError("Socket connection error") from e
        except Exception as e:
            logger.error("Error during receive", error=str(e))
            raise BlenderMCPError("Error during receive") from e

        if not buffer:
            raise ConnectionError("No data received")

        raise ConnectionError("Incomplete newline-delimited JSON response received")

    def _send_command_once(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Sends a single command to Blender and returns the response."""
        self._ensure_connected()

        with LogContext(
            logger,
            component="socket_command",
            command_type=command["type"],
            request_id=command["request_id"],
        ) as command_logger:
            try:
                command_logger.info(
                    "Sending command",
                    params=_summarize_command_params_for_logging(command["params"]),
                )
                self.sock.sendall((json.dumps(command) + "\n").encode("utf-8"))
                self.sock.settimeout(self.response_timeout)
                response_data = self.receive_full_response(self.sock)
                response = json.loads(response_data.decode("utf-8"))
                command_logger.info(
                    "Received command response",
                    response_request_id=response.get("request_id", "unknown"),
                )
            except socket.timeout as error:
                self._invalidate_socket()
                raise ConnectionError(
                    "Timeout waiting for Blender response - try simplifying your request"
                ) from error
            except (
                ConnectionError,
                BrokenPipeError,
                ConnectionResetError,
                OSError,
            ) as error:
                self._invalidate_socket()
                raise ConnectionError(
                    f"Connection to Blender lost: {str(error)}"
                ) from error

        response_request_id = response.get("request_id")
        if response_request_id not in (None, "", command["request_id"]):
            raise CommandError(
                f"Mismatched response request_id: expected {command['request_id']}, got {response_request_id}"
            )

        if "ok" in response:
            if not response.get("ok"):
                error = response.get("error") or {}
                logger.error(
                    "Blender returned error response", error=error.get("message")
                )
                raise CommandError(error.get("message", "Unknown error from Blender"))
            return response.get("data", {})

        if response.get("status") == "error":
            logger.error(
                "Blender returned legacy error response", error=response.get("message")
            )
            raise CommandError(response.get("message", "Unknown error from Blender"))

        return response.get("result", response)

    def send_command(
        self,
        command_type: str,
        params: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sends a command to Blender and returns the response."""
        self._ensure_connected()

        validated_params = params or {}
        if has_command_schema(command_type):
            try:
                validated_params = validate_command_payload(
                    command_type, validated_params
                ).model_dump(exclude_none=True)
            except ValidationError as error:
                raise ValueError(
                    f"Invalid payload for command '{command_type}': {error}"
                ) from error

        command: Dict[str, Any] = {
            "type": command_type,
            "params": validated_params,
            "request_id": uuid.uuid4().hex,
        }
        if idempotency_key is not None:
            command["idempotency_key"] = idempotency_key

        try:
            if not self.circuit_breaker.allow_request():
                raise CircuitBreakerOpen(CIRCUIT_BREAKER_OPEN_MESSAGE)

            result = self._retry_strategy()(self._send_command_once, command)
            self.circuit_breaker.record_success()
            return result
        except CircuitBreakerOpen as error:
            logger.error(
                "Socket communication blocked by open circuit", error=str(error)
            )
            self._invalidate_socket()
            raise ConnectionError(str(error)) from error
        except TimeoutError as error:
            logger.error(
                "Socket timeout while waiting for response from Blender",
                error=str(error),
            )
            self.circuit_breaker.record_failure(error)
            self._invalidate_socket()
            raise ConnectionError(str(error)) from error
        except ConnectionError as error:
            logger.error("Socket connection error", error=str(error))
            self.circuit_breaker.record_failure(error)
            self._invalidate_socket()
            raise ConnectionError(str(error)) from error
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Blender: {str(e)}")
            raise CommandError(f"Invalid response from Blender: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error communicating with Blender: {str(e)}")
            self._invalidate_socket()
            raise BlenderMCPError(f"Communication error with Blender: {str(e)}") from e


_blender_connection: Optional[BlenderConnection] = None

def get_blender_connection() -> BlenderConnection:
    """Gets or creates a persistent Blender connection.

    Returns:
        The BlenderConnection instance.
    """
    global _blender_connection

    if _blender_connection is not None:
        try:
            _blender_connection.send_command("get_scene_hash", {})
            return _blender_connection
        except BlenderMCPError as e:
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            try:
                _blender_connection.disconnect()
            except:
                pass
            _blender_connection = None

    if _blender_connection is None:
        host = os.getenv("BLENDER_HOST", DEFAULT_HOST)
        port = int(os.getenv("BLENDER_PORT", DEFAULT_PORT))
        _blender_connection = BlenderConnection(host=host, port=port)
        if not _blender_connection.connect():
            _blender_connection = None
            raise ConnectionError(
                "Could not connect to Blender. Make sure the Blender addon is running."
            )
        logger.info("Created new persistent connection to Blender")

    return _blender_connection


def shutdown_connection() -> None:
    """Disconnect and clear the global Blender connection. Call from server shutdown."""
    global _blender_connection
    if _blender_connection is not None:
        try:
            _blender_connection.disconnect()
        except Exception as error:
            logger.warning("Failed to disconnect Blender on shutdown", error=str(error))
        _blender_connection = None