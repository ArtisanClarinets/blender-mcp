"""
Professional animation tools for timeline management and keyframe animation

Provides comprehensive animation workflow tools for studio-quality production.
"""

import json
import logging
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from ..mcp_compat import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

class InterpolationType(Enum):
    LINEAR = "LINEAR"
    BEZIER = "BEZIER"
    EASE_IN = "EASE_IN"
    EASE_OUT = "EASE_OUT"
    EASE_IN_OUT = "EASE_IN_OUT"

@telemetry_tool("create_animation_layer")
@mcp.tool()
async def create_animation_layer(
    ctx: Context,
    layer_name: str,
    objects: List[str],
    properties: List[str],
    influence: float = 1.0,
) -> str:
    """
    Create an animation layer for non-destructive animation.
    
    Parameters:
    - layer_name: Name of the animation layer
    - objects: List of object names to include
    - properties: List of properties to animate
    - influence: Layer influence (0.0 to 1.0)
    
    Returns:
    - JSON string with layer creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "layer_name": layer_name,
            "objects": objects,
            "properties": properties,
            "influence": influence,
        }
        
        result = blender.send_command("create_animation_layer", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating animation layer: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("set_keyframe")
@mcp.tool()
async def set_keyframe(
    ctx: Context,
    object_name: str,
    property_path: str,
    frame: int,
    value: Union[float, List[float]],
    interpolation: str = "BEZIER",
) -> str:
    """
    Set a keyframe for animation.
    
    Parameters:
    - object_name: Name of the object
    - property_path: Property path (e.g., "location", "rotation_euler")
    - frame: Frame number
    - value: Keyframe value
    - interpolation: Interpolation type
    
    Returns:
    - JSON string with keyframe setting result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "object_name": object_name,
            "property_path": property_path,
            "frame": frame,
            "value": value,
            "interpolation": interpolation,
        }
        
        result = blender.send_command("set_keyframe", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error setting keyframe: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("create_animation_curve")
@mcp.tool()
async def create_animation_curve(
    ctx: Context,
    object_name: str,
    property_path: str,
    keyframes: List[Dict[str, Any]],
    curve_type: str = "bezier",
) -> str:
    """
    Create an animation curve with multiple keyframes.
    
    Parameters:
    - object_name: Name of the object
    - property_path: Property path
    - keyframes: List of keyframe dictionaries with frame, value, handles
    - curve_type: Type of curve ("bezier", "linear", "stepped")
    
    Returns:
    - JSON string with curve creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "object_name": object_name,
            "property_path": property_path,
            "keyframes": keyframes,
            "curve_type": curve_type,
        }
        
        result = blender.send_command("create_animation_curve", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating animation curve: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("import_motion_capture")
@mcp.tool()
async def import_motion_capture(
    ctx: Context,
    file_path: str,
    target_armature: str,
    scale_factor: float = 1.0,
    frame_offset: int = 0,
) -> str:
    """
    Import motion capture data to an armature.
    
    Parameters:
    - file_path: Path to motion capture file (BVH, FBX)
    - target_armature: Name of target armature
    - scale_factor: Scale factor for motion
    - frame_offset: Frame offset for animation
    
    Returns:
    - JSON string with motion capture import result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "file_path": file_path,
            "target_armature": target_armature,
            "scale_factor": scale_factor,
            "frame_offset": frame_offset,
        }
        
        result = blender.send_command("import_motion_capture", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error importing motion capture: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("retarget_animation")
@mcp.tool()
async def retarget_animation(
    ctx: Context,
    source_armature: str,
    target_armature: str,
    bone_mapping: Optional[Dict[str, str]] = None,
    preserve_timing: bool = True,
) -> str:
    """
    Retarget animation from one armature to another.
    
    Parameters:
    - source_armature: Source armature name
    - target_armature: Target armature name
    - bone_mapping: Optional bone name mapping
    - preserve_timing: Preserve original timing
    
    Returns:
    - JSON string with retargeting result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "source_armature": source_armature,
            "target_armature": target_armature,
            "preserve_timing": preserve_timing,
        }
        
        if bone_mapping:
            params["bone_mapping"] = bone_mapping
            
        result = blender.send_command("retarget_animation", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error retargeting animation: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("create_facial_animation")
@mcp.tool()
async def create_facial_animation(
    ctx: Context,
    character_name: str,
    audio_file: Optional[str] = None,
    emotion_curve: Optional[Dict[str, Any]] = None,
    viseme_library: Optional[str] = None,
) -> str:
    """
    Create facial animation from audio or emotion curves.
    
    Parameters:
    - character_name: Name of the character
    - audio_file: Optional audio file for lip-sync
    - emotion_curve: Emotion animation data
    - viseme_library: Viseme library name
    
    Returns:
    - JSON string with facial animation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "character_name": character_name,
        }
        
        if audio_file:
            params["audio_file"] = audio_file
        if emotion_curve:
            params["emotion_curve"] = emotion_curve
        if viseme_library:
            params["viseme_library"] = viseme_library
            
        result = blender.send_command("create_facial_animation", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating facial animation: {str(e)}")
        return json.dumps({"error": str(e)})
