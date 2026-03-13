
"""
Production management and pipeline tools

Provides comprehensive shot management, version control, and collaboration features.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..mcp_compat import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


@telemetry_tool("list_sequences")
@mcp.tool()
async def list_sequences(ctx: Context) -> str:
    """
    List all sequence names in the production.
    Returns JSON with sequences array.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("list_sequences", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error listing sequences: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_sequence")
@mcp.tool()
async def get_sequence(ctx: Context, sequence_name: str) -> str:
    """
    Get all shots in a sequence.
    Parameters:
    - sequence_name: Name of the sequence
    Returns JSON with sequence name and shots array.
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_sequence", {"sequence_name": sequence_name})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting sequence: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("list_shots")
@mcp.tool()
async def list_shots(ctx: Context, sequence_name: Optional[str] = None) -> str:
    """
    List all shots, optionally filtered by sequence.
    Parameters:
    - sequence_name: Optional sequence name to filter by
    Returns JSON with shots array.
    """
    try:
        blender = get_blender_connection()
        params = {}
        if sequence_name:
            params["sequence_name"] = sequence_name
        result = blender.send_command("list_shots", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error listing shots: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_shot")
@mcp.tool()
async def create_shot(
    ctx: Context,
    shot_name: str,
    sequence: str,
    shot_number: int,
    description: str,
    duration: float,
    assets: Optional[List[str]] = None,
) -> str:
    """
    Create a new shot in the production pipeline.
    
    Parameters:
    - shot_name: Unique shot name
    - sequence: Sequence name
    - shot_number: Shot number
    - description: Shot description
    - duration: Shot duration in seconds
    - assets: List of required assets
    
    Returns:
    - JSON string with shot creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "shot_name": shot_name,
            "sequence": sequence,
            "shot_number": shot_number,
            "description": description,
            "duration": duration,
        }
        
        if assets:
            params["assets"] = assets
            
        result = blender.send_command("create_shot", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating shot: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("setup_shot_camera")
@mcp.tool()
async def setup_shot_camera(
    ctx: Context,
    shot_name: str,
    camera_type: str = "cinema",
    focal_length: float = 35.0,
    aperture: float = 2.8,
    shot_type: str = "wide",
) -> str:
    """
    Setup camera for a specific shot.
    
    Parameters:
    - shot_name: Shot name
    - camera_type: Type of camera setup
    - focal_length: Focal length in mm
    - aperture: F-stop value
    - shot_type: Shot type ("wide", "medium", "closeup", "extreme")
    
    Returns:
    - JSON string with camera setup result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "shot_name": shot_name,
            "camera_type": camera_type,
            "focal_length": focal_length,
            "aperture": aperture,
            "shot_type": shot_type,
        }
        
        result = blender.send_command("setup_shot_camera", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error setting up shot camera: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("create_shot_version")
@mcp.tool()
async def create_shot_version(
    ctx: Context,
    shot_name: str,
    version_type: str = "animation",
    notes: Optional[str] = None,
    artist: Optional[str] = None,
) -> str:
    """
    Create a new version of a shot.
    
    Parameters:
    - shot_name: Shot name
    - version_type: Type of version ("layout", "animation", "lighting", "render")
    - notes: Version notes
    - artist: Artist name
    
    Returns:
    - JSON string with version creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "shot_name": shot_name,
            "version_type": version_type,
        }
        
        if notes:
            params["notes"] = notes
        if artist:
            params["artist"] = artist
            
        result = blender.send_command("create_shot_version", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating shot version: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("review_shot")
@mcp.tool()
async def review_shot(
    ctx: Context,
    shot_name: str,
    version: str,
    review_type: str = "visual",
    notes: Optional[str] = None,
    approved: bool = False,
) -> str:
    """
    Review and approve/reject a shot version.
    
    Parameters:
    - shot_name: Shot name
    - version: Version number
    - review_type: Type of review ("visual", "technical", "director")
    - notes: Review notes
    - approved: Approval status
    
    Returns:
    - JSON string with review result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "shot_name": shot_name,
            "version": version,
            "review_type": review_type,
            "approved": approved,
        }
        
        if notes:
            params["notes"] = notes
            
        result = blender.send_command("review_shot", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error reviewing shot: {str(e)}")
        return json.dumps({"error": str(e)})
