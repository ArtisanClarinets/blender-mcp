"""Camera handlers for Blender MCP addon.

Implements focused camera creation, presets, and framing operations.
"""

import math
from typing import Any, Dict, List, Optional

import bpy
import structlog

from ...exceptions import BlenderMCPError

try:
    import mathutils
except ImportError:
    mathutils = None

logger = structlog.get_logger(__name__)

_COMPOSITION_OFFSETS: Dict[str, List[float]] = {
    "center": [0.0, 0.0, 0.0],
    "rule_of_thirds": [0.33, 0.0, 0.2],
    "golden_ratio": [0.38, 0.0, 0.24],
    "diagonal": [0.45, 0.0, 0.45],
    "frame": [0.6, 0.0, 0.0],
}

_CAMERA_PRESETS: Dict[str, Dict[str, float]] = {
    "portrait": {"lens": 85.0, "aperture": 2.8},
    "landscape": {"lens": 35.0, "aperture": 11.0},
    "macro": {"lens": 100.0, "aperture": 16.0},
    "cinematic": {"lens": 50.0, "aperture": 2.0},
    "action": {"lens": 24.0, "aperture": 5.6},
    "telephoto": {"lens": 135.0, "aperture": 4.0},
    "product": {"lens": 50.0, "aperture": 8.0},
}

def _normalize_vector(value: List[float], field_name: str) -> List[float]:
    """Normalize a vector to a list of 3 floats."""
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(component) for component in value]

def _get_active_scene_objects() -> Any:
    """Get the objects in the active scene."""
    scene = getattr(bpy.context, "scene", None)
    if scene is None:
        raise BlenderMCPError("No active scene")
    scene_objects = getattr(scene, "objects", None)
    if scene_objects is not None:
        return scene_objects

    collection = getattr(scene, "collection", None)
    if collection is None:
        raise BlenderMCPError("No active collection in scene")
    collection_objects = getattr(collection, "objects", None)
    if collection_objects is not None:
        return collection_objects

    return []

def _get_collection_for_linking() -> Any:
    """Get the collection to link new objects to."""
    collection = getattr(bpy.context, "collection", None)
    if collection is not None and getattr(collection, "objects", None) is not None:
        return collection

    scene = getattr(bpy.context, "scene", None)
    if scene is None:
        raise BlenderMCPError("No active scene")
    scene_collection = getattr(scene, "collection", None)
    if (
        scene_collection is not None
        and getattr(scene_collection, "objects", None) is not None
    ):
        return scene_collection

    raise BlenderMCPError("No active collection available to link new camera")

def _ensure_camera_object(name: str) -> Any:
    """Ensure a camera object with the given name exists."""
    existing_object = bpy.data.objects.get(name)
    if existing_object is not None:
        if getattr(existing_object, "type", None) != "CAMERA":
            raise BlenderMCPError(f"Object exists and is not a camera: {name}")
        return existing_object

    camera_data = bpy.data.cameras.new(name=name)
    camera_object = bpy.data.objects.new(name=name, object_data=camera_data)
    _get_collection_for_linking().objects.link(camera_object)
    return camera_object

def _get_camera_object(camer-name: str) -> Any:
    """Get a camera object by name."""
    camera_object = bpy.data.objects.get(camer-name)
    if camera_object is None or getattr(camera_object, "type", None) != "CAMERA":
        raise BlenderMCPError(f"Camera not found: {camer-name}")
    return camera_object

def _look_at_rotation(location: List[float], target: List[float]) -> List[float]:
    """Calculate the rotation to look at a target."""
    if mathutils is not None:
        direction = mathutils.Vector(target) - mathutils.Vector(location)
        return list(direction.to_track_quat("-Z", "Y").to_euler())

    dx = target[0] - location[0]
    dy = target[1] - location[1]
    dz = target[2] - location[2]
    horizontal_distance = math.sqrt((dx * dx) + (dy * dy))
    pitch = math.atan2(dz, max(horizontal_distance, 1e-6))
    yaw = math.atan2(dx, -dy)
    return [pitch, 0.0, yaw]

def _set_camera_look_at(camera_object: Any, target: List[float]) -> None:
    """Set the camera to look at a target."""
    camera_object.rotation_euler = _look_at_rotation(
        list(camera_object.location),
        target,
    )

def _get_selected_scene_objects() -> List[Any]:
    """Get the selected objects in the scene."""
    selected_objects = getattr(bpy.context, "selected_objects", None)
    if selected_objects is not None:
        return list(selected_objects)

    scene_objects = []
    for obj in _get_active_scene_objects():
        select_get = getattr(obj, "select_get", None)
        if callable(select_get):
            if select_get():
                scene_objects.append(obj)
            continue
        if getattr(obj, "selected", False):
            scene_objects.append(obj)
    return scene_objects

def _coerce_dimensions(obj: Any) -> List[float]:
    """Coerce an object's dimensions to a list of floats."""
    dimensions = getattr(obj, "dimensions", None)
    if dimensions is None:
        return [0.0, 0.0, 0.0]
    return [float(component) for component in dimensions]

def _coerce_point3(value: Any) -> Optional[List[float]]:
    """Coerce a value to a 3D point."""
    try:
        components = list(value)
    except TypeError:
        return None

    if len(components) < 3:
        return None

    return [float(components[index]) for index in range(3)]

def _transform_bound_box_corner(
    matrix_world: Any, corner: List[float]
) -> Optional[List[float]]:
    """Transform a bounding box corner."""
    if matrix_world is None:
        return None

    candidates: List[Any] = [corner, tuple(corner)]
    if mathutils is not None:
        candidates.insert(0, mathutils.Vector(corner))

    for candidate in candidates:
        try:
            transformed = matrix_world @ candidate
        except Exception:
            continue

        point = _coerce_point3(transformed)
        if point is not None:
            return point

    transform_point = getattr(matrix_world, "transform_point", None)
    if callable(transform_point):
        point = _coerce_point3(transform_point(corner))
        if point is not None:
            return point

    return None

def _object_bounds(obj: Any) -> Optional[Dict[str, List[float]]]:
    """Get the bounds of an object."""
    bound_box = getattr(obj, "bound_box", None)
    if bound_box is None:
        return None

    world_points = []
    for corner in bound_box:
        point = _coerce_point3(corner)
        if point is None:
            return None

        transformed = _transform_bound_box_corner(
            getattr(obj, "matrix_world", None), point
        )
        if transformed is None:
            return None
        world_points.append(transformed)

    if not world_points:
        return None

    min_corner = [min(point[index] for point in world_points) for index in range(3)]
    max_corner = [max(point[index] for point in world_points) for index in range(3)]
    center = [(min_corner[index] + max_corner[index]) / 2.0 for index in range(3)]
    size = [max_corner[index] - min_corner[index] for index in range(3)]
    return {"center": center, "size": size}

def _selection_bounds(selected_objects: List[Any]) -> Dict[str, List[float]]:
    """Get the bounds of the selection."""
    if not selected_objects:
        raise BlenderMCPError("No selected objects to frame")

    min_corner = [float("inf"), float("inf"), float("inf")]
    max_corner = [float("-inf"), float("-inf"), float("-inf")]

    for obj in selected_objects:
        object_bounds = _object_bounds(obj)
        if object_bounds is not None:
            center = object_bounds["center"]
            half_size = [component / 2.0 for component in object_bounds["size"]]
        else:
            center = _normalize_vector(
                list(getattr(obj, "location", [0.0, 0.0, 0.0])), "location"
            )
            half_size = [dimension / 2.0 for dimension in _coerce_dimensions(obj)]

        for index in range(3):
            min_corner[index] = min(min_corner[index], center[index] - half_size[index])
            max_corner[index] = max(max_corner[index], center[index] + half_size[index])

    center = [(min_corner[index] + max_corner[index]) / 2.0 for index in range(3)]
    size = [max_corner[index] - min_corner[index] for index in range(3)]
    return {"center": center, "size": size}

def _describe_camera(camera_object: Any) -> Dict[str, Any]:
    """Describe a camera object."""
    camera_data = getattr(camera_object, "data", None)
    active_camera = getattr(getattr(bpy.context, "scene", None), "camera", None)
    dof_settings = getattr(camera_data, "dof", None)
    return {
        "name": camera_object.name,
        "type": getattr(camera_data, "type", "PERSP"),
        "lens": float(getattr(camera_data, "lens", 50.0)),
        "location": list(getattr(camera_object, "location", [0.0, 0.0, 0.0])),
        "rotation": list(getattr(camera_object, "rotation_euler", [0.0, 0.0, 0.0])),
        "is_active": active_camera is camera_object,
        "focus_distance": float(getattr(dof_settings, "focus_distance", 0.0)),
    }

def create_composition_camera(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace a camera tuned for a composition pattern."""
    name = str(params.get("name", "Camera"))
    composition = str(params.get("composition", "center")).lower()
    focal_length = float(params.get("focal_length", 50.0))
    if composition not in _COMPOSITION_OFFSETS:
        raise BlenderMCPError(f"Unsupported composition: {composition}")

    location = _normalize_vector(params.get("location", [0.0, -6.0, 3.0]), "location")
    target = _normalize_vector(params.get("target", [0.0, 0.0, 1.0]), "target")
    offset = _COMPOSITION_OFFSETS[composition]
    framed_target = [target[index] + offset[index] for index in range(3)]

    camera_object = _ensure_camera_object(name)
    camera_object.location = location
    camera_object.data.type = "PERSP"
    camera_object.data.lens = focal_length
    _set_camera_look_at(camera_object, framed_target)

    logger.info("Created composition camera", name=name, composition=composition)
    return {
        "status": "success",
        "name": camera_object.name,
        "composition": composition,
        "lens": camera_object.data.lens,
    }

def create_isometric_camera(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace an isometric orthographic camera."""
    name = str(params.get("name", "Isometric"))
    ortho_scale = float(params.get("ortho_scale", 10.0))
    angle = float(params.get("angle", 35.264))

    camera_object = _ensure_camera_object(name)
    camera_object.data.type = "ORTHO"
    camera_object.data.ortho_scale = ortho_scale
    camera_object.location = [10.0, -10.0, 10.0]
    camera_object.rotation_euler = [math.radians(angle), 0.0, math.radians(45.0)]

    logger.info("Created isometric camera", name=name)
    return {
        "status": "success",
        "name": camera_object.name,
        "type": "orthographic",
        "ortho_scale": camera_object.data.ortho_scale,
        "angle": angle,
    }

def set_camera_depth_of_field(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply depth-of-field settings to a camera."""
    camer-name = params.get("camer-name")
    if not camer-name:
        raise BlenderMCPError("camer-name is required")

    camera_object = _get_camera_object(str(camer-name))
    aperture = float(params.get("aperture", 5.6))
    focus_distance = float(params.get("focus_distance", 10.0))
    focal_length = params.get("focal_length")

    camera_object.data.dof.use_dof = True
    camera_object.data.dof.focus_distance = focus_distance
    camera_object.data.dof.aperture_fstop = aperture
    if focal_length is not None:
        camera_object.data.lens = float(focal_length)

    logger.info("Set camera depth of field", camer-name=camer-name)
    return {
        "status": "success",
        "camera": camera_object.name,
        "focus_distance": camera_object.data.dof.focus_distance,
        "aperture": camera_object.data.dof.aperture_fstop,
        "lens": camera_object.data.lens,
    }

def apply_camera_preset(params: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a named camera preset."""
    camer-name = params.get("camer-name")
    preset = str(params.get("preset", "")).lower()
    if not camer-name:
        raise BlenderMCPError("camer-name is required")
    if not preset:
        raise BlenderMCPError("preset is required")

    preset_settings = _CAMERA_PRESETS.get(preset)
    if preset_settings is None:
        raise BlenderMCPError(f"Unsupported camera preset: {preset}")

    camera_object = _get_camera_object(str(camer-name))
    camera_object.data.lens = float(preset_settings["lens"])
    camera_object.data.dof.use_dof = True
    camera_object.data.dof.aperture_fstop = float(preset_settings["aperture"])

    logger.info("Applied camera preset", camer-name=camer-name, preset=preset)
    return {
        "status": "success",
        "camera": camera_object.name,
        "preset": preset,
        "lens": camera_object.data.lens,
        "aperture": camera_object.data.dof.aperture_fstop,
    }

def set_active_camera(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set the active scene camera."""
    camer-name = params.get("camer-name")
    if not camer-name:
        raise BlenderMCPError("camer-name is required")

    camera_object = _get_camera_object(str(camer-name))
    bpy.context.scene.camera = camera_object
    logger.info("Set active camera", camer-name=camer-name)
    return {"status": "success", "active_camera": camera_object.name}

def list_cameras() -> Dict[str, Any]:
    """List cameras in the active scene."""
    cameras = [
        _describe_camera(obj)
        for obj in _get_active_scene_objects()
        if getattr(obj, "type", None) == "CAMERA"
    ]
    active_camera = getattr(getattr(bpy.context, "scene", None), "camera", None)
    return {
        "cameras": cameras,
        "count": len(cameras),
        "active_camera": getattr(active_camera, "name", None),
    }

def frame_camera_to_selection(params: Dict[str, Any]) -> Dict[str, Any]:
    """Move the camera to frame the current selection."""
    camer-name = params.get("camer-name")
    if not camer-name:
        raise BlenderMCPError("camer-name is required")

    camera_object = _get_camera_object(str(camer-name))
    margin = float(params.get("margin", 1.1))
    if margin <= 0.0:
        raise ValueError("margin must be greater than 0")

    bounds = _selection_bounds(_get_selected_scene_objects())
    center = bounds["center"]
    max_dimension = max(max(bounds["size"]), 0.5)
    framing_distance = max_dimension * margin * 2.0
    camera_object.location = [
        center[0],
        center[1] - framing_distance,
        center[2] + (framing_distance * 0.5),
    ]
    _set_camera_look_at(camera_object, center)
    if getattr(camera_object.data, "type", "PERSP") == "ORTHO":
        camera_object.data.ortho_scale = max_dimension * margin

    logger.info("Framed camera to selection", camer-name=camer-name)
    return {
        "status": "success",
        "camera": camera_object.name,
        "center": center,
        "size": bounds["size"],
        "margin": margin,
    }