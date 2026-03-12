"""
Scene composition tools.

Provides focused MCP tools for common scene composition presets and render setup.
"""

import json
import logging

from mcp.server.fastmcp import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


def _json_error(message: str) -> str:
    return json.dumps({"error": message})


def _send_composition_command(command_type: str, params: dict) -> str:
    try:
        blender = get_blender_connection()
        result = blender.send_command(command_type, params)
        return json.dumps(result, indent=2)
    except Exception as exc:
        logger.error(f"Error running {command_type}: {str(exc)}")
        return _json_error(str(exc))


@telemetry_tool("compose_product_shot")
@mcp.tool()
async def compose_product_shot(
    ctx: Context,
    product_name: str = "Product",
    style: str = "clean",
    background: str = "white",
) -> str:
    """Compose a product-shot scene preset."""
    return _send_composition_command(
        "compose_product_shot",
        {
            "product_name": product_name,
            "style": style,
            "background": background,
        },
    )


@telemetry_tool("compose_isometric_scene")
@mcp.tool()
async def compose_isometric_scene(
    ctx: Context,
    grid_size: float = 10.0,
    floor: bool = True,
    shadow_catcher: bool = True,
) -> str:
    """Compose an isometric scene preset."""
    return _send_composition_command(
        "compose_isometric_scene",
        {
            "grid_size": grid_size,
            "floor": floor,
            "shadow_catcher": shadow_catcher,
        },
    )


@telemetry_tool("compose_character_scene")
@mcp.tool()
async def compose_character_scene(
    ctx: Context,
    character_name: str = "Character",
    ground_plane: bool = True,
    environment: str = "studio",
) -> str:
    """Compose a character-scene preset."""
    return _send_composition_command(
        "compose_character_scene",
        {
            "character_name": character_name,
            "ground_plane": ground_plane,
            "environment": environment,
        },
    )


@telemetry_tool("compose_automotive_shot")
@mcp.tool()
async def compose_automotive_shot(
    ctx: Context,
    car_name: str = "Car",
    angle: str = "three_quarter",
    environment: str = "studio",
) -> str:
    """Compose an automotive-shot preset."""
    return _send_composition_command(
        "compose_automotive_shot",
        {
            "car_name": car_name,
            "angle": angle,
            "environment": environment,
        },
    )


@telemetry_tool("compose_food_shot")
@mcp.tool()
async def compose_food_shot(ctx: Context, style: str = "flat_lay") -> str:
    """Compose a food-shot preset."""
    return _send_composition_command("compose_food_shot", {"style": style})


@telemetry_tool("compose_jewelry_shot")
@mcp.tool()
async def compose_jewelry_shot(
    ctx: Context,
    style: str = "macro",
    reflections: bool = True,
) -> str:
    """Compose a jewelry-shot preset."""
    return _send_composition_command(
        "compose_jewelry_shot",
        {"style": style, "reflections": reflections},
    )


@telemetry_tool("compose_architectural_shot")
@mcp.tool()
async def compose_architectural_shot(
    ctx: Context,
    interior: bool = False,
    natural_light: bool = True,
) -> str:
    """Compose an architectural-shot preset."""
    return _send_composition_command(
        "compose_architectural_shot",
        {"interior": interior, "natural_light": natural_light},
    )


@telemetry_tool("compose_studio_setup")
@mcp.tool()
async def compose_studio_setup(
    ctx: Context,
    subject_type: str = "generic",
    mood: str = "neutral",
) -> str:
    """Compose a studio setup preset."""
    return _send_composition_command(
        "compose_studio_setup",
        {"subject_type": subject_type, "mood": mood},
    )


@telemetry_tool("clear_scene")
@mcp.tool()
async def clear_scene(
    ctx: Context,
    keep_camera: bool = False,
    keep_lights: bool = False,
) -> str:
    """Remove scene objects while optionally preserving cameras and lights."""
    return _send_composition_command(
        "clear_scene",
        {"keep_camera": keep_camera, "keep_lights": keep_lights},
    )


@telemetry_tool("setup_render_settings")
@mcp.tool()
async def setup_render_settings(
    ctx: Context,
    engine: str = "CYCLES",
    samples: int = 128,
    resolution_x: int = 1920,
    resolution_y: int = 1080,
    denoise: bool = True,
) -> str:
    """Configure render settings for the active scene."""
    return _send_composition_command(
        "setup_render_settings",
        {
            "engine": engine,
            "samples": samples,
            "resolution_x": resolution_x,
            "resolution_y": resolution_y,
            "denoise": denoise,
        },
    )
