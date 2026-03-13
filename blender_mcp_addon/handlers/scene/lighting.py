"""Lighting handlers for Blender MCP addon.

Implements focused lighting presets, environment setup, and light management.
"""

import json
import math
from typing import Any, Dict, List, Optional

import bpy
import structlog

from ...exceptions import BlenderMCPError

logger = structlog.get_logger(__name__)

_AREA_LIGHT_SHAPES = {"RECTANGLE", "SQUARE", "CIRCLE", "DISC"}
_STUDIO_PRESET_SPECS: Dict[str, List[Dict[str, Any]]] = {
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
    """Generate a placeholder color for an HDRI."""
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
    """Normalize a color to a list of 3 floats."""
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(channel) for channel in value]

def _resolve_optional_color(
    value: Optional[List[float]], default_color: List[float], field_name: str
) -> List[float]:
    """Resolve an optional color to a list of 3 floats."""
    if value is None:
        return list(default_color)
    return _normalize_color(value, field_name)

def _normalize_vector(value: List[float], field_name: str) -> List[float]:
    """Normalize a vector to a list of 3 floats."""
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(component) for component in value]

def _get_or_create_world() -> bpy.types.World:
    """Get or create a world for the scene."""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    return world

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

    raise BlenderMCPError("No active collection available to link new light")

def _ensure_light_object(name: str, light_data_type: str = "AREA") -> Any:
    """Ensure a light object with the given name exists."""
    existing_object = bpy.data.objects.get(name)
    if existing_object is not None:
        if getattr(existing_object, "type", None) != "LIGHT":
            raise BlenderMCPError(f"Object exists and is not a light: {name}")
        existing_object.data.type = light_data_type
        return existing_object

    light_data = bpy.data.lights.new(name=name, type=light_data_type)
    light_object = bpy.data.objects.new(name=name, object_data=light_data)
    _get_collection_for_linking().objects.link(light_object)
    return light_object

def _configure_area_shape(
    light_data: Any, light_shape: str, size: float, size_y: Optional[float]
) -> str:
    """Configure the shape of an area light."""
    normalized_shape = str(light_shape).upper()
    if normalized_shape not in _AREA_LIGHT_SHAPES:
        raise BlenderMCPError(f"Unsupported area light shape: {light_shape}")

    light_data.shape = normalized_shape
    light_data.size = float(size)
    if normalized_shape == "RECTANGLE":
        light_data.size_y = float(size if size_y is None else size_y)

    return normalized_shape

def _describe_light(light_object: Any) -> Dict[str, Any]:
    """Describe a light object."""
    light_data = getattr(light_object, "data", None)
    return {
        "name": light_object.name,
        "type": getattr(light_data, "type", "UNKNOWN"),
        "energy": float(getattr(light_data, "energy", 0.0)),
        "color": list(getattr(light_data, "color", [1.0, 1.0, 1.0])),
        "location": list(getattr(light_object, "location", [0.0, 0.0, 0.0])),
        "rotation": list(getattr(light_object, "rotation_euler", [0.0, 0.0, 0.0])),
    }

def _find_node(nodes: Any, node_idname: str) -> Any:
    """Find a node in a node tree."""
    for node in nodes:
        if getattr(node, "bl_idname", None) == node_idname:
            return node
        if getattr(node, "type", None) == node_idname:
            return node
    return None

def _build_three_point_specs(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build the specifications for a three-point lighting setup."""
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
        raise BlenderMCPError("Light name is required")

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

    logger.info("Created area light", name=name, shape=normalized_shape)
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

    logger.info("Created three-point lighting setup")
    return {"status": "success", "preset": "three_point", "lights": lights}

def create_studio_lighting(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a named studio preset."""
    preset = str(params.get("preset", "")).lower()
    if not preset:
        raise BlenderMCPError("preset is required")
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
        raise BlenderMCPError(f"Unsupported studio lighting preset: {preset}")

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

    logger.info("Created studio lighting setup", preset=preset)
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

    logger.info("Created HDRI environment", hdri_name=hdri_name)
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

    logger.info("Created volumetric lighting", density=density)
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
    logger.info("Adjusted light exposure", exposure=exposure, gamma=gamma)
    return {"status": "success", "exposure": exposure, "gamma": gamma}

def clear_lights() -> Dict[str, Any]:
    """Remove all light objects from the scene."""
    removed_count = 0
    for obj in list(_get_active_scene_objects()):
        if getattr(obj, "type", None) != "LIGHT":
            continue
        bpy.data.objects.remove(obj, do_unlink=True)
        removed_count += 1

    logger.info("Cleared lights", removed_count=removed_count)
    return {"status": "success", "removed_count": removed_count}

def list_lights() -> Dict[str, Any]:
    """List light objects in the scene."""
    lights = [
        _describe_light(obj)
        for obj in _get_active_scene_objects()
        if obj.type == "LIGHT"
    ]
    return {"lights": lights, "count": len(lights)}

def create_hdri_lighting_setup(params: Dict[str, Any]) -> Dict[str, Any]:
    """Compatibility wrapper for a more descriptive HDRI lighting command."""
    return create_hdri_environment(
        {
            "hdri_name": params.get("hdri_name") or params.get("hdri_path"),
            "rotation": params.get("rotation", 0.0),
            "strength": params.get("strength", 1.0),
            "blur": params.get("blur", 0.0),
        }
    )

def create_volumetric_light_effect(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a lightweight volumetric lighting helper object."""
    light_name = params.get("light_name")
    if not light_name:
        raise BlenderMCPError("light_name is required")
    density = float(params.get("density", 0.1))
    scatter_amount = float(params.get("scatter_amount", 1.0))
    anisotropy = float(params.get("anisotropy", 0.0))
    volume_type = str(params.get("volume_type", "god_rays"))

    light_object = bpy.data.objects.get(light_name)
    if light_object is None or light_object.type != "LIGHT":
        raise BlenderMCPError(f"Light not found: {light_name}")

    helper_name = f"{light_name}_volume"
    existing = bpy.data.objects.get(helper_name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    bpy.ops.mesh.primitive_cone_add(radius1=1.0, depth=3.0)
    helper = bpy.context.active_object
    helper.name = helper_name
    helper.location = light_object.location
    helper.rotation_euler = light_object.rotation_euler

    mat = bpy.data.materials.new(name=f"{helper_name}_mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    output = nodes.new(type="ShaderNodeOutputMaterial")
    volume = nodes.new(type="ShaderNodeVolumeScatter")
    volume.inputs["Density"].default_value = density * max(scatter_amount, 0.001)
    volume.inputs["Anisotropy"].default_value = anisotropy
    links.new(volume.outputs["Volume"], output.inputs["Volume"])
    helper.data.materials.append(mat)
    helper.display_type = "WIRE"

    logger.info("Created volumetric light effect", helper_object=helper.name)
    return {
        "status": "success",
        "helper_object": helper.name,
        "light_name": light_name,
        "volume_type": volume_type,
        "density": density,
    }

def create_studio_light_rig(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a named studio light rig using the base lighting primitives."""
    rig_type = str(params.get("rig_type", "portrait"))
    key_light_intensity = float(params.get("key_light_intensity", 1000.0))
    fill_light_intensity = float(params.get("fill_light_intensity", 500.0))
    rim_light_intensity = float(params.get("rim_light_intensity", 800.0))
    background_light_intensity = float(params.get("background_light_intensity", 200.0))

    base = create_three_point_lighting(
        {
            "key_intensity": key_light_intensity,
            "fill_intensity": fill_light_intensity,
            "rim_intensity": rim_light_intensity,
        }
    )
    background = create_area_light(
        {
            "name": f"{rig_type.title()}_Background",
            "size": 3.0,
            "energy": background_light_intensity,
            "location": [0.0, 4.0, 2.0],
            "rotation": [1.57, 0.0, 3.14],
        }
    )
    logger.info("Created studio light rig", rig_type=rig_type)
    return {
        "status": "success",
        "rig_type": rig_type,
        "base_rig": base,
        "background_light": background,
    }

def setup_light_linking(params: Dict[str, Any]) -> Dict[str, Any]:
    """Record a light-linking intent and apply collection tags when possible."""
    light_objects = list(params.get("light_objects") or [])
    target_objects = list(params.get("target_objects") or [])
    link_type = str(params.get("link_type", "include"))

    missing_lights = [name for name in light_objects if bpy.data.objects.get(name) is None]
    missing_targets = [name for name in target_objects if bpy.data.objects.get(name) is None]
    if missing_lights:
        raise BlenderMCPError(f"Missing lights: {', '.join(missing_lights)}")
    if missing_targets:
        raise BlenderMCPError(f"Missing target objects: {', '.join(missing_targets)}")

    for light_name in light_objects:
        light = bpy.data.objects[light_name]
        light["blender_mcp_light_link_targets"] = json.dumps(target_objects)
        light["blender_mcp_light_link_type"] = link_type

    logger.info("Set up light linking", lights=light_objects, targets=target_objects)
    return {
        "status": "success",
        "light_objects": light_objects,
        "target_objects": target_objects,
        "link_type": link_type,
        "mode": "metadata_backed",
    }