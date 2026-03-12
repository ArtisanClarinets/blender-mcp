"""
Scene composition handlers for Blender MCP addon.

Implements focused composition presets, scene cleanup, and render setup.
"""

import math
from typing import Any, Dict, List

import bpy


_BACKGROUND_COLORS = {
    "white": [1.0, 1.0, 1.0],
    "black": [0.02, 0.02, 0.02],
    "gradient": [0.82, 0.86, 0.92],
    "neutral": [0.5, 0.5, 0.5],
}
_SUPPORTED_BACKGROUNDS = set(_BACKGROUND_COLORS) | {"transparent"}
_PRODUCT_STYLES = {"clean", "lifestyle", "dramatic", "gradient"}
_CHARACTER_ENVIRONMENTS = {"studio", "outdoor", "night", "dramatic"}
_AUTOMOTIVE_ANGLES = {"front", "rear", "three_quarter", "side", "top"}
_AUTOMOTIVE_ENVIRONMENTS = {"studio", "outdoor", "motion"}
_FOOD_STYLES = {"flat_lay", "angled", "side"}
_JEWELRY_STYLES = {"macro", "editorial", "catalog"}
_STUDIO_MOODS = {"neutral", "dramatic", "bright", "moody"}


def _get_scene():
    scene = getattr(bpy.context, "scene", None)
    if scene is None:
        raise ValueError("No active scene available")
    return scene


def _normalize_vector(value: List[float], field_name: str) -> List[float]:
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(component) for component in value]


def _get_collection_for_linking(scene):
    collection = getattr(bpy.context, "collection", None)
    if collection is not None and getattr(collection, "objects", None) is not None:
        return collection

    scene_collection = getattr(scene, "collection", None)
    if (
        scene_collection is not None
        and getattr(scene_collection, "objects", None) is not None
    ):
        return scene_collection

    raise ValueError("No active collection available to link new camera")


def _ensure_camera_object(name: str):
    existing_object = bpy.data.objects.get(name)
    if existing_object is not None:
        if getattr(existing_object, "type", None) != "CAMERA":
            raise ValueError(f"Object exists and is not a camera: {name}")
        return existing_object

    camera_data = bpy.data.cameras.new(name=name)
    camera_object = bpy.data.objects.new(name=name, object_data=camera_data)
    scene = _get_scene()
    _get_collection_for_linking(scene).objects.link(camera_object)
    return camera_object


def _ensure_world(scene):
    world = getattr(scene, "world", None)
    if world is not None:
        return world

    worlds = getattr(getattr(bpy.data, "worlds", None), "new", None)
    if callable(worlds):
        scene.world = bpy.data.worlds.new(name="BlenderMCP World")
        return scene.world

    return None


def _set_world_background(scene, background: str) -> str:
    normalized_background = str(background or "white").lower()
    if normalized_background not in _SUPPORTED_BACKGROUNDS:
        raise ValueError(f"Unsupported product background: {normalized_background}")

    if normalized_background == "transparent":
        scene.render.film_transparent = True
        normalized_background = "white"
    else:
        scene.render.film_transparent = False

    world = _ensure_world(scene)
    color = _BACKGROUND_COLORS.get(normalized_background, _BACKGROUND_COLORS["neutral"])
    if world is not None and hasattr(world, "color"):
        world.color = list(color)

    return str(background or "white").lower()


def _activate_camera(scene, camera_object) -> None:
    scene.camera = camera_object


def _apply_camera(camera_object, location: List[float], rotation: List[float]) -> None:
    camera_object.location = _normalize_vector(location, "location")
    camera_object.rotation_euler = _normalize_vector(rotation, "rotation")


def _composition_result(
    preset: str, camera_object, extra: Dict[str, Any]
) -> Dict[str, Any]:
    result = {
        "status": "success",
        "preset": preset,
        "camera": camera_object.name,
        "camera_type": getattr(camera_object.data, "type", "PERSP"),
        "location": list(getattr(camera_object, "location", [0.0, 0.0, 0.0])),
    }
    result.update(extra)
    return result


def compose_product_shot(params: Dict[str, Any]) -> Dict[str, Any]:
    scene = _get_scene()
    product_name = str(params.get("product_name", "Product"))
    style = str(params.get("style", "clean")).lower()
    if style not in _PRODUCT_STYLES:
        raise ValueError(f"Unsupported product style: {style}")

    background = _set_world_background(scene, str(params.get("background", "white")))
    camera_object = _ensure_camera_object(f"{product_name} Camera")
    lens = 60.0 if style == "dramatic" else 85.0
    _apply_camera(camera_object, [0.0, -4.5, 2.1], [math.radians(68.0), 0.0, 0.0])
    camera_object.data.type = "PERSP"
    camera_object.data.lens = lens
    _activate_camera(scene, camera_object)
    return _composition_result(
        "product_shot",
        camera_object,
        {
            "product_name": product_name,
            "style": style,
            "background": background,
            "lens": lens,
        },
    )


def compose_isometric_scene(params: Dict[str, Any]) -> Dict[str, Any]:
    scene = _get_scene()
    grid_size = float(params.get("grid_size", 10.0))
    if grid_size <= 0.0:
        raise ValueError("grid_size must be greater than 0")

    camera_object = _ensure_camera_object("Isometric Camera")
    camera_object.data.type = "ORTHO"
    camera_object.data.ortho_scale = grid_size
    _apply_camera(
        camera_object,
        [grid_size, -grid_size, grid_size],
        [math.radians(35.264), 0.0, math.radians(45.0)],
    )
    _activate_camera(scene, camera_object)
    return _composition_result(
        "isometric",
        camera_object,
        {
            "grid_size": grid_size,
            "floor": bool(params.get("floor", True)),
            "shadow_catcher": bool(params.get("shadow_catcher", True)),
            "ortho_scale": camera_object.data.ortho_scale,
        },
    )


def compose_character_scene(params: Dict[str, Any]) -> Dict[str, Any]:
    scene = _get_scene()
    character_name = str(params.get("character_name", "Character"))
    environment = str(params.get("environment", "studio")).lower()
    if environment not in _CHARACTER_ENVIRONMENTS:
        raise ValueError(f"Unsupported character environment: {environment}")

    camera_object = _ensure_camera_object(f"{character_name} Camera")
    _apply_camera(camera_object, [0.0, -6.0, 2.4], [math.radians(74.0), 0.0, 0.0])
    camera_object.data.type = "PERSP"
    camera_object.data.lens = 70.0
    _activate_camera(scene, camera_object)
    return _composition_result(
        "character",
        camera_object,
        {
            "character_name": character_name,
            "ground_plane": bool(params.get("ground_plane", True)),
            "environment": environment,
            "lens": 70.0,
        },
    )


def compose_automotive_shot(params: Dict[str, Any]) -> Dict[str, Any]:
    scene = _get_scene()
    car_name = str(params.get("car_name", "Car"))
    angle = str(params.get("angle", "three_quarter")).lower()
    environment = str(params.get("environment", "studio")).lower()
    if angle not in _AUTOMOTIVE_ANGLES:
        raise ValueError(f"Unsupported automotive angle: {angle}")
    if environment not in _AUTOMOTIVE_ENVIRONMENTS:
        raise ValueError(f"Unsupported automotive environment: {environment}")

    location_map = {
        "front": [0.0, -9.0, 2.5],
        "rear": [0.0, 9.0, 2.5],
        "three_quarter": [6.0, -8.0, 3.0],
        "side": [8.5, 0.0, 2.6],
        "top": [0.0, -0.5, 11.0],
    }
    rotation_map = {
        "front": [math.radians(78.0), 0.0, 0.0],
        "rear": [math.radians(78.0), 0.0, math.radians(180.0)],
        "three_quarter": [math.radians(76.0), 0.0, math.radians(35.0)],
        "side": [math.radians(79.0), 0.0, math.radians(90.0)],
        "top": [math.radians(5.0), 0.0, 0.0],
    }
    camera_object = _ensure_camera_object(f"{car_name} Camera")
    _apply_camera(camera_object, location_map[angle], rotation_map[angle])
    camera_object.data.type = "PERSP"
    camera_object.data.lens = 50.0 if angle == "top" else 70.0
    _activate_camera(scene, camera_object)
    return _composition_result(
        "automotive",
        camera_object,
        {
            "car_name": car_name,
            "angle": angle,
            "environment": environment,
            "lens": camera_object.data.lens,
        },
    )


def compose_food_shot(params: Dict[str, Any]) -> Dict[str, Any]:
    scene = _get_scene()
    style = str(params.get("style", "flat_lay")).lower()
    if style not in _FOOD_STYLES:
        raise ValueError(f"Unsupported food style: {style}")

    camera_object = _ensure_camera_object("Food Camera")
    if style == "flat_lay":
        _apply_camera(camera_object, [0.0, 0.0, 6.5], [0.0, 0.0, 0.0])
        camera_object.data.lens = 55.0
    elif style == "angled":
        _apply_camera(camera_object, [0.0, -5.0, 3.2], [math.radians(66.0), 0.0, 0.0])
        camera_object.data.lens = 65.0
    else:
        _apply_camera(camera_object, [0.0, -4.8, 1.8], [math.radians(83.0), 0.0, 0.0])
        camera_object.data.lens = 80.0
    camera_object.data.type = "PERSP"
    _activate_camera(scene, camera_object)
    return _composition_result(
        "food",
        camera_object,
        {"style": style, "lens": camera_object.data.lens},
    )


def compose_jewelry_shot(params: Dict[str, Any]) -> Dict[str, Any]:
    scene = _get_scene()
    style = str(params.get("style", "macro")).lower()
    if style not in _JEWELRY_STYLES:
        raise ValueError(f"Unsupported jewelry style: {style}")

    camera_object = _ensure_camera_object("Jewelry Camera")
    _apply_camera(camera_object, [0.0, -2.5, 1.4], [math.radians(76.0), 0.0, 0.0])
    camera_object.data.type = "PERSP"
    camera_object.data.lens = 105.0
    _activate_camera(scene, camera_object)
    return _composition_result(
        "jewelry",
        camera_object,
        {
            "style": style,
            "reflections": bool(params.get("reflections", True)),
            "lens": 105.0,
        },
    )


def compose_architectural_shot(params: Dict[str, Any]) -> Dict[str, Any]:
    scene = _get_scene()
    interior = bool(params.get("interior", False))
    natural_light = bool(params.get("natural_light", True))

    camera_object = _ensure_camera_object("Architectural Camera")
    if interior:
        _apply_camera(camera_object, [0.0, -5.0, 1.7], [math.radians(85.0), 0.0, 0.0])
        camera_object.data.lens = 24.0
    else:
        _apply_camera(
            camera_object,
            [7.5, -9.0, 4.5],
            [math.radians(68.0), 0.0, math.radians(35.0)],
        )
        camera_object.data.lens = 35.0
    camera_object.data.type = "PERSP"
    _activate_camera(scene, camera_object)
    return _composition_result(
        "architectural",
        camera_object,
        {
            "interior": interior,
            "natural_light": natural_light,
            "lens": camera_object.data.lens,
        },
    )


def compose_studio_setup(params: Dict[str, Any]) -> Dict[str, Any]:
    scene = _get_scene()
    subject_type = str(params.get("subject_type", "generic"))
    mood = str(params.get("mood", "neutral")).lower()
    if mood not in _STUDIO_MOODS:
        raise ValueError(f"Unsupported studio mood: {mood}")

    camera_object = _ensure_camera_object(f"{subject_type.title()} Studio Camera")
    mood_offsets = {
        "neutral": ([0.0, -5.5, 2.2], [math.radians(72.0), 0.0, 0.0]),
        "dramatic": ([1.2, -6.5, 2.8], [math.radians(68.0), 0.0, math.radians(8.0)]),
        "bright": ([0.0, -4.8, 2.0], [math.radians(74.0), 0.0, 0.0]),
        "moody": ([-1.0, -6.2, 2.4], [math.radians(69.0), 0.0, math.radians(-8.0)]),
    }
    location, rotation = mood_offsets[mood]
    _apply_camera(camera_object, location, rotation)
    camera_object.data.type = "PERSP"
    camera_object.data.lens = 80.0
    _activate_camera(scene, camera_object)
    return _composition_result(
        "studio",
        camera_object,
        {"subject_type": subject_type, "mood": mood, "lens": 80.0},
    )


def _remove_from_scene_lists(scene, obj) -> None:
    scene_objects = getattr(scene, "objects", None)
    if isinstance(scene_objects, list) and obj in scene_objects:
        scene_objects.remove(obj)

    collection_objects = getattr(getattr(scene, "collection", None), "objects", None)
    linked = getattr(collection_objects, "linked", None)
    if isinstance(linked, list) and obj in linked:
        linked.remove(obj)


def clear_scene(params: Dict[str, Any]) -> Dict[str, Any]:
    scene = _get_scene()
    keep_camera = bool(params.get("keep_camera", False))
    keep_lights = bool(params.get("keep_lights", False))

    removed_names = []
    kept_names = []
    for obj in list(getattr(scene, "objects", [])):
        object_type = getattr(obj, "type", None)
        if keep_camera and object_type == "CAMERA":
            kept_names.append(obj.name)
            continue
        if keep_lights and object_type == "LIGHT":
            kept_names.append(obj.name)
            continue

        removed_names.append(obj.name)
        _remove_from_scene_lists(scene, obj)
        bpy.data.objects.remove(obj, do_unlink=True)

    if not keep_camera and getattr(scene, "camera", None) is not None:
        scene.camera = None

    return {
        "status": "success",
        "removed": removed_names,
        "removed_count": len(removed_names),
        "kept": kept_names,
    }


def setup_render_settings(params: Dict[str, Any]) -> Dict[str, Any]:
    scene = _get_scene()
    render = getattr(scene, "render", None)
    if render is None:
        raise ValueError("Scene render settings are unavailable")

    engine_input = str(params.get("engine", "CYCLES")).upper()
    engine_map = {
        "CYCLES": "CYCLES",
        "EEVEE": "BLENDER_EEVEE",
        "BLENDER_EEVEE": "BLENDER_EEVEE",
        "BLENDER_EEVEE_NEXT": "BLENDER_EEVEE_NEXT",
    }
    if engine_input not in engine_map:
        raise ValueError(f"Unsupported render engine: {engine_input}")

    samples = int(params.get("samples", 128))
    resolution_x = int(params.get("resolution_x", 1920))
    resolution_y = int(params.get("resolution_y", 1080))
    if samples <= 0:
        raise ValueError("samples must be greater than 0")
    if resolution_x <= 0 or resolution_y <= 0:
        raise ValueError("resolution_x and resolution_y must be greater than 0")

    normalized_engine = engine_map[engine_input]
    render.engine = normalized_engine
    render.resolution_x = resolution_x
    render.resolution_y = resolution_y
    denoise = bool(params.get("denoise", True))

    if normalized_engine == "CYCLES":
        cycles = getattr(scene, "cycles", None)
        if cycles is not None:
            cycles.samples = samples
            if hasattr(cycles, "use_denoising"):
                cycles.use_denoising = denoise
    else:
        eevee = getattr(scene, "eevee", None)
        if eevee is not None and hasattr(eevee, "taa_render_samples"):
            eevee.taa_render_samples = samples

    return {
        "status": "success",
        "engine": "EEVEE"
        if normalized_engine.startswith("BLENDER_EEVEE")
        else normalized_engine,
        "samples": samples,
        "resolution_x": resolution_x,
        "resolution_y": resolution_y,
        "denoise": denoise,
    }
