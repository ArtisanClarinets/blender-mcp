"""
Scene observation handlers

Implements scene inspection and observation commands.
"""

import bpy
import hashlib
import json
from typing import Any, Dict, List

from .. import id
from .. import utils


def observe_scene(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Observe the current scene with configurable detail.

    Args:
        params: Parameters including detail level and screenshot option

    Returns:
        Scene observation data
    """
    detail = params.get("detail", "med")
    include_screenshot = params.get("include_screenshot", False)
    max_screenshot_size = params.get("max_screenshot_size", 800)

    result = {
        "scene_hash": get_scene_hash(),
        "objects": [],
        "collections": [],
        "cameras": [],
        "lights": [],
        "world": {},
        "render_settings": {},
        "bounds": utils.get_scene_bounds(),
    }

    # Get objects based on detail level
    if detail == "low":
        result["objects"] = [
            {"name": obj.name, "type": obj.type} for obj in bpy.data.objects
        ]
    elif detail == "med":
        result["objects"] = [
            id.get_object_info_with_uuid(obj) for obj in bpy.data.objects
        ]
    else:  # high
        result["objects"] = [get_detailed_object_info(obj) for obj in bpy.data.objects]

    # Get collections
    result["collections"] = [
        {"name": col.name, "objects": [obj.name for obj in col.objects]}
        for col in bpy.data.collections
    ]

    # Get cameras
    result["cameras"] = [
        {
            "name": cam.name,
            "location": list(cam.location),
            "rotation": list(cam.rotation_euler),
            "lens": cam.data.lens if cam.data else 50,
        }
        for cam in bpy.data.objects
        if cam.type == "CAMERA"
    ]

    # Get lights
    result["lights"] = [
        {
            "name": light.name,
            "type": light.data.type if light.data else "POINT",
            "energy": light.data.energy if light.data else 0,
            "color": list(light.data.color) if light.data else [1, 1, 1],
            "location": list(light.location),
        }
        for light in bpy.data.objects
        if light.type == "LIGHT"
    ]

    # Get world settings
    if bpy.context.scene.world:
        world = bpy.context.scene.world
        result["world"] = {
            "name": world.name,
            "use_nodes": world.use_nodes,
            "color": list(world.color) if not world.use_nodes else None,
        }

    # Get render settings
    render = bpy.context.scene.render
    result["render_settings"] = {
        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "resolution_percentage": render.resolution_percentage,
        "engine": render.engine,
    }

    # Capture screenshot if requested
    if include_screenshot:
        result["screenshot"] = capture_viewport_screenshot(max_screenshot_size)

    return result


def get_scene_hash() -> str:
    """
    Compute a stable hash of the scene state.

    Returns:
        Hash string
    """
    data = {
        "objects": [
            {
                "name": obj.name,
                "type": obj.type,
                "location": [round(x, 4) for x in obj.location],
                "rotation": [round(x, 4) for x in obj.rotation_euler],
                "scale": [round(x, 4) for x in obj.scale],
                "materials": [mat.name for mat in obj.data.materials]
                if hasattr(obj.data, "materials")
                else [],
            }
            for obj in sorted(bpy.data.objects, key=lambda x: x.name)
        ]
    }
    return utils.compute_hash(data)


def get_scene_info() -> Dict[str, Any]:
    """
    Get detailed scene information.

    Returns:
        Scene information dictionary
    """
    return {
        "name": bpy.context.scene.name,
        "frame_start": bpy.context.scene.frame_start,
        "frame_end": bpy.context.scene.frame_end,
        "frame_current": bpy.context.scene.frame_current,
        "objects_count": len(bpy.data.objects),
        "objects": [id.get_object_info_with_uuid(obj) for obj in bpy.data.objects],
        "collections": [col.name for col in bpy.data.collections],
        "active_object": bpy.context.active_object.name
        if bpy.context.active_object
        else None,
    }


def get_object_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get detailed information about a specific object.

    Args:
        params: Parameters including object_name

    Returns:
        Object information dictionary
    """
    object_name = params.get("object_name")
    if not object_name:
        raise ValueError("object_name is required")

    obj = id.resolve_id(object_name)
    if not obj:
        raise ValueError(f"Object not found: {object_name}")

    return get_detailed_object_info(obj)


def get_detailed_object_info(obj: bpy.types.Object) -> Dict[str, Any]:
    """
    Get detailed information about an object.

    Args:
        obj: Blender object

    Returns:
        Detailed object information
    """
    info = id.get_object_info_with_uuid(obj)

    # Add type-specific info
    if obj.type == "MESH":
        mesh = obj.data
        info["mesh"] = {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
            "materials": [mat.name for mat in mesh.materials],
        }
    elif obj.type == "CAMERA":
        info["camera"] = {
            "lens": obj.data.lens,
            "sensor_width": obj.data.sensor_width,
            "sensor_height": obj.data.sensor_height,
        }
    elif obj.type == "LIGHT":
        info["light"] = {
            "type": obj.data.type,
            "energy": obj.data.energy,
            "color": list(obj.data.color),
        }

    # Add modifiers
    info["modifiers"] = [{"name": mod.name, "type": mod.type} for mod in obj.modifiers]

    # Add constraints
    info["constraints"] = [
        {"name": con.name, "type": con.type} for con in obj.constraints
    ]

    # Add parent info
    if obj.parent:
        info["parent"] = obj.parent.name

    # Add collection membership
    info["collections"] = [
        col.name for col in bpy.data.collections if obj.name in col.objects
    ]

    return info


def get_viewport_screenshot(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capture a screenshot of the viewport.

    Args:
        params: Parameters including max_size

    Returns:
        Screenshot information
    """
    max_size = params.get("max_size", 800)
    return capture_viewport_screenshot(max_size)


def capture_viewport_screenshot(max_size: int = 800) -> Dict[str, Any]:
    """
    Capture the current viewport as an image.

    Args:
        max_size: Maximum dimension

    Returns:
        Screenshot information with base64 data
    """
    import tempfile
    import base64
    from pathlib import Path

    # Create temporary file
    temp_path = Path(tempfile.gettempdir()) / "blender_mcp_screenshot.png"

    # Set up render settings
    scene = bpy.context.scene
    original_filepath = scene.render.filepath
    original_format = scene.render.image_settings.file_format

    try:
        scene.render.filepath = str(temp_path)
        scene.render.image_settings.file_format = "PNG"

        # Render viewport
        bpy.ops.render.opengl(write_still=True)

        # Read and encode image
        with open(temp_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        return {"format": "png", "data": image_data, "path": str(temp_path)}

    finally:
        scene.render.filepath = original_filepath
        scene.render.image_settings.file_format = original_format

        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


def get_selection() -> Dict[str, Any]:
    """
    Get information about selected objects.

    Returns:
        Selection information
    """
    selected = bpy.context.selected_objects
    active = bpy.context.active_object

    return {
        "count": len(selected),
        "selected": [id.get_object_info_with_uuid(obj) for obj in selected],
        "active": id.get_object_info_with_uuid(active) if active else None,
    }
