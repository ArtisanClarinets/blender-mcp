"""
Socket server for Blender MCP Addon

Handles TCP socket connections and dispatches commands.
"""

import bpy
import threading
import socket
import json
import traceback
from typing import Dict, Any, Optional

from . import protocol
from .command_registry import dispatch_command


def _log(level: str, message: str, request_id: Optional[str] = None, **kwargs: Any) -> None:
    """Structured log line for addon; includes request_id when available for correlation."""
    parts = ["[BlenderMCP]", f"[{level}]", message]
    if request_id:
        parts.insert(1, f"[request_id={request_id}]")
    if kwargs:
        parts.append(" " + " ".join(f"{k}={v!r}" for k, v in kwargs.items()))
    print(" ".join(parts))


class BlenderMCPServer:
    """TCP socket server for Blender MCP."""

    def __init__(self, host="localhost", port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
        self.idempotency_cache = {}  # Cache for idempotent commands

    def start(self):
        """Start the server."""
        if self.running:
            _log("INFO", "Server is already running")
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.running = True

            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()

            _log("INFO", f"Server started on {self.host}:{self.port}")
        except Exception as e:
            _log("ERROR", "Failed to start server", error=str(e))
            self.running = False

    def stop(self):
        """Stop the server."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        _log("INFO", "Server stopped")

    def _server_loop(self):
        """Main server loop."""
        while self.running:
            try:
                self.socket.settimeout(1.0)
                client, address = self.socket.accept()
                _log("INFO", "Client connected", address=address)
                self._handle_client(client)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    _log("ERROR", "Server error", error=str(e))

    def _handle_client(self, client: socket.socket):
        """Handle a client connection."""
        buffer = b""

        try:
            while self.running:
                # Receive data
                data = client.recv(4096)
                if not data:
                    break

                buffer += data

                # Process complete messages (newline-delimited)
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)

                    # Parse command
                    command = protocol.parse_command(line)
                    if not command:
                        request_id = protocol.try_request_id_from_raw(line) or ""
                        response = protocol.create_error_response(
                            "invalid_command",
                            "Could not parse command",
                            request_id=request_id,
                        )
                    else:
                        # Execute command
                        response = self._execute_command(command)

                    # Send response
                    response_bytes = protocol.encode_command(response)
                    client.sendall(response_bytes)

        except Exception as e:
            _log("ERROR", "Client handler error", error=str(e))
        finally:
            client.close()
            _log("INFO", "Client disconnected")

    def _execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command and return response."""
        command_type = protocol.get_command_type(command)
        params = protocol.get_command_params(command)
        request_id = protocol.get_request_id(command)
        idempotency_key = protocol.get_idempotency_key(command)
        _log("INFO", "Executing command", request_id=request_id, command_type=command_type)

        # Check idempotency cache
        if idempotency_key and idempotency_key in self.idempotency_cache:
            cached_response = self.idempotency_cache[idempotency_key].copy()
            cached_response["request_id"] = request_id  # Update request ID
            return cached_response

        # Execute on main thread
        result_container: Dict[str, Any] = {}

        def execute_wrapper():
            try:
                result_container["result"] = self._dispatch_command(
                    command_type, params
                )
            except Exception as exc:
                traceback.print_exc()
                result_container["error"] = exc
            return None

        bpy.app.timers.register(execute_wrapper, first_interval=0.0)

        # Wait for result (blocking); use longer timeout for render/export
        import time
        import os as _os
        base_timeout = float(_os.environ.get("BLENDER_MCP_CMD_TIMEOUT", "30"))
        if command_type.startswith("render_") or command_type.startswith("export_"):
            timeout = min(600.0, max(base_timeout, 300.0))
        else:
            timeout = base_timeout
        # Allow client to request longer timeout via params (capped)
        if isinstance(params.get("timeout_sec"), (int, float)):
            timeout = min(600.0, max(timeout, float(params["timeout_sec"])))
        start_time = time.time()
        while time.time() - start_time < timeout:
            if "result" in result_container or "error" in result_container:
                break
            time.sleep(0.01)

        # Build response
        if "error" in result_container:
            response = protocol.create_error_response(
                code="execution_error",
                message=str(result_container["error"]),
                request_id=request_id,
            )
        elif "result" in result_container:
            response = protocol.create_success_response(
                data=result_container["result"],
                request_id=request_id,
            )
        else:
            response = protocol.create_error_response(
                "timeout", "Command execution timed out", request_id=request_id
            )

        # Cache if idempotent
        if idempotency_key and "error" not in result_container:
            self.idempotency_cache[idempotency_key] = response.copy()

        return response

    def _dispatch_command(self, command_type: str, params: Dict[str, Any]) -> Any:
        """Dispatch command to the canonical handler registry."""
        return dispatch_command(command_type, params)



# Global server instance
_server_instance = None


def get_server() -> Optional[BlenderMCPServer]:
    """Get the global server instance."""
    return _server_instance


def start_server(host="localhost", port=9876):
    """Start the global server."""
    global _server_instance
    if _server_instance is None:
        _server_instance = BlenderMCPServer(host, port)
    _server_instance.start()


def stop_server():
    """Stop the global server."""
    global _server_instance
    if _server_instance:
        _server_instance.stop()
        _server_instance = None


def register():
    """Register server module."""
    pass


def unregister():
    """Unregister server module."""
    stop_server()
