"""Custom exceptions for Blender MCP."""

class BlenderMCPError(Exception):
    """Base exception for Blender MCP errors."""
    pass

class ConnectionError(BlenderMCPError):
    """Raised when there is a problem connecting to Blender."""
    pass

class CommandError(BlenderMCPError):
    """Raised when a command fails to execute."""
    pass
