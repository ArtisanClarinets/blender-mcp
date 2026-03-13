"""
Job management tools

Provides unified job management for async generators.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..mcp_compat import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


@telemetry_tool("create_job")
@mcp.tool()
async def create_job(ctx: Context, provider: str, payload: Dict[str, Any]) -> str:
    """
    Create a new async job for AI generation.

    Parameters:
    - provider: Provider name ("hyper3d", "hunyuan3d", "tripo3d")
    - payload: Job-specific payload
      - For Hyper3D: {"text_prompt": "...", "bbox_condition": [...]}
      - For Hunyuan3D: {"text_prompt": "...", "input_image_url": "..."}
      - For Tripo3D: {"text_prompt": "..."} or {"image_url": "..."}

    Returns:
    - JSON string with job_id, provider, and status
    """
    try:
        blender = get_blender_connection()

        params = {"provider": provider, "payload": payload}

        result = blender.send_command("create_job", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_job")
@mcp.tool()
async def get_job(ctx: Context, job_id: str) -> str:
    """
    Get the status of a job.

    Parameters:
    - job_id: Job ID from create_job

    Returns:
    - JSON string with job status and result
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_job", {"job_id": job_id})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting job: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("import_job_result")
@mcp.tool()
async def import_job_result(
    ctx: Context, job_id: str, name: str, target_size: Optional[float] = None
) -> str:
    """
    Import the result of a completed job.

    Parameters:
    - job_id: Job ID from create_job
    - name: Object name in scene
    - target_size: Optional target size in meters

    Returns:
    - JSON string with import result
    """
    try:
        blender = get_blender_connection()

        params = {"job_id": job_id, "name": name}
        if target_size is not None:
            params["target_size"] = target_size

        result = blender.send_command("import_job_result", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error importing job result: {str(e)}")
        return json.dumps({"error": str(e)})


# Hyper3D Specific Tools


@telemetry_tool("get_hyper3d_status")
@mcp.tool()
async def get_hyper3d_status(ctx: Context) -> str:
    """Check Hyper3D Rodin integration status."""
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_hyper3d_status", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting Hyper3D status: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("generate_hyper3d_model_via_text")
@mcp.tool()
async def generate_hyper3d_model_via_text(
    ctx: Context, text_prompt: str, bbox_condition: Optional[List[float]] = None
) -> str:
    """
    Generate 3D model using Hyper3D from text prompt.

    Parameters:
    - text_prompt: English description of desired model
    - bbox_condition: Optional [length, width, height] ratio

    Returns:
    - JSON string with generation result
    """
    try:
        blender = get_blender_connection()
        params = {"text_prompt": text_prompt}
        if bbox_condition:
            params["bbox_condition"] = bbox_condition
        result = blender.send_command("generate_hyper3d_model_via_text", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error generating Hyper3D model: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("generate_hyper3d_model_via_images")
@mcp.tool()
async def generate_hyper3d_model_via_images(
    ctx: Context,
    input_image_paths: Optional[List[str]] = None,
    input_image_urls: Optional[List[str]] = None,
    bbox_condition: Optional[List[float]] = None,
) -> str:
    """
    Generate 3D model using Hyper3D from images.

    Parameters:
    - input_image_paths: Absolute paths to images (list)
    - input_image_urls: URLs to images (list)
    - bbox_condition: Optional [L,W,H] ratio

    Returns:
    - JSON string with generation result
    """
    try:
        blender = get_blender_connection()
        params = {}
        if input_image_paths:
            params["input_image_paths"] = input_image_paths
        if input_image_urls:
            params["input_image_urls"] = input_image_urls
        if bbox_condition:
            params["bbox_condition"] = bbox_condition
        result = blender.send_command("generate_hyper3d_model_via_images", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error generating Hyper3D model from images: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("poll_rodin_job_status")
@mcp.tool()
async def poll_rodin_job_status(
    ctx: Context,
    subscription_key: Optional[str] = None,
    request_id: Optional[str] = None,
) -> str:
    """
    Check Hyper3D generation task status.

    Parameters:
    - subscription_key: For MAIN_SITE mode
    - request_id: For FAL_AI mode

    Returns:
    - JSON string with job status
    """
    try:
        blender = get_blender_connection()
        params = {}
        if subscription_key:
            params["subscription_key"] = subscription_key
        if request_id:
            params["request_id"] = request_id
        result = blender.send_command("poll_rodin_job_status", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error polling Rodin job: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("import_generated_asset")
@mcp.tool()
async def import_generated_asset(
    ctx: Context,
    name: str,
    task_uuid: Optional[str] = None,
    request_id: Optional[str] = None,
) -> str:
    """
    Import Hyper3D generated asset.

    Parameters:
    - name: Object name in scene
    - task_uuid: For MAIN_SITE mode
    - request_id: For FAL_AI mode

    Returns:
    - JSON string with import result
    """
    try:
        blender = get_blender_connection()
        params = {"name": name}
        if task_uuid:
            params["task_uuid"] = task_uuid
        if request_id:
            params["request_id"] = request_id
        result = blender.send_command("import_generated_asset", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error importing generated asset: {str(e)}")
        return json.dumps({"error": str(e)})


# Hunyuan3D Specific Tools


@telemetry_tool("get_hunyuan3d_status")
@mcp.tool()
async def get_hunyuan3d_status(ctx: Context) -> str:
    """Check Hunyuan3D integration status."""
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_hunyuan3d_status", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting Hunyuan3D status: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("generate_hunyuan3d_model")
@mcp.tool()
async def generate_hunyuan3d_model(
    ctx: Context,
    text_prompt: Optional[str] = None,
    input_image_url: Optional[str] = None,
) -> str:
    """
    Generate 3D model using Hunyuan3D.

    Parameters:
    - text_prompt: Description in English/Chinese
    - input_image_url: Optional image URL

    Returns:
    - JSON string with generation result
    """
    try:
        if not text_prompt and not input_image_url:
            raise ValueError("Either text_prompt or input_image_url must be provided")

        blender = get_blender_connection()
        params = {}
        if text_prompt:
            params["text_prompt"] = text_prompt
        if input_image_url:
            params["input_image_url"] = input_image_url
        result = blender.send_command("generate_hunyuan3d_model", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error generating Hunyuan3D model: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("poll_hunyuan_job_status")
@mcp.tool()
async def poll_hunyuan_job_status(ctx: Context, job_id: str) -> str:
    """
    Check Hunyuan3D job status.

    Parameters:
    - job_id: Job ID from generation

    Returns:
    - JSON string with job status
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("poll_hunyuan_job_status", {"job_id": job_id})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error polling Hunyuan job: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("import_generated_asset_hunyuan")
@mcp.tool()
async def import_generated_asset_hunyuan(
    ctx: Context, name: str, zip_file_url: str
) -> str:
    """
    Import Hunyuan3D generated asset.

    Parameters:
    - name: Object name in scene
    - zip_file_url: ZIP file URL from job status

    Returns:
    - JSON string with import result
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command(
            "import_generated_asset_hunyuan",
            {"name": name, "zip_file_url": zip_file_url},
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error importing Hunyuan asset: {str(e)}")
        return json.dumps({"error": str(e)})
