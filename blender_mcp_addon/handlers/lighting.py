"""
Lighting handlers for Blender MCP addon.

Implements focused lighting presets, environment setup, and light management.
"""

import math
from typing import Any, Dict, List, Optional

import bpy


_AREA_LIGHT_SHAPES = {"RECTANGLE", "SQUARE", "CIRCLE", "DISC"}
_STUDIO_PRESET_SPECS = {
    "butterfly": [
        {
            "name": "Butterfly Key",
            "energy_multiplier": 1.8,
            "location": [0.0, -3.5, 4.5],
            "rotation": [0.95, 0.0, 0.0],
            "size": 2.4,
            "color": [1.0, 0.97, 0.92],
        },
        {
            "name": "Butterfly Fill",
            "energy_multiplier": 0.8,
            "location": [0.0, -1.5, 1.5],
            "rotation": [1.2, 0.0, 0.0],
            "size": 2.8,
            "color": [0.95, 0.97, 1.0],
        },
    ],
    "cinematic": [
        {
            "name": "Cinematic Key",
            "energy_multiplier": 1.7,
            "location": [4.0, -4.5, 4.0],
            "rotation": [0.9, 0.0, 0.8],
            "size": 2.8,
            "color": [1.0, 0.9, 0.78],
        },
        {
            "name": "Cinematic Rim",
            "energy_multiplier": 1.1,
            "location": [-3.5, 3.5, 4.5],
            "rotation": [0.7, 0.0, -2.3],
            "size": 2.2,
            "color": [0.7, 0.82, 1.0],
        },
    ],
    "high_key": [
        {
            "name": "High Key Main",
            "energy_multiplier": 1.6,
            "location": [3.5, -3.0, 4.0],
            "rotation": [0.8, 0.0, 0.7],
            "size": 3.0,
            "color": [1.0, 1.0, 1.0],
        },
        {
            "name": "High Key Fill",
            "energy_multiplier": 1.2,
            "location": [-3.5, -2.5, 3.2],
            "rotation": [0.85, 0.0, -0.8],
            "size": 3.2,
            "color": [1.0, 1.0, 1.0],
        },
        {
            "name": "High Key Background",
            "energy_multiplier": 0.9,
            "location": [0.0, 4.5, 2.5],
            "rotation": [1.55, 0.0, 3.14],
            "size": 4.0,
            "color": [1.0, 1.0, 1.0],
        },
    ],
    "loop": [
        {
            "name": "Loop Key",
            "energy_multiplier": 1.6,
            "location": [2.5, -4.0, 4.0],
            "rotation": [0.9, 0.0, 0.55],
            "size": 2.6,
            "color": [1.0, 0.96, 0.9],
        },
        {
            "name": "Loop Fill",
            "energy_multiplier": 0.7,
            "location": [-2.0, -3.0, 2.5],
            "rotation": [1.0, 0.0, -0.6],
            "size": 2.4,
            "color": [0.92, 0.96, 1.0],
        },
    ],
    "low_key": [
        {
            "name": "Low Key Main",
            "energy_multiplier": 1.5,
            "location": [4.0, -4.5, 4.2],
            "rotation": [0.95, 0.0, 0.85],
            "size": 2.5,
            "color": [1.0, 0.92, 0.82],
        },
        {
            "name": "Low Key Rim",
            "energy_multiplier": 0.9,
            "location": [-2.5, 4.0, 4.5],
            "rotation": [0.75, 0.0, -2.4],
            "size": 1.8,
            "color": [0.72, 0.82, 1.0],
        },
    ],
    "portrait": [
        {
            "name": "Portrait Key",
            "energy_multiplier": 1.7,
            "location": [3.0, -3.8, 4.0],
            "rotation": [0.88, 0.0, 0.68],
            "size": 2.7,
            "color": [1.0, 0.95, 0.88],
        },
        {
            "name": "Portrait Fill",
            "energy_multiplier": 0.8,
            "location": [-2.5, -3.0, 2.8],
            "rotation": [0.95, 0.0, -0.72],
            "size": 2.8,
            "color": [0.92, 0.96, 1.0],
        },
        {
            "name": "Portrait Hair",
            "energy_multiplier": 0.95,
            "location": [-1.0, 3.6, 4.8],
            "rotation": [0.7, 0.0, -2.9],
            "size": 1.8,
            "color": [1.0, 0.95, 0.85],
        },
    ],
    "product": [
        {
            "name": "Product Key",
            "energy_multiplier": 1.5,
            "location": [3.5, -3.5, 3.5],
            "rotation": [0.85, 0.0, 0.75],
            "size": 3.0,
            "color": [1.0, 1.0, 1.0],
        },
        {
            "name": "Product Fill",
            "energy_multiplier": 1.1,
            "location": [-3.0, -2.8, 3.2],
            "rotation": [0.9, 0.0, -0.78],
            "size": 3.2,
            "color": [1.0, 1.0, 1.0],
        },
        {
            "name": "Product Rim",
            "energy_multiplier": 0.9,
            "location": [0.0, 4.0, 3.8],
            "rotation": [0.75, 0.0, 3.14],
            "size": 2.4,
            "color": [1.0, 1.0, 1.0],
        },
    ],
    "rim": [
        {
            "name": "Rim Light",
            "energy_multiplier": 1.2,
            "location": [0.0, 4.0, 4.8],
            "rotation": [0.7, 0.0, 3.14],
            "size": 2.0,
            "color": [1.0, 0.96, 0.88],
        },
        {
            "name": "Rim Fill",
            "energy_multiplier": 0.7,
            "location": [0.0, -3.0, 2.4],
            "rotation": [1.1, 0.0, 0.0],
            "size": 2.4,
            "color": [0.88, 0.93, 1.0],
        },
    ],
    "split": [
        {
            "name": "Split Key",
            "energy_multiplier": 1.4,
            "location": [4.0, 0.0, 3.5],
            "rotation": [0.9, 0.0, 1.57],
            "size": 2.3,
            "color": [1.0, 0.94, 0.86],
        }
    ],
    "three_point": [],
}


def _hdri_placeholder_color(hdri_name: Optional[str], blur: float) -> List[float]:
    normalized_name = str(hdri_name or "default")
    name_seed = sum(
        (index + 1) * ord(char) for index, char in enumerate(normalized_name)
    )
    blur_mix = max(0.0, min(1.0, float(blur)))
    base_color = [0.25 + ((name_seed >> shift) & 31) / 31 * 0.5 for shift in (0, 5, 10)]
    softened_color = [
        round((channel * (1.0 - blur_mix)) + (0.5 * blur_mix), 4)
        for channel in base_color
    ]
    return softened_color + [1.0]


def _normalize_color(value: List[float], field_name: str) -> List[float]:
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(channel) for channel in value]


def _resolve_optional_color(
    value: Optional[List[float]], default_color: List[float], field_name: str
) -> List[float]:
    if value is None:
        return list(default_color)
    return _normalize_color(value, field_name)


def _normalize_vector(value: List[float], field_name: str) -> List[float]:
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(component) for component in value]


def _get_or_create_world() -> bpy.types.World:
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    return world


def _get_active_scene_objects():
    scene = getattr(bpy.context, "scene", None)
    scene_objects = getattr(scene, "objects", None)
    if scene_objects is not None:
        return scene_objects

    collection = getattr(scene, "collection", None)
    collection_objects = getattr(collection, "objects", None)
    if collection_objects is not None:
        return collection_objects

    return []


def _get_collection_for_linking():
    collection = getattr(bpy.context, "collection", None)
    if collection is not None and getattr(collection, "objects", None) is not None:
        return collection

    scene_collection = getattr(getattr(bpy.context, "scene", None), "collection", None)
    if (
        scene_collection is not None
        and getattr(scene_collection, "objects", None) is not None
    ):
        return scene_collection

    raise ValueError("No active collection available to link new light")


def _ensure_light_object(name: str, light_data_type: str = "AREA"):
    existing_object = bpy.data.objects.get(name)
    if existing_object is not None:
        if getattr(existing_object, "type", None) != "LIGHT":
            raise ValueError(f"Object exists and is not a light: {name}")
        existing_object.data.type = light_data_type
        return existing_object

    light_data = bpy.data.lights.new(name=name, type=light_data_type)
    light_object = bpy.data.objects.new(name=name, object_data=light_data)
    _get_collection_for_linking().objects.link(light_object)
    return light_object


def _configure_area_shape(
    light_data, light_shape: str, size: float, size_y: Optional[float]
):
    normalized_shape = str(light_shape).upper()
    if normalized_shape not in _AREA_LIGHT_SHAPES:
        raise ValueError(f"Unsupported area light shape: {light_shape}")

    light_data.shape = normalized_shape
    light_data.size = float(size)
    if normalized_shape == "RECTANGLE":
        light_data.size_y = float(size if size_y is None else size_y)

    return normalized_shape


def _describe_light(light_object) -> Dict[str, Any]:
    light_data = getattr(light_object, "data", None)
    return {
        "name": light_object.name,
        "type": getattr(light_data, "type", "UNKNOWN"),
        "energy": float(getattr(light_data, "energy", 0.0)),
        "color": list(getattr(light_data, "color", [1.0, 1.0, 1.0])),
        "location": list(getattr(light_object, "location", [0.0, 0.0, 0.0])),
        "rotation": list(getattr(light_object, "rotation_euler", [0.0, 0.0, 0.0])),
    }


def _find_node(nodes, node_idname: str):
    for node in nodes:
        if getattr(node, "bl_idname", None) == node_idname:
            return node
        if getattr(node, "type", None) == node_idname:
            return node
    return None


def _build_three_point_specs(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "name": "Three Point Key",
            "light_type": "RECTANGLE",
            "size": 2.8,
            "energy": float(params.get("key_intensity", 1000.0)),
            "location": [4.0, -4.0, 5.0],
            "rotation": [0.85, 0.0, 0.78],
            "color": _resolve_optional_color(
                params.get("key_color"), [1.0, 0.95, 0.9], "key_color"
            ),
        },
        {
            "name": "Three Point Fill",
            "light_type": "RECTANGLE",
            "size": 3.2,
            "energy": float(params.get("fill_intensity", 500.0)),
            "location": [-4.5, -3.0, 2.5],
            "rotation": [1.05, 0.0, -0.78],
            "color": _resolve_optional_color(
                params.get("fill_color"), [0.85, 0.9, 1.0], "fill_color"
            ),
        },
        {
            "name": "Three Point Rim",
            "light_type": "RECTANGLE",
            "size": 2.0,
            "energy": float(params.get("rim_intensity", 800.0)),
            "location": [-2.0, 4.0, 5.5],
            "rotation": [0.65, 0.0, -2.5],
            "color": _resolve_optional_color(
                params.get("rim_color"), [1.0, 0.98, 0.92], "rim_color"
            ),
        },
    ]


def create_area_light(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace an area light."""
    name = params.get("name")
    if not name:
        raise ValueError("Light name is required")

    light_shape = str(params.get("light_type", "RECTANGLE"))
    size = float(params.get("size", 1.0))
    energy = float(params.get("energy", 100.0))
    location = _normalize_vector(params.get("location", [0.0, 0.0, 5.0]), "location")
    rotation = _normalize_vector(params.get("rotation", [0.0, 0.0, 0.0]), "rotation")
    color = _normalize_color(params.get("color", [1.0, 1.0, 1.0]), "color")

    light_object = _ensure_light_object(name, "AREA")
    light_object.location = location
    light_object.rotation_euler = rotation
    light_object.data.energy = energy
    light_object.data.color = color
    normalized_shape = _configure_area_shape(
        light_object.data, light_shape, size, params.get("size_y")
    )

    return {
        "status": "success",
        "name": light_object.name,
        "type": "area",
        "shape": normalized_shape,
        "energy": light_object.data.energy,
    }


def create_three_point_lighting(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace a three-point lighting setup."""
    lights = []
    for light_spec in _build_three_point_specs(params):
        create_area_light(light_spec)
        lights.append(light_spec["name"])

    return {"status": "success", "preset": "three_point", "lights": lights}


def create_studio_lighting(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a named studio preset."""
    preset = str(params.get("preset", "")).lower()
    if not preset:
        raise ValueError("preset is required")
    if preset == "three_point":
        return create_three_point_lighting(
            {
                "key_intensity": float(params.get("intensity", 500.0)) * 1.6,
                "fill_intensity": float(params.get("intensity", 500.0)) * 0.9,
                "rim_intensity": float(params.get("intensity", 500.0)) * 1.2,
                "key_color": params.get("color"),
                "fill_color": params.get("color"),
                "rim_color": params.get("color"),
            }
        )

    preset_specs = _STUDIO_PRESET_SPECS.get(preset)
    if preset_specs is None:
        raise ValueError(f"Unsupported studio lighting preset: {preset}")

    base_intensity = float(params.get("intensity", 500.0))
    override_color = params.get("color")
    lights = []
    for spec in preset_specs:
        light_params = {
            "name": spec["name"],
            "light_type": spec.get("light_type", "RECTANGLE"),
            "size": spec.get("size", 2.0),
            "energy": base_intensity * spec.get("energy_multiplier", 1.0),
            "location": spec["location"],
            "rotation": spec["rotation"],
            "color": override_color if override_color is not None else spec["color"],
        }
        create_area_light(light_params)
        lights.append(spec["name"])

    return {"status": "success", "preset": preset, "lights": lights}


def create_hdri_environment(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create an HDRI-style world background network."""
    strength = float(params.get("strength", 1.0))
    rotation = float(params.get("rotation", 0.0))
    blur = float(params.get("blur", 0.0))
    hdri_name = params.get("hdri_name")

    world = _get_or_create_world()
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)
    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-600, 0)
    env_tex = nodes.new(type="ShaderNodeTexEnvironment")
    env_tex.location = (-350, 0)
    placeholder_color = nodes.new(type="ShaderNodeRGB")
    placeholder_color.location = (-350, -180)
    mix = nodes.new(type="ShaderNodeMixRGB")
    mix.location = (-180, 0)
    background = nodes.new(type="ShaderNodeBackground")
    background.location = (-50, 0)
    output = nodes.new(type="ShaderNodeOutputWorld")
    output.location = (250, 0)

    mapping.inputs["Rotation"].default_value[2] = math.radians(rotation)
    background.inputs["Strength"].default_value = strength
    placeholder_color.outputs["Color"].default_value = _hdri_placeholder_color(
        hdri_name, blur
    )
    mix.inputs["Fac"].default_value = max(0.0, min(1.0, blur))
    env_tex.label = f"HDRI Stub: {hdri_name or 'default'}"
    world["blender_mcp_hdri_name"] = "" if hdri_name is None else str(hdri_name)
    world["blender_mcp_hdri_blur"] = blur

    links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], env_tex.inputs["Vector"])
    links.new(env_tex.outputs["Color"], mix.inputs["Color1"])
    links.new(placeholder_color.outputs["Color"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], background.inputs["Color"])
    links.new(background.outputs["Background"], output.inputs["Surface"])

    return {
        "status": "success",
        "hdri_name": hdri_name,
        "strength": strength,
        "rotation": rotation,
        "blur": blur,
    }


def create_volumetric_lighting(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace a volumetric world node setup."""
    density = float(params.get("density", 0.1))
    anisotropy = float(params.get("anisotropy", 0.0))
    color = _normalize_color(params.get("color", [1.0, 1.0, 1.0]), "color")

    world = _get_or_create_world()
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    output = _find_node(nodes, "ShaderNodeOutputWorld")
    if output is None:
        output = nodes.new(type="ShaderNodeOutputWorld")
        output.location = (250, -250)

    volume = _find_node(nodes, "ShaderNodeVolumeScatter")
    if volume is None:
        volume = nodes.new(type="ShaderNodeVolumeScatter")
        volume.location = (-50, -250)

    volume.inputs["Color"].default_value = color + [1.0]
    volume.inputs["Density"].default_value = density
    volume.inputs["Anisotropy"].default_value = anisotropy
    links.new(volume.outputs["Volume"], output.inputs["Volume"])

    return {
        "status": "success",
        "density": density,
        "anisotropy": anisotropy,
        "color": color,
    }


def adjust_light_exposure(params: Dict[str, Any]) -> Dict[str, Any]:
    """Adjust scene exposure settings."""
    exposure = float(params.get("exposure", 0.0))
    gamma = float(params.get("gamma", 1.0))
    bpy.context.scene.view_settings.exposure = exposure
    bpy.context.scene.view_settings.gamma = gamma
    return {"status": "success", "exposure": exposure, "gamma": gamma}


def clear_lights() -> Dict[str, Any]:
    """Remove all light objects from the scene."""
    removed_count = 0
    for obj in list(_get_active_scene_objects()):
        if getattr(obj, "type", None) != "LIGHT":
            continue
        bpy.data.objects.remove(obj, do_unlink=True)
        removed_count += 1

    return {"status": "success", "removed_count": removed_count}


def list_lights() -> Dict[str, Any]:
    """List light objects in the scene."""
    lights = [
        _describe_light(obj)
        for obj in _get_active_scene_objects()
        if obj.type == "LIGHT"
    ]
    return {"lights": lights, "count": len(lights)}
