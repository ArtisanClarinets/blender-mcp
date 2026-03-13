"""
Asset integration tools

Provides tools for importing assets from various sources.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..mcp_compat import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


# PolyHaven Integration


@telemetry_tool("get_polyhaven_status")
@mcp.tool()
async def get_polyhaven_status(ctx: Context) -> str:
    """Check PolyHaven integration status."""
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_polyhaven_status", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting PolyHaven status: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_polyhaven_categories")
@mcp.tool()
async def get_polyhaven_categories(ctx: Context, asset_type: str = "all") -> str:
    """
    Get categories for PolyHaven assets.

    Parameters:
    - asset_type: Type of assets ("hdris", "textures", "models", "all")

    Returns:
    - JSON string with categories
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "get_polyhaven_categories", {"asset_type": asset_type}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting PolyHaven categories: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("search_polyhaven_assets")
@mcp.tool()
async def search_polyhaven_assets(
    ctx: Context, asset_type: str = "all", categories: Optional[str] = None
) -> str:
    """
    Search PolyHaven for assets.

    Parameters:
    - asset_type: Type of assets ("hdris", "textures", "models", "all")
    - categories: Optional comma-separated categories

    Returns:
    - JSON string with search results
    """
    try:
        blender = get_blender_connection()
        params = {"asset_type": asset_type}
        if categories:
            params["categories"] = categories
        result = blender.send_command("search_polyhaven_assets", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error searching PolyHaven: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("download_polyhaven_asset")
@mcp.tool()
async def download_polyhaven_asset(
    ctx: Context,
    asset_id: str,
    asset_type: str,
    resolution: str = "2k",
    file_format: Optional[str] = None,
) -> str:
    """
    Download and import a PolyHaven asset.

    Parameters:
    - asset_id: The ID of the asset
    - asset_type: Type ("hdris", "textures", "models")
    - resolution: Resolution like "1k", "2k", "4k"
    - file_format: Optional format ("hdr", "exr", "gltf", etc.)

    Returns:
    - JSON string with import result
    """
    try:
        blender = get_blender_connection()
        params = {
            "asset_id": asset_id,
            "asset_type": asset_type,
            "resolution": resolution,
        }
        if file_format:
            params["file_format"] = file_format
        result = blender.send_command("download_polyhaven_asset", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error downloading PolyHaven asset: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("set_texture")
@mcp.tool()
async def set_texture(ctx: Context, object_name: str, texture_id: str) -> str:
    """
    Apply a PolyHaven texture to an object.

    Parameters:
    - object_name: Name of the object
    - texture_id: ID of the texture (must be downloaded first)

    Returns:
    - JSON string with texture application result
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "set_texture", {"object_name": object_name, "texture_id": texture_id}
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting texture: {str(e)}")
        return json.dumps({"error": str(e)})


# Sketchfab Integration


@telemetry_tool("get_sketchfab_status")
@mcp.tool()
async def get_sketchfab_status(ctx: Context) -> str:
    """Check Sketchfab integration status."""
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_sketchfab_status", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting Sketchfab status: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("search_sketchfab_models")
@mcp.tool()
async def search_sketchfab_models(
    ctx: Context,
    query: str,
    categories: Optional[str] = None,
    count: int = 20,
    downloadable: bool = True,
) -> str:
    """
    Search Sketchfab for models.

    Parameters:
    - query: Search query
    - categories: Optional comma-separated categories
    - count: Max results (default: 20)
    - downloadable: Only downloadable (default: true)

    Returns:
    - JSON string with search results
    """
    try:
        blender = get_blender_connection()
        params = {"query": query, "count": count, "downloadable": downloadable}
        if categories:
            params["categories"] = categories
        result = blender.send_command("search_sketchfab_models", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error searching Sketchfab: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_sketchfab_model_preview")
@mcp.tool()
async def get_sketchfab_model_preview(ctx: Context, uid: str) -> str:
    """
    Get preview thumbnail of a Sketchfab model.

    Parameters:
    - uid: Model UID from search

    Returns:
    - JSON string with preview information
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_sketchfab_model_preview", {"uid": uid})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting Sketchfab preview: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("download_sketchfab_model")
@mcp.tool()
async def download_sketchfab_model(
    ctx: Context, uid: str, target_size: Optional[float] = None
) -> str:
    """
    Download and import a Sketchfab model.

    Parameters:
    - uid: Model UID
    - target_size: Target size in meters for largest dimension

    Returns:
    - JSON string with import result
    """
    try:
        blender = get_blender_connection()
        params = {"uid": uid}
        if target_size:
            params["target_size"] = target_size
        result = blender.send_command("download_sketchfab_model", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error downloading Sketchfab model: {str(e)}")
        return json.dumps({"error": str(e)})
