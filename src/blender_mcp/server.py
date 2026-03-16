"""
Blender MCP Server

Main MCP server implementation with full protocol compliance.
Integrates tools, prompts, resources, and completions.
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from .mcp_compat import FastMCP, Context, Image
from .logging_config import get_logger
from .telemetry import record_startup
from .telemetry_decorator import telemetry_tool
from .core.connection import get_blender_connection, shutdown_connection
from .core.tool_loader import import_all_tool_modules
from .resources import get_resource_registry
from .completions import get_completion_registry

logger = get_logger("BlenderMCPServer")

# Server metadata
SERVER_NAME = "BlenderMCP"
SERVER_VERSION = "1.5.5"
PROTOCOL_VERSION = "2024-11-05"

# Default configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876


@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle."""
    logger.info(f"{SERVER_NAME} server starting up (protocol: {PROTOCOL_VERSION})")
    
    try:
        # Record startup event for telemetry
        try:
            record_startup()
        except Exception as e:
            logger.debug(f"Failed to record startup telemetry: {e}")
        
        # Try to connect to Blender on startup
        try:
            blender = get_blender_connection()
            logger.info("Successfully connected to Blender on startup")
            logger.info("Connection verified - Blender MCP addon is ready")
        except Exception as e:
            logger.warning(f"Could not connect to Blender on startup: {e}")
            logger.warning("Make sure the Blender addon is running and the server is started")
            logger.warning("You can start the server from the Blender MCP panel in Blender")
        
        # Yield server capabilities and info
        yield {
            "server_name": SERVER_NAME,
            "server_version": SERVER_VERSION,
            "protocol_version": PROTOCOL_VERSION,
        }
        
    finally:
        logger.info("Disconnecting from Blender on shutdown")
        shutdown_connection()
        logger.info(f"{SERVER_NAME} server shut down")


# Create the MCP server with lifespan support
mcp = FastMCP(
    SERVER_NAME,
    lifespan=server_lifespan,
)

# Import all tool modules dynamically so the MCP surface stays synchronized
import_all_tool_modules()


# =============================================================================
# MCP Resources
# =============================================================================

@mcp.resource("catalog://tools")
async def resource_tools() -> str:
    """Tool catalog resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("catalog://tools")


@mcp.resource("catalog://commands")
async def resource_commands() -> str:
    """Command catalog resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("catalog://commands")


@mcp.resource("catalog://schemas")
async def resource_schemas() -> str:
    """Schema catalog resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("catalog://schemas")


@mcp.resource("catalog://protocol")
async def resource_protocol() -> str:
    """Protocol capabilities resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("catalog://protocol")


@mcp.resource("catalog://pipeline")
async def resource_pipeline() -> str:
    """Pipeline capabilities resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("catalog://pipeline")


@mcp.resource("scene://current")
async def resource_scene_current() -> str:
    """Current scene state resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("scene://current")


@mcp.resource("scene://selection")
async def resource_scene_selection() -> str:
    """Current selection resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("scene://selection")


@mcp.resource("pipeline://projects")
async def resource_pipeline_projects() -> str:
    """Pipeline projects resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("pipeline://projects")


@mcp.resource("pipeline://status")
async def resource_pipeline_status() -> str:
    """Pipeline status resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("pipeline://status")


@mcp.resource("publish://status")
async def resource_publish_status() -> str:
    """Publish system status resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("publish://status")


@mcp.resource("ocio://status")
async def resource_ocio_status() -> str:
    """Color pipeline status resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("ocio://status")


@mcp.resource("usd://status")
async def resource_usd_status() -> str:
    """USD system status resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource("usd://status")


# =============================================================================
# MCP Resource Templates
# =============================================================================

@mcp.resource("repo://tree/{path}")
async def resource_repo_tree(path: str) -> str:
    """Repository tree resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"repo://tree/{path}")


@mcp.resource("repo://file/{path}")
async def resource_repo_file(path: str) -> str:
    """Repository file resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"repo://file/{path}")


@mcp.resource("scene://object/{object_name}")
async def resource_scene_object(object_name: str) -> str:
    """Scene object resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"scene://object/{object_name}")


@mcp.resource("pipeline://project/{project_code}")
async def resource_pipeline_project(project_code: str) -> str:
    """Project details resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"pipeline://project/{project_code}")


@mcp.resource("pipeline://sequence/{sequence_code}")
async def resource_pipeline_sequence(sequence_code: str) -> str:
    """Sequence details resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"pipeline://sequence/{sequence_code}")


@mcp.resource("pipeline://shot/{shot_name}")
async def resource_pipeline_shot(shot_name: str) -> str:
    """Shot details resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"pipeline://shot/{shot_name}")


@mcp.resource("pipeline://asset/{asset_type}/{asset_name}")
async def resource_pipeline_asset(asset_type: str, asset_name: str) -> str:
    """Asset details resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"pipeline://asset/{asset_type}/{asset_name}")


@mcp.resource("publish://entity/{entity_type}/{entity_id}")
async def resource_publish_entity(entity_type: str, entity_id: str) -> str:
    """Entity publishes resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"publish://entity/{entity_type}/{entity_id}")


@mcp.resource("publish://manifest/{publish_id}")
async def resource_publish_manifest(publish_id: str) -> str:
    """Publish manifest resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"publish://manifest/{publish_id}")


@mcp.resource("ocio://project/{project_code}")
async def resource_ocio_project(project_code: str) -> str:
    """Project color config resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"ocio://project/{project_code}")


@mcp.resource("usd://package/{package_id}")
async def resource_usd_package(package_id: str) -> str:
    """USD package resource."""
    registry = get_resource_registry(mcp)
    return await registry.read_resource(f"usd://package/{package_id}")


# =============================================================================
# MCP Prompts
# =============================================================================

@mcp.prompt()
def asset_creation_strategy() -> str:
    """Defines the preferred strategy for creating assets in Blender."""
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
    3. Hyper3D(Rodin)
        Hyper3D Rodin is good at generating 3D models for single item.
        Use get_hyper3d_status() to verify its status
    4. Hunyuan3D
        Hunyuan3D is good at generating 3D models for single item.
        Use get_hunyuan3d_status() to verify its status

2. Always check the world_bounding_box for each item so that:
    - Ensure that all objects that should not be clipping are not clipping.
    - Items have right spatial relationship.

Only fall back to scripting when:
- PolyHaven, Sketchfab, Hyper3D, and Hunyuan3D are all disabled
- A simple primitive is explicitly requested
- No suitable asset exists in any of the libraries
"""


@mcp.prompt()
def production_pipeline_strategy() -> str:
    """Defines the preferred strategy for production pipeline and shot management."""
    return """When working in a production pipeline context:

1. Always work in a sequence/shot context:
   - Use create_shot(shot_name, sequence, shot_number, description, duration, assets) to create shots.
   - Use setup_shot_camera(shot_name, camera_type, focal_length, aperture, shot_type) to set up the camera.
   - Use create_shot_version(shot_name, version_type, notes, artist) when saving iterations.
   - Use review_shot(shot_name, version, review_type, notes, approved) to record approval.

2. Observe the scene before and after changes.

3. Check production and render status before starting.

4. When rendering, use create_render_job() and monitor_render_job().

5. Use review_shot and versioning for iterations.
"""


@mcp.prompt()
def animation_rigging_strategy() -> str:
    """Defines the preferred strategy for rigging and animation."""
    return """When rigging and animating characters or objects:

1. Check status first with get_rigging_status() and get_animation_status().

2. Create or use existing rigs before animating.

3. Prefer structured tools over execute_blender_code.

4. Verify results with observe_scene().
"""


@mcp.prompt()
def autonomous_production_workflow() -> str:
    """High-level workflow for end-to-end autonomous production."""
    return """For end-to-end autonomous production, follow this workflow:

1. Start with observation and production context.

2. Block layout (assets, camera, lighting).

3. Rigging and animation.

4. Lighting and render setup.

5. Review.

General rules:
- Observe -> plan -> act -> observe.
- Use request_id and idempotency keys for retries.
- Prefer atomic tools over execute_blender_code.
"""


# =============================================================================
# MCP Completions
# =============================================================================

@mcp.completion(
    ref_type="resource",
    ref_key="pipeline://project/{project_code}",
    argument_key="project_code",
)
async def complete_project_code(prefix: Optional[str] = None) -> List[Dict[str, str]]:
    """Complete project codes."""
    from .completions import complete
    return complete("resource", "pipeline://project/{project_code}", "project_code", prefix)


@mcp.completion(
    ref_type="resource",
    ref_key="pipeline://shot/{shot_name}",
    argument_key="shot_name",
)
async def complete_shot_name(prefix: Optional[str] = None) -> List[Dict[str, str]]:
    """Complete shot names."""
    from .completions import complete
    return complete("resource", "pipeline://shot/{shot_name}", "shot_name", prefix)


@mcp.completion(
    ref_type="tool",
    ref_key="get_object_info",
    argument_key="object_name",
)
async def complete_object_name(prefix: Optional[str] = None) -> List[Dict[str, str]]:
    """Complete object names."""
    from .completions import complete
    return complete("tool", "get_object_info", "object_name", prefix)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
