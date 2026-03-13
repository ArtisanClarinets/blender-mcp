#!/usr/bin/env python3
"""Blender MCP Client Tool for Agent Integration.

This module provides a client interface for agents to interact with Blender
through the Model Context Protocol (MCP).
"""

import argparse
import json
import socket
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876


@dataclass
class BlenderMCPClient:
    """A client for communicating with the Blender MCP server.

    Attributes:
        host: The server host.
        port: The server port.
        _sock: The socket connection.
    """

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    _sock: Optional[socket.socket] = None

    def connect(self) -> bool:
        """Establishes a connection to the Blender MCP server.

        Returns:
            True if the connection is successful, False otherwise.
        """
        if self._sock:
            return True
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self.host, self.port))
            logger.info("Connected to Blender MCP", host=self.host, port=self.port)
            return True
        except socket.error as e:
            logger.error("Failed to connect to Blender MCP", error=e)
            self._sock = None
            return False

    def disconnect(self) -> None:
        """Closes the connection to the Blender MCP server."""
        if self._sock:
            try:
                self._sock.close()
            except socket.error as e:
                logger.error("Error disconnecting from Blender MCP", error=e)
            finally:
                self._sock = None

    def send_command(
        self,
        command_type: str,
        params: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sends a command to the Blender MCP server and returns the response.

        Args:
            command_type: The type of command to send.
            params: The parameters for the command.
            request_id: The request ID.
            idempotency_key: The idempotency key.

        Returns:
            The response from the server.

        Raises:
            ConnectionError: If not connected to the server.
            RuntimeError: If no valid response is received.
        """
        if not self._sock and not self.connect():
            raise ConnectionError("Not connected to Blender MCP")

        request_id = request_id or str(uuid.uuid4())

        command: Dict[str, Any] = {
            "type": command_type,
            "params": params or {},
            "request_id": request_id,
        }

        if idempotency_key:
            command["idempotency_key"] = idempotency_key

        try:
            logger.info(
                "Sending command", command_type=command_type, request_id=request_id
            )
            message = json.dumps(command) + "\n"
            self._sock.sendall(message.encode("utf-8"))

            self._sock.settimeout(180.0)

            buffer = b""
            while True:
                chunk = self._sock.recv(8192)
                if not chunk:
                    break
                buffer += chunk
                if b"\n" in buffer:
                    line, _ = buffer.split(b"\n", 1)
                    try:
                        response = json.loads(line.decode("utf-8"))
                        return response
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON, continuing to read")
                        continue

            raise RuntimeError("No valid response received from Blender MCP")
        except Exception as e:
            logger.error("Error sending command", error=e, exc_info=True)
            self.disconnect()
            raise


# Tool definitions will be loaded dynamically
TOOLS: Dict[str, Any] = {}


def load_tools() -> None:
    """Loads tool definitions from the server."""
    global TOOLS
    try:
        client = BlenderMCPClient()
        if not client.connect():
            logger.error("Could not connect to Blender MCP server to load tools.")
            return
        TOOLS = client.send_command("get_tool_definitions")
        client.disconnect()
    except Exception as e:
        logger.error("Failed to load tools from server", error=e)


def call_tool(
    tool_name: str,
    params: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> str:
    """Calls a Blender MCP tool and returns the result.

    Args:
        tool_name: The name of the tool to call.
        params: The parameters for the tool.
        request_id: The request ID.
        idempotency_key: The idempotency key.

    Returns:
        The result of the tool call.
    """
    client = BlenderMCPClient()
    try:
        if not client.connect():
            return "Error: Could not connect to Blender MCP server. Ensure Blender is running with the addon enabled."

        result = client.send_command(tool_name, params, request_id, idempotency_key)

        if result.get("ok"):
            return json.dumps(result.get("data", {}), indent=2)
        else:
            error = result.get("error", {})
            return f"Error: {error.get('message', 'Unknown error')}"

    except Exception as e:
        logger.error("Error calling tool", tool_name=tool_name, error=e, exc_info=True)
        return f"An error occurred: {e}"
    finally:
        client.disconnect()


if __name__ == "__main__":
    load_tools()

    parser = argparse.ArgumentParser(description="Blender MCP Client")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List all available tools")

    describe_parser = subparsers.add_parser("describe", help="Describe a specific tool")
    describe_parser.add_argument("tool_name", help="The name of the tool to describe")

    call_parser = subparsers.add_parser("call", help="Call a tool")
    call_parser.add_argument("tool_name", help="The name of the tool to call")
    call_parser.add_argument(
        "params", nargs="?", default="{}", help="A JSON string of parameters"
    )

    args = parser.parse_args()

    if args.command == "list":
        if not TOOLS:
            print("No tools available. Could not connect to server.")
        else:
            print("Available tools:")
            for name, info in TOOLS.items():
                print(f"  - {name}: {info.get('description', 'No description')}")
    elif args.command == "describe":
        if not TOOLS:
            print("No tools available. Could not connect to server.")
        else:
            tool_info = TOOLS.get(args.tool_name)
            if not tool_info:
                print(f"Tool not found: {args.tool_name}")
            else:
                print(f"Tool: {args.tool_name}")
                print(f"  Description: {tool_info.get('description', 'No description')}")
                parameters = tool_info.get("parameters", {})
                if parameters:
                    print("  Parameters:")
                    for param, p_info in parameters.items():
                        print(f"    - {param}:")
                        print(f"        Type: {p_info.get('type', 'any')}")
                        print(f"        Required: {p_info.get('required', False)}")
                        if "default" in p_info:
                            print(f"        Default: {p_info['default']}")
                        print(
                            f"        Description: {p_info.get('description', 'No description')}"
                        )
                else:
                    print("  Parameters: None")
    elif args.command == "call":
        try:
            params = json.loads(args.params)
            result = call_tool(args.tool_name, params)
            print(result)
        except json.JSONDecodeError:
            logger.error("Invalid JSON for parameters", params=args.params)
            print("Error: Invalid JSON for parameters.")
        except Exception as e:
            logger.error("An error occurred during tool call", error=e, exc_info=True)
            print(f"An error occurred: {e}")