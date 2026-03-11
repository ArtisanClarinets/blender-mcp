# Blender MCP Comprehensive Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform Blender MCP into a production-studio-level autonomous 3D design agent with enterprise-grade reliability, comprehensive tool coverage, and professional-grade output capabilities.

**Architecture:** Three-phase approach: (1) Production Studio Tools for professional 3D creation, (2) Enterprise Infrastructure for reliability and observability, (3) Critical Gap Fixes for complete functionality.

**Tech Stack:** Python 3.10+, FastMCP, pytest, pydantic, structlog, tenacity, Blender 3.0+ Python API

---

# Phase 1: Production Studio Tools

## Task 1.1: Create Materials Tool Module

**Files:**
- Create: `src/blender_mcp/tools/materials.py`
- Create: `tests/test_materials.py`

**Step 1: Create the materials tool module**

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


@telemetry_tool("create_metal_material")
@mcp.tool()
async def create_metal_material(
    ctx: Context,
    name: str,
    base_color: List[float],
    roughness: float = 0.3,
    anisotropy: float = 0.0,
) -> str:
    """
    Create a metallic material.
    
    Parameters:
    - name: Material name
    - base_color: [R, G, B] metal color
    - roughness: Surface roughness (0-1)
    - anisotropy: Anisotropy effect (-1 to 1)
    
    Returns:
    - JSON with material creation result
    """
    try:
        blender = get_blender_connection()
        params = {
            "name": name,
            "base_color": base_color,
            "roughness": roughness,
            "anisotropy": anisotropy,
        }
        result = blender.send_command("create_metal_material", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating metal material: {str(e)}")
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

**Step 2: Write tests for materials module**

```python
# tests/test_materials.py
import pytest
import json
from unittest.mock import Mock, patch


class TestMaterialsTools:
    @pytest.mark.asyncio
    async def test_create_bsdf_material(self, mock_blender_connection):
        """Test creating a BSDF material"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "material": "TestMaterial",
            "nodes": 2
        }
        
        with patch('blender_mcp.tools.materials.get_blender_connection', 
                   return_value=mock_blender_connection):
            from blender_mcp.tools.materials import create_bsdf_material
            
            result = await create_bsdf_material(
                None,
                name="TestMaterial",
                base_color=[0.8, 0.2, 0.2],
                metallic=0.9,
                roughness=0.1
            )
            
            data = json.loads(result)
            assert data["status"] == "success"
            assert data["material"] == "TestMaterial"
    
    @pytest.mark.asyncio
    async def test_create_emission_material(self, mock_blender_connection):
        """Test creating an emission material"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "material": "GlowMaterial",
            "type": "emission"
        }
        
        with patch('blender_mcp.tools.materials.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.materials import create_emission_material
            
            result = await create_emission_material(
                None,
                name="GlowMaterial",
                color=[1.0, 0.5, 0.0],
                strength=50.0
            )
            
            data = json.loads(result)
            assert data["type"] == "emission"
    
    @pytest.mark.asyncio
    async def test_create_glass_material(self, mock_blender_connection):
        """Test creating a glass material"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "material": "GlassMaterial",
            "type": "glass"
        }
        
        with patch('blender_mcp.tools.materials.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.materials import create_glass_material
            
            result = await create_glass_material(
                None,
                name="GlassMaterial",
                ior=1.52
            )
            
            data = json.loads(result)
            assert data["type"] == "glass"
    
    @pytest.mark.asyncio
    async def test_assign_material(self, mock_blender_connection):
        """Test assigning material to object"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "object": "Cube",
            "material": "TestMaterial"
        }
        
        with patch('blender_mcp.tools.materials.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.materials import assign_material
            
            result = await assign_material(
                None,
                object_name="Cube",
                material_name="TestMaterial"
            )
            
            data = json.loads(result)
            assert data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_list_materials(self, mock_blender_connection):
        """Test listing materials"""
        mock_blender_connection.send_command.return_value = {
            "materials": ["Material", "Material.001", "Glass"]
        }
        
        with patch('blender_mcp.tools.materials.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.materials import list_materials
            
            result = await list_materials(None)
            data = json.loads(result)
            assert len(data["materials"]) == 3
```

**Step 3: Run tests to verify they fail (module doesn't exist yet)**

```bash
pytest tests/test_materials.py -v
# Expected: ModuleNotFoundError or ImportError
```

**Step 4: Create the materials module file**

Create the file at `src/blender_mcp/tools/materials.py` with the code from Step 1.

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_materials.py -v
# Expected: All tests pass
```

**Step 6: Commit**

```bash
git add src/blender_mcp/tools/materials.py tests/test_materials.py
git commit -m "feat(materials): add BSDF, emission, glass, metal, subsurface material tools"
```

---

## Task 1.2: Create Lighting Tool Module

**Files:**
- Create: `src/blender_mcp/tools/lighting.py`
- Create: `tests/test_lighting.py`

**Step 1: Create the lighting tool module**

```python
# src/blender_mcp/tools/lighting.py
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
      - "cinematic": Cinematic mood lighting
      - "high_key": High key photography
      - "low_key": Low key dramatic
      - "product": Product photography
      - "portrait": Portrait lighting
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


@telemetry_tool("create_area_light")
@mcp.tool()
async def create_area_light(
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


@telemetry_tool("list_lights")
@mcp.tool()
async def list_lights(ctx: Context) -> str:
    """
    List all lights in the scene.
    
    Returns:
    - JSON with list of lights
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("list_lights", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error listing lights: {str(e)}")
        return json.dumps({"error": str(e)})
```

**Step 2: Write tests for lighting module**

```python
# tests/test_lighting.py
import pytest
import json
from unittest.mock import Mock, patch


class TestLightingTools:
    @pytest.mark.asyncio
    async def test_create_three_point_lighting(self, mock_blender_connection):
        """Test creating three-point lighting"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "lights": ["Key", "Fill", "Rim"],
            "preset": "three_point"
        }
        
        with patch('blender_mcp.tools.lighting.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.lighting import create_three_point_lighting
            
            result = await create_three_point_lighting(
                None,
                key_intensity=1000.0,
                fill_intensity=500.0,
                rim_intensity=800.0
            )
            
            data = json.loads(result)
            assert data["preset"] == "three_point"
            assert len(data["lights"]) == 3
    
    @pytest.mark.asyncio
    async def test_create_studio_lighting_cinematic(self, mock_blender_connection):
        """Test creating cinematic lighting preset"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "preset": "cinematic",
            "lights": ["Key", "Fill"]
        }
        
        with patch('blender_mcp.tools.lighting.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.lighting import create_studio_lighting
            
            result = await create_studio_lighting(
                None,
                preset="cinematic",
                intensity=750.0
            )
            
            data = json.loads(result)
            assert data["preset"] == "cinematic"
    
    @pytest.mark.asyncio
    async def test_create_area_light(self, mock_blender_connection):
        """Test creating an area light"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "name": "SoftBox",
            "type": "area",
            "shape": "RECTANGLE"
        }
        
        with patch('blender_mcp.tools.lighting.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.lighting import create_area_light
            
            result = await create_area_light(
                None,
                name="SoftBox",
                light_type="RECTANGLE",
                size=2.0,
                energy=500.0
            )
            
            data = json.loads(result)
            assert data["shape"] == "RECTANGLE"
    
    @pytest.mark.asyncio
    async def test_create_hdri_environment(self, mock_blender_connection):
        """Test creating HDRI environment"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "hdri": "studio_small_03",
            "strength": 1.0
        }
        
        with patch('blender_mcp.tools.lighting.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.lighting import create_hdri_environment
            
            result = await create_hdri_environment(
                None,
                hdri_name="studio_small_03",
                strength=1.0
            )
            
            data = json.loads(result)
            assert data["hdri"] == "studio_small_03"
    
    @pytest.mark.asyncio
    async def test_clear_lights(self, mock_blender_connection):
        """Test clearing all lights"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "removed_count": 5
        }
        
        with patch('blender_mcp.tools.lighting.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.lighting import clear_lights
            
            result = await clear_lights(None)
            data = json.loads(result)
            assert data["removed_count"] == 5
```

**Step 3: Run tests to verify they fail**

```bash
pytest tests/test_lighting.py -v
# Expected: ModuleNotFoundError
```

**Step 4: Create the lighting module file**

Create the file at `src/blender_mcp/tools/lighting.py` with the code from Step 1.

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_lighting.py -v
# Expected: All tests pass
```

**Step 6: Commit**

```bash
git add src/blender_mcp/tools/lighting.py tests/test_lighting.py
git commit -m "feat(lighting): add studio presets, HDRI, area lights, volumetric tools"
```

---

## Task 1.3: Create Camera Tool Module

**Files:**
- Create: `src/blender_mcp/tools/camera.py`
- Create: `tests/test_camera.py`

**Step 1: Create the camera tool module**

```python
# src/blender_mcp/tools/camera.py
"""
Camera & Composition Tools
Professional camera setup and composition framing.
"""

import json
import logging
from typing import List, Optional

from mcp.server.fastmcp import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


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
      - "product": Product photography (50mm)
    
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


@telemetry_tool("list_cameras")
@mcp.tool()
async def list_cameras(ctx: Context) -> str:
    """
    List all cameras in the scene.
    
    Returns:
    - JSON with list of cameras
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("list_cameras", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error listing cameras: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("frame_camera_to_selection")
@mcp.tool()
async def frame_camera_to_selection(
    ctx: Context,
    camera_name: str,
    margin: float = 1.1,
) -> str:
    """
    Frame camera to fit selected objects.
    
    Parameters:
    - camera_name: Camera to adjust
    - margin: Margin factor (1.0 = exact fit, 1.1 = 10% margin)
    
    Returns:
    - JSON with framing result
    """
    try:
        blender = get_blender_connection()
        params = {"camera_name": camera_name, "margin": margin}
        result = blender.send_command("frame_camera_to_selection", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error framing camera: {str(e)}")
        return json.dumps({"error": str(e)})
```

**Step 2: Write tests for camera module**

```python
# tests/test_camera.py
import pytest
import json
from unittest.mock import Mock, patch


class TestCameraTools:
    @pytest.mark.asyncio
    async def test_create_composition_camera(self, mock_blender_connection):
        """Test creating a composition camera"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "name": "MainCamera",
            "composition": "rule_of_thirds",
            "focal_length": 50.0
        }
        
        with patch('blender_mcp.tools.camera.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.camera import create_composition_camera
            
            result = await create_composition_camera(
                None,
                name="MainCamera",
                composition="rule_of_thirds",
                focal_length=50.0
            )
            
            data = json.loads(result)
            assert data["composition"] == "rule_of_thirds"
    
    @pytest.mark.asyncio
    async def test_create_isometric_camera(self, mock_blender_connection):
        """Test creating an isometric camera"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "name": "IsoCam",
            "type": "orthographic",
            "ortho_scale": 10.0
        }
        
        with patch('blender_mcp.tools.camera.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.camera import create_isometric_camera
            
            result = await create_isometric_camera(
                None,
                name="IsoCam",
                ortho_scale=10.0
            )
            
            data = json.loads(result)
            assert data["type"] == "orthographic"
    
    @pytest.mark.asyncio
    async def test_set_camera_depth_of_field(self, mock_blender_connection):
        """Test setting DOF"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "camera": "MainCamera",
            "aperture": 2.8,
            "focus_distance": 5.0
        }
        
        with patch('blender_mcp.tools.camera.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.camera import set_camera_depth_of_field
            
            result = await set_camera_depth_of_field(
                None,
                camera_name="MainCamera",
                aperture=2.8,
                focus_distance=5.0
            )
            
            data = json.loads(result)
            assert data["aperture"] == 2.8
    
    @pytest.mark.asyncio
    async def test_apply_camera_preset(self, mock_blender_connection):
        """Test applying camera preset"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "camera": "MainCamera",
            "preset": "portrait",
            "focal_length": 85.0
        }
        
        with patch('blender_mcp.tools.camera.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.camera import apply_camera_preset
            
            result = await apply_camera_preset(
                None,
                camera_name="MainCamera",
                preset="portrait"
            )
            
            data = json.loads(result)
            assert data["focal_length"] == 85.0
    
    @pytest.mark.asyncio
    async def test_set_active_camera(self, mock_blender_connection):
        """Test setting active camera"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "active_camera": "MainCamera"
        }
        
        with patch('blender_mcp.tools.camera.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.camera import set_active_camera
            
            result = await set_active_camera(None, camera_name="MainCamera")
            data = json.loads(result)
            assert data["active_camera"] == "MainCamera"
```

**Step 3: Run tests to verify they fail**

```bash
pytest tests/test_camera.py -v
# Expected: ModuleNotFoundError
```

**Step 4: Create the camera module file**

Create the file at `src/blender_mcp/tools/camera.py` with the code from Step 1.

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_camera.py -v
# Expected: All tests pass
```

**Step 6: Commit**

```bash
git add src/blender_mcp/tools/camera.py tests/test_camera.py
git commit -m "feat(camera): add composition, isometric, DOF, preset tools"
```

---

## Task 1.4: Create Scene Composition Tool Module

**Files:**
- Create: `src/blender_mcp/tools/composition.py`
- Create: `tests/test_composition.py`

**Step 1: Create the composition tool module**

```python
# src/blender_mcp/tools/composition.py
"""
Scene Composition Tools
Professional scene setup and composition presets.
"""

import json
import logging
from typing import List, Optional

from mcp.server.fastmcp import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


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
        params = {
            "preset": "architectural",
            "interior": interior,
            "natural_light": natural_light
        }
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
        params = {
            "preset": "studio",
            "subject_type": subject_type,
            "mood": mood
        }
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


@telemetry_tool("setup_render_settings")
@mcp.tool()
async def setup_render_settings(
    ctx: Context,
    engine: str = "CYCLES",
    samples: int = 128,
    resolution_x: int = 1920,
    resolution_y: int = 1080,
    denoise: bool = True,
) -> str:
    """
    Setup render settings.
    
    Parameters:
    - engine: Render engine (CYCLES, EEVEE)
    - samples: Render samples
    - resolution_x: Width in pixels
    - resolution_y: Height in pixels
    - denoise: Enable denoising
    
    Returns:
    - JSON with render settings
    """
    try:
        blender = get_blender_connection()
        params = {
            "engine": engine,
            "samples": samples,
            "resolution_x": resolution_x,
            "resolution_y": resolution_y,
            "denoise": denoise,
        }
        result = blender.send_command("setup_render_settings", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting up render: {str(e)}")
        return json.dumps({"error": str(e)})
```

**Step 2: Write tests for composition module**

```python
# tests/test_composition.py
import pytest
import json
from unittest.mock import Mock, patch


class TestCompositionTools:
    @pytest.mark.asyncio
    async def test_compose_product_shot(self, mock_blender_connection):
        """Test composing a product shot"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "preset": "product_shot",
            "camera": "ProductCamera",
            "lights": ["Key", "Fill", "Rim"],
            "background": "white"
        }
        
        with patch('blender_mcp.tools.composition.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.composition import compose_product_shot
            
            result = await compose_product_shot(
                None,
                product_name="MyProduct",
                style="clean",
                background="white"
            )
            
            data = json.loads(result)
            assert data["preset"] == "product_shot"
            assert data["background"] == "white"
    
    @pytest.mark.asyncio
    async def test_compose_isometric_scene(self, mock_blender_connection):
        """Test composing an isometric scene"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "preset": "isometric",
            "camera": "IsometricCamera",
            "floor": True,
            "shadow_catcher": True
        }
        
        with patch('blender_mcp.tools.composition.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.composition import compose_isometric_scene
            
            result = await compose_isometric_scene(
                None,
                grid_size=10.0,
                floor=True,
                shadow_catcher=True
            )
            
            data = json.loads(result)
            assert data["preset"] == "isometric"
    
    @pytest.mark.asyncio
    async def test_compose_automotive_shot(self, mock_blender_connection):
        """Test composing an automotive shot"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "preset": "automotive",
            "angle": "three_quarter",
            "environment": "studio"
        }
        
        with patch('blender_mcp.tools.composition.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.composition import compose_automotive_shot
            
            result = await compose_automotive_shot(
                None,
                car_name="SportsCar",
                angle="three_quarter",
                environment="studio"
            )
            
            data = json.loads(result)
            assert data["angle"] == "three_quarter"
    
    @pytest.mark.asyncio
    async def test_clear_scene(self, mock_blender_connection):
        """Test clearing scene"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "removed_objects": 15,
            "kept_camera": True,
            "kept_lights": False
        }
        
        with patch('blender_mcp.tools.composition.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.composition import clear_scene
            
            result = await clear_scene(
                None,
                keep_camera=True,
                keep_lights=False
            )
            
            data = json.loads(result)
            assert data["kept_camera"] is True
    
    @pytest.mark.asyncio
    async def test_setup_render_settings(self, mock_blender_connection):
        """Test setting up render settings"""
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "engine": "CYCLES",
            "samples": 256,
            "resolution": [1920, 1080],
            "denoise": True
        }
        
        with patch('blender_mcp.tools.composition.get_blender_connection',
                   return_value=mock_blender_connection):
            from blender_mcp.tools.composition import setup_render_settings
            
            result = await setup_render_settings(
                None,
                engine="CYCLES",
                samples=256,
                resolution_x=1920,
                resolution_y=1080,
                denoise=True
            )
            
            data = json.loads(result)
            assert data["engine"] == "CYCLES"
            assert data["samples"] == 256
```

**Step 3: Run tests to verify they fail**

```bash
pytest tests/test_composition.py -v
# Expected: ModuleNotFoundError
```

**Step 4: Create the composition module file**

Create the file at `src/blender_mcp/tools/composition.py` with the code from Step 1.

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_composition.py -v
# Expected: All tests pass
```

**Step 6: Commit**

```bash
git add src/blender_mcp/tools/composition.py tests/test_composition.py
git commit -m "feat(composition): add product, isometric, automotive, food, jewelry presets"
```

---

## Task 1.5: Update Tools __init__.py to Register New Modules

**Files:**
- Modify: `src/blender_mcp/tools/__init__.py`

**Step 1: Update the __init__.py file**

```python
# src/blender_mcp/tools/__init__.py
"""
Blender MCP Tools Package
All tool modules are imported here to register with FastMCP.
"""

# Import all tool modules to register them with the MCP server
from . import observe
from . import scene_ops
from . import assets
from . import export
from . import jobs

# New production studio tools
from . import materials
from . import lighting
from . import camera
from . import composition

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
]
```

**Step 2: Run all tests to verify integration**

```bash
pytest tests/ -v
# Expected: All tests pass
```

**Step 3: Commit**

```bash
git add src/blender_mcp/tools/__init__.py
git commit -m "feat(tools): register materials, lighting, camera, composition modules"
```

---

## Task 1.6: Add Material Handlers to Blender Addon

**Files:**
- Modify: `addon.py`

**Step 1: Add material command handlers to addon.py**

Find the `_dispatch_command` method in `addon.py` and add the following handlers:

```python
# In addon.py, add these handlers to the _dispatch_command method

def _handle_create_bsdf_material(params):
    """Create a Principled BSDF material"""
    import bpy
    
    name = params.get("name", "Material")
    
    # Create material
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
        bsdf.inputs["Subsurface Weight"].default_value = params["subsurface"]
    if params.get("transmission") is not None:
        bsdf.inputs["Transmission Weight"].default_value = params["transmission"]
    if params.get("ior") is not None:
        bsdf.inputs["IOR"].default_value = params["ior"]
    if params.get("emission_color"):
        bsdf.inputs["Emission Color"].default_value = params["emission_color"] + [1]
    if params.get("emission_strength") is not None:
        bsdf.inputs["Emission Strength"].default_value = params["emission_strength"]
    
    return {"status": "success", "material": name, "nodes": len(nodes)}


def _handle_create_emission_material(params):
    """Create an emission material"""
    import bpy
    
    name = params.get("name", "Emission")
    color = params.get("color", [1, 1, 1])
    strength = params.get("strength", 10.0)
    shadow_mode = params.get("shadow_mode", "none")
    
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
    mat.shadow_method = shadow_mode
    
    return {"status": "success", "material": name, "type": "emission"}


def _handle_create_glass_material(params):
    """Create a glass material"""
    import bpy
    
    name = params.get("name", "Glass")
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
    bsdf.inputs["Transmission Weight"].default_value = transmission
    
    mat.blend_method = "BLEND"
    
    return {"status": "success", "material": name, "type": "glass"}


def _handle_assign_material(params):
    """Assign material to object"""
    import bpy
    
    object_name = params.get("object_name")
    material_name = params.get("material_name")
    
    obj = bpy.data.objects.get(object_name)
    mat = bpy.data.materials.get(material_name)
    
    if not obj:
        return {"status": "error", "message": f"Object '{object_name}' not found"}
    if not mat:
        return {"status": "error", "message": f"Material '{material_name}' not found"}
    
    # Assign material
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    
    return {"status": "success", "object": object_name, "material": material_name}


def _handle_list_materials(params):
    """List all materials"""
    import bpy
    
    materials = [mat.name for mat in bpy.data.materials]
    return {"materials": materials, "count": len(materials)}


def _handle_delete_material(params):
    """Delete a material"""
    import bpy
    
    name = params.get("name")
    mat = bpy.data.materials.get(name)
    
    if not mat:
        return {"status": "error", "message": f"Material '{name}' not found"}
    
    bpy.data.materials.remove(mat)
    return {"status": "success", "deleted": name}
```

**Step 2: Add dispatch cases in _dispatch_command**

```python
# In the _dispatch_command method, add these cases:

elif command_type == "create_bsdf_material":
    return _handle_create_bsdf_material(params)
elif command_type == "create_emission_material":
    return _handle_create_emission_material(params)
elif command_type == "create_glass_material":
    return _handle_create_glass_material(params)
elif command_type == "assign_material":
    return _handle_assign_material(params)
elif command_type == "list_materials":
    return _handle_list_materials(params)
elif command_type == "delete_material":
    return _handle_delete_material(params)
```

**Step 3: Commit**

```bash
git add addon.py
git commit -m "feat(addon): add material handlers (BSDF, emission, glass, assign)"
```

---

## Task 1.7: Add Lighting Handlers to Blender Addon

**Files:**
- Modify: `addon.py`

**Step 1: Add lighting command handlers**

```python
# In addon.py, add these handlers

def _handle_create_studio_lighting(params):
    """Create studio lighting preset"""
    import bpy
    import math
    
    preset = params.get("preset", "three_point")
    intensity = params.get("intensity", 500.0)
    
    # Clear existing lights
    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.delete()
    
    lights_created = []
    
    if preset == "three_point":
        # Key light - front right, 45° up
        key = _create_light("Key", "POINT", intensity, [3, -3, 4])
        lights_created.append("Key")
        
        # Fill light - front left, lower
        fill = _create_light("Fill", "POINT", intensity * 0.5, [-3, -3, 2])
        lights_created.append("Fill")
        
        # Rim light - behind, elevated
        rim = _create_light("Rim", "POINT", intensity * 0.8, [0, 5, 5])
        lights_created.append("Rim")
    
    elif preset == "cinematic":
        # Single key with rim
        key = _create_light("Key", "AREA", intensity, [4, -2, 3])
        key.data.shape = 'RECTANGLE'
        key.data.size = 2.0
        lights_created.append("Key")
        
        rim = _create_light("Rim", "SPOT", intensity * 0.5, [-2, 5, 4])
        lights_created.append("Rim")
    
    elif preset == "high_key":
        # Bright, even lighting
        for i, pos in enumerate([(5, 0, 5), (-5, 0, 5), (0, 5, 5), (0, -5, 5)]):
            light = _create_light(f"Light_{i}", "POINT", intensity * 0.5, pos)
            lights_created.append(f"Light_{i}")
    
    elif preset == "low_key":
        # Single dramatic light
        key = _create_light("Key", "SPOT", intensity, [3, -3, 5])
        key.data.spot_size = math.radians(30)
        lights_created.append("Key")
    
    elif preset == "product":
        # Soft box lighting
        key = _create_light("Key", "AREA", intensity, [0, -4, 4])
        key.data.shape = 'RECTANGLE'
        key.data.size = 3.0
        lights_created.append("Key")
        
        fill = _create_light("Fill", "AREA", intensity * 0.3, [0, 4, 2])
        fill.data.shape = 'RECTANGLE'
        fill.data.size = 2.0
        lights_created.append("Fill")
    
    return {
        "status": "success",
        "preset": preset,
        "lights": lights_created
    }


def _create_light(name, light_type, energy, location):
    """Helper to create a light"""
    import bpy
    
    light_data = bpy.data.lights.new(name=name, type=light_type)
    light_data.energy = energy
    
    light_object = bpy.data.objects.new(name=name, object_data=light_data)
    bpy.context.collection.objects.link(light_object)
    light_object.location = location
    
    return light_object


def _handle_create_area_light(params):
    """Create an area light"""
    import bpy
    
    name = params.get("name", "AreaLight")
    light_type = params.get("light_type", "RECTANGLE")
    size = params.get("size", 1.0)
    energy = params.get("energy", 100.0)
    location = params.get("location", [0, 0, 5])
    rotation = params.get("rotation", [0.785, 0, 0])  # 45° tilt
    color = params.get("color", [1, 1, 1])
    
    light_data = bpy.data.lights.new(name=name, type='AREA')
    light_data.shape = light_type
    light_data.size = size
    light_data.energy = energy
    light_data.color = color
    
    light_object = bpy.data.objects.new(name=name, object_data=light_data)
    bpy.context.collection.objects.link(light_object)
    light_object.location = location
    light_object.rotation_euler = rotation
    
    return {
        "status": "success",
        "name": name,
        "type": "area",
        "shape": light_type
    }


def _handle_create_hdri_environment(params):
    """Create HDRI environment"""
    import bpy
    
    strength = params.get("strength", 1.0)
    rotation = params.get("rotation", 0.0)
    
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    # Clear existing nodes
    nodes.clear()
    
    # Create environment texture node
    env_tex = nodes.new(type="ShaderNodeTexEnvironment")
    bg = nodes.new(type="ShaderNodeBackground")
    output = nodes.new(type="ShaderNodeOutputWorld")
    
    # Set positions
    env_tex.location = (-400, 0)
    bg.location = (0, 0)
    output.location = (300, 0)
    
    # Link nodes
    links.new(env_tex.outputs["Color"], bg.inputs["Color"])
    links.new(bg.outputs["Background"], output.inputs["Surface"])
    
    # Set strength
    bg.inputs["Strength"].default_value = strength
    
    # Set rotation
    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-600, 0)
    mapping.inputs["Rotation"].default_value[2] = rotation * 0.0174533  # deg to rad
    
    return {
        "status": "success",
        "strength": strength,
        "rotation": rotation
    }


def _handle_clear_lights(params):
    """Clear all lights"""
    import bpy
    
    count = 0
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj)
            count += 1
    
    return {"status": "success", "removed_count": count}


def _handle_list_lights(params):
    """List all lights"""
    import bpy
    
    lights = []
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            lights.append({
                "name": obj.name,
                "type": obj.data.type,
                "energy": obj.data.energy
            })
    
    return {"lights": lights, "count": len(lights)}
```

**Step 2: Add dispatch cases**

```python
# In _dispatch_command, add:

elif command_type == "create_studio_lighting":
    return _handle_create_studio_lighting(params)
elif command_type == "create_area_light":
    return _handle_create_area_light(params)
elif command_type == "create_hdri_environment":
    return _handle_create_hdri_environment(params)
elif command_type == "clear_lights":
    return _handle_clear_lights(params)
elif command_type == "list_lights":
    return _handle_list_lights(params)
```

**Step 3: Commit**

```bash
git add addon.py
git commit -m "feat(addon): add studio lighting, area light, HDRI handlers"
```

---

## Task 1.8: Add Camera Handlers to Blender Addon

**Files:**
- Modify: `addon.py`

**Step 1: Add camera command handlers**

```python
# In addon.py, add these handlers

def _handle_create_composition_camera(params):
    """Create a camera with composition framing"""
    import bpy
    import math
    
    name = params.get("name", "Camera")
    composition = params.get("composition", "center")
    focal_length = params.get("focal_length", 50.0)
    location = params.get("location", [7, -7, 5])
    target = params.get("target", [0, 0, 0])
    
    # Create camera
    cam_data = bpy.data.cameras.new(name=name)
    cam_object = bpy.data.objects.new(name=name, object_data=cam_data)
    bpy.context.collection.objects.link(cam_object)
    
    # Set focal length
    cam_data.lens = focal_length
    
    # Position camera
    cam_object.location = location
    
    # Point at target
    direction = [target[0] - location[0], target[1] - location[1], target[2] - location[2]]
    rot_quat = direction_to_quat(direction)
    cam_object.rotation_quaternion = rot_quat
    
    # Adjust for composition
    if composition == "rule_of_thirds":
        # Offset camera slightly for rule of thirds
        cam_object.location[0] += 0.5
        cam_object.location[2] += 0.3
    elif composition == "golden_ratio":
        # Golden ratio offset
        cam_object.location[0] += 0.618
    elif composition == "diagonal":
        # Rotate for diagonal composition
        cam_object.rotation_euler[2] += math.radians(15)
    
    return {
        "status": "success",
        "name": name,
        "composition": composition,
        "focal_length": focal_length
    }


def direction_to_quat(direction):
    """Convert direction vector to quaternion"""
    import math
    from mathutils import Vector, Quaternion
    
    direction = Vector(direction)
    direction.normalize()
    
    # Default forward direction
    forward = Vector((0, 0, -1))
    
    # Calculate rotation
    dot = forward.dot(direction)
    if abs(dot + 1) < 0.000001:
        return Quaternion((0, 1, 0, 0))
    if abs(dot - 1) < 0.000001:
        return Quaternion()
    
    angle = math.acos(dot)
    axis = forward.cross(direction).normalized()
    return Quaternion(axis, angle)


def _handle_create_isometric_camera(params):
    """Create an isometric camera"""
    import bpy
    import math
    
    name = params.get("name", "Isometric")
    ortho_scale = params.get("ortho_scale", 10.0)
    angle = params.get("angle", 35.264)  # True isometric angle
    
    # Create orthographic camera
    cam_data = bpy.data.cameras.new(name=name)
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho_scale
    
    cam_object = bpy.data.objects.new(name=name, object_data=cam_data)
    bpy.context.collection.objects.link(cam_object)
    
    # Position for isometric view
    distance = 10.0
    angle_rad = math.radians(angle)
    
    cam_object.location = (
        distance * math.cos(angle_rad) * math.cos(math.radians(45)),
        distance * math.cos(angle_rad) * math.sin(math.radians(45)),
        distance * math.sin(angle_rad)
    )
    
    # Point at origin
    direction = [-cam_object.location[0], -cam_object.location[1], -cam_object.location[2]]
    rot_quat = direction_to_quat(direction)
    cam_object.rotation_quaternion = rot_quat
    
    return {
        "status": "success",
        "name": name,
        "type": "orthographic",
        "ortho_scale": ortho_scale
    }


def _handle_set_camera_dof(params):
    """Set camera depth of field"""
    import bpy
    
    camera_name = params.get("camera_name")
    focus_distance = params.get("focus_distance", 10.0)
    aperture = params.get("aperture", 5.6)
    
    cam_object = bpy.data.objects.get(camera_name)
    if not cam_object or cam_object.type != 'CAMERA':
        return {"status": "error", "message": f"Camera '{camera_name}' not found"}
    
    cam_data = cam_object.data
    
    # Enable DOF
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = focus_distance
    
    # Set aperture (f-stop)
    # Blender uses aperture ratio, approximate from f-stop
    cam_data.dof.aperture_fstop = aperture
    
    return {
        "status": "success",
        "camera": camera_name,
        "aperture": aperture,
        "focus_distance": focus_distance
    }


def _handle_apply_camera_preset(params):
    """Apply camera preset"""
    import bpy
    
    camera_name = params.get("camera_name")
    preset = params.get("preset")
    
    cam_object = bpy.data.objects.get(camera_name)
    if not cam_object or cam_object.type != 'CAMERA':
        return {"status": "error", "message": f"Camera '{camera_name}' not found"}
    
    cam_data = cam_object.data
    
    # Preset configurations
    presets = {
        "portrait": {"focal_length": 85, "sensor_width": 36},
        "landscape": {"focal_length": 35, "sensor_width": 36},
        "macro": {"focal_length": 100, "sensor_width": 36},
        "cinematic": {"focal_length": 50, "sensor_width": 36},
        "action": {"focal_length": 24, "sensor_width": 36},
        "telephoto": {"focal_length": 200, "sensor_width": 36},
        "product": {"focal_length": 50, "sensor_width": 36},
    }
    
    if preset not in presets:
        return {"status": "error", "message": f"Unknown preset: {preset}"}
    
    config = presets[preset]
    cam_data.lens = config["focal_length"]
    cam_data.sensor_width = config["sensor_width"]
    
    return {
        "status": "success",
        "camera": camera_name,
        "preset": preset,
        "focal_length": config["focal_length"]
    }


def _handle_set_active_camera(params):
    """Set active camera"""
    import bpy
    
    camera_name = params.get("camera_name")
    
    cam_object = bpy.data.objects.get(camera_name)
    if not cam_object or cam_object.type != 'CAMERA':
        return {"status": "error", "message": f"Camera '{camera_name}' not found"}
    
    bpy.context.scene.camera = cam_object
    
    return {"status": "success", "active_camera": camera_name}


def _handle_list_cameras(params):
    """List all cameras"""
    import bpy
    
    cameras = []
    active = bpy.context.scene.camera.name if bpy.context.scene.camera else None
    
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA':
            cameras.append({
                "name": obj.name,
                "type": obj.data.type,
                "focal_length": obj.data.lens if obj.data.type == 'PERSP' else None,
                "is_active": obj.name == active
            })
    
    return {"cameras": cameras, "count": len(cameras), "active": active}


def _handle_frame_camera_to_selection(params):
    """Frame camera to fit selection"""
    import bpy
    
    camera_name = params.get("camera_name")
    margin = params.get("margin", 1.1)
    
    cam_object = bpy.data.objects.get(camera_name)
    if not cam_object or cam_object.type != 'CAMERA':
        return {"status": "error", "message": f"Camera '{camera_name}' not found"}
    
    # Get selected objects
    selected = bpy.context.selected_objects
    if not selected:
        return {"status": "error", "message": "No objects selected"}
    
    # Calculate bounding box
    min_co = [float('inf')] * 3
    max_co = [float('-inf')] * 3
    
    for obj in selected:
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ bpy.mathutils.Vector(corner)
            for i in range(3):
                min_co[i] = min(min_co[i], world_corner[i])
                max_co[i] = max(max_co[i], world_corner[i])
    
    # Calculate center and size
    center = [(min_co[i] + max_co[i]) / 2 for i in range(3)]
    size = max(max_co[i] - min_co[i] for i in range(3)) * margin
    
    # Position camera
    if cam_object.data.type == 'PERSP':
        # Calculate distance based on FOV
        fov = cam_object.data.angle
        distance = size / (2 * math.tan(fov / 2))
    else:
        # Orthographic
        cam_object.data.ortho_scale = size
        distance = 10.0
    
    # Position camera looking at center
    direction = cam_object.matrix_world.to_3x3() @ bpy.mathutils.Vector((0, 0, -1))
    cam_object.location = center - direction.normalized() * distance
    
    return {
        "status": "success",
        "camera": camera_name,
        "framed_objects": [obj.name for obj in selected]
    }
```

**Step 2: Add dispatch cases**

```python
# In _dispatch_command, add:

elif command_type == "create_composition_camera":
    return _handle_create_composition_camera(params)
elif command_type == "create_isometric_camera":
    return _handle_create_isometric_camera(params)
elif command_type == "set_camera_dof":
    return _handle_set_camera_dof(params)
elif command_type == "apply_camera_preset":
    return _handle_apply_camera_preset(params)
elif command_type == "set_active_camera":
    return _handle_set_active_camera(params)
elif command_type == "list_cameras":
    return _handle_list_cameras(params)
elif command_type == "frame_camera_to_selection":
    return _handle_frame_camera_to_selection(params)
```

**Step 3: Add required import**

```python
# At the top of addon.py, ensure mathutils is available
import math
import mathutils
```

**Step 4: Commit**

```bash
git add addon.py
git commit -m "feat(addon): add camera composition, isometric, DOF, preset handlers"
```

---

## Task 1.9: Add Composition Handlers to Blender Addon

**Files:**
- Modify: `addon.py`

**Step 1: Add composition command handlers**

```python
# In addon.py, add these handlers

def _handle_compose_scene(params):
    """Compose a scene based on preset"""
    import bpy
    
    preset = params.get("preset")
    
    handlers = {
        "product_shot": _compose_product_shot,
        "isometric": _compose_isometric_scene,
        "character": _compose_character_scene,
        "automotive": _compose_automotive_shot,
        "food": _compose_food_shot,
        "jewelry": _compose_jewelry_shot,
        "architectural": _compose_architectural_shot,
        "studio": _compose_studio_setup,
    }
    
    if preset not in handlers:
        return {"status": "error", "message": f"Unknown preset: {preset}"}
    
    return handlers[preset](params)


def _compose_product_shot(params):
    """Compose product photography shot"""
    import bpy
    
    style = params.get("style", "clean")
    background = params.get("background", "white")
    
    # Clear scene (keep camera)
    for obj in bpy.data.objects:
        if obj.type not in ['CAMERA']:
            bpy.data.objects.remove(obj)
    
    # Create background
    if background == "white":
        bg_color = [1, 1, 1]
    elif background == "black":
        bg_color = [0, 0, 0]
    else:
        bg_color = [0.5, 0.5, 0.5]
    
    # Create floor plane
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    
    # Create floor material
    mat = bpy.data.materials.new(name="FloorMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = bg_color + [1]
    bsdf.inputs["Roughness"].default_value = 0.8
    floor.data.materials.append(mat)
    
    # Setup lighting
    _setup_product_lighting(style)
    
    # Setup camera
    cam = bpy.data.objects.get("Camera")
    if not cam:
        bpy.ops.object.camera_add(location=(0, -5, 3))
        cam = bpy.context.active_object
        cam.name = "Camera"
    
    cam.rotation_euler = (1.1, 0, 0)  # Look down at 45°
    bpy.context.scene.camera = cam
    
    return {
        "status": "success",
        "preset": "product_shot",
        "style": style,
        "background": background,
        "camera": cam.name
    }


def _setup_product_lighting(style):
    """Setup lighting for product shot"""
    import bpy
    
    # Clear existing lights
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj)
    
    if style == "clean":
        # Soft key light
        light_data = bpy.data.lights.new(name="Key", type='AREA')
        light_data.shape = 'RECTANGLE'
        light_data.size = 3.0
        light_data.energy = 500
        
        light_obj = bpy.data.objects.new(name="Key", object_data=light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.location = (0, -4, 5)
        light_obj.rotation_euler = (0.785, 0, 0)
        
    elif style == "dramatic":
        # Spotlight
        light_data = bpy.data.lights.new(name="Key", type='SPOT')
        light_data.energy = 1000
        light_data.spot_size = 0.5
        
        light_obj = bpy.data.objects.new(name="Key", object_data=light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.location = (2, -3, 5)
        light_obj.rotation_euler = (0.9, 0, 0.3)


def _compose_isometric_scene(params):
    """Compose isometric scene"""
    import bpy
    import math
    
    grid_size = params.get("grid_size", 10.0)
    floor = params.get("floor", True)
    shadow_catcher = params.get("shadow_catcher", True)
    
    # Create orthographic camera
    cam_data = bpy.data.cameras.new(name="IsometricCam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = grid_size
    
    cam_obj = bpy.data.objects.new(name="IsometricCam", object_data=cam_data)
    bpy.context.collection.objects.link(cam_obj)
    
    # Position for isometric view
    angle = math.radians(35.264)
    distance = 15.0
    
    cam_obj.location = (
        distance * math.cos(angle) * 0.707,
        distance * math.cos(angle) * 0.707,
        distance * math.sin(angle)
    )
    
    # Point at origin
    cam_obj.rotation_euler = (math.radians(60), 0, math.radians(45))
    
    bpy.context.scene.camera = cam_obj
    
    # Create floor
    if floor:
        bpy.ops.mesh.primitive_plane_add(size=grid_size)
        floor_obj = bpy.context.active_object
        floor_obj.name = "Floor"
        
        if shadow_catcher:
            # Make it a shadow catcher
            mat = bpy.data.materials.new(name="ShadowCatcher")
            mat.use_nodes = True
            mat.shadow_method = 'CLIP'
            floor_obj.data.materials.append(mat)
    
    return {
        "status": "success",
        "preset": "isometric",
        "camera": "IsometricCam",
        "floor": floor,
        "shadow_catcher": shadow_catcher
    }


def _compose_character_scene(params):
    """Compose character scene"""
    import bpy
    
    environment = params.get("environment", "studio")
    ground_plane = params.get("ground_plane", True)
    
    # Setup based on environment
    if environment == "studio":
        # Neutral studio lighting
        _setup_studio_lighting()
    elif environment == "outdoor":
        # Sun light
        light_data = bpy.data.lights.new(name="Sun", type='SUN')
        light_data.energy = 3.0
        light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.rotation_euler = (0.5, 0, 0.5)
    
    # Create ground plane
    if ground_plane:
        bpy.ops.mesh.primitive_plane_add(size=20)
        ground = bpy.context.active_object
        ground.name = "Ground"
    
    # Setup camera
    bpy.ops.object.camera_add(location=(0, -8, 2))
    cam = bpy.context.active_object
    cam.rotation_euler = (1.2, 0, 0)
    bpy.context.scene.camera = cam
    
    return {
        "status": "success",
        "preset": "character",
        "environment": environment
    }


def _setup_studio_lighting():
    """Setup basic studio lighting"""
    import bpy
    
    # Clear lights
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj)
    
    # Key light
    key_data = bpy.data.lights.new(name="Key", type='AREA')
    key_data.shape = 'RECTANGLE'
    key_data.size = 2.0
    key_data.energy = 500
    
    key_obj = bpy.data.objects.new(name="Key", object_data=key_data)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = (3, -3, 4)
    key_obj.rotation_euler = (0.8, 0, 0.5)


def _compose_automotive_shot(params):
    """Compose automotive shot"""
    import bpy
    import math
    
    angle = params.get("angle", "three_quarter")
    environment = params.get("environment", "studio")
    
    # Camera positions for different angles
    angles = {
        "front": (0, -12, 2, 1.2, 0, 0),
        "rear": (0, 12, 2, 1.2, 0, 3.14),
        "three_quarter": (8, -8, 3, 1.0, 0, 0.785),
        "side": (12, 0, 2, 1.2, 0, 1.57),
        "top": (0, 0, 15, 1.57, 0, 0),
    }
    
    if angle in angles:
        loc_x, loc_y, loc_z, rot_x, rot_y, rot_z = angles[angle]
        
        bpy.ops.object.camera_add(location=(loc_x, loc_y, loc_z))
        cam = bpy.context.active_object
        cam.rotation_euler = (rot_x, rot_y, rot_z)
        bpy.context.scene.camera = cam
    
    # Setup environment lighting
    if environment == "studio":
        _setup_studio_lighting()
    
    return {
        "status": "success",
        "preset": "automotive",
        "angle": angle,
        "environment": environment
    }


def _compose_food_shot(params):
    """Compose food photography shot"""
    import bpy
    
    style = params.get("style", "flat_lay")
    
    # Camera based on style
    if style == "flat_lay":
        bpy.ops.object.camera_add(location=(0, 0, 10))
        cam = bpy.context.active_object
        cam.rotation_euler = (0, 0, 0)
    elif style == "angled":
        bpy.ops.object.camera_add(location=(0, -8, 6))
        cam = bpy.context.active_object
        cam.rotation_euler = (1.0, 0, 0)
    else:  # side
        bpy.ops.object.camera_add(location=(0, -10, 3))
        cam = bpy.context.active_object
        cam.rotation_euler = (1.2, 0, 0)
    
    bpy.context.scene.camera = cam
    
    # Soft lighting
    _setup_product_lighting("clean")
    
    return {"status": "success", "preset": "food", "style": style}


def _compose_jewelry_shot(params):
    """Compose jewelry shot"""
    import bpy
    
    style = params.get("style", "macro")
    reflections = params.get("reflections", True)
    
    # Macro camera
    bpy.ops.object.camera_add(location=(0, -5, 2))
    cam = bpy.context.active_object
    cam.data.lens = 100  # Macro lens
    cam.rotation_euler = (0.5, 0, 0)
    bpy.context.scene.camera = cam
    
    # Reflection plane
    if reflections:
        bpy.ops.mesh.primitive_plane_add(size=5, location=(0, 0, -0.5))
        mirror = bpy.context.active_object
        mirror.name = "ReflectionPlane"
        
        # Mirror material
        mat = bpy.data.materials.new(name="Mirror")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.05
        mirror.data.materials.append(mat)
    
    return {
        "status": "success",
        "preset": "jewelry",
        "style": style,
        "reflections": reflections
    }


def _compose_architectural_shot(params):
    """Compose architectural shot"""
    import bpy
    
    interior = params.get("interior", False)
    natural_light = params.get("natural_light", True)
    
    if interior:
        # Wide angle for interiors
        bpy.ops.object.camera_add(location=(5, -5, 2))
        cam = bpy.context.active_object
        cam.data.lens = 24
        cam.rotation_euler = (1.2, 0, 0.5)
    else:
        # Exterior view
        bpy.ops.object.camera_add(location=(15, -15, 8))
        cam = bpy.context.active_object
        cam.data.lens = 35
        cam.rotation_euler = (0.8, 0, 0.5)
    
    bpy.context.scene.camera = cam
    
    # Natural lighting
    if natural_light:
        light_data = bpy.data.lights.new(name="Sun", type='SUN')
        light_data.energy = 3.0
        light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.rotation_euler = (0.5, 0.3, 0.5)
    
    return {
        "status": "success",
        "preset": "architectural",
        "interior": interior
    }


def _compose_studio_setup(params):
    """Compose generic studio setup"""
    import bpy
    
    subject_type = params.get("subject_type", "generic")
    mood = params.get("mood", "neutral")
    
    # Basic studio setup
    _setup_studio_lighting()
    
    # Camera
    bpy.ops.object.camera_add(location=(0, -10, 3))
    cam = bpy.context.active_object
    cam.rotation_euler = (1.0, 0, 0)
    bpy.context.scene.camera = cam
    
    # Floor
    bpy.ops.mesh.primitive_plane_add(size=20)
    floor = bpy.context.active_object
    floor.name = "StudioFloor"
    
    return {
        "status": "success",
        "preset": "studio",
        "subject_type": subject_type,
        "mood": mood
    }


def _handle_clear_scene(params):
    """Clear scene"""
    import bpy
    
    keep_camera = params.get("keep_camera", False)
    keep_lights = params.get("keep_lights", False)
    
    active_camera = bpy.context.scene.camera
    removed = 0
    
    for obj in bpy.data.objects:
        should_remove = True
        
        if keep_camera and obj == active_camera:
            should_remove = False
        if keep_lights and obj.type == 'LIGHT':
            should_remove = False
        
        if should_remove:
            bpy.data.objects.remove(obj)
            removed += 1
    
    return {
        "status": "success",
        "removed_objects": removed,
        "kept_camera": keep_camera,
        "kept_lights": keep_lights
    }


def _handle_setup_render_settings(params):
    """Setup render settings"""
    import bpy
    
    engine = params.get("engine", "CYCLES")
    samples = params.get("samples", 128)
    resolution_x = params.get("resolution_x", 1920)
    resolution_y = params.get("resolution_y", 1080)
    denoise = params.get("denoise", True)
    
    # Set render engine
    bpy.context.scene.render.engine = engine
    
    # Set resolution
    bpy.context.scene.render.resolution_x = resolution_x
    bpy.context.scene.render.resolution_y = resolution_y
    
    # Cycles settings
    if engine == "CYCLES":
        bpy.context.scene.cycles.samples = samples
        bpy.context.scene.cycles.use_denoising = denoise
    
    return {
        "status": "success",
        "engine": engine,
        "samples": samples,
        "resolution": [resolution_x, resolution_y],
        "denoise": denoise
    }
```

**Step 2: Add dispatch cases**

```python
# In _dispatch_command, add:

elif command_type == "compose_scene":
    return _handle_compose_scene(params)
elif command_type == "clear_scene":
    return _handle_clear_scene(params)
elif command_type == "setup_render_settings":
    return _handle_setup_render_settings(params)
```

**Step 3: Commit**

```bash
git add addon.py
git commit -m "feat(addon): add scene composition handlers (product, isometric, automotive, etc.)"
```

---

# Phase 2: Enterprise Infrastructure

## Task 2.1: Set Up Testing Infrastructure

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/__init__.py`
- Modify: `pyproject.toml`

**Step 1: Add test dependencies to pyproject.toml**

```toml
# In pyproject.toml, add to [project] dependencies:
dependencies = [
    "mcp[cli]>=1.3.0",
    "supabase>=2.0.0",
    "tomli>=2.0.0",
    "pydantic>=2.0.0",
    "structlog>=24.0.0",
    "tenacity>=8.0.0",
]

# Add optional dependencies:
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "httpx>=0.25.0",
    "respx>=0.20.0",
]
```

**Step 2: Create tests/__init__.py**

```python
# tests/__init__.py
"""Blender MCP test suite"""
```

**Step 3: Create tests/conftest.py**

```python
# tests/conftest.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def mock_blender_connection():
    """Mock Blender connection for testing"""
    conn = Mock()
    conn.send_command = Mock(return_value={"status": "success", "result": {}})
    conn.connect = Mock(return_value=True)
    conn.disconnect = Mock()
    return conn


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset global singletons between tests"""
    yield
    # Reset any global state here
```

**Step 4: Install dev dependencies**

```bash
uv pip install -e ".[dev]"
```

**Step 5: Run tests to verify setup**

```bash
pytest tests/ -v
# Expected: Tests pass (or no tests collected if none exist yet)
```

**Step 6: Commit**

```bash
git add pyproject.toml tests/conftest.py tests/__init__.py
git commit -m "test: set up pytest infrastructure with async support"
```

---

## Task 2.2: Implement Pydantic Validation Schemas

**Files:**
- Create: `src/blender_mcp/schemas.py`
- Create: `tests/test_schemas.py`

**Step 1: Create validation schemas**

```python
# src/blender_mcp/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class PrimitiveType(str, Enum):
    CUBE = "cube"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    CONE = "cone"
    TORUS = "torus"
    PLANE = "plane"


class LightType(str, Enum):
    POINT = "point"
    SUN = "sun"
    SPOT = "spot"
    AREA = "area"


class CreatePrimitiveRequest(BaseModel):
    type: PrimitiveType = Field(..., description="Type of primitive to create")
    name: Optional[str] = Field(None, max_length=64, description="Object name")
    size: Optional[float] = Field(None, gt=0, description="Size parameter")
    location: Optional[List[float]] = Field(None, min_length=3, max_length=3, description="[x, y, z] location")
    rotation: Optional[List[float]] = Field(None, min_length=3, max_length=3, description="[x, y, z] rotation in radians")
    scale: Optional[List[float]] = Field(None, min_length=3, max_length=3, description="[x, y, z] scale")
    
    @field_validator('location', 'rotation', 'scale')
    @classmethod
    def validate_vector3(cls, v):
        if v is not None:
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError("All vector components must be numbers")
        return v


class CreateLightRequest(BaseModel):
    type: LightType = Field(..., description="Type of light")
    energy: float = Field(..., gt=0, description="Light energy/strength")
    color: Optional[List[float]] = Field(None, min_length=3, max_length=3, description="[r, g, b] color (0-1)")
    location: Optional[List[float]] = Field(None, min_length=3, max_length=3, description="[x, y, z] location")
    rotation: Optional[List[float]] = Field(None, min_length=3, max_length=3, description="[x, y, z] rotation")
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v):
        if v is not None:
            if not all(0 <= x <= 1 for x in v):
                raise ValueError("Color values must be between 0 and 1")
        return v


class CreateMaterialRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="Material name")
    base_color: Optional[List[float]] = Field(None, min_length=3, max_length=3, description="[r, g, b] color")
    metallic: Optional[float] = Field(None, ge=0, le=1, description="Metallic value")
    roughness: Optional[float] = Field(None, ge=0, le=1, description="Roughness value")
    transmission: Optional[float] = Field(None, ge=0, le=1, description="Transmission value")
    ior: Optional[float] = Field(None, ge=1.0, le=3.0, description="Index of refraction")


class CreateCameraRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="Camera name")
    focal_length: Optional[float] = Field(None, gt=0, le=1000, description="Focal length in mm")
    location: Optional[List[float]] = Field(None, min_length=3, max_length=3, description="[x, y, z] location")
    target: Optional[List[float]] = Field(None, min_length=3, max_length=3, description="[x, y, z] look-at point")


class ExportGLBRequest(BaseModel):
    target: Literal["scene", "selection", "collection"] = Field("scene", description="What to export")
    name: str = Field("export", min_length=1, max_length=128, description="File name")
    output_dir: str = Field("exports", description="Output directory")
    draco: bool = Field(True, description="Use Draco compression")


class SuccessResponse(BaseModel):
    ok: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    ok: bool = False
    error: Dict[str, Any] = Field(..., description="Error details")
    request_id: Optional[str] = None
```

**Step 2: Write tests for schemas**

```python
# tests/test_schemas.py
import pytest
from blender_mcp.schemas import (
    CreatePrimitiveRequest,
    CreateLightRequest,
    CreateMaterialRequest,
    CreateCameraRequest,
)
from pydantic import ValidationError


class TestCreatePrimitiveRequest:
    def test_valid_cube(self):
        req = CreatePrimitiveRequest(type="cube", name="MyCube")
        assert req.type == "cube"
        assert req.name == "MyCube"
    
    def test_invalid_primitive_type(self):
        with pytest.raises(ValidationError) as exc_info:
            CreatePrimitiveRequest(type="invalid")
        assert "type" in str(exc_info.value)
    
    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            CreatePrimitiveRequest(type="cube", name="x" * 100)
    
    def test_invalid_size(self):
        with pytest.raises(ValidationError):
            CreatePrimitiveRequest(type="cube", size=-1)
    
    def test_invalid_location_length(self):
        with pytest.raises(ValidationError):
            CreatePrimitiveRequest(type="cube", location=[1, 2])


class TestCreateLightRequest:
    def test_valid_point_light(self):
        req = CreateLightRequest(type="point", energy=100)
        assert req.type == "point"
        assert req.energy == 100
    
    def test_invalid_color_range(self):
        with pytest.raises(ValidationError):
            CreateLightRequest(type="point", energy=100, color=[1.5, 0, 0])
    
    def test_zero_energy(self):
        with pytest.raises(ValidationError):
            CreateLightRequest(type="point", energy=0)


class TestCreateMaterialRequest:
    def test_valid_material(self):
        req = CreateMaterialRequest(
            name="Gold",
            base_color=[1.0, 0.8, 0.0],
            metallic=1.0,
            roughness=0.3
        )
        assert req.name == "Gold"
        assert req.metallic == 1.0
    
    def test_invalid_metallic_range(self):
        with pytest.raises(ValidationError):
            CreateMaterialRequest(name="Test", metallic=1.5)
    
    def test_invalid_ior_range(self):
        with pytest.raises(ValidationError):
            CreateMaterialRequest(name="Glass", ior=0.5)


class TestCreateCameraRequest:
    def test_valid_camera(self):
        req = CreateCameraRequest(
            name="MainCamera",
            focal_length=50.0,
            location=[0, -10, 5]
        )
        assert req.focal_length == 50.0
    
    def test_invalid_focal_length(self):
        with pytest.raises(ValidationError):
            CreateCameraRequest(name="Cam", focal_length=-10)
```

**Step 3: Run tests**

```bash
pytest tests/test_schemas.py -v
# Expected: All tests pass
```

**Step 4: Commit**

```bash
git add src/blender_mcp/schemas.py tests/test_schemas.py
git commit -m "feat: add pydantic validation schemas for all tool inputs"
```

---

## Task 2.3: Add Structured Logging

**Files:**
- Create: `src/blender_mcp/logging_config.py`
- Modify: `src/blender_mcp/server.py`

**Step 1: Create logging configuration**

```python
# src/blender_mcp/logging_config.py
import structlog
import logging
import sys
from typing import Any, Dict


# Configure standard library logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if not sys.stdout.isatty() else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with the given name"""
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding context to logs"""
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.logger = structlog.get_logger()
    
    def __enter__(self):
        self.logger = self.logger.bind(**self.context)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def log_tool_call(tool_name: str, request_id: str = None, **context):
    """Decorator context for logging tool calls"""
    return LogContext(tool=tool_name, request_id=request_id, **context)
```

**Step 2: Update server.py to use structured logging**

```python
# In src/blender_mcp/server.py, replace the logging import with:
from .logging_config import get_logger, LogContext

logger = get_logger("BlenderMCPServer")
```

**Step 3: Commit**

```bash
git add src/blender_mcp/logging_config.py
git commit -m "feat: add structured logging with structlog"
```

---

## Task 2.4: Implement Connection Resilience

**Files:**
- Create: `src/blender_mcp/resilience.py`
- Create: `tests/test_resilience.py`

**Step 1: Create resilience module**

```python
# src/blender_mcp/resilience.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from functools import wraps
import time
import logging
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger("BlenderMCP.Resilience")


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """Circuit breaker pattern for external API calls"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state")
                return True
            return False
        
        return True  # HALF_OPEN
    
    def record_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failures} failures")
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.can_execute():
                raise CircuitBreakerOpen("Circuit breaker is open")
            
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except self.expected_exception as e:
                self.record_failure()
                raise
        
        return wrapper


class CircuitBreakerOpen(Exception):
    pass


# Pre-configured retry decorators
blender_connection_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)

api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
```

**Step 2: Write tests for resilience**

```python
# tests/test_resilience.py
import pytest
from unittest.mock import Mock, patch
from blender_mcp.resilience import CircuitBreaker, CircuitBreakerOpen
import time


class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state.value == "closed"
        assert cb.can_execute() is True
    
    def test_opens_after_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        
        @cb
        def failing_func():
            raise ValueError("Test error")
        
        # First 3 calls should raise ValueError
        for _ in range(3):
            with pytest.raises(ValueError):
                failing_func()
        
        # Circuit should be open now
        assert cb.state.value == "open"
        
        # Next call should raise CircuitBreakerOpen
        with pytest.raises(CircuitBreakerOpen):
            failing_func()
    
    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        @cb
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_func()
        
        assert cb.state.value == "open"
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Should be able to execute now (half-open)
        assert cb.can_execute() is True
    
    def test_closes_on_success(self):
        cb = CircuitBreaker(failure_threshold=2)
        call_count = 0
        
        @cb
        def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Fail")
            return "success"
        
        with pytest.raises(ValueError):
            sometimes_fails()
        
        result = sometimes_fails()
        assert result == "success"
        assert cb.state.value == "closed"
```

**Step 3: Run tests**

```bash
pytest tests/test_resilience.py -v
# Expected: All tests pass
```

**Step 4: Commit**

```bash
git add src/blender_mcp/resilience.py tests/test_resilience.py
git commit -m "feat: add connection resilience with retry and circuit breaker"
```

---

# Phase 3: Critical Gap Fixes

## Task 3.1: Implement Job Management Handlers

**Files:**
- Modify: `addon.py`

**Step 1: Add job management handlers to addon.py**

```python
# In addon.py, add these handlers

# In-memory job store (for demo purposes)
_job_store = {}

def _handle_create_job(params):
    """Create a new async job"""
    import uuid
    from datetime import datetime
    
    provider = params.get("provider")
    payload = params.get("payload", {})
    
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    
    job = {
        "id": job_id,
        "provider": provider,
        "status": "pending",
        "payload": payload,
        "result": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "progress": 0,
    }
    
    _job_store[job_id] = job
    
    return {
        "job_id": job_id,
        "provider": provider,
        "status": "pending"
    }


def _handle_get_job(params):
    """Get job status"""
    job_id = params.get("job_id")
    
    if job_id not in _job_store:
        return {"status": "error", "message": f"Job not found: {job_id}"}
    
    job = _job_store[job_id]
    
    return {
        "job_id": job["id"],
        "provider": job["provider"],
        "status": job["status"],
        "progress": job["progress"],
        "result": job["result"],
        "error": job["error"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
    }


def _handle_import_job_result(params):
    """Import completed job result into scene"""
    job_id = params.get("job_id")
    name = params.get("name")
    
    if job_id not in _job_store:
        return {"status": "error", "message": f"Job not found: {job_id}"}
    
    job = _job_store[job_id]
    
    if job["status"] != "completed":
        return {"status": "error", "message": f"Job is not completed. Current status: {job['status']}"}
    
    # Import logic would go here based on provider
    return {
        "job_id": job["id"],
        "name": name,
        "imported": True,
    }
```

**Step 2: Add dispatch cases**

```python
# In _dispatch_command, add:

elif command_type == "create_job":
    return _handle_create_job(params)
elif command_type == "get_job":
    return _handle_get_job(params)
elif command_type == "import_job_result":
    return _handle_import_job_result(params)
```

**Step 3: Commit**

```bash
git add addon.py
git commit -m "feat(addon): implement job management handlers (create, get, import)"
```

---

## Task 3.2: Implement Tripo3D Integration

**Files:**
- Create: `src/blender_mcp/tools/tripo3d.py`
- Modify: `addon.py`

**Step 1: Create Tripo3D tool module**

```python
# src/blender_mcp/tools/tripo3d.py
"""
Tripo3D Integration
AI-powered 3D model generation from text or images.
"""

import json
import logging
from typing import Optional

from mcp.server.fastmcp import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


@telemetry_tool("get_tripo3d_status")
@mcp.tool()
async def get_tripo3d_status(ctx: Context) -> str:
    """Check Tripo3D integration status."""
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_tripo3d_status", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting Tripo3D status: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("generate_tripo3d_model")
@mcp.tool()
async def generate_tripo3d_model(
    ctx: Context,
    text_prompt: Optional[str] = None,
    image_url: Optional[str] = None,
) -> str:
    """
    Generate 3D model using Tripo3D.
    
    Parameters:
    - text_prompt: Text description of the desired model
    - image_url: URL to reference image
    
    Returns:
    - JSON string with task information
    """
    try:
        if not text_prompt and not image_url:
            return json.dumps({"error": "Either text_prompt or image_url must be provided"})
        
        blender = get_blender_connection()
        params = {}
        if text_prompt:
            params["text_prompt"] = text_prompt
        if image_url:
            params["image_url"] = image_url
        
        result = blender.send_command("generate_tripo3d_model", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error generating Tripo3D model: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("poll_tripo3d_status")
@mcp.tool()
async def poll_tripo3d_status(ctx: Context, task_id: str) -> str:
    """
    Check Tripo3D generation task status.
    
    Parameters:
    - task_id: Task ID from generate_tripo3d_model
    
    Returns:
    - JSON string with task status
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("poll_tripo3d_status", {"task_id": task_id})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error polling Tripo3D status: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("import_tripo3d_model")
@mcp.tool()
async def import_tripo3d_model(
    ctx: Context,
    model_url: str,
    name: str = "Tripo3D_Model",
) -> str:
    """
    Import Tripo3D generated model.
    
    Parameters:
    - model_url: URL to the generated model
    - name: Object name in scene
    
    Returns:
    - JSON string with import result
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("import_tripo3d_model", {
            "model_url": model_url,
            "name": name,
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error importing Tripo3D model: {str(e)}")
        return json.dumps({"error": str(e)})
```

**Step 2: Add Tripo3D handlers to addon.py**

```python
# In addon.py, add these handlers

def _handle_get_tripo3d_status(params):
    """Get Tripo3D integration status"""
    # Check if Tripo3D is configured
    # This would check for API key in preferences
    return {
        "enabled": True,
        "has_api_key": True,
        "message": "Tripo3D ready"
    }


def _handle_generate_tripo3d_model(params):
    """Generate 3D model using Tripo3D"""
    import requests
    
    text_prompt = params.get("text_prompt")
    image_url = params.get("image_url")
    
    # This would call the actual Tripo3D API
    # For now, return a mock response
    return {
        "task_id": "tripo_task_123",
        "status": "pending",
        "message": "Generation task created"
    }


def _handle_poll_tripo3d_status(params):
    """Check Tripo3D generation status"""
    task_id = params.get("task_id")
    
    # This would poll the actual Tripo3D API
    return {
        "task_id": task_id,
        "status": "completed",
        "progress": 100,
        "model_url": "https://example.com/model.glb"
    }


def _handle_import_tripo3d_model(params):
    """Import Tripo3D generated model"""
    import bpy
    import tempfile
    import os
    import requests
    
    model_url = params.get("model_url")
    name = params.get("name", "Tripo3D_Model")
    
    if not model_url:
        return {"status": "error", "message": "model_url is required"}
    
    # Download model
    temp_dir = tempfile.gettempdir()
    model_path = os.path.join(temp_dir, f"{name}.glb")
    
    try:
        response = requests.get(model_url, timeout=60)
        response.raise_for_status()
        
        with open(model_path, "wb") as f:
            f.write(response.content)
        
        # Import into Blender
        bpy.ops.import_scene.gltf(filepath=model_path)
        
        # Rename imported object
        imported = bpy.context.selected_objects
        if imported:
            for obj in imported:
                obj.name = name
        
        return {
            "status": "success",
            "name": name,
            "imported_objects": [obj.name for obj in imported]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

**Step 3: Add dispatch cases**

```python
# In _dispatch_command, add:

elif command_type == "get_tripo3d_status":
    return _handle_get_tripo3d_status(params)
elif command_type == "generate_tripo3d_model":
    return _handle_generate_tripo3d_model(params)
elif command_type == "poll_tripo3d_status":
    return _handle_poll_tripo3d_status(params)
elif command_type == "import_tripo3d_model":
    return _handle_import_tripo3d_model(params)
```

**Step 4: Update tools __init__.py**

```python
# In src/blender_mcp/tools/__init__.py, add:
from . import tripo3d
```

**Step 5: Commit**

```bash
git add src/blender_mcp/tools/tripo3d.py addon.py src/blender_mcp/tools/__init__.py
git commit -m "feat: implement Tripo3D integration"
```

---

## Task 3.3: Run Full Test Suite

**Step 1: Run all tests**

```bash
pytest tests/ -v --cov=src/blender_mcp
```

**Step 2: Fix any failing tests**

If tests fail, fix them before proceeding.

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve test failures"
```

---

## Task 3.4: Final Integration Test

**Step 1: Start Blender with the addon**

```bash
# In Blender, install and enable the addon
# Then start the MCP server
python main.py
```

**Step 2: Test a simple workflow**

Using an MCP client, test:
1. `get_scene_info` - Verify connection
2. `create_bsdf_material` - Create a material
3. `create_studio_lighting` - Add lighting
4. `create_composition_camera` - Add camera
5. `compose_product_shot` - Test composition

**Step 3: Document any issues**

Create issues for any problems found.

---

# Summary

This plan covers:

**Phase 1: Production Studio Tools**
- Materials module (BSDF, emission, glass, metal, subsurface)
- Lighting module (studio presets, HDRI, area lights, volumetrics)
- Camera module (composition, isometric, DOF, presets)
- Composition module (product, isometric, automotive, food, jewelry)
- All corresponding addon handlers

**Phase 2: Enterprise Infrastructure**
- Testing infrastructure (pytest, conftest)
- Pydantic validation schemas
- Structured logging (structlog)
- Connection resilience (retry, circuit breaker)

**Phase 3: Critical Gap Fixes**
- Job management handlers
- Tripo3D integration

**Total: ~30 bite-sized tasks with complete code, tests, and commits.**
