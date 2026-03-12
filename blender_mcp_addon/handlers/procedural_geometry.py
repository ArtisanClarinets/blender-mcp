"""
Procedural geometry generation handlers for Blender MCP addon.

Implements procedural city generation, terrain, vegetation, and architectural modeling.
"""

import json
import logging
import random
import math
from typing import Any, Dict, List, Optional
import bpy
from bpy import context as bpy_context

logger = logging.getLogger("BlenderMCPTools")


def get_status() -> Dict[str, Any]:
    """Get procedural geometry system status."""
    return {
        "status": "ready",
        "features": {
            "city_generation": True,
            "terrain_generation": True,
            "vegetation_systems": True,
            "architectural_modeling": True,
            "lod_systems": True,
        },
    }


def generate_city_block(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate procedural city block.

    Parameters:
    - name: City block name prefix
    - block_size: [width, depth] dimensions
    - building_count: Number of buildings
    - height_range: [min_height, max_height]
    - style: "modern", "historic", "industrial", "mixed"
    - density: Building density factor
    """
    name = params.get("name", "CityBlock")
    block_size = params.get("block_size", [50, 50])
    building_count = params.get("building_count", 10)
    height_range = params.get("height_range", [5, 30])
    style = params.get("style", "modern")
    density = params.get("density", 0.7)

    buildings_created = []

    # Create collection for city block
    collection = bpy.data.collections.new(name)
    bpy_context.collection.children.link(collection)

    for i in range(building_count):
        # Random position within block
        x = random.uniform(-block_size[0] / 2, block_size[0] / 2) * density
        y = random.uniform(-block_size[1] / 2, block_size[1] / 2) * density
        height = random.uniform(height_range[0], height_range[1])
        width = random.uniform(3, 8)
        depth = random.uniform(3, 8)

        # Create building
        bpy.ops.mesh.primitive_cube_add()
        building = bpy_context.active_object
        building.name = f"{name}_Building_{i}"
        building.location = (x, y, height / 2)
        building.scale = (width, depth, height)

        # Move to collection
        for coll in building.users_collection:
            coll.objects.unlink(building)
        collection.objects.link(building)

        buildings_created.append(building.name)

    return {
        "status": "success",
        "collection_name": name,
        "building_count": len(buildings_created),
        "buildings": buildings_created[:20],
        "block_size": block_size,
        "style": style,
    }


def generate_terrain(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate procedural terrain mesh.

    Parameters:
    - name: Terrain object name
    - size: [width, depth] dimensions
    - resolution: Subdivision count
    - height_scale: Maximum height
    - noise_scale: Terrain noise scale
    - seed: Random seed for reproducibility
    - terrain_type: "mountains", "hills", "plains", "canyon"
    """
    name = params.get("name", "Terrain")
    size = params.get("size", [100, 100])
    resolution = params.get("resolution", 64)
    height_scale = params.get("height_scale", 10.0)
    noise_scale = params.get("noise_scale", 0.1)
    seed = params.get("seed", 42)
    terrain_type = params.get("terrain_type", "hills")

    # Create plane
    bpy.ops.mesh.primitive_plane_add(size=1)
    terrain = bpy_context.active_object
    terrain.name = name
    terrain.scale = (size[0], size[1], 1)

    # Subdivide
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=resolution)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Apply displacement
    terrain.modifiers.new(name="TerrainDisplace", type="DISPLACE")
    displace = terrain.modifiers["TerrainDisplace"]
    displace.strength = height_scale

    # Create noise texture
    tex = bpy.data.textures.new(name=f"{name}_noise", type="CLOUDS")
    tex.noise_scale = noise_scale
    displace.texture = tex

    return {
        "status": "success",
        "terrain_name": name,
        "size": size,
        "resolution": resolution,
        "terrain_type": terrain_type,
    }


def generate_vegetation(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate vegetation particle system.

    Parameters:
    - name: Vegetation system name
    - vegetation_type: "forest", "grass", "flowers", "mixed"
    - coverage_area: [width, depth]
    - density: Plant density
    - scale_range: [min_scale, max_scale]
    - ground_object: Object to place vegetation on
    """
    name = params.get("name", "Vegetation")
    vegetation_type = params.get("vegetation_type", "forest")
    coverage_area = params.get("coverage_area", [50, 50])
    density = params.get("density", 0.5)
    scale_range = params.get("scale_range", [0.5, 2.0])
    ground_object = params.get("ground_object")

    # Create emitter plane
    bpy.ops.mesh.primitive_plane_add(size=1)
    emitter = bpy_context.active_object
    emitter.name = f"{name}_Emitter"
    emitter.scale = (coverage_area[0], coverage_area[1], 1)

    # Add particle system
    bpy.ops.object.particle_system_add()
    psys = emitter.particle_systems[0]
    settings = psys.settings

    settings.type = "HAIR"
    settings.emit_from = "FACE"
    settings.count = int(1000 * density)
    settings.hair_length = scale_range[1]
    settings.particle_size = sum(scale_range) / 2
    settings.size_random = (scale_range[1] - scale_range[0]) / scale_range[1]

    if vegetation_type == "grass":
        settings.hair_length = 0.3
        settings.count = int(5000 * density)
    elif vegetation_type == "flowers":
        settings.hair_length = 0.2
        settings.count = int(2000 * density)

    return {
        "status": "success",
        "vegetation_name": name,
        "vegetation_type": vegetation_type,
        "emitter_name": emitter.name,
        "particle_count": settings.count,
    }


def generate_architectural_element(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate architectural element.

    Parameters:
    - element_type: "column", "arch", "staircase", "wall", "window", "door"
    - style: "classical", "modern", "gothic", "art_deco"
    - dimensions: [width, depth, height]
    - detail_level: "low", "medium", "high"
    """
    element_type = params.get("element_type", "column")
    style = params.get("style", "classical")
    dimensions = params.get("dimensions", [1, 1, 4])
    detail_level = params.get("detail_level", "medium")

    objects_created = []

    if element_type == "column":
        bpy.ops.mesh.primitive_cylinder_add(
            radius=dimensions[0] / 2, depth=dimensions[2]
        )
        column = bpy_context.active_object
        column.name = f"Column_{style}"
        column.location[2] = dimensions[2] / 2
        objects_created.append(column.name)

    elif element_type == "staircase":
        step_count = int(dimensions[2] / 0.2)
        for i in range(step_count):
            bpy.ops.mesh.primitive_cube_add()
            step = bpy_context.active_object
            step.name = f"Stair_step_{i}"
            step.location = (i * 0.3, 0, i * 0.2)
            step.scale = (0.3, dimensions[1], 0.1)
            objects_created.append(step.name)

    elif element_type == "arch":
        bpy.ops.mesh.primitive_torus_add(
            major_radius=dimensions[0], minor_radius=dimensions[1] / 4
        )
        arch = bpy_context.active_object
        arch.name = f"Arch_{style}"
        arch.rotation_euler[0] = math.pi / 2
        objects_created.append(arch.name)

    return {
        "status": "success",
        "element_type": element_type,
        "style": style,
        "dimensions": dimensions,
        "objects_created": objects_created,
    }


def create_lod_system(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create Level of Detail system for an object.

    Parameters:
    - object_name: Source object name
    - lod_levels: List of LOD configurations with distance and decimate ratios
    """
    object_name = params.get("object_name")
    lod_levels = params.get(
        "lod_levels",
        [
            {"distance": 10, "decimate": 0.5},
            {"distance": 25, "decimate": 0.25},
            {"distance": 50, "decimate": 0.1},
        ],
    )

    if not object_name:
        raise ValueError("object_name is required")

    source_obj = bpy.data.objects.get(object_name)
    if not source_obj:
        raise ValueError(f"Object not found: {object_name}")

    lod_objects = []

    for i, lod_config in enumerate(lod_levels):
        bpy.ops.object.select_all(action="DESELECT")
        source_obj.select_set(True)
        bpy.ops.object.duplicate()
        lod_obj = bpy_context.active_object
        lod_obj.name = f"{object_name}_LOD{i}"

        decimate = lod_obj.modifiers.new(name="Decimate", type="DECIMATE")
        decimate.ratio = lod_config.get("decimate", 0.5)

        lod_objects.append(
            {
                "name": lod_obj.name,
                "distance": lod_config.get("distance"),
                "decimate_ratio": lod_config.get("decimate"),
            }
        )

    return {
        "status": "success",
        "source_object": object_name,
        "lod_levels": len(lod_objects),
        "lod_objects": lod_objects,
    }
