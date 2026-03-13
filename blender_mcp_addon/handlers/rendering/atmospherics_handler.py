"""
Atmospheric effects handlers for Blender MCP addon.

Implements volumetric fog, weather systems, sky generation, and atmospheric scattering.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import bpy
from bpy import context as bpy_context

logger = logging.getLogger("BlenderMCPTools")


def get_status() -> Dict[str, Any]:
    """Get atmospheric system status."""
    return {
        "status": "ready",
        "features": {
            "volumetric_fog": True,
            "weather_systems": True,
            "sky_generation": True,
            "atmospheric_scattering": True,
        },
    }


def create_volumetric_fog(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create volumetric fog effect.

    Parameters:
    - name: Fog volume name
    - density: Fog density (0.001-1.0)
    - height: Maximum height
    - color: Fog color [r, g, b]
    - noise_scale: Noise variation scale
    - noise_depth: Noise detail level
    """
    name = params.get("name", "VolumetricFog")
    density = params.get("density", 0.1)
    height = params.get("height", 10.0)
    color = params.get("color", [0.9, 0.9, 0.95])
    noise_scale = params.get("noise_scale", 1.0)

    # Create volume cube
    bpy.ops.mesh.primitive_cube_add(size=10)
    cube = bpy_context.active_object
    cube.name = name
    cube.scale = [50, 50, height / 10]

    # Create volume material
    mat = bpy.data.materials.new(name=f"{name}_mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    # Volume scatter
    scatter = nodes.new("ShaderNodeVolumeScatter")
    scatter.inputs["Density"].default_value = density
    scatter.inputs["Color"].default_value = color + [1.0]

    # Connect to output
    output = nodes.get("Material Output")
    mat.node_tree.links.new(scatter.outputs["Volume"], output.inputs["Volume"])

    cube.data.materials.append(mat)

    return {
        "status": "success",
        "fog_name": name,
        "density": density,
        "height": height,
    }


def create_weather_system(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create weather particle system.

    Parameters:
    - weather_type: "rain", "snow", "dust", "leaves", "sparkles"
    - intensity: Particle count multiplier
    - coverage: Area coverage size
    - wind_speed: Wind effect strength
    - wind_direction: Wind direction [x, y, z]
    """
    weather_type = params.get("weather_type", "rain")
    intensity = params.get("intensity", 0.5)
    coverage = params.get("coverage", 20.0)
    wind_speed = params.get("wind_speed", 0.0)
    wind_direction = params.get("wind_direction", [1.0, 0.0, 0.0])

    # Create emitter plane
    bpy.ops.mesh.primitive_plane_add(size=coverage)
    emitter = bpy_context.active_object
    emitter.name = f"Weather_{weather_type}"

    # Add particle system
    bpy.ops.object.particle_system_add()
    psys = emitter.particle_systems[0]
    settings = psys.settings

    # Configure based on weather type
    if weather_type == "rain":
        settings.type = "HAIR"
        settings.emit_from = "FACE"
        settings.count = int(1000 * intensity)
        settings.hair_length = 2.0
        settings.use_rotations = True
    elif weather_type == "snow":
        settings.type = "HAIR"
        settings.count = int(500 * intensity)
        settings.hair_length = 0.1
        settings.particle_size = 0.05
    elif weather_type == "dust":
        settings.type = "EMITTER"
        settings.count = int(2000 * intensity)
        settings.lifetime = 200
        settings.particle_size = 0.02

    return {
        "status": "success",
        "weather_type": weather_type,
        "emitter_name": emitter.name,
        "particle_count": settings.count,
    }


def create_sky_system(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create physically accurate sky system.

    Parameters:
    - sky_type: "nishita", "preetham", "hosek_wilkie"
    - time_of_day: Hour (0-24)
    - turbidity: Atmospheric haziness (2-10)
    - ground_albedo: Ground reflection
    - sun_elevation: Sun angle override
    - sun_rotation: Sun position rotation
    """
    sky_type = params.get("sky_type", "nishita")
    time_of_day = params.get("time_of_day", 12.0)
    turbidity = params.get("turbidity", 2.0)
    ground_albedo = params.get("ground_albedo", 0.3)
    sun_elevation = params.get("sun_elevation", 0.5)
    sun_rotation = params.get("sun_rotation", 0.0)

    # Create sun with sky texture
    bpy.ops.object.light_add(type="SUN")
    sun = bpy_context.active_object
    sun.name = "SkySun"

    # Create world with sky texture
    world = bpy.data.worlds.new("SkyWorld")
    world.use_nodes = True
    nodes = world.node_tree.nodes

    # Add sky texture node
    sky_texture = nodes.new("ShaderNodeTexSky")
    sky_texture.sky_type = sky_type.upper()
    sky_texture.turbidity = turbidity
    sky_texture.ground_albedo = ground_albedo
    sky_texture.sun_elevation = sun_elevation
    sky_texture.sun_rotation = sun_rotation

    # Connect to background
    background = nodes.get("Background")
    world.node_tree.links.new(sky_texture.outputs["Color"], background.inputs["Color"])

    # Set as active world
    bpy_context.scene.world = world

    return {
        "status": "success",
        "sky_type": sky_type,
        "world_name": world.name,
        "sun_name": sun.name,
        "time_of_day": time_of_day,
    }


def create_atmospheric_scattering(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create atmospheric scattering effect.

    Parameters:
    - scattering_type: "rayleigh", "mie", "combined"
    - density: Atmosphere density
    - color: Scattering color
    - anisotropy: Scattering directionality
    """
    scattering_type = params.get("scattering_type", "combined")
    density = params.get("density", 1.0)
    color = params.get("color", [0.5, 0.7, 1.0])
    anisotropy = params.get("anisotropy", 0.0)

    # Create world volume material
    world = bpy_context.scene.world
    if not world:
        world = bpy.data.worlds.new("AtmosphereWorld")
        bpy_context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes

    # Add volume scatter for atmosphere
    scatter = nodes.new("ShaderNodeVolumeScatter")
    scatter.inputs["Density"].default_value = density * 0.001
    scatter.inputs["Color"].default_value = color + [1.0]
    scatter.inputs["Anisotropy"].default_value = anisotropy

    output = nodes.get("Output")
    if output:
        world.node_tree.links.new(scatter.outputs["Volume"], output.inputs["Volume"])

    return {
        "status": "success",
        "scattering_type": scattering_type,
        "density": density,
    }
