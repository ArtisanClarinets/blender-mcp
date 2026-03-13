"""
Blender MCP Addon Package

This is the main entry point for the Blender MCP addon.
Install this package in Blender to enable MCP server functionality.
"""

bl_info = {
    "name": "Blender MCP",
    "author": "BlenderMCP",
    "version": (1, 5, 5),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to AI assistants via MCP",
    "category": "Interface",
    "support": "COMMUNITY",
    "doc_url": "https://github.com/ahujasid/blender-mcp",
    "tracker_url": "https://github.com/ahujasid/blender-mcp/issues",
}

import bpy
from . import server
from . import ui

# Module registration
modules = [
    server,
    ui,
]


def register():
    """Register all addon modules."""
    for module in modules:
        module.register()


def unregister():
    """Unregister all addon modules."""
    for module in reversed(modules):
        module.unregister()


if __name__ == "__main__":
    register()
