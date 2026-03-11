"""
Scene operations tools

Provides atomic tools for creating and manipulating scene objects.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


@telemetry_tool("create_primitive")
@mcp.tool()
async def create_primitive(
    ctx: Context,
    type: str,
    name: Optional[str] = None,
    size: Optional[float] = None,
    location: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
    scale: Optional[List[float]] = None,
) -> str:
    """
    Create a primitive object in the scene.

    Parameters:
    - type: Primitive type ("cube", "sphere", "cylinder", "cone", "torus", "plane")
    - name: Optional name for the object
    - size: Optional size parameter
    - location: Optional [x, y, z] location
    - rotation: Optional [x, y, z] rotation in radians
    - scale: Optional [x, y, z] scale

    Returns:
    - JSON string with created object information
    """
    try:
        blender = get_blender_connection()

        params = {"type": type}
        if name:
            params["name"] = name
        if size is not None:
            params["size"] = size
        if location:
            params["location"] = location
        if rotation:
            params["rotation"] = rotation
        if scale:
            params["scale"] = scale

        result = blender.send_command("create_primitive", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating primitive: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_empty")
@mcp.tool()
async def create_empty(
    ctx: Context, name: Optional[str] = None, location: Optional[List[float]] = None
) -> str:
    """
    Create an empty object in the scene.

    Parameters:
    - name: Optional name for the object
    - location: Optional [x, y, z] location

    Returns:
    - JSON string with created object information
    """
    try:
        blender = get_blender_connection()

        params = {}
        if name:
            params["name"] = name
        if location:
            params["location"] = location

        result = blender.send_command("create_empty", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating empty: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_camera")
@mcp.tool()
async def create_camera(
    ctx: Context,
    name: Optional[str] = None,
    lens: Optional[float] = None,
    location: Optional[List[float]] = None,
    look_at: Optional[List[float]] = None,
) -> str:
    """
    Create a camera in the scene.

    Parameters:
    - name: Optional name for the camera
    - lens: Optional focal length in mm
    - location: Optional [x, y, z] location
    - look_at: Optional [x, y, z] point to look at

    Returns:
    - JSON string with created camera information
    """
    try:
        blender = get_blender_connection()

        params = {}
        if name:
            params["name"] = name
        if lens:
            params["lens"] = lens
        if location:
            params["location"] = location
        if look_at:
            params["look_at"] = look_at

        result = blender.send_command("create_camera", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating camera: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_light")
@mcp.tool()
async def create_light(
    ctx: Context,
    type: str,
    energy: float,
    color: Optional[List[float]] = None,
    location: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
) -> str:
    """
    Create a light in the scene.

    Parameters:
    - type: Light type ("point", "sun", "spot", "area")
    - energy: Light energy/strength
    - color: Optional [r, g, b] color (0-1 range)
    - location: Optional [x, y, z] location
    - rotation: Optional [x, y, z] rotation in radians

    Returns:
    - JSON string with created light information
    """
    try:
        blender = get_blender_connection()

        params = {"type": type, "energy": energy}
        if color:
            params["color"] = color
        if location:
            params["location"] = location
        if rotation:
            params["rotation"] = rotation

        result = blender.send_command("create_light", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating light: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("set_transform")
@mcp.tool()
async def set_transform(
    ctx: Context,
    target_id: str,
    location: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
    scale: Optional[List[float]] = None,
    apply: bool = False,
) -> str:
    """
    Set the transform of an object.

    Parameters:
    - target_id: Object name or ID
    - location: Optional [x, y, z] location
    - rotation: Optional [x, y, z] rotation in radians
    - scale: Optional [x, y, z] scale
    - apply: Whether to apply the transform

    Returns:
    - JSON string with updated object information
    """
    try:
        blender = get_blender_connection()

        params = {"target_id": target_id}
        if location:
            params["location"] = location
        if rotation:
            params["rotation"] = rotation
        if scale:
            params["scale"] = scale
        params["apply"] = apply

        result = blender.send_command("set_transform", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting transform: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("select_objects")
@mcp.tool()
async def select_objects(ctx: Context, ids: List[str], mode: str = "set") -> str:
    """
    Select objects in the scene.

    Parameters:
    - ids: List of object names or IDs to select
    - mode: Selection mode ("set", "add", "remove")

    Returns:
    - JSON string with selection information
    """
    try:
        blender = get_blender_connection()

        params = {"ids": ids, "mode": mode}

        result = blender.send_command("select_objects", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error selecting objects: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("delete_objects")
@mcp.tool()
async def delete_objects(ctx: Context, ids: List[str]) -> str:
    """
    Delete objects from the scene.

    Parameters:
    - ids: List of object names or IDs to delete

    Returns:
    - JSON string with deletion status
    """
    try:
        blender = get_blender_connection()

        params = {"ids": ids}

        result = blender.send_command("delete_objects", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error deleting objects: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("duplicate_object")
@mcp.tool()
async def duplicate_object(
    ctx: Context, id: str, linked: bool = False, count: int = 1
) -> str:
    """
    Duplicate an object in the scene.

    Parameters:
    - id: Object name or ID to duplicate
    - linked: Whether to create linked duplicates
    - count: Number of duplicates to create

    Returns:
    - JSON string with duplicated object information
    """
    try:
        blender = get_blender_connection()

        params = {"id": id, "linked": linked, "count": count}

        result = blender.send_command("duplicate_object", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error duplicating object: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("assign_material_pbr")
@mcp.tool()
async def assign_material_pbr(
    ctx: Context, target_id: str, material_spec: Dict[str, Any]
) -> str:
    """
    Assign a PBR material to an object.

    Parameters:
    - target_id: Object name or ID
    - material_spec: Material specification with:
      - base_color: [r, g, b] or texture path
      - metallic: 0-1 value
      - roughness: 0-1 value
      - normal_map: texture path

    Returns:
    - JSON string with material assignment status
    """
    try:
        blender = get_blender_connection()

        params = {"target_id": target_id, "material_spec": material_spec}

        result = blender.send_command("assign_material_pbr", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error assigning material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("set_world_hdri")
@mcp.tool()
async def set_world_hdri(ctx: Context, asset_id: str, resolution: str = "2k") -> str:
    """
    Set the world HDRI environment.

    Parameters:
    - asset_id: PolyHaven HDRI asset ID
    - resolution: Resolution ("1k", "2k", "4k", "8k")

    Returns:
    - JSON string with HDRI setting status
    """
    try:
        blender = get_blender_connection()

        params = {"asset_id": asset_id, "resolution": resolution}

        result = blender.send_command("set_world_hdri", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting HDRI: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("execute_blender_code")
@mcp.tool()
async def execute_blender_code(ctx: Context, code: str) -> str:
    """
    Execute arbitrary Python code in Blender.

    WARNING: This tool allows running arbitrary code. Use with caution.

    Parameters:
    - code: Python code to execute

    Returns:
    - JSON string with execution result
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("execute_blender_code", {"code": code})

        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}")
        return json.dumps({"error": str(e)})
