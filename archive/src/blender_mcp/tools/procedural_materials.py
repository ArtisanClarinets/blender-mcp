"""
Procedural material generation using AI and mathematical algorithms

Provides advanced procedural material creation for infinite variety.
"""

import json
import logging
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from ..mcp_compat import Context
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
