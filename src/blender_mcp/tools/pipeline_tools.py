"""
Pipeline management tools for Blender MCP.

Provides tools for managing the production pipeline including
projects, sequences, shots, assets, and publishes.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..mcp_compat import Context
from ..server import mcp
from ..telemetry_decorator import telemetry_tool
from ..pipeline import (
    get_pipeline_storage,
    get_publish_manager,
    get_lineage_tracker,
)
from ..pipeline.entities import (
    Project,
    Sequence,
    Shot,
    Asset,
    AssetType,
    EntityStatus,
    PublishStage,
)

logger = logging.getLogger("BlenderMCPTools")


# =============================================================================
# Project Management Tools
# =============================================================================

@telemetry_tool("create_project")
@mcp.tool()
async def create_project(
    ctx: Context,
    project_code: str,
    project_name: str,
    description: str = "",
    created_by: str = "unknown",
) -> str:
    """
    Create a new pipeline project.
    
    Parameters:
    - project_code: Unique project code (alphanumeric, starts with letter)
    - project_name: Human-readable project name
    - description: Project description
    - created_by: Creator identifier
    
    Returns:
    - JSON string with project creation result
    """
    try:
        storage = get_pipeline_storage()
        
        # Check if project already exists
        existing = storage.get_project(project_code)
        if existing:
            return json.dumps({"error": f"Project already exists: {project_code}"})
        
        project = Project(
            code=project_code,
            name=project_name,
            description=description,
            created_by=created_by,
            root_path=str(storage.root / "projects" / project_code),
        )
        
        storage.create_project(project)
        
        return json.dumps({
            "success": True,
            "project": project.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_project")
@mcp.tool()
async def get_project(ctx: Context, project_code: str) -> str:
    """
    Get project details.
    
    Parameters:
    - project_code: Project code
    
    Returns:
    - JSON string with project details
    """
    try:
        storage = get_pipeline_storage()
        project = storage.get_project(project_code)
        
        if not project:
            return json.dumps({"error": f"Project not found: {project_code}"})
        
        return json.dumps({
            "success": True,
            "project": project.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("list_projects")
@mcp.tool()
async def list_projects(ctx: Context) -> str:
    """
    List all pipeline projects.
    
    Returns:
    - JSON string with list of projects
    """
    try:
        storage = get_pipeline_storage()
        projects = storage.list_projects()
        
        return json.dumps({
            "success": True,
            "projects": [p.model_dump() for p in projects],
            "count": len(projects),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Sequence Management Tools
# =============================================================================

@telemetry_tool("create_sequence")
@mcp.tool()
async def create_sequence(
    ctx: Context,
    project_code: str,
    sequence_code: str,
    sequence_name: str,
    description: str = "",
) -> str:
    """
    Create a new sequence in a project.
    
    Parameters:
    - project_code: Parent project code
    - sequence_code: Unique sequence code
    - sequence_name: Human-readable sequence name
    - description: Sequence description
    
    Returns:
    - JSON string with sequence creation result
    """
    try:
        storage = get_pipeline_storage()
        
        # Check project exists
        project = storage.get_project(project_code)
        if not project:
            return json.dumps({"error": f"Project not found: {project_code}"})
        
        sequence = Sequence(
            code=sequence_code,
            name=sequence_name,
            description=description,
            project_code=project_code,
        )
        
        storage.create_sequence(sequence)
        
        return json.dumps({
            "success": True,
            "sequence": sequence.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error creating sequence: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("list_sequences")
@mcp.tool()
async def list_sequences(ctx: Context, project_code: str) -> str:
    """
    List all sequences in a project.
    
    Parameters:
    - project_code: Project code
    
    Returns:
    - JSON string with list of sequences
    """
    try:
        storage = get_pipeline_storage()
        sequences = storage.list_sequences(project_code)
        
        return json.dumps({
            "success": True,
            "sequences": [s.model_dump() for s in sequences],
            "count": len(sequences),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error listing sequences: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Shot Management Tools
# =============================================================================

@telemetry_tool("create_shot_pipeline")
@mcp.tool()
async def create_shot_pipeline(
    ctx: Context,
    project_code: str,
    sequence_code: str,
    shot_name: str,
    shot_number: int,
    description: str = "",
    frame_start: int = 1001,
    frame_end: int = 1100,
) -> str:
    """
    Create a new shot in the pipeline (durable storage).
    
    Parameters:
    - project_code: Parent project code
    - sequence_code: Parent sequence code
    - shot_name: Unique shot name
    - shot_number: Shot number for ordering
    - description: Shot description
    - frame_start: Start frame
    - frame_end: End frame
    
    Returns:
    - JSON string with shot creation result
    """
    try:
        storage = get_pipeline_storage()
        
        shot = Shot(
            name=shot_name,
            shot_number=shot_number,
            description=description,
            project_code=project_code,
            sequence_code=sequence_code,
            frame_start=frame_start,
            frame_end=frame_end,
        )
        
        storage.create_shot(shot)
        
        return json.dumps({
            "success": True,
            "shot": shot.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error creating shot: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("list_shots_pipeline")
@mcp.tool()
async def list_shots_pipeline(
    ctx: Context,
    project_code: str,
    sequence_code: Optional[str] = None,
) -> str:
    """
    List shots in the pipeline.
    
    Parameters:
    - project_code: Project code
    - sequence_code: Optional sequence filter
    
    Returns:
    - JSON string with list of shots
    """
    try:
        storage = get_pipeline_storage()
        shots = storage.list_shots(project_code, sequence_code)
        
        return json.dumps({
            "success": True,
            "shots": [s.model_dump() for s in shots],
            "count": len(shots),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error listing shots: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Asset Management Tools
# =============================================================================

@telemetry_tool("create_asset_pipeline")
@mcp.tool()
async def create_asset_pipeline(
    ctx: Context,
    project_code: str,
    asset_name: str,
    asset_type: str,
    description: str = "",
) -> str:
    """
    Create a new asset in the pipeline.
    
    Parameters:
    - project_code: Parent project code
    - asset_name: Unique asset name
    - asset_type: Asset type (character, prop, environment, etc.)
    - description: Asset description
    
    Returns:
    - JSON string with asset creation result
    """
    try:
        storage = get_pipeline_storage()
        
        asset = Asset(
            name=asset_name,
            asset_type=AssetType(asset_type),
            description=description,
            project_code=project_code,
        )
        
        storage.create_asset(asset)
        
        return json.dumps({
            "success": True,
            "asset": asset.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error creating asset: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("list_assets_pipeline")
@mcp.tool()
async def list_assets_pipeline(
    ctx: Context,
    project_code: str,
    asset_type: Optional[str] = None,
) -> str:
    """
    List assets in the pipeline.
    
    Parameters:
    - project_code: Project code
    - asset_type: Optional asset type filter
    
    Returns:
    - JSON string with list of assets
    """
    try:
        storage = get_pipeline_storage()
        assets = storage.list_assets(project_code, asset_type)
        
        return json.dumps({
            "success": True,
            "assets": [a.model_dump() for a in assets],
            "count": len(assets),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error listing assets: {e}")
        return json.dumps({"error": str(e)})


# =============================================================================
# Publish Management Tools
# =============================================================================

@telemetry_tool("create_publish_pipeline")
@mcp.tool()
async def create_publish_pipeline(
    ctx: Context,
    entity_type: str,
    entity_id: str,
    stage: str,
    description: str = "",
    created_by: str = "unknown",
    parent_publish_id: Optional[str] = None,
) -> str:
    """
    Create a new publish for an entity.
    
    Parameters:
    - entity_type: "shot" or "asset"
    - entity_id: Entity ID
    - stage: Pipeline stage (layout, animation, lighting, render, final)
    - description: Publish description
    - created_by: Creator identifier
    - parent_publish_id: Optional parent publish for lineage
    
    Returns:
    - JSON string with publish creation result
    """
    try:
        manager = get_publish_manager()
        
        publish = manager.create_publish(
            entity_type=entity_type,
            entity_id=entity_id,
            stage=stage,
            description=description,
            created_by=created_by,
            parent_publish_id=parent_publish_id,
        )
        
        return json.dumps({
            "success": True,
            "publish": publish.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error creating publish: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("list_publishes_pipeline")
@mcp.tool()
async def list_publishes_pipeline(
    ctx: Context,
    entity_type: str,
    entity_id: str,
    stage: Optional[str] = None,
) -> str:
    """
    List publishes for an entity.
    
    Parameters:
    - entity_type: "shot" or "asset"
    - entity_id: Entity ID
    - stage: Optional stage filter
    
    Returns:
    - JSON string with list of publishes
    """
    try:
        manager = get_publish_manager()
        publishes = manager.list_publishes_for_entity(entity_type, entity_id, stage)
        
        return json.dumps({
            "success": True,
            "publishes": [p.model_dump() for p in publishes],
            "count": len(publishes),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error listing publishes: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_publish_manifest")
@mcp.tool()
async def get_publish_manifest(ctx: Context, publish_id: str) -> str:
    """
    Get the complete manifest for a publish.
    
    Parameters:
    - publish_id: Publish ID
    
    Returns:
    - JSON string with publish manifest
    """
    try:
        manager = get_publish_manager()
        manifest = manager.get_publish_manifest(publish_id)
        
        return json.dumps({
            "success": True,
            "manifest": manifest,
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error getting publish manifest: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_publish_lineage")
@mcp.tool()
async def get_publish_lineage(
    ctx: Context,
    publish_id: str,
    direction: str = "both",
    max_depth: int = 10,
) -> str:
    """
    Get the lineage for a publish.
    
    Parameters:
    - publish_id: Publish ID
    - direction: "up" (ancestors), "down" (descendants), or "both"
    - max_depth: Maximum depth to traverse
    
    Returns:
    - JSON string with lineage information
    """
    try:
        tracker = get_lineage_tracker()
        lineage = tracker.get_lineage(publish_id, direction, max_depth)
        
        return json.dumps({
            "success": True,
            "lineage": {
                "nodes": [n.__dict__ for n in lineage.nodes],
                "length": lineage.length,
            },
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error getting publish lineage: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("approve_publish")
@mcp.tool()
async def approve_publish(
    ctx: Context,
    publish_id: str,
    notes: str = "",
) -> str:
    """
    Approve a pending publish.
    
    Parameters:
    - publish_id: Publish ID
    - notes: Approval notes
    
    Returns:
    - JSON string with approval result
    """
    try:
        manager = get_publish_manager()
        publish = manager.approve_publish(publish_id, notes)
        
        return json.dumps({
            "success": True,
            "publish": publish.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error approving publish: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("rollback_publish")
@mcp.tool()
async def rollback_publish(
    ctx: Context,
    entity_type: str,
    entity_id: str,
    target_version: int,
) -> str:
    """
    Rollback to a specific publish version.
    
    Parameters:
    - entity_type: "shot" or "asset"
    - entity_id: Entity ID
    - target_version: Version to rollback to
    
    Returns:
    - JSON string with rollback result
    """
    try:
        tracker = get_lineage_tracker()
        publish = tracker.rollback_to_publish(entity_type, entity_id, target_version)
        
        return json.dumps({
            "success": True,
            "publish": publish.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error rolling back publish: {e}")
        return json.dumps({"error": str(e)})
