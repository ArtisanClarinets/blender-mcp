"""Tripo3D MCP tools."""

import json
import logging
from typing import Optional

from ..mcp_compat import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


@telemetry_tool("get_tripo3d_status")
@mcp.tool()
async def get_tripo3d_status(ctx: Context) -> str:
    """Check Tripo3D integration status."""
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_tripo3d_status", {})
        return json.dumps(result, indent=2)
    except Exception as error:
        logger.error(f"Error getting Tripo3D status: {str(error)}")
        return json.dumps({"error": str(error)})


@telemetry_tool("generate_tripo3d_model")
@mcp.tool()
async def generate_tripo3d_model(
    ctx: Context,
    text_prompt: Optional[str] = None,
    image_url: Optional[str] = None,
) -> str:
    """Generate a Tripo3D model from text or image input."""
    try:
        if not text_prompt and not image_url:
            raise ValueError("Either text_prompt or image_url must be provided")

        blender = get_blender_connection()
        params = {}
        if text_prompt:
            params["text_prompt"] = text_prompt
        if image_url:
            params["image_url"] = image_url

        result = blender.send_command("generate_tripo3d_model", params)
        return json.dumps(result, indent=2)
    except Exception as error:
        logger.error(f"Error generating Tripo3D model: {str(error)}")
        return json.dumps({"error": str(error)})


@telemetry_tool("poll_tripo3d_status")
@mcp.tool()
async def poll_tripo3d_status(ctx: Context, task_id: str) -> str:
    """Poll a Tripo3D generation task."""
    try:
        blender = get_blender_connection()
        result = blender.send_command("poll_tripo3d_status", {"task_id": task_id})
        return json.dumps(result, indent=2)
    except Exception as error:
        logger.error(f"Error polling Tripo3D status: {str(error)}")
        return json.dumps({"error": str(error)})


@telemetry_tool("import_tripo3d_model")
@mcp.tool()
async def import_tripo3d_model(
    ctx: Context,
    model_url: str,
    name: str = "Tripo3D_Model",
) -> str:
    """Import a generated Tripo3D model."""
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "import_tripo3d_model",
            {"model_url": model_url, "name": name},
        )
        return json.dumps(result, indent=2)
    except Exception as error:
        logger.error(f"Error importing Tripo3D model: {str(error)}")
        return json.dumps({"error": str(error)})
