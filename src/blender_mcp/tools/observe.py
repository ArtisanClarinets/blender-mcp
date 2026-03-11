"""
Observation tools for scene inspection

Provides tools for observing and analyzing the Blender scene state.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool
from ..protocol import SceneInfo, ViewportScreenshot

logger = logging.getLogger("BlenderMCPTools")


@telemetry_tool("observe_scene")
@mcp.tool()
async def observe_scene(
    ctx: Context,
    detail: str = "med",
    include_screenshot: bool = False,
    max_screenshot_size: int = 800,
) -> str:
    """
    Observe the current scene state with configurable detail level.

    Parameters:
    - detail: Level of detail ("low", "med", "high")
    - include_screenshot: Whether to capture a screenshot
    - max_screenshot_size: Maximum screenshot dimension in pixels

    Returns:
    - JSON string with scene information
    """
    try:
        blender = get_blender_connection()

        params = {
            "detail": detail,
            "include_screenshot": include_screenshot,
            "max_screenshot_size": max_screenshot_size,
        }

        result = blender.send_command("observe_scene", params)

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error observing scene: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_scene_hash")
@mcp.tool()
async def get_scene_hash(ctx: Context) -> str:
    """
    Get a stable hash of the current scene state.

    Returns:
    - Hash string representing scene state
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_scene_hash", {})

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting scene hash: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_scene_info")
@mcp.tool()
async def get_scene_info(ctx: Context) -> str:
    """
    Get detailed information about the current Blender scene.

    Returns:
    - JSON string with scene information
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_scene_info", {})

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting scene info: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_object_info")
@mcp.tool()
async def get_object_info(ctx: Context, object_name: str) -> str:
    """
    Get detailed information about a specific object.

    Parameters:
    - object_name: Name of the object to get information about

    Returns:
    - JSON string with object information
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_object_info", {"object_name": object_name})

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting object info: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_viewport_screenshot")
@mcp.tool()
async def get_viewport_screenshot(ctx: Context, max_size: int = 800) -> str:
    """
    Capture a screenshot of the current Blender 3D viewport.

    Parameters:
    - max_size: Maximum size in pixels (default: 800)

    Returns:
    - JSON string with screenshot information
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_viewport_screenshot", {"max_size": max_size})

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_selection")
@mcp.tool()
async def get_selection(ctx: Context) -> str:
    """
    Get information about currently selected objects.

    Returns:
    - JSON string with selection information
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_selection", {})

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting selection: {str(e)}")
        return json.dumps({"error": str(e)})
