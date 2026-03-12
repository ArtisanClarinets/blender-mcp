"""
Lighting tools.

Provides focused MCP tools for creating and managing Blender lighting rigs.
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


def _send_lighting_command(command_type: str, params: dict) -> str:
    try:
        blender = get_blender_connection()
        result = blender.send_command(command_type, params)
        return json.dumps(result, indent=2)
    except Exception as exc:
        logger.error(f"Error running {command_type}: {str(exc)}")
        return _json_error(str(exc))


@telemetry_tool("create_three_point_lighting")
@mcp.tool()
async def create_three_point_lighting(
    ctx: Context,
    key_intensity: float = 1000.0,
    fill_intensity: float = 500.0,
    rim_intensity: float = 800.0,
    key_color: Optional[List[float]] = None,
    fill_color: Optional[List[float]] = None,
    rim_color: Optional[List[float]] = None,
) -> str:
    """Create a three-point lighting rig."""
    params = {
        "key_intensity": key_intensity,
        "fill_intensity": fill_intensity,
        "rim_intensity": rim_intensity,
    }
    if key_color is not None:
        params["key_color"] = key_color
    if fill_color is not None:
        params["fill_color"] = fill_color
    if rim_color is not None:
        params["rim_color"] = rim_color

    return _send_lighting_command("create_three_point_lighting", params)


@telemetry_tool("create_studio_lighting")
@mcp.tool()
async def create_studio_lighting(
    ctx: Context,
    preset: str,
    intensity: float = 500.0,
    color: Optional[List[float]] = None,
) -> str:
    """Create a named studio lighting preset."""
    params = {"preset": preset, "intensity": intensity}
    if color is not None:
        params["color"] = color

    return _send_lighting_command("create_studio_lighting", params)


@telemetry_tool("create_hdri_environment")
@mcp.tool()
async def create_hdri_environment(
    ctx: Context,
    hdri_name: Optional[str] = None,
    strength: float = 1.0,
    rotation: float = 0.0,
    blur: float = 0.0,
) -> str:
    """Create an HDRI-style world environment."""
    params = {
        "strength": strength,
        "rotation": rotation,
        "blur": blur,
    }
    if hdri_name is not None:
        params["hdri_name"] = hdri_name

    return _send_lighting_command("create_hdri_environment", params)


@telemetry_tool("create_area_light")
@mcp.tool()
async def create_area_light(
    ctx: Context,
    name: str,
    light_type: str = "RECTANGLE",
    size: float = 1.0,
    location: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
    energy: float = 100.0,
    color: Optional[List[float]] = None,
) -> str:
    """Create or replace an area light."""
    params = {
        "name": name,
        "light_type": light_type,
        "size": size,
        "energy": energy,
    }
    if location is not None:
        params["location"] = location
    if rotation is not None:
        params["rotation"] = rotation
    if color is not None:
        params["color"] = color

    return _send_lighting_command("create_area_light", params)


@telemetry_tool("create_volumetric_lighting")
@mcp.tool()
async def create_volumetric_lighting(
    ctx: Context,
    density: float = 0.1,
    anisotropy: float = 0.0,
    color: Optional[List[float]] = None,
) -> str:
    """Create volumetric world lighting."""
    params = {"density": density, "anisotropy": anisotropy}
    if color is not None:
        params["color"] = color

    return _send_lighting_command("create_volumetric_lighting", params)


@telemetry_tool("adjust_light_exposure")
@mcp.tool()
async def adjust_light_exposure(
    ctx: Context,
    exposure: float = 0.0,
    gamma: float = 1.0,
) -> str:
    """Adjust scene exposure and gamma."""
    return _send_lighting_command(
        "adjust_light_exposure",
        {"exposure": exposure, "gamma": gamma},
    )


@telemetry_tool("clear_lights")
@mcp.tool()
async def clear_lights(ctx: Context) -> str:
    """Remove all scene lights."""
    return _send_lighting_command("clear_lights", {})


@telemetry_tool("list_lights")
@mcp.tool()
async def list_lights(ctx: Context) -> str:
    """List scene lights."""
    return _send_lighting_command("list_lights", {})



# Add these new functions to the existing lighting.py file

@telemetry_tool("create_hdri_lighting_setup")
@mcp.tool()
async def create_hdri_lighting_setup(
    ctx: Context,
    hdri_path: Optional[str] = None,
    hdri_name: Optional[str] = None,
    rotation: float = 0.0,
    strength: float = 1.0,
    saturation: float = 1.0,
) -> str:
    """
    Create an HDRI-based lighting setup.
    
    Parameters:
    - hdri_path: Path to HDRI file
    - hdri_name: PolyHaven HDRI name
    - rotation: HDRI rotation
    - strength: Lighting strength
    - saturation: Color saturation
    
    Returns:
    - JSON string with HDRI lighting result
    """
    params = {
        "rotation": rotation,
        "strength": strength,
        "saturation": saturation,
    }
    
    if hdri_path:
        params["hdri_path"] = hdri_path
    if hdri_name:
        params["hdri_name"] = hdri_name
        
    return _send_lighting_command("create_hdri_lighting_setup", params)

@telemetry_tool("create_volumetric_lighting")
@mcp.tool()
async def create_volumetric_lighting(
    ctx: Context,
    light_name: str,
    volume_type: str = "god_rays",
    density: float = 0.1,
    scatter_amount: float = 1.0,
    anisotropy: float = 0.0,
) -> str:
    """
    Create volumetric lighting effects.
    
    Parameters:
    - light_name: Name of the light to make volumetric
    - volume_type: Type of volumetric effect
    - density: Volume density
    - scatter_amount: Scattering amount
    - anisotropy: Scattering anisotropy
    
    Returns:
    - JSON string with volumetric lighting result
    """
    params = {
        "light_name": light_name,
        "volume_type": volume_type,
        "density": density,
        "scatter_amount": scatter_amount,
        "anisotropy": anisotropy,
    }
    
    return _send_lighting_command("create_volumetric_lighting", params)

@telemetry_tool("create_studio_light_rig")
@mcp.tool()
async def create_studio_light_rig(
    ctx: Context,
    rig_type: str = "portrait",
    key_light_intensity: float = 1000.0,
    fill_light_intensity: float = 500.0,
    rim_light_intensity: float = 800.0,
    background_light_intensity: float = 200.0,
) -> str:
    """
    Create a professional studio lighting rig.
    
    Parameters:
    - rig_type: Type of rig ("portrait", "product", "fashion")
    - key_light_intensity: Key light intensity
    - fill_light_intensity: Fill light intensity
    - rim_light_intensity: Rim light intensity
    - background_light_intensity: Background light intensity
    
    Returns:
    - JSON string with studio rig creation result
    """
    params = {
        "rig_type": rig_type,
        "key_light_intensity": key_light_intensity,
        "fill_light_intensity": fill_light_intensity,
        "rim_light_intensity": rim_light_intensity,
        "background_light_intensity": background_light_intensity,
    }
    
    return _send_lighting_command("create_studio_light_rig", params)

@telemetry_tool("setup_light_linking")
@mcp.tool()
async def setup_light_linking(
    ctx: Context,
    light_objects: List[str],
    target_objects: List[str],
    link_type: str = "include",
) -> str:
    """
    Setup light linking for selective illumination.
    
    Parameters:
    - light_objects: List of light names
    - target_objects: List of objects to affect
    - link_type: "include" or "exclude"
    
    Returns:
    - JSON string with light linking result
    """
    params = {
        "light_objects": light_objects,
        "target_objects": target_objects,
        "link_type": link_type,
    }
    
    return _send_lighting_command("setup_light_linking", params)
