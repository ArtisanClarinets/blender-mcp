"""
Material handlers for Blender MCP addon.

Implements focused material creation and assignment commands.
"""

from typing import Any, Dict, Iterable, List

import bpy


_PROCEDURAL_NODE_TYPES = {
    "noise": "ShaderNodeTexNoise",
    "voronoi": "ShaderNodeTexVoronoi",
    "wave": "ShaderNodeTexWave",
    "musgrave": "ShaderNodeTexMusgrave",
    "checker": "ShaderNodeTexChecker",
    "brick": "ShaderNodeTexBrick",
    "gradient": "ShaderNodeTexGradient",
    "magic": "ShaderNodeTexMagic",
}


def _normalize_color(value: List[float], field_name: str) -> List[float]:
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(channel) for channel in value] + [1.0]


def _normalize_vector(value: List[float], field_name: str) -> List[float]:
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(component) for component in value]


def _get_material(name: str) -> bpy.types.Material:
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    return material


def _reset_material_nodes(material: bpy.types.Material):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (300, 0)
    shader = nodes.new(type="ShaderNodeBsdfPrincipled")
    shader.location = (0, 0)
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return shader, output


def _set_first_socket(
    node: bpy.types.Node, socket_names: Iterable[str], value: Any
) -> None:
    for socket_name in socket_names:
        socket = node.inputs.get(socket_name)
        if socket is None:
            continue
        socket.default_value = value
        return


def _describe_material(material: bpy.types.Material) -> Dict[str, Any]:
    object_names = []
    for obj in bpy.data.objects:
        materials = getattr(getattr(obj, "data", None), "materials", None)
        if not materials:
            continue
        if any(slot and slot.name == material.name for slot in materials):
            object_names.append(obj.name)

    return {
        "name": material.name,
        "use_nodes": bool(material.use_nodes),
        "users": int(material.users),
        "assigned_objects": object_names,
    }


def create_bsdf_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace a Principled BSDF material."""
    name = params.get("name")
    if not name:
        raise ValueError("Material name is required")

    material = _get_material(name)
    shader, _ = _reset_material_nodes(material)

    if params.get("base_color") is not None:
        shader.inputs["Base Color"].default_value = _normalize_color(
            params["base_color"], "base_color"
        )
    if params.get("metallic") is not None:
        shader.inputs["Metallic"].default_value = float(params["metallic"])
    if params.get("roughness") is not None:
        shader.inputs["Roughness"].default_value = float(params["roughness"])
    if params.get("specular") is not None:
        _set_first_socket(
            shader,
            ("Specular", "Specular IOR Level"),
            float(params["specular"]),
        )
    if params.get("subsurface") is not None:
        _set_first_socket(
            shader,
            ("Subsurface", "Subsurface Weight"),
            float(params["subsurface"]),
        )
    if params.get("subsurface_color") is not None:
        _set_first_socket(
            shader,
            ("Subsurface Color",),
            _normalize_color(params["subsurface_color"], "subsurface_color"),
        )
    if params.get("transmission") is not None:
        _set_first_socket(
            shader,
            ("Transmission", "Transmission Weight"),
            float(params["transmission"]),
        )
    if params.get("ior") is not None:
        _set_first_socket(shader, ("IOR",), float(params["ior"]))
    if params.get("emission_color") is not None:
        _set_first_socket(
            shader,
            ("Emission", "Emission Color"),
            _normalize_color(params["emission_color"], "emission_color"),
        )
    if params.get("emission_strength") is not None:
        _set_first_socket(
            shader,
            ("Emission Strength",),
            float(params["emission_strength"]),
        )

    return {
        "status": "success",
        "material": material.name,
        "type": "principled_bsdf",
        "nodes": len(material.node_tree.nodes),
    }


def create_emission_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace an emission material."""
    name = params.get("name")
    color = params.get("color")
    if not name:
        raise ValueError("Material name is required")
    if color is None:
        raise ValueError("color is required")

    material = _get_material(name)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (200, 0)
    emission = nodes.new(type="ShaderNodeEmission")
    emission.location = (0, 0)
    emission.inputs["Color"].default_value = _normalize_color(color, "color")
    emission.inputs["Strength"].default_value = float(params.get("strength", 10.0))
    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    shadow_mode = str(params.get("shadow_mode", "none")).upper()
    if hasattr(material, "shadow_method"):
        material.shadow_method = shadow_mode

    return {
        "status": "success",
        "material": material.name,
        "type": "emission",
        "shadow_mode": shadow_mode.lower(),
    }


def create_glass_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace a glass-like Principled material."""
    name = params.get("name")
    if not name:
        raise ValueError("Material name is required")

    material = _get_material(name)
    shader, _ = _reset_material_nodes(material)

    color = params.get("color")
    if color is not None:
        shader.inputs["Base Color"].default_value = _normalize_color(color, "color")
    shader.inputs["Roughness"].default_value = float(params.get("roughness", 0.0))
    _set_first_socket(shader, ("IOR",), float(params.get("ior", 1.45)))
    _set_first_socket(
        shader,
        ("Transmission", "Transmission Weight"),
        float(params.get("transmission", 1.0)),
    )

    return {
        "status": "success",
        "material": material.name,
        "type": "glass",
    }


def create_metal_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace a metallic material."""
    name = params.get("name")
    base_color = params.get("base_color")
    if not name:
        raise ValueError("Material name is required")
    if base_color is None:
        raise ValueError("base_color is required")

    material = _get_material(name)
    shader, _ = _reset_material_nodes(material)
    shader.inputs["Base Color"].default_value = _normalize_color(
        base_color, "base_color"
    )
    shader.inputs["Metallic"].default_value = 1.0
    shader.inputs["Roughness"].default_value = float(params.get("roughness", 0.3))
    _set_first_socket(
        shader,
        ("Anisotropic", "Anisotropy"),
        float(params.get("anisotropy", 0.0)),
    )

    return {
        "status": "success",
        "material": material.name,
        "type": "metal",
    }


def create_subsurface_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace a subsurface scattering material."""
    name = params.get("name")
    base_color = params.get("base_color")
    subsurface_color = params.get("subsurface_color")
    if not name:
        raise ValueError("Material name is required")
    if base_color is None:
        raise ValueError("base_color is required")
    if subsurface_color is None:
        raise ValueError("subsurface_color is required")

    material = _get_material(name)
    shader, _ = _reset_material_nodes(material)
    shader.inputs["Base Color"].default_value = _normalize_color(
        base_color, "base_color"
    )
    _set_first_socket(
        shader,
        ("Subsurface", "Subsurface Weight"),
        float(params.get("subsurface", 0.5)),
    )
    _set_first_socket(
        shader,
        ("Subsurface Color",),
        _normalize_color(subsurface_color, "subsurface_color"),
    )
    _set_first_socket(
        shader,
        ("Subsurface Radius",),
        _normalize_vector(
            params.get("subsurface_radius", [1.0, 0.2, 0.1]), "subsurface_radius"
        ),
    )
    shader.inputs["Roughness"].default_value = float(params.get("roughness", 0.5))

    return {
        "status": "success",
        "material": material.name,
        "type": "subsurface",
    }


def create_procedural_texture(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create or replace a material driven by a procedural texture node."""
    texture_type = str(params.get("texture_type", "noise")).lower()
    node_type = _PROCEDURAL_NODE_TYPES.get(texture_type)
    if node_type is None:
        raise ValueError(f"Unsupported procedural texture type: {texture_type}")

    name = params.get("name")
    if not name:
        raise ValueError("Material name is required")

    material = _get_material(name)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (600, 0)
    shader = nodes.new(type="ShaderNodeBsdfPrincipled")
    shader.location = (350, 0)
    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-250, 0)
    texture_coords = nodes.new(type="ShaderNodeTexCoord")
    texture_coords.location = (-450, 0)
    texture = nodes.new(type=node_type)
    texture.location = (50, 0)

    mapping.inputs["Scale"].default_value[0] = float(params.get("scale", 5.0))
    mapping.inputs["Scale"].default_value[1] = float(params.get("scale", 5.0))
    mapping.inputs["Scale"].default_value[2] = float(params.get("scale", 5.0))
    _set_first_socket(texture, ("Scale",), float(params.get("scale", 5.0)))
    _set_first_socket(texture, ("Detail",), float(params.get("detail", 2.0)))
    _set_first_socket(texture, ("Roughness",), float(params.get("roughness", 0.5)))
    _set_first_socket(texture, ("Distortion",), float(params.get("distortion", 0.0)))

    links.new(texture_coords.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], texture.inputs["Vector"])
    if texture.outputs.get("Color") is not None:
        links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    else:
        links.new(texture.outputs["Fac"], shader.inputs["Base Color"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    return {
        "status": "success",
        "material": material.name,
        "texture_type": texture_type,
        "nodes": len(nodes),
    }


def assign_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Assign a material to an object by name."""
    object_name = params.get("object_name")
    material_name = params.get("material_name")
    if not object_name:
        raise ValueError("object_name is required")
    if not material_name:
        raise ValueError("material_name is required")

    obj = bpy.data.objects.get(object_name)
    if obj is None:
        raise ValueError(f"Object not found: {object_name}")
    if getattr(obj.data, "materials", None) is None:
        raise ValueError(f"Object does not support materials: {object_name}")

    material = bpy.data.materials.get(material_name)
    if material is None:
        raise ValueError(f"Material not found: {material_name}")

    material_slots = obj.data.materials
    if not material_slots:
        material_slots.append(material)
    elif len(material_slots) == 1:
        material_slots[0] = material
    else:
        for slot_index, existing_material in enumerate(material_slots):
            if existing_material is None:
                material_slots[slot_index] = material
                break
            if existing_material.name == material.name:
                break
        else:
            material_slots.append(material)

    return {
        "status": "success",
        "object": obj.name,
        "material": material.name,
    }


def list_materials() -> Dict[str, Any]:
    """List materials in the current Blender file."""
    materials = [_describe_material(material) for material in bpy.data.materials]
    return {"materials": materials, "count": len(materials)}


def delete_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete a material by name."""
    name = params.get("name")
    if not name:
        raise ValueError("Material name is required")

    material = bpy.data.materials.get(name)
    if material is None:
        raise ValueError(f"Material not found: {name}")

    users_before_delete = int(material.users)
    bpy.data.materials.remove(material, do_unlink=True)
    return {
        "status": "success",
        "material": name,
        "users_before_delete": users_before_delete,
    }
