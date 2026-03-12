"""
Material and shader tools.

Provides focused MCP tools for creating and managing Blender materials.
"""

import json
import logging
from typing import Any, Dict, List, Optional

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


@telemetry_tool("create_subsurface_material")
@mcp.tool()
async def create_subsurface_material(
    ctx: Context,
    name: str,
    base_color: List[float],
    subsurface_color: List[float],
    subsurface_radius: List[float],
    subsurface: float = 0.5,
    roughness: float = 0.5,
    subsurface_method: str = "random_walk",
) -> str:
    """
    Create an advanced subsurface scattering material.

    Parameters:
    - name: Material name
    - base_color: Base color [r, g, b]
    - subsurface_color: Subsurface color [r, g, b]
    - subsurface_radius: Scattering radius [r, g, b]
    - subsurface: Subsurface strength
    - roughness: Surface roughness
    - subsurface_method: Scattering method

    Returns:
    - JSON string with material creation result
    """
    params = {
        "name": name,
        "base_color": base_color,
        "subsurface_color": subsurface_color,
        "subsurface_radius": subsurface_radius,
        "subsurface": subsurface,
        "roughness": roughness,
        "subsurface_method": subsurface_method,
    }

    return _send_material_command("create_subsurface_material", params)


@telemetry_tool("create_volume_material")
@mcp.tool()
async def create_volume_material(
    ctx: Context,
    name: str,
    density: float = 0.1,
    anisotropy: float = 0.0,
    absorption_color: Optional[List[float]] = None,
    emission_color: Optional[List[float]] = None,
    emission_strength: float = 0.0,
) -> str:
    """
    Create a volume material for clouds, smoke, or fire.

    Parameters:
    - name: Material name
    - density: Volume density
    - anisotropy: Scattering anisotropy
    - absorption_color: Absorption color
    - emission_color: Emission color
    - emission_strength: Emission strength

    Returns:
    - JSON string with volume material creation result
    """
    params = {
        "name": name,
        "density": density,
        "anisotropy": anisotropy,
        "emission_strength": emission_strength,
    }

    if absorption_color:
        params["absorption_color"] = absorption_color
    if emission_color:
        params["emission_color"] = emission_color

    return _send_material_command("create_volume_material", params)


@telemetry_tool("create_layered_material")
@mcp.tool()
async def create_layered_material(
    ctx: Context,
    name: str,
    base_material: str,
    layers: List[Dict[str, Any]],
    blend_modes: Optional[List[str]] = None,
) -> str:
    """
    Create a multi-layered material system.

    Parameters:
    - name: Material name
    - base_material: Base material name
    - layers: List of layer definitions
    - blend_modes: Blend modes for each layer

    Returns:
    - JSON string with layered material creation result
    """
    params = {
        "name": name,
        "base_material": base_material,
        "layers": layers,
    }

    if blend_modes:
        params["blend_modes"] = blend_modes

    return _send_material_command("create_layered_material", params)


@telemetry_tool("create_hair_material")
@mcp.tool()
async def create_hair_material(
    ctx: Context,
    name: str,
    base_color: List[float],
    roughness: float = 0.3,
    radial_roughness: float = 0.1,
    coat: float = 0.0,
    ior: float = 1.55,
    melanin: float = 0.5,
    melanin_redness: float = 0.0,
) -> str:
    """
    Create a realistic hair material.

    Parameters:
    - name: Material name
    - base_color: Hair color
    - roughness: Longitudinal roughness
    - radial_roughness: Radial roughness
    - coat: Coat strength
    - ior: Index of refraction
    - melanin: Melanin concentration
    - melanin_redness: Red melanin concentration

    Returns:
    - JSON string with hair material creation result
    """
    params = {
        "name": name,
        "base_color": base_color,
        "roughness": roughness,
        "radial_roughness": radial_roughness,
        "coat": coat,
        "ior": ior,
        "melanin": melanin,
        "melanin_redness": melanin_redness,
    }

    return _send_material_command("create_hair_material", params)
