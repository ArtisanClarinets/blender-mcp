# BlenderMCP Studio-Quality Upgrade Guide

## Overview

This guide provides detailed implementation instructions for upgrading BlenderMCP to studio-quality content production capabilities. Each section includes code examples, file structures, and step-by-step implementation details.

## Phase 1: Advanced Rigging & Animation Foundation

### 1.1 Rigging System Implementation

#### Create New File: `src/blender_mcp/tools/rigging.py`

```python
"""
Advanced rigging tools for professional character animation

Provides automated rigging solutions for bipeds, quadrupeds, and custom creatures.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from enum import Enum

from mcp.server.fastmcp import Context
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
```

#### Update `src/blender_mcp/tools/__init__.py`

```python
__all__ = [
    "observe",
    "scene_ops",
    "assets",
    "export",
    "jobs",
    "materials",
    "lighting",
    "camera",
    "composition",
    "rigging",  # Add this line
    "animation",  # Add this line
    "tripo3d",
]
```

### 1.2 Animation Timeline Management

#### Create New File: `src/blender_mcp/tools/animation.py`

```python
"""
Professional animation tools for timeline management and keyframe animation

Provides comprehensive animation workflow tools for studio-quality production.
"""

import json
import logging
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from mcp.server.fastmcp import Context
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
```

## Phase 2: Advanced Material & Shading Systems

### 2.1 Enhanced Materials System

#### Update `src/blender_mcp/tools/materials.py`

```python
# Add these new functions to the existing materials.py file

@telemetry_tool("create_subsurface_material")
@mcp.tool()
async def create_subsurface_material(
    ctx: Context,
    name: str,
    base_color: List[float],
    subsurface_color: List[float],
    subsurface_radius: List[float],
    subsurface: float = 0.5,
    roughness: float = 0.5,
    subsurface_method: str = "random_walk",
) -> str:
    """
    Create an advanced subsurface scattering material.
    
    Parameters:
    - name: Material name
    - base_color: Base color [r, g, b]
    - subsurface_color: Subsurface color [r, g, b]
    - subsurface_radius: Scattering radius [r, g, b]
    - subsurface: Subsurface strength
    - roughness: Surface roughness
    - subsurface_method: Scattering method
    
    Returns:
    - JSON string with material creation result
    """
    params = {
        "name": name,
        "base_color": base_color,
        "subsurface_color": subsurface_color,
        "subsurface_radius": subsurface_radius,
        "subsurface": subsurface,
        "roughness": roughness,
        "subsurface_method": subsurface_method,
    }
    
    return _send_material_command("create_subsurface_material", params)

@telemetry_tool("create_volume_material")
@mcp.tool()
async def create_volume_material(
    ctx: Context,
    name: str,
    density: float = 0.1,
    anisotropy: float = 0.0,
    absorption_color: Optional[List[float]] = None,
    emission_color: Optional[List[float]] = None,
    emission_strength: float = 0.0,
) -> str:
    """
    Create a volume material for clouds, smoke, or fire.
    
    Parameters:
    - name: Material name
    - density: Volume density
    - anisotropy: Scattering anisotropy
    - absorption_color: Absorption color
    - emission_color: Emission color
    - emission_strength: Emission strength
    
    Returns:
    - JSON string with volume material creation result
    """
    params = {
        "name": name,
        "density": density,
        "anisotropy": anisotropy,
        "emission_strength": emission_strength,
    }
    
    if absorption_color:
        params["absorption_color"] = absorption_color
    if emission_color:
        params["emission_color"] = emission_color
        
    return _send_material_command("create_volume_material", params)

@telemetry_tool("create_layered_material")
@mcp.tool()
async def create_layered_material(
    ctx: Context,
    name: str,
    base_material: str,
    layers: List[Dict[str, Any]],
    blend_modes: Optional[List[str]] = None,
) -> str:
    """
    Create a multi-layered material system.
    
    Parameters:
    - name: Material name
    - base_material: Base material name
    - layers: List of layer definitions
    - blend_modes: Blend modes for each layer
    
    Returns:
    - JSON string with layered material creation result
    """
    params = {
        "name": name,
        "base_material": base_material,
        "layers": layers,
    }
    
    if blend_modes:
        params["blend_modes"] = blend_modes
        
    return _send_material_command("create_layered_material", params)

@telemetry_tool("create_hair_material")
@mcp.tool()
async def create_hair_material(
    ctx: Context,
    name: str,
    base_color: List[float],
    roughness: float = 0.3,
    radial_roughness: float = 0.1,
    coat: float = 0.0,
    ior: float = 1.55,
    melanin: float = 0.5,
    melanin_redness: float = 0.0,
) -> str:
    """
    Create a realistic hair material.
    
    Parameters:
    - name: Material name
    - base_color: Hair color
    - roughness: Longitudinal roughness
    - radial_roughness: Radial roughness
    - coat: Coat strength
    - ior: Index of refraction
    - melanin: Melanin concentration
    - melanin_redness: Red melanin concentration
    
    Returns:
    - JSON string with hair material creation result
    """
    params = {
        "name": name,
        "base_color": base_color,
        "roughness": roughness,
        "radial_roughness": radial_roughness,
        "coat": coat,
        "ior": ior,
        "melanin": melanin,
        "melanin_redness": melanin_redness,
    }
    
    return _send_material_command("create_hair_material", params)
```

### 2.2 Procedural Material Generation

#### Create New File: `src/blender_mcp/tools/procedural_materials.py`

```python
"""
Procedural material generation using AI and mathematical algorithms

Provides advanced procedural material creation for infinite variety.
"""

import json
import logging
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from mcp.server.fastmcp import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

class MaterialType(Enum):
    WOOD = "wood"
    STONE = "stone"
    METAL = "metal"
    FABRIC = "fabric"
    ORGANIC = "organic"
    TERRAIN = "terrain"

@telemetry_tool("generate_procedural_material")
@mcp.tool()
async def generate_procedural_material(
    ctx: Context,
    material_type: str,
    name: str,
    parameters: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None,
    resolution: str = "2k",
) -> str:
    """
    Generate a procedural material based on type and parameters.
    
    Parameters:
    - material_type: Type of material to generate
    - name: Material name
    - parameters: Material-specific parameters
    - seed: Random seed for reproducibility
    - resolution: Texture resolution
    
    Returns:
    - JSON string with material generation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "material_type": material_type,
            "name": name,
            "resolution": resolution,
        }
        
        if parameters:
            params["parameters"] = parameters
        if seed:
            params["seed"] = seed
            
        result = blender.send_command("generate_procedural_material", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating procedural material: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("ai_generate_material")
@mcp.tool()
async def ai_generate_material(
    ctx: Context,
    description: str,
    name: str,
    style_reference: Optional[str] = None,
    quality: str = "high",
) -> str:
    """
    Generate material using AI from text description.
    
    Parameters:
    - description: Text description of desired material
    - name: Material name
    - style_reference: Optional reference image or style
    - quality: Generation quality
    
    Returns:
    - JSON string with AI material generation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "description": description,
            "name": name,
            "quality": quality,
        }
        
        if style_reference:
            params["style_reference"] = style_reference
            
        result = blender.send_command("ai_generate_material", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating AI material: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("create_material_variations")
@mcp.tool()
async def create_material_variations(
    ctx: Context,
    base_material: str,
    variation_count: int = 5,
    variation_type: str = "color",
    parameters: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create variations of an existing material.
    
    Parameters:
    - base_material: Base material name
    - variation_count: Number of variations to create
    - variation_type: Type of variation ("color", "roughness", "pattern")
    - parameters: Variation parameters
    
    Returns:
    - JSON string with material variations result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "base_material": base_material,
            "variation_count": variation_count,
            "variation_type": variation_type,
        }
        
        if parameters:
            params["parameters"] = parameters
            
        result = blender.send_command("create_material_variations", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating material variations: {str(e)}")
        return json.dumps({"error": str(e)})
```

## Phase 3: Professional Lighting & Atmospherics

### 3.1 Advanced Lighting Systems

#### Update `src/blender_mcp/tools/lighting.py`

```python
# Add these new functions to the existing lighting.py file

@telemetry_tool("create_hdri_lighting_setup")
@mcp.tool()
async def create_hdri_lighting_setup(
    ctx: Context,
    hdri_path: Optional[str] = None,
    hdri_name: Optional[str] = None,
    rotation: float = 0.0,
    strength: float = 1.0,
    saturation: float = 1.0,
) -> str:
    """
    Create an HDRI-based lighting setup.
    
    Parameters:
    - hdri_path: Path to HDRI file
    - hdri_name: PolyHaven HDRI name
    - rotation: HDRI rotation
    - strength: Lighting strength
    - saturation: Color saturation
    
    Returns:
    - JSON string with HDRI lighting result
    """
    params = {
        "rotation": rotation,
        "strength": strength,
        "saturation": saturation,
    }
    
    if hdri_path:
        params["hdri_path"] = hdri_path
    if hdri_name:
        params["hdri_name"] = hdri_name
        
    return _send_lighting_command("create_hdri_lighting_setup", params)

@telemetry_tool("create_volumetric_lighting")
@mcp.tool()
async def create_volumetric_lighting(
    ctx: Context,
    light_name: str,
    volume_type: str = "god_rays",
    density: float = 0.1,
    scatter_amount: float = 1.0,
    anisotropy: float = 0.0,
) -> str:
    """
    Create volumetric lighting effects.
    
    Parameters:
    - light_name: Name of the light to make volumetric
    - volume_type: Type of volumetric effect
    - density: Volume density
    - scatter_amount: Scattering amount
    - anisotropy: Scattering anisotropy
    
    Returns:
    - JSON string with volumetric lighting result
    """
    params = {
        "light_name": light_name,
        "volume_type": volume_type,
        "density": density,
        "scatter_amount": scatter_amount,
        "anisotropy": anisotropy,
    }
    
    return _send_lighting_command("create_volumetric_lighting", params)

@telemetry_tool("create_studio_light_rig")
@mcp.tool()
async def create_studio_light_rig(
    ctx: Context,
    rig_type: str = "portrait",
    key_light_intensity: float = 1000.0,
    fill_light_intensity: float = 500.0,
    rim_light_intensity: float = 800.0,
    background_light_intensity: float = 200.0,
) -> str:
    """
    Create a professional studio lighting rig.
    
    Parameters:
    - rig_type: Type of rig ("portrait", "product", "fashion")
    - key_light_intensity: Key light intensity
    - fill_light_intensity: Fill light intensity
    - rim_light_intensity: Rim light intensity
    - background_light_intensity: Background light intensity
    
    Returns:
    - JSON string with studio rig creation result
    """
    params = {
        "rig_type": rig_type,
        "key_light_intensity": key_light_intensity,
        "fill_light_intensity": fill_light_intensity,
        "rim_light_intensity": rim_light_intensity,
        "background_light_intensity": background_light_intensity,
    }
    
    return _send_lighting_command("create_studio_light_rig", params)

@telemetry_tool("setup_light_linking")
@mcp.tool()
async def setup_light_linking(
    ctx: Context,
    light_objects: List[str],
    target_objects: List[str],
    link_type: str = "include",
) -> str:
    """
    Setup light linking for selective illumination.
    
    Parameters:
    - light_objects: List of light names
    - target_objects: List of objects to affect
    - link_type: "include" or "exclude"
    
    Returns:
    - JSON string with light linking result
    """
    params = {
        "light_objects": light_objects,
        "target_objects": target_objects,
        "link_type": link_type,
    }
    
    return _send_lighting_command("setup_light_linking", params)
```

### 3.2 Atmospheric Effects

#### Create New File: `src/blender_mcp/tools/atmospherics.py`

```python
"""
Atmospheric effects and environmental systems

Provides tools for creating realistic atmospheric conditions and weather effects.
"""

import json
import logging
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

@telemetry_tool("create_volumetric_fog")
@mcp.tool()
async def create_volumetric_fog(
    ctx: Context,
    density: float = 0.1,
    height: float = 10.0,
    falloff: float = 1.0,
    color: Optional[List[float]] = None,
    noise_scale: float = 1.0,
) -> str:
    """
    Create volumetric fog effect.
    
    Parameters:
    - density: Fog density
    - height: Fog height
    - falloff: Height falloff
    - color: Fog color
    - noise_scale: Noise scale for variation
    
    Returns:
    - JSON string with fog creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "density": density,
            "height": height,
            "falloff": falloff,
            "noise_scale": noise_scale,
        }
        
        if color:
            params["color"] = color
            
        result = blender.send_command("create_volumetric_fog", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating volumetric fog: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("create_weather_system")
@mcp.tool()
async def create_weather_system(
    ctx: Context,
    weather_type: str,
    intensity: float = 0.5,
    coverage: float = 0.5,
    wind_speed: float = 0.0,
    wind_direction: Optional[List[float]] = None,
) -> str:
    """
    Create a weather system with particles and effects.
    
    Parameters:
    - weather_type: Type of weather ("rain", "snow", "dust", "leaves")
    - intensity: Weather intensity
    - coverage: Area coverage
    - wind_speed: Wind speed
    - wind_direction: Wind direction vector
    
    Returns:
    - JSON string with weather system creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "weather_type": weather_type,
            "intensity": intensity,
            "coverage": coverage,
            "wind_speed": wind_speed,
        }
        
        if wind_direction:
            params["wind_direction"] = wind_direction
            
        result = blender.send_command("create_weather_system", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating weather system: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("create_sky_system")
@mcp.tool()
async def create_sky_system(
    ctx: Context,
    sky_type: str = "nishita",
    time_of_day: float = 12.0,
    turbidity: float = 2.0,
    rayleigh: float = 2.0,
    mie: float = 0.005,
) -> str:
    """
    Create a physically accurate sky system.
    
    Parameters:
    - sky_type: Sky model ("nishita", "preetham", "hosek_wilkie")
    - time_of_day: Time of day (0-24)
    - turbidity: Atmospheric turbidity
    - rayleigh: Rayleigh scattering
    - mie: Mie scattering
    
    Returns:
    - JSON string with sky system creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "sky_type": sky_type,
            "time_of_day": time_of_day,
            "turbidity": turbidity,
            "rayleigh": rayleigh,
            "mie": mie,
        }
        
        result = blender.send_command("create_sky_system", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating sky system: {str(e)}")
        return json.dumps({"error": str(e)})
```

## Phase 5: Professional Rendering Pipeline

### 5.1 Multi-Pass Rendering System

#### Update `src/blender_mcp/tools/export.py`

```python
# Add these new functions to the existing export.py file

@telemetry_tool("setup_render_passes")
@mcp.tool()
async def setup_render_passes(
    ctx: Context,
    passes: List[str],
    file_format: str = "EXR",
    color_depth: str = "16",
    compression: str = "zip",
) -> str:
    """
    Setup multiple render passes for compositing.
    
    Parameters:
    - passes: List of render passes ("AO", "Z", "Normal", "Vector", etc.)
    - file_format: Output file format
    - color_depth: Bit depth
    - compression: Compression method
    
    Returns:
    - JSON string with render passes setup result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "passes": passes,
            "file_format": file_format,
            "color_depth": color_depth,
            "compression": compression,
        }
        
        result = blender.send_command("setup_render_passes", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error setting up render passes: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("render_animation_passes")
@mcp.tool()
async def render_animation_passes(
    ctx: Context,
    frame_start: int,
    frame_end: int,
    output_path: str,
    passes: Optional[List[str]] = None,
    resolution: Optional[List[int]] = None,
) -> str:
    """
    Render animation with multiple passes.
    
    Parameters:
    - frame_start: Start frame
    - frame_end: End frame
    - output_path: Output directory
    - passes: Optional list of passes
    - resolution: Optional resolution [width, height]
    
    Returns:
    - JSON string with animation render result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "frame_start": frame_start,
            "frame_end": frame_end,
            "output_path": output_path,
        }
        
        if passes:
            params["passes"] = passes
        if resolution:
            params["resolution"] = resolution
            
        result = blender.send_command("render_animation_passes", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error rendering animation passes: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("setup_stereoscopic_render")
@mcp.tool()
async def setup_stereoscopic_render(
    ctx: Context,
    eye_separation: float = 0.065,
    convergence_distance: float = 1.0,
    mode: str = "parallel",
) -> str:
    """
    Setup stereoscopic rendering for VR/3D content.
    
    Parameters:
    - eye_separation: Distance between eyes
    - convergence_distance: Convergence distance
    - mode: Stereo mode ("parallel", "toe-in", "off-axis")
    
    Returns:
    - JSON string with stereoscopic setup result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "eye_separation": eye_separation,
            "convergence_distance": convergence_distance,
            "mode": mode,
        }
        
        result = blender.send_command("setup_stereoscopic_render", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error setting up stereoscopic render: {str(e)}")
        return json.dumps({"error": str(e)})
```

### 5.2 Render Farm Integration

#### Create New File: `src/blender_mcp/tools/render_farm.py`

```python
"""
Render farm integration and distributed rendering

Provides tools for managing large-scale rendering operations.
"""

import json
import logging
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

@telemetry_tool("create_render_job")
@mcp.tool()
async def create_render_job(
    ctx: Context,
    job_name: str,
    frame_range: List[int],
    output_path: str,
    priority: int = 1,
    nodes: int = 1,
    render_settings: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a render farm job.
    
    Parameters:
    - job_name: Name of the render job
    - frame_range: [start, end] frame range
    - output_path: Output directory
    - priority: Job priority (1-10)
    - nodes: Number of render nodes
    - render_settings: Additional render settings
    
    Returns:
    - JSON string with job creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "job_name": job_name,
            "frame_range": frame_range,
            "output_path": output_path,
            "priority": priority,
            "nodes": nodes,
        }
        
        if render_settings:
            params["render_settings"] = render_settings
            
        result = blender.send_command("create_render_job", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating render job: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("monitor_render_job")
@mcp.tool()
async def monitor_render_job(
    ctx: Context,
    job_id: str,
) -> str:
    """
    Monitor render job progress.
    
    Parameters:
    - job_id: Render job ID
    
    Returns:
    - JSON string with job status
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "job_id": job_id,
        }
        
        result = blender.send_command("monitor_render_job", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error monitoring render job: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("optimize_render_settings")
@mcp.tool()
async def optimize_render_settings(
    ctx: Context,
    quality_target: str = "production",
    time_budget: Optional[float] = None,
    memory_limit: Optional[float] = None,
) -> str:
    """
    Optimize render settings for quality/time balance.
    
    Parameters:
    - quality_target: Target quality ("preview", "draft", "production")
    - time_budget: Time budget per frame (seconds)
    - memory_limit: Memory limit (GB)
    
    Returns:
    - JSON string with optimized settings
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "quality_target": quality_target,
        }
        
        if time_budget:
            params["time_budget"] = time_budget
        if memory_limit:
            params["memory_limit"] = memory_limit
            
        result = blender.send_command("optimize_render_settings", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error optimizing render settings: {str(e)}")
        return json.dumps({"error": str(e)})
```

## Phase 7: Production Management & Pipeline

### 7.1 Shot Management System

#### Create New File: `src/blender_mcp/tools/production.py`

```python
"""
Production management and pipeline tools

Provides comprehensive shot management, version control, and collaboration features.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from mcp.server.fastmcp import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

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
```

## Phase 8: AI-Enhanced Creative Tools

### 8.1 Advanced Generative AI Integration

#### Create New File: `src/blender_mcp/tools/ai_creative.py`

```python
"""
AI-enhanced creative tools and intelligent assistance

Provides advanced AI capabilities for creative workflows and automation.
"""

import json
import logging
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

@telemetry_tool("ai_scene_composition")
@mcp.tool()
async def ai_scene_composition(
    ctx: Context,
    scene_type: str,
    mood: str,
    complexity: str = "medium",
    style_reference: Optional[str] = None,
) -> str:
    """
    Generate scene composition using AI.
    
    Parameters:
    - scene_type: Type of scene ("interior", "exterior", "product", "character")
    - mood: Desired mood ("dramatic", "calm", "energetic", "mysterious")
    - complexity: Scene complexity ("simple", "medium", "complex")
    - style_reference: Optional style reference image
    
    Returns:
    - JSON string with composition result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "scene_type": scene_type,
            "mood": mood,
            "complexity": complexity,
        }
        
        if style_reference:
            params["style_reference"] = style_reference
            
        result = blender.send_command("ai_scene_composition", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in AI scene composition: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("ai_lighting_design")
@mcp.tool()
async def ai_lighting_design(
    ctx: Context,
    scene_description: str,
    time_of_day: str,
    mood: str,
    style: str = "cinematic",
) -> str:
    """
    Design lighting setup using AI.
    
    Parameters:
    - scene_description: Description of the scene
    - time_of_day: Time of day ("dawn", "morning", "noon", "afternoon", "dusk", "night")
    - mood: Desired mood
    - style: Lighting style ("cinematic", "natural", "studio", "dramatic")
    
    Returns:
    - JSON string with lighting design result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "scene_description": scene_description,
            "time_of_day": time_of_day,
            "mood": mood,
            "style": style,
        }
        
        result = blender.send_command("ai_lighting_design", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in AI lighting design: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("ai_animation_assist")
@mcp.tool()
async def ai_animation_assist(
    ctx: Context,
    animation_type: str,
    character_name: str,
    action_description: str,
    style: Optional[str] = None,
) -> str:
    """
    AI-assisted animation generation.
    
    Parameters:
    - animation_type: Type of animation ("walk", "run", "jump", "gesture", "facial")
    - character_name: Character to animate
    - action_description: Description of the action
    - style: Animation style ("realistic", "cartoon", "stylized")
    
    Returns:
    - JSON string with animation assistance result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "animation_type": animation_type,
            "character_name": character_name,
            "action_description": action_description,
        }
        
        if style:
            params["style"] = style
            
        result = blender.send_command("ai_animation_assist", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in AI animation assist: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("ai_quality_check")
@mcp.tool()
async def ai_quality_check(
    ctx: Context,
    check_type: str,
    target_objects: Optional[List[str]] = None,
    quality_level: str = "production",
) -> str:
    """
    Perform AI-powered quality checks.
    
    Parameters:
    - check_type: Type of check ("lighting", "materials", "animation", "composition")
    - target_objects: Optional list of objects to check
    - quality_level: Quality standard ("preview", "draft", "production")
    
    Returns:
    - JSON string with quality check results
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "check_type": check_type,
            "quality_level": quality_level,
        }
        
        if target_objects:
            params["target_objects"] = target_objects
            
        result = blender.send_command("ai_quality_check", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in AI quality check: {str(e)}")
        return json.dumps({"error": str(e)})
```

## Implementation Instructions

### Step 1: Update Import Statements

For each new tool file created, update the corresponding `__init__.py` files:

```python
# In src/blender_mcp/tools/__init__.py
__all__ = [
    "observe",
    "scene_ops",
    "assets",
    "export",
    "jobs",
    "materials",
    "lighting",
    "camera",
    "composition",
    "rigging",
    "animation",
    "procedural_materials",
    "atmospherics",
    "render_farm",
    "production",
    "ai_creative",
    "tripo3d",
]
```

### Step 2: Update Blender Addon

Add corresponding command handlers in `addon.py`:

```python
# Add these handlers to the addon.py file in the command processing section

elif command_type == "create_auto_rig":
    # Auto rigging implementation
    return {"status": "success", "result": {...}}

elif command_type == "create_animation_layer":
    # Animation layer implementation
    return {"status": "success", "result": {...}}

elif command_type == "generate_procedural_material":
    # Procedural material generation
    return {"status": "success", "result": {...}}

# Add all other command handlers following the same pattern
```

### Step 3: Update Protocol Schemas

Add new schema definitions to `src/blender_mcp/schemas.py`:

```python
# Add these new schemas to the existing file

class CreateAutoRigPayload(CommandPayloadModel):
    character_name: str = Field(min_length=1)
    rig_type: Literal["biped", "quadruped", "creature"]
    skeleton_template: Optional[str] = None
    ik_fk_switch: bool = True
    facial_rig: bool = False

class CreateAnimationLayerPayload(CommandPayloadModel):
    layer_name: str = Field(min_length=1)
    objects: List[str] = Field(min_items=1)
    properties: List[str] = Field(min_items=1)
    influence: float = Field(default=1.0, ge=0.0, le=1.0)

# Update COMMAND_SCHEMAS dictionary
COMMAND_SCHEMAS.update({
    "create_auto_rig": CreateAutoRigPayload,
    "create_animation_layer": CreateAnimationLayerPayload,
    # Add all other new schemas
})
```

### Step 4: Testing and Validation

Create comprehensive test suites for each new module:

```python
# Create tests/test_rigging.py
import pytest
from blender_mcp.tools.rigging import create_auto_rig, generate_skeleton

@pytest.mark.asyncio
async def test_create_auto_rig():
    # Test auto rigging functionality
    pass

# Create similar test files for all new modules
```

### Step 5: Documentation and Training

Update documentation with new capabilities:

1. **API Documentation**: Update all tool docstrings
2. **User Guides**: Create comprehensive user guides
3. **Video Tutorials**: Record tutorial videos
4. **Best Practices**: Document best practices for each feature

### Step 6: Performance Optimization

Implement performance optimizations:

1. **Caching**: Add intelligent caching for expensive operations
2. **Parallel Processing**: Implement multi-threading where applicable
3. **Memory Management**: Optimize memory usage for large scenes
4. **GPU Acceleration**: Leverage GPU for computation-heavy tasks

### Step 7: Integration Testing

Test integration with existing systems:

1. **Asset Libraries**: Test with existing asset management
2. **Render Farms**: Test distributed rendering
3. **Version Control**: Test with Git/SVN integration
4. **Pipeline Tools**: Test with FTrack/ShotGrid

## Deployment Strategy

### Phase-Based Rollout

1. **Phase 1**: Deploy rigging and animation tools
2. **Phase 2**: Add advanced materials and lighting
3. **Phase 3**: Implement rendering pipeline
4. **Phase 4**: Add production management
5. **Phase 5**: Deploy AI-enhanced tools

### Continuous Integration

1. **Automated Testing**: Run tests on every commit
2. **Performance Monitoring**: Track performance metrics
3. **User Feedback**: Collect and incorporate feedback
4. **Iterative Improvement**: Continuous feature enhancement

This comprehensive upgrade guide provides the roadmap and detailed implementation instructions needed to transform BlenderMCP into a studio-quality content creation platform capable of producing Pixar-level animated content.
