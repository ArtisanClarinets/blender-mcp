# Blender MCP Production Studio - Complete Enhancement Plan

> **For Claude:** Use superpowers:executing-plans to implement this plan.

**Goal:** Transform Blender MCP into a production-studio-level autonomous 3D design agent capable of creating professional-grade assets, scenes, and models through intelligent automation and comprehensive tool coverage.

**Architecture:** Modular tool system with preset libraries, material composition engine, camera system, render pipeline integration, and autonomous scene composition intelligence.

**Tech Stack:** Blender 3.0+ Python API, OpenEXR, USD, Alembic, Cycles/Eevee

---

# Executive Summary

## Current vs. Target State

| Aspect | Current | Target |
|--------|---------|--------|
| Materials | Basic PBR assignment | Full node system, procedural |
| Lighting | Single lights | Studio presets, HDRI, volumetrics |
| Cameras | Basic creation | Composition system, presets |
| Animation | None | Keyframe, sequencing |
| Export | GLB only | USD, Alembic, multi-format |
| Scenes | Manual composition | Intelligent presets |
| Rendering | Default settings | Professional pipelines |
| Tools | ~25 tools | 80+ tools |

## Tool Categories (Target)

1. **Scene Management** (8 tools) - Scene setup, clearing, saving
2. **Object Creation** (12 tools) - Primitives, curves, text, Grease Pencil
3. **Materials & Shaders** (18 tools) - PBR, emission, glass, procedural, nodes
4. **Lighting Studio** (10 tools) - Presets, HDRI, volumetrics
5. **Camera & Composition** (8 tools) - Professional composition
6. **Animation** (6 tools) - Keyframing, timeline
7. **Scene Composition** (10 tools) - Product, isometric, character, landscape
8. **Professional Export** (8 tools) - USD, Alembic, multi-format
9. **Rendering** (6 tools) - Cycles, Eevee, presets
10. **Autonomous Workflows** (4 tools) - Intelligent scene creation

**Total: 80+ Production Tools**

---

# Phase 1: Advanced Materials & Shaders

## Task 1.1: Create Material System Foundation

**Files:**
- Create: `src/blender_mcp/tools/materials.py`
- Create: `blender_mcp_addon/handlers/materials.py`

```python
# src/blender_mcp/tools/materials.py
"""
Advanced Material & Shader Tools
Provides production-level material creation and node-based shading.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

@telemetry_tool("create_bsdf_material")
@mcp.tool()
async def create_bsdf_material(
    ctx: Context,
    name: str,
    base_color: Optional[List[float]] = None,
    metallic: Optional[float] = None,
    roughness: Optional[float] = None,
    specular: Optional[float] = None,
    subsurface: Optional[float] = None,
    subsurface_color: Optional[List[float]] = None,
    transmission: Optional[float] = None,
    ior: Optional[float] = None,
    emission_color: Optional[List[float]] = None,
    emission_strength: Optional[float] = None,
) -> str:
    """
    Create a Principled BSDF material with full PBR properties.
    
    Parameters:
    - name: Material name
    - base_color: [R, G, B] color (0-1 range)
    - metallic: 0-1 metallic value
    - roughness: 0-1 roughness value
    - specular: 0-1 specular intensity
    - subsurface: 0-1 subsurface scattering
    - subsurface_color: [R, G, B] subsurface color
    - transmission: 0-1 transmission (glass-like)
    - ior: Index of refraction (1.0-2.5)
    - emission_color: [R, G, B] emission color
    - emission_strength: Emission strength
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        
        params = {"name": name}
        if base_color: params["base_color"] = base_color
        if metallic is not None: params["metallic"] = metallic
        if roughness is not None: params["roughness"] = roughness
        if specular is not None: params["specular"] = specular
        if subsurface is not None: params["subsurface"] = subsurface
        if subsurface_color: params["subsurface_color"] = subsurface_color
        if transmission is not None: params["transmission"] = transmission
        if ior is not None: params["ior"] = ior
        if emission_color: params["emission_color"] = emission_color
        if emission_strength is not None: params["emission_strength"] = emission_strength
        
        result = blender.send_command("create_bsdf_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating BSDF material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_emission_material")
@mcp.tool()
async def create_emission_material(
    ctx: Context,
    name: str,
    color: List[float],
    strength: float = 10.0,
    shadow_mode: str = "none",
) -> str:
    """
    Create an emission (glow) material.
    
    Parameters:
    - name: Material name
    - color: [R, G, B] emission color
    - strength: Emission strength (default: 10.0)
    - shadow_mode: Shadow mode (none, opaque, clip, hashed)
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "color": color,
            "strength": strength,
            "shadow_mode": shadow_mode,
        }
        result = blender.send_command("create_emission_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating emission material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_glass_material")
@mcp.tool()
async def create_glass_material(
    ctx: Context,
    name: str,
    color: Optional[List[float]] = None,
    roughness: float = 0.0,
    ior: float = 1.45,
    transmission: float = 1.0,
) -> str:
    """
    Create a glass material with realistic refraction.
    
    Parameters:
    - name: Material name
    - color: [R, G, B] tint color
    - roughness: Surface roughness (0-1)
    - ior: Index of refraction (default: 1.45)
    - transmission: Transmission amount (0-1)
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "roughness": roughness,
            "ior": ior,
            "transmission": transmission,
        }
        if color: params["color"] = color
        result = blender.send_command("create_glass_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating glass material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_subsurface_material")
@mcp.tool()
async def create_subsurface_material(
    ctx: Context,
    name: str,
    base_color: List[float],
    subsurface_color: List[float],
    subsurface_radius: List[float] = None,
    subsurface: float = 0.5,
    roughness: float = 0.5,
) -> str:
    """
    Create a subsurface scattering (skin/wax/fruit) material.
    
    Parameters:
    - name: Material name
    - base_color: [R, G, B] surface color
    - subsurface_color: [R, G, B] subsurface scatter color
    - subsurface_radius: [R, G, B] scatter radius
    - subsurface: Subsurface amount (0-1)
    - roughness: Surface roughness (0-1)
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "base_color": base_color,
            "subsurface_color": subsurface_color,
            "subsurface": subsurface,
            "roughness": roughness,
        }
        if subsurface_radius: params["subsurface_radius"] = subsurface_radius
        result = blender.send_command("create_subsurface_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating subsurface material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_node_material")
@mcp.tool()
async def create_node_material(
    ctx: Context,
    name: str,
    node_setup: Dict[str, Any],
) -> str:
    """
    Create a complex node-based material.
    
    Parameters:
    - name: Material name
    - node_setup: Dictionary defining nodes and connections
      {
        "nodes": [
          {"type": "ShaderNodeBsdfPrincipled", "name": "BSDF", "location": [0, 0]},
          {"type": "ShaderNodeOutputMaterial", "name": "Output", "location": [300, 0]},
          {"type": "ShaderNodeTexNoise", "name": "Noise", "location": [-300, 0]}
        ],
        "links": [
          {"from": ["Noise", "Fac"], "to": ["BSDF", "Roughness"]},
          {"from": ["BSDF", "BSDF"], "to": ["Output", "Surface"]}
        ]
      }
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        params = {"name": name, "node_setup": node_setup}
        result = blender.send_command("create_node_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating node material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_procedural_texture")
@mcp.tool()
async def create_procedural_texture(
    ctx: Context,
    texture_type: str,
    name: str,
    scale: float = 5.0,
    detail: float = 2.0,
    roughness: float = 0.5,
    distortion: float = 0.0,
) -> str:
    """
    Create a procedural texture (noise, voronoi, wave, etc.).
    
    Parameters:
    - texture_type: Type of procedural texture
      (noise, voronoi, wave, musgrave, checker, brick, gradient, magic)
    - name: Texture name
    - scale: Texture scale
    - detail: Noise detail (for noise/musgrave)
    - roughness: Roughness (for noise/musgrave)
    - distortion: Distortion amount
    
    Returns:
    - JSON with texture creation result
    """
    try:
        blender = get_blender_connection()
        params = {
            "texture_type": texture_type,
            "name": name,
            "scale": scale,
            "detail": detail,
            "roughness": roughness,
            "distortion": distortion,
        }
        result = blender.send_command("create_procedural_texture", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating procedural texture: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_layer_weight_material")
@mcp.tool()
async def create_layer_weight_material(
    ctx: Context,
    name: str,
    fresnel: float = 0.5,
    blend: float = 0.5,
) -> str:
    """
    Create a Layer Weight material for advanced coating effects.
    
    Parameters:
    - name: Material name
    - fresnel: Fresnel effect amount (0-1)
    - blend: Layer weight blend (0-1)
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        params = {"name": name, "fresnel": fresnel, "blend": blend}
        result = blender.send_command("create_layer_weight_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating layer weight material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("assign_material")
@mcp.tool()
async def assign_material(
    ctx: Context,
    object_name: str,
    material_name: str,
) -> str:
    """
    Assign a material to an object.
    
    Parameters:
    - object_name: Name of the object
    - material_name: Name of the material to assign
    
    Returns:
    - JSON with assignment result
    """
    try:
        blender = get_blender_connection()
        params = {"object_name": object_name, "material_name": material_name}
        result = blender.send_command("assign_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error assigning material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_wood_material")
@mcp.tool()
async def create_wood_material(
    ctx: Context,
    name: str,
    wood_color: List[float],
    noise_scale: float = 5.0,
    turbulence: float = 5.0,
) -> str:
    """
    Create a wood procedural material.
    
    Parameters:
    - name: Material name
    - wood_color: [R, G, B] wood color
    - noise_scale: Scale of wood grain
    - turbulence: Turbulence of grain pattern
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "wood_color": wood_color,
            "noise_scale": noise_scale,
            "turbulence": turbulence,
        }
        result = blender.send_command("create_wood_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating wood material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_gradient_material")
@mcp.tool()
async def create_gradient_material(
    ctx: Context,
    name: str,
    color1: List[float],
    color2: List[float],
    gradient_type: str = "linear",
) -> str:
    """
    Create a gradient material.
    
    Parameters:
    - name: Material name
    - color1: [R, G, B] first color
    - color2: [R, G, B] second color
    - gradient_type: linear, quadratic, spherical, quadratic_sphere
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "color1": color1,
            "color2": color2,
            "gradient_type": gradient_type,
        }
        result = blender.send_command("create_gradient_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating gradient material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_holographic_material")
@mcp.tool()
async def create_holographic_material(
    ctx: Context,
    name: str,
    base_color: List[float] = None,
    scanline_count: float = 50.0,
    rainbow_effect: float = 0.3,
) -> str:
    """
    Create a holographic/iridescent material.
    
    Parameters:
    - name: Material name
    - base_color: [R, G, B] base color
    - scanline_count: Number of scanlines
    - rainbow_effect: Iridescence amount
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "scanline_count": scanline_count,
            "rainbow_effect": rainbow_effect,
        }
        if base_color: params["base_color"] = base_color
        result = blender.send_command("create_holographic_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating holographic material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_toon_material")
@mcp.tool()
async def create_toon_material(
    ctx: Context,
    name: str,
    base_color: List[float],
    diffuse_threshold: float = 0.3,
    specular_threshold: float = 0.5,
    specular_width: float = 0.2,
) -> str:
    """
    Create a toon/cel-shaded material.
    
    Parameters:
    - name: Material name
    - base_color: [R, G, B] base color
    - diffuse_threshold: Diffuse shadow threshold
    - specular_threshold: Specular highlight threshold
    - specular_width: Specular highlight width
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "base_color": base_color,
            "diffuse_threshold": diffuse_threshold,
            "specular_threshold": specular_threshold,
            "specular_width": specular_width,
        }
        result = blender.send_command("create_toon_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating toon material: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("list_materials")
@mcp.tool()
async def list_materials(ctx: Context) -> str:
    """
    List all materials in the scene.
    
    Returns:
    - JSON with list of materials
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("list_materials", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error listing materials: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("delete_material")
@mcp.tool()
async def delete_material(ctx: Context, name: str) -> str:
    """
    Delete a material from the scene.
    
    Parameters:
    - name: Material name to delete
    
    Returns:
    - JSON with deletion result
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("delete_material", {"name": name})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error deleting material: {str(e)}")
        return json.dumps({"error": str(e)})
```

## Task 1.2: Add Material Handlers to Addon

**Files:**
- Modify: `addon.py`

```python
# In addon.py, add handlers for materials

def create_bsdf_material(params):
    """Create a Principled BSDF material"""
    name = params.get("name")
    
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    
    # Set parameters
    if params.get("base_color"):
        bsdf.inputs["Base Color"].default_value = params["base_color"] + [1]
    if params.get("metallic") is not None:
        bsdf.inputs["Metallic"].default_value = params["metallic"]
    if params.get("roughness") is not None:
        bsdf.inputs["Roughness"].default_value = params["roughness"]
    if params.get("specular") is not None:
        bsdf.inputs["Specular IOR Level"].default_value = params["specular"]
    if params.get("subsurface") is not None:
        bsdf.inputs["Subsurface"].default_value = params["subsurface"]
    if params.get("transmission") is not None:
        bsdf.inputs["Transmission"].default_value = params["transmission"]
    if params.get("ior") is not None:
        bsdf.inputs["IOR"].default_value = params["ior"]
    
    return {"material": name, "nodes": len(nodes)}

def create_emission_material(params):
    """Create an emission material"""
    name = params.get("name")
    color = params.get("color", [1, 1, 1])
    strength = params.get("strength", 10.0)
    
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Create emission shader
    emission = nodes.new(type="ShaderNodeEmission")
    emission.inputs["Color"].default_value = color + [1]
    emission.inputs["Strength"].default_value = strength
    
    output = nodes.new(type="ShaderNodeOutputMaterial")
    mat.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    
    # Set shadow mode
    mat.shadow_method = params.get("shadow_mode", "none")
    
    return {"material": name, "type": "emission"}

def create_glass_material(params):
    """Create a glass material"""
    name = params.get("name")
    color = params.get("color", [1, 1, 1])
    roughness = params.get("roughness", 0.0)
    ior = params.get("ior", 1.45)
    transmission = params.get("transmission", 1.0)
    
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    
    bsdf.inputs["Base Color"].default_value = color + [1]
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Transmission"].default_value = transmission
    
    mat.blend_method = "BLEND"
    
    return {"material": name, "type": "glass"}

def create_node_material(params):
    """Create a node-based material"""
    name = params.get("name")
    node_setup = params.get("node_setup", {})
    
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default nodes
    nodes.clear()
    
    created_nodes = {}
    
    # Create nodes
    for node_data in node_setup.get("nodes", []):
        node_type = node_data.get("type")
        node_name = node_data.get("name")
        location = node_data.get("location", [0, 0])
        
        node = nodes.new(type=node_type)
        node.name = node_name
        node.location = location
        created_nodes[node_name] = node
    
    # Create links
    for link_data in node_setup.get("links", []):
        from_node = link_data["from"][0]
        from_socket = link_data["from"][1]
        to_node = link_data["to"][0]
        to_socket = link_data["to"][1]
        
        if from_node in created_nodes and to_node in created_nodes:
            links.new(
                created_nodes[from_node].outputs[from_socket],
                created_nodes[to_node].inputs[to_socket]
            )
    
    return {"material": name, "node_count": len(nodes)}

# Add to dispatch
elif command_type == "create_bsdf_material":
    return create_bsdf_material(params)
elif command_type == "create_emission_material":
    return create_emission_material(params)
elif command_type == "create_glass_material":
    return create_glass_material(params)
elif command_type == "create_node_material":
    return create_node_material(params)
# ... continue for all material types
```

---

# Phase 2: Studio Lighting System

## Task 2.1: Create Professional Lighting Tools

**Files:**
- Create: `src/blender_mcp/tools/lighting.py`

```python
"""
Studio Lighting Tools
Professional lighting presets and configurations.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context
from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")

@telemetry_tool("create_three_point_lighting")
@mcp.tool()
async def create_three_point_lighting(
    ctx: Context,
    key_intensity: float = 1000.0,
    fill_intensity: float = 500.0,
    rim_intensity: float = 800.0,
    key_color: List[float] = None,
    fill_color: List[float] = None,
    rim_color: List[float] = None,
) -> str:
    """
    Create professional three-point lighting setup.
    
    Parameters:
    - key_intensity: Key light power (W for Sun, lumens for others)
    - fill_intensity: Fill light power
    - rim_intensity: Rim/back light power
    - key_color: [R, G, B] key light color
    - fill_color: [R, G, B] fill light color  
    - rim_color: [R, G, B] rim light color
    
    Lighting positions:
    - Key: Front-right, 45° elevation
    - Fill: Front-left, 0° elevation
    - Rim: Behind subject, elevated
    
    Returns:
    - JSON with lighting setup details
    """
    try:
        blender = get_blender_connection()
        params = {
            "preset": "three_point",
            "key_intensity": key_intensity,
            "fill_intensity": fill_intensity,
            "rim_intensity": rim_intensity,
        }
        if key_color: params["key_color"] = key_color
        if fill_color: params["fill_color"] = fill_color
        if rim_color: params["rim_color"] = rim_color
        
        result = blender.send_command("create_studio_lighting", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating three-point lighting: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_studio_lighting")
@mcp.tool()
async def create_studio_lighting(
    ctx: Context,
    preset: str,
    intensity: float = 500.0,
    color: List[float] = None,
) -> str:
    """
    Create professional studio lighting preset.
    
    Parameters:
    - preset: Lighting preset name
      - "three_point": Classic three-point setup
      - "butterfly": Butterfly/Paramount lighting
      - "loop": Loop lighting
      - "split": Split lighting
      - "rim": Rim/fill lighting
      - "short": Short lighting
      - "broad": Broad lighting
      - "under": Under lighting
      - "natural": Natural window light
      - "cinematic": Cinematic mood lighting
      - "high_key": High key photography
      - "low_key": Low key dramatic
    - intensity: Light intensity multiplier
    - color: [R, G, B] light color
    
    Returns:
    - JSON with lighting setup details
    """
    try:
        blender = get_blender_connection()
        params = {
            "preset": preset,
            "intensity": intensity,
        }
        if color: params["color"] = color
        result = blender.send_command("create_studio_lighting", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating studio lighting: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_hdri_environment")
@mcp.tool()
async def create_hdri_environment(
    ctx: Context,
    hdri_name: str = None,
    strength: float = 1.0,
    rotation: float = 0.0,
    blur: float = 0.0,
) -> str:
    """
    Create HDRI world environment.
    
    Parameters:
    - hdri_name: PolyHaven HDRI asset name (if downloading)
    - strength: Environment strength (0-10)
    - rotation: Rotation in degrees (0-360)
    - blur: Background blur amount (0-1)
    
    Returns:
    - JSON with environment setup
    """
    try:
        blender = get_blender_connection()
        params = {
            "strength": strength,
            "rotation": rotation,
            "blur": blur,
        }
        if hdri_name: params["hdri_name"] = hdri_name
        result = blender.send_command("create_hdri_environment", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating HDRI environment: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_area_lights")
@mcp.tool()
async def create_area_lights(
    ctx: Context,
    name: str,
    light_type: str = "RECTANGLE",
    size: float = 1.0,
    location: List[float] = None,
    rotation: List[float] = None,
    energy: float = 100.0,
    color: List[float] = None,
) -> str:
    """
    Create an area light.
    
    Parameters:
    - name: Light object name
    - light_type: Area light shape (SQUARE, RECTANGLE, CIRCLE, DISC)
    - size: Light size
    - location: [X, Y, Z] position
    - rotation: [X, Y, Z] rotation
    - energy: Light power (watts for Cycles)
    - color: [R, G, B] light color
    
    Returns:
    - JSON with light details
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "light_type": light_type,
            "size": size,
            "energy": energy,
        }
        if location: params["location"] = location
        if rotation: params["rotation"] = rotation
        if color: params["color"] = color
        result = blender.send_command("create_area_light", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating area light: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_volumetric_lighting")
@mcp.tool()
async def create_volumetric_lighting(
    ctx: Context,
    density: float = 0.1,
    anisotropy: float = 0.0,
    color: List[float] = None,
) -> str:
    """
    Create volumetric lighting setup (fog/atmosphere).
    
    Parameters:
    - density: Fog density
    - anisotropy: Light scattering (0=isotropic, 1=forward)
    - color: [R, G, B] fog color
    
    Returns:
    - JSON with volumetric setup
    """
    try:
        blender = get_blender_connection()
        params = {
            "density": density,
            "anisotropy": anisotropy,
        }
        if color: params["color"] = color
        result = blender.send_command("create_volumetric_lighting", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating volumetric lighting: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("adjust_light_exposure")
@mcp.tool()
async def adjust_light_exposure(
    ctx: Context,
    exposure: float = 0.0,
    gamma: float = 1.0,
) -> str:
    """
    Adjust world exposure and gamma.
    
    Parameters:
    - exposure: Exposure adjustment in stops
    - gamma: Gamma correction
    
    Returns:
    - JSON with adjustment result
    """
    try:
        blender = get_blender_connection()
        params = {"exposure": exposure, "gamma": gamma}
        result = blender.send_command("adjust_light_exposure", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error adjusting exposure: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_sun_light")
@mcp.tool()
async def create_sun_light(
    ctx: Context,
    name: str = "Sun",
    energy: float = 3.0,
    angle: float = 0.0087,
    rotation: List[float] = None,
    color: List[float] = None,
) -> str:
    """
    Create a sun (directional) light.
    
    Parameters:
    - name: Light name
    - energy: Sun strength
    - angle: Angular diameter (for shadow softness)
    - rotation: [X, Y, Z] rotation
    - color: [R, G, B] light color
    
    Returns:
    - JSON with sun light details
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "energy": energy,
            "angle": angle,
        }
        if rotation: params["rotation"] = rotation
        if color: params["color"] = color
        result = blender.send_command("create_sun_light", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating sun light: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("setup_product_lighting")
@mcp.tool()
async def setup_product_lighting(
    ctx: Context,
    style: str = "soft",
) -> str:
    """
    Setup lighting optimized for product photography.
    
    Parameters:
    - style: Lighting style
      - "soft": Soft, even lighting
      - "dramatic": High contrast
      - "gradient": Gradient background
      - "infinite": Infinite white cyc
    
    Returns:
    - JSON with lighting setup
    """
    try:
        blender = get_blender_connection()
        params = {"preset": "product", "style": style}
        result = blender.send_command("create_studio_lighting", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting up product lighting: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("clear_lights")
@mcp.tool()
async def clear_lights(ctx: Context) -> str:
    """
    Remove all lights from the scene.
    
    Returns:
    - JSON with cleanup result
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("clear_lights", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error clearing lights: {str(e)}")
        return json.dumps({"error": str(e)})
```

---

# Phase 3: Camera & Composition

## Task 3.1: Create Camera Tools

```python
# src/blender_mcp/tools/camera.py

@telemetry_tool("create_composition_camera")
@mcp.tool()
async def create_composition_camera(
    ctx: Context,
    name: str = "Camera",
    composition: str = "center",
    focal_length: float = 50.0,
    location: List[float] = None,
    target: List[float] = None,
) -> str:
    """
    Create a camera with composition framing.
    
    Parameters:
    - name: Camera name
    - composition: Composition type
      - "center": Centered subject
      - "rule_of_thirds": Rule of thirds
      - "golden_ratio": Golden ratio
      - "diagonal": Diagonal composition
      - "frame": Edge framing
    - focal_length: Lens focal length in mm
    - location: [X, Y, Z] camera position
    - target: [X, Y, Z] look-at point
    
    Returns:
    - JSON with camera details
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "composition": composition,
            "focal_length": focal_length,
        }
        if location: params["location"] = location
        if target: params["target"] = target
        result = blender.send_command("create_composition_camera", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating composition camera: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_isometric_camera")
@mcp.tool()
async def create_isometric_camera(
    ctx: Context,
    name: str = "Isometric",
    ortho_scale: float = 10.0,
    angle: float = 35.264,
) -> str:
    """
    Create an isometric camera.
    
    Parameters:
    - name: Camera name
    - ortho_scale: Orthographic scale
    - angle: Isometric angle (default: true isometric)
    
    Returns:
    - JSON with camera details
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "type": "orthographic",
            "ortho_scale": ortho_scale,
            "angle": angle,
        }
        result = blender.send_command("create_isometric_camera", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating isometric camera: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_dolly_camera")
async def create_dolly_camera(
   @mcp.tool()
 ctx: Context,
    name: str = "Dolly",
    start_location: List[float] = None,
    end_location: List[float] = None,
    target: List[float] = None,
    frames: int = 60,
) -> str:
    """
    Create a camera with dolly (move) animation.
    
    Parameters:
    - name: Camera name
    - start_location: [X, Y, Z] start position
    - end_location: [X, Y, Z] end position
    - target: [X, Y, Z] look-at point
    - frames: Animation duration
    
    Returns:
    - JSON with camera and animation details
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "frames": frames,
        }
        if start_location: params["start_location"] = start_location
        if end_location: params["end_location"] = end_location
        if target: params["target"] = target
        result = blender.send_command("create_dolly_camera", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating dolly camera: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("set_camera_depth_of_field")
@mcp.tool()
async def set_camera_depth_of_field(
    ctx: Context,
    camera_name: str,
    focus_distance: float = None,
    focal_length: float = None,
    aperture: float = 5.6,
) -> str:
    """
    Configure camera depth of field.
    
    Parameters:
    - camera_name: Camera to configure
    - focus_distance: Focus distance in meters
    - focal_length: Lens focal length
    - aperture: F-stop (lower = more blur)
    
    Returns:
    - JSON with DOF settings
    """
    try:
        blender = get_blender_connection()
        params = {
            "camera_name": camera_name,
            "aperture": aperture,
        }
        if focus_distance: params["focus_distance"] = focus_distance
        if focal_length: params["focal_length"] = focal_length
        result = blender.send_command("set_camera_dof", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting DOF: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("apply_camera_preset")
@mcp.tool()
async def apply_camera_preset(
    ctx: Context,
    camera_name: str,
    preset: str,
) -> str:
    """
    Apply camera preset for common scenarios.
    
    Parameters:
    - camera_name: Camera to modify
    - preset: Camera preset
      - "portrait": Portrait lens (85mm)
      - "landscape": Landscape (35mm)
      - "macro": Macro (100mm, high DOF)
      - "cinematic": Cinema (50-85mm, anamorphic)
      - "action": Action (24-35mm, wide)
      - "telephoto": Telephoto (135-200mm)
    
    Returns:
    - JSON with camera settings
    """
    try:
        blender = get_blender_connection()
        params = {"camera_name": camera_name, "preset": preset}
        result = blender.send_command("apply_camera_preset", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error applying camera preset: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("set_active_camera")
@mcp.tool()
async def set_active_camera(ctx: Context, camera_name: str) -> str:
    """
    Set the active camera for rendering.
    
    Parameters:
    - camera_name: Name of camera to make active
    
    Returns:
    - JSON with result
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("set_active_camera", {"camera_name": camera_name})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting active camera: {str(e)}")
        return json.dumps({"error": str(e)})
```

---

# Phase 4: Scene Composition Presets

## Task 4.1: Create Scene Composition Tools

```python
# src/blender_mcp/tools/composition.py

@telemetry_tool("compose_product_shot")
@mcp.tool()
async def compose_product_shot(
    ctx: Context,
    product_name: str = "Product",
    style: str = "clean",
    background: str = "white",
) -> str:
    """
    Compose a professional product photography shot.
    
    Parameters:
    - product_name: Name for the product object
    - style: Product shot style
      - "clean": White background, soft shadows
      - "lifestyle": Contextual, environmental
      - "dramatic": Dark background, spotlight
      - "gradient": Gradient background
    - background: Background type (white, black, transparent, gradient)
    
    Returns:
    - JSON with scene setup
    """
    try:
        blender = get_blender_connection()
        params = {
            "preset": "product_shot",
            "product_name": product_name,
            "style": style,
            "background": background,
        }
        result = blender.send_command("compose_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error composing product shot: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("compose_isometric_scene")
@mcp.tool()
async def compose_isometric_scene(
    ctx: Context,
    grid_size: float = 10.0,
    floor: bool = True,
    shadow_catcher: bool = True,
) -> str:
    """
    Compose an isometric scene.
    
    Parameters:
    - grid_size: Isometric grid size
    - floor: Include floor plane
    - shadow_catcher: Enable shadow catching floor
    
    Returns:
    - JSON with scene setup
    """
    try:
        blender = get_blender_connection()
        params = {
            "preset": "isometric",
            "grid_size": grid_size,
            "floor": floor,
            "shadow_catcher": shadow_catcher,
        }
        result = blender.send_command("compose_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error composing isometric scene: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("compose_character_scene")
@mcp.tool()
async def compose_character_scene(
    ctx: Context,
    character_name: str = "Character",
    ground_plane: bool = True,
    environment: str = "studio",
) -> str:
    """
    Compose a character/scene setup.
    
    Parameters:
    - character_name: Character object name
    - ground_plane: Include ground
    - environment: Environment type
      - "studio": Neutral studio
      - "outdoor": Outdoor daylight
      - "night": Night scene
      - "dramatic": Dramatic lighting
    
    Returns:
    - JSON with scene setup
    """
    try:
        blender = get_blender_connection()
        params = {
            "preset": "character",
            "character_name": character_name,
            "ground_plane": ground_plane,
            "environment": environment,
        }
        result = blender.send_command("compose_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error composing character scene: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("compose_landscape_scene")
@mcp.tool()
async def compose_landscape_scene(
    ctx: Context,
    terrain_type: str = "flat",
    sky: bool = True,
    fog: bool = False,
) -> str:
    """
    Compose a landscape/natural environment.
    
    Parameters:
    - terrain_type: Terrain type (flat, hills, mountains)
    - sky: Include sky
    - fog: Enable atmospheric fog
    
    Returns:
    - JSON with scene setup
    """
    try:
        blender = get_blender_connection()
        params = {
            "preset": "landscape",
            "terrain_type": terrain_type,
            "sky": sky,
            "fog": fog,
        }
        result = blender.send_command("compose_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error composing landscape: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("compose_automotive_shot")
@mcp.tool()
async def compose_automotive_shot(
    ctx: Context,
    car_name: str = "Car",
    angle: str = "three_quarter",
    environment: str = "studio",
) -> str:
    """
    Compose an automotive photography shot.
    
    Parameters:
    - car_name: Car object name
    - angle: Camera angle
      - "front": Front 3/4 view
      - "rear": Rear 3/4 view
      - "three_quarter": Classic 3/4 view
      - "side": Profile
      - "top": Top down
    - environment: Setting
      - "studio": Showroom
      - "outdoor": Location
      - "motion": Motion blur setup
    
    Returns:
    - JSON with scene setup
    """
    try:
        blender = get_blender_connection()
        params = {
            "preset": "automotive",
            "car_name": car_name,
            "angle": angle,
            "environment": environment,
        }
        result = blender.send_command("compose_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error composing automotive: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("compose_food_shot")
@mcp.tool()
async def compose_food_shot(
    ctx: Context,
    style: str = "flat_lay",
) -> str:
    """
    Compose a food photography setup.
    
    Parameters:
    - style: Food photography style
      - "flat_lay": Top-down
      - "angled": 45° angle
      - "side": Profile view
    
    Returns:
    - JSON with scene setup
    """
    try:
        blender = get_blender_connection()
        params = {"preset": "food", "style": style}
        result = blender.send_command("compose_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error composing food shot: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("compose_jewelry_shot")
@mcp.tool()
async def compose_jewelry_shot(
    ctx: Context,
    style: str = "macro",
    reflections: bool = True,
) -> str:
    """
    Compose a jewelry photography setup.
    
    Parameters:
    - style: Photography style
    - reflections: Enable reflection plane
    
    Returns:
    - JSON with scene setup
    """
    try:
        blender = get_blender_connection()
        params = {"preset": "jewelry", "style": style, "reflections": reflections}
        result = blender.send_command("compose_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error composing jewelry shot: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("compose_architectural_shot")
@mcp.tool()
async def compose_architectural_shot(
    ctx: Context,
    interior: bool = False,
    natural_light: bool = True,
) -> str:
    """
    Compose an architectural photography setup.
    
    Parameters:
    - interior: Interior vs exterior
    - natural_light: Use natural lighting
    
    Returns:
    - JSON with scene setup
    """
    try:
        blender = get_blender_connection()
        params = {"preset": "architectural", "interior": interior, "natural_light": natural_light}
        result = blender.send_command("compose_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error composing architectural: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("compose_studio_setup")
@mcp.tool()
async def compose_studio_setup(
    ctx: Context,
    subject_type: str = "generic",
    mood: str = "neutral",
) -> str:
    """
    Compose a generic studio setup.
    
    Parameters:
    - subject_type: Type of subject
    - mood: Lighting mood
    
    Returns:
    - JSON with scene setup
    """
    try:
        blender = get_blender_connection()
        params = {"preset": "studio", "subject_type": subject_type, "mood": mood}
        result = blender.send_command("compose_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error composing studio: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("clear_scene")
@mcp.tool()
async def clear_scene(
    ctx: Context,
    keep_camera: bool = False,
    keep_lights: bool = False,
) -> str:
    """
    Clear all objects from scene.
    
    Parameters:
    - keep_camera: Preserve active camera
    - keep_lights: Preserve lighting setup
    
    Returns:
    - JSON with cleanup result
    """
    try:
        blender = get_blender_connection()
        params = {"keep_camera": keep_camera, "keep_lights": keep_lights}
        result = blender.send_command("clear_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error clearing scene: {str(e)}")
        return json.dumps({"error": str(e)})
```

---

# Phase 5: Professional Export Pipeline

## Task 5.1: Create Export Tools

```python
# src/blender_mcp/tools/export_pro.py

@telemetry_tool("export_usd")
@mcp.tool()
async def export_usd(
    ctx: Context,
    filepath: str,
    export_selection: bool = False,
    export_materials: bool = True,
    export_cameras: bool = True,
    export_lights: bool = True,
    export_animation: bool = True,
    use_mesh_uvs: bool = True,
    use_mesh_colors: bool = True,
) -> str:
    """
    Export scene to USD (Universal Scene Description).
    
    Parameters:
    - filepath: Output file path
    - export_selection: Export only selection
    - export_materials: Include materials
    - export_cameras: Include cameras
    - export_lights: Include lights
    - export_animation: Include animation
    - export_materials: Export materials
    - use_mesh_uvs: Export UV coordinates
    - use_mesh_colors: Export vertex colors
    
    Returns:
    - JSON with export result
    """
    try:
        blender = get_blender_connection()
        params = {
            "filepath": filepath,
            "format": "usd",
            "export_selection": export_selection,
            "export_materials": export_materials,
            "export_cameras": export_cameras,
            "export_lights": export_lights,
            "export_animation": export_animation,
            "use_mesh_uvs": use_mesh_uvs,
            "use_mesh_colors": use_mesh_colors,
        }
        result = blender.send_command("export_usd", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error exporting USD: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("export_alembic")
@mcp.tool()
async def export_alembic(
    ctx: Context,
    filepath: str,
    export_selection: bool = False,
    export_animation: bool = True,
    start_frame: int = 1,
    end_frame: int = 250,
) -> str:
    """
    Export scene to Alembic format.
    
    Parameters:
    - filepath: Output file path
    - export_selection: Export only selection
    - export_animation: Include animation
    - start_frame: Start frame
    - end_frame: End frame
    
    Returns:
    - JSON with export result
    """
    try:
        blender = get_blender_connection()
        params = {
            "filepath": filepath,
            "format": "alembic",
            "export_selection": export_selection,
            "export_animation": export_animation,
            "start_frame": start_frame,
            "end_frame": end_frame,
        }
        result = blender.send_command("export_alembic", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error exporting Alembic: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("export_obj_with_mtl")
@mcp.tool()
async def export_obj_with_mtl(
    ctx: Context,
    filepath: str,
    export_selection: bool = False,
    apply_modifiers: bool = True,
) -> str:
    """
    Export scene to OBJ with MTL material file.
    
    Parameters:
    - filepath: Output file path (without extension)
    - export_selection: Export only selection
    - apply_modifiers: Apply modifiers
    
    Returns:
    - JSON with export result
    """
    try:
        blender = get_blender_connection()
        params = {
            "filepath": filepath,
            "format": "obj_mtl",
            "export_selection": export_selection,
            "apply_modifiers": apply_modifiers,
        }
        result = blender.send_command("export_obj", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error exporting OBJ: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("export_multi_format")
@mcp.tool()
async def export_multi_format(
    ctx: Context,
    output_dir: str,
    formats: List[str] = None,
    name: str = "export",
) -> str:
    """
    Export scene to multiple formats.
    
    Parameters:
    - output_dir: Output directory
    - formats: List of formats (glb, usd, obj, fbx)
    - name: Base name for exports
    
    Returns:
    - JSON with all export results
    """
    try:
        if formats is None:
            formats = ["glb", "usd", "obj"]
        
        blender = get_blender_connection()
        params = {
            "output_dir": output_dir,
            "formats": formats,
            "name": name,
        }
        result = blender.send_command("export_multi_format", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error exporting multi-format: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("export_layers")
@mcp.tool()
async def export_layers(
    ctx: Context,
    output_dir: str,
    layers: List[str] = None,
) -> str:
    """
    Export scene layers to separate files.
    
    Parameters:
    - output_dir: Output directory
    - layers: List of collection names to export
    
    Returns:
    - JSON with export results
    """
    try:
        blender = get_blender_connection()
        params = {"output_dir": output_dir}
        if layers: params["layers"] = layers
        result = blender.send_command("export_layers", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error exporting layers: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("export_glb_optimal")
@mcp.tool()
async def export_glb_optimal(
    ctx: Context,
    filepath: str,
    quality: str = "high",
    draco: bool = True,
    textures: bool = True,
) -> str:
    """
    Export optimized GLB for web/AR.
    
    Parameters:
    - filepath: Output file path
    - quality: Quality preset (low, medium, high, ultra)
    - draco: Use Draco compression
    - textures: Embed textures
    
    Returns:
    - JSON with export result
    """
    try:
        blender = get_blender_connection()
        params = {
            "filepath": filepath,
            "quality": quality,
            "draco": draco,
            "textures": textures,
        }
        result = blender.send_command("export_glb_optimal", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error exporting optimal GLB: {str(e)}")
        return json.dumps({"error": str(e)})
```

---

# Phase 6: Rendering

## Task 6.1: Create Rendering Tools

```python
# src/blender_mcp/tools/rendering.py

@telemetry_tool("configure_cycles_render")
@mcp.tool()
async def configure_cycles_render(
    ctx: Context,
    samples: int = 128,
    max_bounces: int = 12,
    diffuse_bounces: int = 4,
    glossy_bounces: int = 4,
    transmission_bounces: int = 8,
    volume_bounces: int = 4,
    use_denoising: bool = True,
    device: str = "cpu",
    tile_size: int = 256,
) -> str:
    """
    Configure Cycles render engine.
    
    Parameters:
    - samples: Render samples
    - max_bounces: Total light bounces
    - diffuse_bounces: Diffuse bounces
    - glossy_bounces: Glossy bounces
    - transmission_bounces: Transmission bounces
    - volume_bounces: Volume bounces
    - use_denoising: Use AI denoising
    - device: Render device (cpu, gpu, cuda, opencl)
    - tile_size: Tile size for GPU
    
    Returns:
    - JSON with render settings
    """
    try:
        blender = get_blender_connection()
        params = {
            "engine": "cycles",
            "samples": samples,
            "max_bounces": max_bounces,
            "diffuse_bounces": diffuse_bounces,
            "glossy_bounces": glossy_bounces,
            "transmission_bounces": transmission_bounces,
            "volume_bounces": volume_bounces,
            "use_denoising": use_denoising,
            "device": device,
            "tile_size": tile_size,
        }
        result = blender.send_command("configure_render", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error configuring Cycles: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("configure_eevee_render")
@mcp.tool()
async def configure_eevee_render(
    ctx: Context,
    samples: int = 128,
    use_ambient_occlusion: bool = True,
    use_bloom: bool = False,
    use_shadows: bool = True,
    use_raytracing: bool = False,
    shadow_cube_size: int = 2048,
    shadow_cascade_size: int = 2048,
) -> str:
    """
    Configure Eevee render engine.
    
    Parameters:
    - samples: Render samples
    - use_ambient_occlusion: Enable AO
    - use_bloom: Enable bloom effect
    - use_shadows: Enable shadows
    - use_raytracing: Enable ray tracing
    - shadow_cube_size: Shadow cube size
    - shadow_cascade_size: Shadow cascade size
    
    Returns:
    - JSON with render settings
    """
    try:
        blender = get_blender_connection()
        params = {
            "engine": "eevee",
            "samples": samples,
            "use_ambient_occlusion": use_ambient_occlusion,
            "use_bloom": use_bloom,
            "use_shadows": use_shadows,
            "use_raytracing": use_raytracing,
            "shadow_cube_size": shadow_cube_size,
            "shadow_cascade_size": shadow_cascade_size,
        }
        result = blender.send_command("configure_render", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error configuring Eevee: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_render_preset")
@mcp.tool()
async def create_render_preset(
    ctx: Context,
    preset: str,
) -> str:
    """
    Apply render preset for common scenarios.
    
    Parameters:
    - preset: Render preset
      - "preview": Fast preview
      - "product": Product photography
      - "architectural": Architectural
      - "animation": Animated content
      - "photorealistic": High quality
      - "realtime": Real-time/games
    
    Returns:
    - JSON with render settings
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("create_render_preset", {"preset": preset})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error applying render preset: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("render_image")
@mcp.tool()
async def render_image(
    ctx: Context,
    filepath: str,
    camera: str = None,
    resolution_x: int = 1920,
    resolution_y: int = 1080,
    engine: str = "cycles",
) -> str:
    """
    Render an image.
    
    Parameters:
    - filepath: Output file path
    - camera: Camera name (uses active if None)
    - resolution_x: Image width
    - resolution_y: Image height
    - engine: Render engine (cycles, eevee)
    
    Returns:
    - JSON with render result
    """
    try:
        blender = get_blender_connection()
        params = {
            "filepath": filepath,
            "resolution_x": resolution_x,
            "resolution_y": resolution_y,
            "engine": engine,
        }
        if camera: params["camera"] = camera
        result = blender.send_command("render_image", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error rendering image: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("render_animation")
@mcp.tool()
async def render_animation(
    ctx: Context,
    output_dir: str,
    format: str = "png",
    engine: str = "cycles",
    start_frame: int = 1,
    end_frame: int = 250,
) -> str:
    """
    Render animation sequence.
    
    Parameters:
    - output_dir: Output directory
    - format: Output format (png, exr, jpeg)
    - engine: Render engine
    - start_frame: Start frame
    - end_frame: End frame
    
    Returns:
    - JSON with render result
    """
    try:
        blender = get_blender_connection()
        params = {
            "output_dir": output_dir,
            "format": format,
            "engine": engine,
            "start_frame": start_frame,
            "end_frame": end_frame,
        }
        result = blender.send_command("render_animation", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error rendering animation: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("set_render_resolution")
@mcp.tool()
async def set_render_resolution(
    ctx: Context,
    resolution_x: int = 1920,
    resolution_y: int = 1080,
    percentage: int = 100,
) -> str:
    """
    Set render resolution.
    
    Parameters:
    - resolution_x: Image width
    - resolution_y: Image height
    - percentage: Resolution percentage
    
    Returns:
    - JSON with resolution settings
    """
    try:
        blender = get_blender_connection()
        params = {
            "resolution_x": resolution_x,
            "resolution_y": resolution_y,
            "percentage": percentage,
        }
        result = blender.send_command("set_render_resolution", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting resolution: {str(e)}")
        return json.dumps({"error": str(e)})
```

---

# Phase 7: Autonomous Agent Workflows

## Task 7.1: Create Autonomous Scene Creation

```python
# src/blender_mcp/tools/autonomous.py

@telemetry_tool("create_autonomous_scene")
@mcp.tool()
async def create_autonomous_scene(
    ctx: Context,
    scene_type: str,
    description: str = None,
    quality: str = "high",
) -> str:
    """
    Create a complete scene autonomously based on description.
    
    Parameters:
    - scene_type: Type of scene to create
      - "product": Product photography
      - "character": Character shot
      - "landscape": Natural environment
      - "interior": Interior design
      - "automotive": Vehicle shot
      - "isometric": Isometric scene
    - description: Natural language description
    - quality: Quality level (preview, standard, high, ultra)
    
    Returns:
    - JSON with complete scene details
    """
    try:
        blender = get_blender_connection()
        params = {
            "scene_type": scene_type,
            "quality": quality,
        }
        if description:
            params["description"] = description
        result = blender.send_command("create_autonomous_scene", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating autonomous scene: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("enhance_scene")
@mcp.tool()
async def enhance_scene(
    ctx: Context,
    level: str = "standard",
) -> str:
    """
    Enhance current scene with professional touches.
    
    Parameters:
    - level: Enhancement level
      - "basic": Basic improvements
      - "standard": Professional look
      - "cinematic": Cinematic quality
    
    Returns:
    - JSON with enhancement details
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("enhance_scene", {"level": level})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error enhancing scene: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("optimize_for_target")
@mcp.tool()
async def optimize_for_target(
    ctx: Context,
    target: str,
) -> str:
    """
    Optimize scene for specific target platform.
    
    Parameters:
    - target: Target platform
      - "web": Web/HTML5
      - "mobile": Mobile AR
      - "vr": Virtual Reality
      - "print": Print/Publication
      - "film": Film/VFX
    
    Returns:
    - JSON with optimization details
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("optimize_for_target", {"target": target})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error optimizing scene: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("generate_variations")
@mcp.tool()
async def generate_variations(
    ctx: Context,
    count: int = 4,
    variation_type: str = "lighting",
) -> str:
    """
    Generate variations of current scene.
    
    Parameters:
    - count: Number of variations
    - variation_type: What to vary
      - "lighting": Different lighting
      - "angle": Different camera angles
      - "materials": Different materials
      - "mood": Different moods
    
    Returns:
    - JSON with variation details
    """
    try:
        blender = get_blender_connection()
        params = {"count": count, "variation_type": variation_type}
        result = blender.send_command("generate_variations", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error generating variations: {str(e)}")
        return json.dumps({"error": str(e)})
```

---

# Implementation Priority

## Priority 1: Materials & Shaders (Most Impact)
1. create_bsdf_material - Foundation
2. create_emission_material - Common need
3. create_glass_material - Common need
4. create_node_material - Advanced
5. assign_material - Integration

## Priority 2: Lighting (High Impact)
1. create_three_point_lighting - Essential
2. create_studio_lighting - Professional
3. create_hdri_environment - Environment

## Priority 3: Camera (High Impact)
1. create_composition_camera - Framing
2. create_isometric_camera - Common
3. set_camera_depth_of_field - Professional

## Priority 4: Scene Composition (High Impact)
1. compose_product_shot - Common
2. compose_isometric_scene - Common
3. compose_character_scene
4. clear_scene / setup

## Priority 5: Export & Render
1. export_usd - Industry standard
2. configure_cycles_render - Quality
3. export_multi_format - Workflow

## Priority 6: Autonomous
1. create_autonomous_scene
2. enhance_scene
3. optimize_for_target

---

# Success Criteria

After implementation:
- ✅ 80+ production tools available
- ✅ Complete material system (PBR to procedural)
- ✅ Professional lighting presets
- ✅ Camera composition system
- ✅ Scene composition presets for all major use cases
- ✅ Professional export pipeline
- ✅ Render configuration
- ✅ Autonomous scene creation

This transforms Blender MCP from a basic tool into a **production-studio-level autonomous 3D design agent**.
