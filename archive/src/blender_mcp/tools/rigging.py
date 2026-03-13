"""
Advanced rigging tools for professional character animation

Provides automated rigging solutions for bipeds, quadrupeds, and custom creatures.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from enum import Enum

from ..mcp_compat import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

class RigType(Enum):
    BIPED = "biped"
    QUADRUPED = "quadruped"
    CREATURE = "creature"
    FACIAL = "facial"

@telemetry_tool("create_auto_rig")
@mcp.tool()
async def create_auto_rig(
    ctx: Context,
    character_name: str,
    rig_type: str,
    skeleton_template: Optional[str] = None,
    ik_fk_switch: bool = True,
    facial_rig: bool = False,
) -> str:
    """
    Create an automated rig for a character.
    
    Parameters:
    - character_name: Name of the character mesh
    - rig_type: Type of rig ("biped", "quadruped", "creature")
    - skeleton_template: Optional custom skeleton template
    - ik_fk_switch: Enable IK/FK switching
    - facial_rig: Include facial rigging
    
    Returns:
    - JSON string with rig creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "character_name": character_name,
            "rig_type": rig_type,
            "ik_fk_switch": ik_fk_switch,
            "facial_rig": facial_rig,
        }
        
        if skeleton_template:
            params["skeleton_template"] = skeleton_template
            
        result = blender.send_command("create_auto_rig", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating auto rig: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("generate_skeleton")
@mcp.tool()
async def generate_skeleton(
    ctx: Context,
    mesh_name: str,
    skeleton_type: str,
    bone_count: Optional[int] = None,
    symmetry: bool = True,
) -> str:
    """
    Generate a skeleton based on mesh analysis.
    
    Parameters:
    - mesh_name: Name of the target mesh
    - skeleton_type: Type of skeleton generation
    - bone_count: Optional target bone count
    - symmetry: Generate symmetrical skeleton
    
    Returns:
    - JSON string with skeleton generation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "mesh_name": mesh_name,
            "skeleton_type": skeleton_type,
            "symmetry": symmetry,
        }
        
        if bone_count:
            params["bone_count"] = bone_count
            
        result = blender.send_command("generate_skeleton", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating skeleton: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("auto_weight_paint")
@mcp.tool()
async def auto_weight_paint(
    ctx: Context,
    mesh_name: str,
    armature_name: str,
    heat_method: str = "bones",
    quality: str = "high",
) -> str:
    """
    Automatically weight paint a mesh to an armature.
    
    Parameters:
    - mesh_name: Name of the mesh to weight paint
    - armature_name: Name of the armature
    - heat_method: Heat method ("bones", "envelopes", "harmonic")
    - quality: Quality level ("low", "medium", "high")
    
    Returns:
    - JSON string with weight painting result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "mesh_name": mesh_name,
            "armature_name": armature_name,
            "heat_method": heat_method,
            "quality": quality,
        }
        
        result = blender.send_command("auto_weight_paint", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error auto weight painting: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("create_control_rig")
@mcp.tool()
async def create_control_rig(
    ctx: Context,
    armature_name: str,
    control_style: str = "studio",
    ik_chains: Optional[List[str]] = None,
    fk_layers: Optional[List[str]] = None,
) -> str:
    """
    Create a control rig for animation.
    
    Parameters:
    - armature_name: Name of the base armature
    - control_style: Style of controls ("studio", "game", "cartoon")
    - ik_chains: List of IK chain bone names
    - fk_layers: List of FK layer bone names
    
    Returns:
    - JSON string with control rig creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "armature_name": armature_name,
            "control_style": control_style,
        }
        
        if ik_chains:
            params["ik_chains"] = ik_chains
        if fk_layers:
            params["fk_layers"] = fk_layers
            
        result = blender.send_command("create_control_rig", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating control rig: {str(e)}")
        return json.dumps({"error": str(e)})
