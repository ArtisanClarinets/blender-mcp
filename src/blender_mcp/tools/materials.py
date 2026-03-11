"""
Material and shader tools.

Provides focused MCP tools for creating and managing Blender materials.
"""

import json
import logging
from typing import List, Optional

from mcp.server.fastmcp import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


def _json_error(message: str) -> str:
    return json.dumps({"error": message})


def _send_material_command(command_type: str, params: dict) -> str:
    try:
        blender = get_blender_connection()
        result = blender.send_command(command_type, params)
        return json.dumps(result, indent=2)
    except Exception as exc:
        logger.error(f"Error running {command_type}: {str(exc)}")
        return _json_error(str(exc))


@telemetry_tool("create_bsdf_material")
@mcp.tool()
async def create_bsdf_material(
    ctx: Context,
    name: str,
    base_color: Optional[List[float]] = None,
    metallic: Optional[float] = None,
    roughness: Optional[float] = None,
    specular: Optional[float] = None,
    subsurface: Optional[float] = None,
    subsurface_color: Optional[List[float]] = None,
    transmission: Optional[float] = None,
    ior: Optional[float] = None,
    emission_color: Optional[List[float]] = None,
    emission_strength: Optional[float] = None,
) -> str:
    """Create or replace a Principled BSDF material."""
    params = {"name": name}
    if base_color is not None:
        params["base_color"] = base_color
    if metallic is not None:
        params["metallic"] = metallic
    if roughness is not None:
        params["roughness"] = roughness
    if specular is not None:
        params["specular"] = specular
    if subsurface is not None:
        params["subsurface"] = subsurface
    if subsurface_color is not None:
        params["subsurface_color"] = subsurface_color
    if transmission is not None:
        params["transmission"] = transmission
    if ior is not None:
        params["ior"] = ior
    if emission_color is not None:
        params["emission_color"] = emission_color
    if emission_strength is not None:
        params["emission_strength"] = emission_strength

    return _send_material_command("create_bsdf_material", params)


@telemetry_tool("create_emission_material")
@mcp.tool()
async def create_emission_material(
    ctx: Context,
    name: str,
    color: List[float],
    strength: float = 10.0,
    shadow_mode: str = "none",
) -> str:
    """Create or replace an emission material."""
    return _send_material_command(
        "create_emission_material",
        {
            "name": name,
            "color": color,
            "strength": strength,
            "shadow_mode": shadow_mode,
        },
    )


@telemetry_tool("create_glass_material")
@mcp.tool()
async def create_glass_material(
    ctx: Context,
    name: str,
    color: Optional[List[float]] = None,
    roughness: float = 0.0,
    ior: float = 1.45,
    transmission: float = 1.0,
) -> str:
    """Create or replace a glass material."""
    params = {
        "name": name,
        "roughness": roughness,
        "ior": ior,
        "transmission": transmission,
    }
    if color is not None:
        params["color"] = color

    return _send_material_command("create_glass_material", params)


@telemetry_tool("create_metal_material")
@mcp.tool()
async def create_metal_material(
    ctx: Context,
    name: str,
    base_color: List[float],
    roughness: float = 0.3,
    anisotropy: float = 0.0,
) -> str:
    """Create or replace a metal material."""
    return _send_material_command(
        "create_metal_material",
        {
            "name": name,
            "base_color": base_color,
            "roughness": roughness,
            "anisotropy": anisotropy,
        },
    )


@telemetry_tool("create_subsurface_material")
@mcp.tool()
async def create_subsurface_material(
    ctx: Context,
    name: str,
    base_color: List[float],
    subsurface_color: List[float],
    subsurface_radius: Optional[List[float]] = None,
    subsurface: float = 0.5,
    roughness: float = 0.5,
) -> str:
    """Create or replace a subsurface scattering material."""
    params = {
        "name": name,
        "base_color": base_color,
        "subsurface_color": subsurface_color,
        "subsurface": subsurface,
        "roughness": roughness,
    }
    if subsurface_radius is not None:
        params["subsurface_radius"] = subsurface_radius

    return _send_material_command("create_subsurface_material", params)


@telemetry_tool("create_procedural_texture")
@mcp.tool()
async def create_procedural_texture(
    ctx: Context,
    texture_type: str,
    name: str,
    scale: float = 5.0,
    detail: float = 2.0,
    roughness: float = 0.5,
    distortion: float = 0.0,
) -> str:
    """Create a material driven by a procedural texture node."""
    return _send_material_command(
        "create_procedural_texture",
        {
            "texture_type": texture_type,
            "name": name,
            "scale": scale,
            "detail": detail,
            "roughness": roughness,
            "distortion": distortion,
        },
    )


@telemetry_tool("assign_material")
@mcp.tool()
async def assign_material(ctx: Context, object_name: str, material_name: str) -> str:
    """Assign an existing material to an object by name."""
    return _send_material_command(
        "assign_material",
        {"object_name": object_name, "material_name": material_name},
    )


@telemetry_tool("list_materials")
@mcp.tool()
async def list_materials(ctx: Context) -> str:
    """List scene materials."""
    return _send_material_command("list_materials", {})


@telemetry_tool("delete_material")
@mcp.tool()
async def delete_material(ctx: Context, name: str) -> str:
    """Delete a material by name."""
    return _send_material_command("delete_material", {"name": name})
