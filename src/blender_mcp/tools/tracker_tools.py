"""
Tracker integration tools for Blender MCP.

Provides tools for production tracker management.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..mcp_compat import Context
from ..server import mcp
from ..telemetry_decorator import telemetry_tool
from ..pipeline.tracker import (
    get_tracker_adapter,
    set_tracker_adapter,
    get_tracker_status,
    get_available_adapters,
)

logger = logging.getLogger("BlenderMCPTools")


@telemetry_tool("get_tracker_status")
@mcp.tool()
async def get_tracker_status_tool(ctx: Context) -> str:
    """
    Get the current tracker status.
    
    Returns:
    - JSON string with tracker status
    """
    try:
        status = get_tracker_status()
        
        return json.dumps({
            "success": True,
            "status": status,
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting tracker status: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("set_tracker_adapter")
@mcp.tool()
async def set_tracker_adapter_tool(
    ctx: Context,
    adapter_name: str,
) -> str:
    """
    Set the current tracker adapter.
    
    Parameters:
    - adapter_name: Adapter name (local, shotgrid, ayon, ftrack)
    
    Returns:
    - JSON string with result
    """
    try:
        available = get_available_adapters()
        
        if adapter_name not in available:
            return json.dumps({
                "error": f"Unknown adapter: {adapter_name}",
                "available_adapters": available,
            })
        
        adapter = set_tracker_adapter(adapter_name)
        
        return json.dumps({
            "success": True,
            "adapter": adapter.name,
            "connected": adapter.is_connected(),
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error setting tracker adapter: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("list_tracker_adapters")
@mcp.tool()
async def list_tracker_adapters(ctx: Context) -> str:
    """
    List available tracker adapters.
    
    Returns:
    - JSON string with adapter list
    """
    try:
        adapters = get_available_adapters()
        
        return json.dumps({
            "success": True,
            "adapters": adapters,
            "descriptions": {
                "local": "Local file-based tracker (default)",
                "shotgrid": "Autodesk ShotGrid / Flow Production Tracking",
                "ayon": "Ynput AYON",
                "ftrack": "ftrack Studio",
            },
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error listing tracker adapters: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("sync_project_context")
@mcp.tool()
async def sync_project_context(
    ctx: Context,
    project_code: str,
) -> str:
    """
    Sync project context with the tracker.
    
    Parameters:
    - project_code: Project code to sync
    
    Returns:
    - JSON string with sync result
    """
    try:
        from ..pipeline import get_pipeline_storage
        storage = get_pipeline_storage()
        
        project = storage.get_project(project_code)
        if not project:
            return json.dumps({"error": f"Project not found: {project_code}"})
        
        adapter = get_tracker_adapter()
        
        if not adapter.is_connected():
            adapter.connect()
        
        # Get sync state
        sync_state = adapter.sync_entity_status("project", project.id, project.tracker_project_id)
        
        # Update project's tracker reference
        project.tracker_project_id = sync_state.tracker_id
        storage.update_project(project)
        
        return json.dumps({
            "success": True,
            "sync_state": sync_state.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error syncing project: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("sync_shot_context")
@mcp.tool()
async def sync_shot_context(
    ctx: Context,
    project_code: str,
    shot_name: str,
) -> str:
    """
    Sync shot context with the tracker.
    
    Parameters:
    - project_code: Project code
    - shot_name: Shot name to sync
    
    Returns:
    - JSON string with sync result
    """
    try:
        from ..pipeline import get_pipeline_storage
        storage = get_pipeline_storage()
        
        shot = storage.get_shot(project_code, shot_name)
        if not shot:
            return json.dumps({"error": f"Shot not found: {shot_name}"})
        
        adapter = get_tracker_adapter()
        
        if not adapter.is_connected():
            adapter.connect()
        
        # Get sync state
        sync_state = adapter.sync_entity_status("shot", shot.id, shot.tracker_shot_id)
        
        # Update shot's tracker reference
        shot.tracker_shot_id = sync_state.tracker_id
        storage.update_shot(shot)
        
        return json.dumps({
            "success": True,
            "sync_state": sync_state.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error syncing shot: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("push_publish_status")
@mcp.tool()
async def push_publish_status(
    ctx: Context,
    publish_id: str,
) -> str:
    """
    Push publish status to the tracker.
    
    Parameters:
    - publish_id: Publish ID to push
    
    Returns:
    - JSON string with push result
    """
    try:
        from ..pipeline import get_pipeline_storage
        storage = get_pipeline_storage()
        
        publish = storage.get_publish(publish_id)
        if not publish:
            return json.dumps({"error": f"Publish not found: {publish_id}"})
        
        adapter = get_tracker_adapter()
        
        if not adapter.is_connected():
            adapter.connect()
        
        # Push publish to tracker
        result = adapter.publish_version(
            entity_id=publish.entity_id,
            version_number=publish.version,
            description=publish.description,
            files=[{"path": a.path, "type": a.artifact_type} for a in publish.artifacts],
        )
        
        return json.dumps({
            "success": True,
            "tracker_result": result,
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error pushing publish status: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_tracker_projects")
@mcp.tool()
async def get_tracker_projects(ctx: Context) -> str:
    """
    Get projects from the tracker.
    
    Returns:
    - JSON string with project list
    """
    try:
        adapter = get_tracker_adapter()
        
        if not adapter.is_connected():
            adapter.connect()
        
        projects = adapter.get_projects()
        
        return json.dumps({
            "success": True,
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "code": p.code,
                    "status": p.status,
                }
                for p in projects
            ],
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting tracker projects: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_tracker_shots")
@mcp.tool()
async def get_tracker_shots(
    ctx: Context,
    sequence_id: str,
) -> str:
    """
    Get shots from the tracker for a sequence.
    
    Parameters:
    - sequence_id: Sequence ID
    
    Returns:
    - JSON string with shot list
    """
    try:
        adapter = get_tracker_adapter()
        
        if not adapter.is_connected():
            adapter.connect()
        
        shots = adapter.get_shots(sequence_id)
        
        return json.dumps({
            "success": True,
            "shots": [
                {
                    "id": s.id,
                    "name": s.name,
                    "shot_number": s.shot_number,
                    "status": s.status,
                }
                for s in shots
            ],
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting tracker shots: {e}")
        return json.dumps({"error": str(e)})
