# blender_mcp_server.py
from .mcp_compat import FastMCP, Context, Image
import json
import asyncio
import logging
import tempfile
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List
import os
import uuid
from pathlib import Path
import base64
from urllib.parse import urlparse

from .logging_config import get_logger
from .telemetry import record_startup
from .telemetry_decorator import telemetry_tool
from .core.connection import get_blender_connection, shutdown_connection
from .core.tool_loader import import_all_tool_modules

logger = get_logger("BlenderMCPServer")

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876
CIRCUIT_BREAKER_OPEN_MESSAGE = (
    "Connection to Blender temporarily unavailable after repeated failures"
)


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    # We don't need to create a connection here since we're using the global connection
    # for resources and tools

    try:
        # Just log that we're starting up
        logger.info("BlenderMCP server starting up")

        # Record startup event for telemetry
        try:
            record_startup()
        except Exception as e:
            logger.debug(f"Failed to record startup telemetry: {e}")

        # Try to connect to Blender on startup to verify it's available
        try:
            # This will initialize the global connection if needed
            blender = get_blender_connection()
            logger.info("Successfully connected to Blender on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Blender on startup: {str(e)}")
            logger.warning(
                "Make sure the Blender addon is running before using Blender resources or tools"
            )

        # Return an empty context - we're using the global connection
        yield {}
    finally:
        # Clean up the global connection on shutdown
        logger.info("Disconnecting from Blender on shutdown")
        shutdown_connection()
        logger.info("BlenderMCP server shut down")


# Create the MCP server with lifespan support
mcp = FastMCP("BlenderMCP", lifespan=server_lifespan)

# Import all tool modules dynamically so the MCP surface stays synchronized.
import_all_tool_modules()


@mcp.prompt()
def asset_creation_strategy() -> str:
    """Defines the preferred strategy for creating assets in Blender"""
    return """When creating 3D content in Blender, always start by checking if integrations are available:

    0. Before anything, always check the scene from get_scene_info()
    1. First use the following tools to verify if the following integrations are enabled:
        1. PolyHaven
            Use get_polyhaven_status() to verify its status
            If PolyHaven is enabled:
            - For objects/models: Use download_polyhaven_asset() with asset_type="models"
            - For materials/textures: Use download_polyhaven_asset() with asset_type="textures"
            - For environment lighting: Use download_polyhaven_asset() with asset_type="hdris"
        2. Sketchfab
            Sketchfab is good at Realistic models, and has a wider variety of models than PolyHaven.
            Use get_sketchfab_status() to verify its status
            If Sketchfab is enabled:
            - For objects/models: First search using search_sketchfab_models() with your query
            - Then download specific models using download_sketchfab_model() with the UID
            - Note that only downloadable models can be accessed, and API key must be properly configured
            - Sketchfab has a wider variety of models than PolyHaven, especially for specific subjects
        3. Hyper3D(Rodin)
            Hyper3D Rodin is good at generating 3D models for single item.
            So don't try to:
            1. Generate the whole scene with one shot
            2. Generate ground using Hyper3D
            3. Generate parts of the items separately and put them together afterwards

            Use get_hyper3d_status() to verify its status
            If Hyper3D is enabled:
            - For objects/models, do the following steps:
                1. Create the model generation task
                    - Use generate_hyper3d_model_vi-images() if image(s) is/are given
                    - Use generate_hyper3d_model_via_text() if generating 3D asset using text prompt
                    If key type is free_trial and insufficient balance error returned, tell the user that the free trial key can only generated limited models everyday, they can choose to:
                    - Wait for another day and try again
                    - Go to hyper3d.ai to find out how to get their own API key
                    - Go to fal.ai to get their own private API key
                2. Poll the status
                    - Use poll_rodin_job_status() to check if the generation task has completed or failed
                3. Import the asset
                    - Use import_generated_asset() to import the generated GLB model the asset
                4. After importing the asset, ALWAYS check the world_bounding_box of the imported mesh, and adjust the mesh's location and size
                    Adjust the imported mesh's location, scale, rotation, so that the mesh is on the right spot.

                You can reuse assets previous generated by running python code to duplicate the object, without creating another generation task.
        4. Hunyuan3D
            Hunyuan3D is good at generating 3D models for single item.
            So don't try to:
            1. Generate the whole scene with one shot
            2. Generate ground using Hunyuan3D
            3. Generate parts of the items separately and put them together afterwards

            Use get_hunyuan3d_status() to verify its status
            If Hunyuan3D is enabled:
                if Hunyuan3D mode is "OFFICIAL_API":
                    - For objects/models, do the following steps:
                        1. Create the model generation task
                            - Use generate_hunyuan3d_model by providing either a **text description** OR an **image(local or urls) reference**.
                            - Go to cloud.tencent.com out how to get their own SecretId and SecretKey
                        2. Poll the status
                            - Use poll_hunyuan_job_status() to check if the generation task has completed or failed
                        3. Import the asset
                            - Use import_generated_asset_hunyuan() to import the generated OBJ model the asset
                    if Hunyuan3D mode is "LOCAL_API":
                        - For objects/models, do the following steps:
                        1. Create the model generation task
                            - Use generate_hunyuan3d_model if image (local or urls)  or text prompt is given and import the asset

                You can reuse assets previous generated by running python code to duplicate the object, without creating another generation task.

    3. Always check the world_bounding_box for each item so that:
        - Ensure that all objects that should not be clipping are not clipping.
        - Items have right spatial relationship.
    
    4. Recommended asset source priority:
        - For specific existing objects: First try Sketchfab, then PolyHaven
        - For generic objects/furniture: First try PolyHaven, then Sketchfab
        - For custom or unique items not available in libraries: Use Hyper3D Rodin or Hunyuan3D
        - For environment lighting: Use PolyHaven HDRIs
        - For materials/textures: Use PolyHaven textures

    Only fall back to scripting when:
    - PolyHaven, Sketchfab, Hyper3D, and Hunyuan3D are all disabled
    - A simple primitive is explicitly requested
    - No suitable asset exists in any of the libraries
    - Hyper3D Rodin or Hunyuan3D failed to generate the desired asset
    - The task specifically requires a basic material/color
    """


@mcp.prompt()
def production_pipeline_strategy() -> str:
    """Defines the preferred strategy for production pipeline and shot management."""
    return """When working in a production pipeline context:

    1. Always work in a sequence/shot context:
       - Use create_shot(shot_name, sequence, shot_number, description, duration, assets) to create shots.
       - Use setup_shot_camera(shot_name, camera_type, focal_length, aperture, shot_type) to set up the camera for each shot.
       - Use create_shot_version(shot_name, version_type, notes, artist) when saving iterations (layout, animation, lighting, render).
       - Use review_shot(shot_name, version, review_type, notes, approved) to record approval or feedback.

    2. Observe the scene before and after changes:
       - Call get_scene_info() or observe_scene() before making changes and after major steps.
       - Use get_scene_hash() to detect if the scene actually changed.

    3. Check production and render status before starting:
       - Use get_production_status() to see existing shots and versioning state.
       - Use get_render_pipeline_status() to see queued render jobs.

    4. When rendering:
       - Use create_render_job(job_name, frame_range, output_path, priority, nodes, render_settings) to queue a job.
       - Use monitor_render_job(job_id) to check progress.
       - Use setup_render_passes() and render_animation_passes() for multi-pass output.
       - When a render manifest or farm handoff is available, use it to export a job description for external runners.

    5. Use review_shot and versioning for iterations so that feedback is tracked and changes are non-destructive where possible.
    """


@mcp.prompt()
def animation_rigging_strategy() -> str:
    """Defines the preferred strategy for rigging and animation."""
    return """When rigging and animating characters or objects:

    1. Check status first:
       - Use get_rigging_status() to see if rigging tools are available.
       - Use get_animation_status() to see if animation tools are available.

    2. Create or use existing rigs before animating:
       - Use create_auto_rig(character_name, rig_type, skeleton_template, ik_fk_switch, facial_rig) for character rigs.
       - Use generate_skeleton(mesh_name, skeleton_type, bone_count, symmetry) when you need custom skeletons.
       - Use auto_weight_paint and create_control_rig as needed.

    3. Prefer structured tools over execute_blender_code:
       - Use set_keyframe(object_name, property_path, frame, value, interpolation) for keyframes.
       - Use create_animation_curve() for curve-based animation.
       - Use create_animation_layer() for non-destructive animation layers.
       - Use import_motion_capture() and retarget_animation() when using mocap data.
       - Use create_facial_animation() for facial performance.

    4. Verify results:
       - Use observe_scene() or get_object_info(object_name) to confirm rig and keyframes are present and correct.
    """


@mcp.prompt()
def autonomous_production_workflow() -> str:
    """High-level workflow for end-to-end autonomous production (Pixar-style pipeline)."""
    return """For end-to-end autonomous production, follow this workflow:

    1. Start with observation and production context:
       - get_scene_info() to understand the current scene.
       - get_production_status() and get_render_pipeline_status() to see existing shots and jobs.
       - Create sequence/shot with create_shot() when starting a new shot.

    2. Block layout (assets, camera, lighting):
       - Use asset_creation_strategy (PolyHaven, Sketchfab, Hyper3D, Hunyuan3D) for models and materials.
       - Use setup_shot_camera() or create_composition_camera() and lighting tools (create_three_point_lighting, create_studio_lighting, etc.).
       - observe_scene() after layout to verify.

    3. Rigging and animation:
       - Follow animation_rigging_strategy: create rigs, then set keyframes and animation layers.
       - create_shot_version(shot_name, version_type="animation") when animation is blocked.

    4. Lighting and render setup:
       - Adjust lighting as needed; create_shot_version(shot_name, version_type="lighting").
       - setup_render_passes() and create_render_job() or export render manifest for farm handoff.

    5. Review:
       - review_shot(shot_name, version, approved=...) to record approval or request changes.

    General rules:
    - Observe → plan → act → observe. Always verify with get_scene_info/get_scene_hash after significant changes.
    - Use request_id and idempotency keys for retries so duplicate operations are safe.
    - Prefer atomic tools over execute_blender_code for predictable, debuggable results.
    """


# Main execution

def main():
    """Run the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()