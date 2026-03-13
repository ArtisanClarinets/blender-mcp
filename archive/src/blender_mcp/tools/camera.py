"""
Camera tools.

Provides focused MCP tools for creating and managing Blender cameras.
"""

import json
import logging
from typing import List, Optional

from ..mcp_compat import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


def _json_error(message: str) -> str:
    return json.dumps({"error": message})


def _send_camera_command(command_type: str, params: dict) -> str:
    try:
        blender = get_blender_connection()
        result = blender.send_command(command_type, params)
        return json.dumps(result, indent=2)
    except Exception as exc:
        logger.error(f"Error running {command_type}: {str(exc)}")
        return _json_error(str(exc))


@telemetry_tool("create_composition_camera")
@mcp.tool()
async def create_composition_camera(
    ctx: Context,
    name: str = "Camera",
    composition: str = "center",
    focal_length: float = 50.0,
    location: Optional[List[float]] = None,
    target: Optional[List[float]] = None,
) -> str:
    """Create or replace a composition camera."""
    params = {
        "name": name,
        "composition": composition,
        "focal_length": focal_length,
    }
    if location is not None:
        params["location"] = location
    if target is not None:
        params["target"] = target

    return _send_camera_command("create_composition_camera", params)


@telemetry_tool("create_isometric_camera")
@mcp.tool()
async def create_isometric_camera(
    ctx: Context,
    name: str = "Isometric",
    ortho_scale: float = 10.0,
    angle: float = 35.264,
) -> str:
    """Create or replace an isometric camera."""
    return _send_camera_command(
        "create_isometric_camera",
        {
            "name": name,
            "ortho_scale": ortho_scale,
            "angle": angle,
        },
    )


@telemetry_tool("set_camera_depth_of_field")
@mcp.tool()
async def set_camera_depth_of_field(
    ctx: Context,
    camera_name: str,
    focus_distance: Optional[float] = None,
    focal_length: Optional[float] = None,
    aperture: float = 5.6,
) -> str:
    """Configure camera depth of field settings."""
    params = {"camera_name": camera_name, "aperture": aperture}
    if focus_distance is not None:
        params["focus_distance"] = focus_distance
    if focal_length is not None:
        params["focal_length"] = focal_length

    return _send_camera_command("set_camera_depth_of_field", params)


@telemetry_tool("apply_camera_preset")
@mcp.tool()
async def apply_camera_preset(ctx: Context, camera_name: str, preset: str) -> str:
    """Apply a named camera preset."""
    return _send_camera_command(
        "apply_camera_preset",
        {"camera_name": camera_name, "preset": preset},
    )


@telemetry_tool("set_active_camera")
@mcp.tool()
async def set_active_camera(ctx: Context, camera_name: str) -> str:
    """Set the scene's active camera."""
    return _send_camera_command(
        "set_active_camera",
        {"camera_name": camera_name},
    )


@telemetry_tool("list_cameras")
@mcp.tool()
async def list_cameras(ctx: Context) -> str:
    """List cameras in the active scene."""
    return _send_camera_command("list_cameras", {})


@telemetry_tool("frame_camera_to_selection")
@mcp.tool()
async def frame_camera_to_selection(
    ctx: Context,
    camera_name: str,
    margin: float = 1.1,
) -> str:
    """Frame the named camera to the current selection."""
    return _send_camera_command(
        "frame_camera_to_selection",
        {"camera_name": camera_name, "margin": margin},
    )
