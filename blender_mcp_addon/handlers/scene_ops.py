"""
Scene operations handlers

Implements atomic scene manipulation commands.
"""

import bpy
import mathutils
from typing import Any, Dict, List, Optional

from .. import id


def create_primitive(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a primitive object."""
    primitive_type = params.get("type", "cube")
    name = params.get("name")
    size = params.get("size")
    location = params.get("location", [0, 0, 0])
    rotation = params.get("rotation", [0, 0, 0])
    scale = params.get("scale", [1, 1, 1])

    # Deselect all
    bpy.ops.object.select_all(action="DESELECT")

    # Create primitive based on type
    if primitive_type == "cube":
        bpy.ops.mesh.primitive_cube_add(
            size=size or 2, location=location, rotation=rotation
        )
    elif primitive_type == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=size or 1, location=location, rotation=rotation
        )
    elif primitive_type == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(
            radius=size or 1,
            depth=size or 2 if size else 2,
            location=location,
            rotation=rotation,
        )
    elif primitive_type == "cone":
        bpy.ops.mesh.primitive_cone_add(
            radius1=size or 1,
            depth=size or 2 if size else 2,
            location=location,
            rotation=rotation,
        )
    elif primitive_type == "torus":
        bpy.ops.mesh.primitive_torus_add(
            major_radius=size or 1,
            minor_radius=size or 0.25 if size else 0.25,
            location=location,
            rotation=rotation,
        )
    elif primitive_type == "plane":
        bpy.ops.mesh.primitive_plane_add(
            size=size or 2, location=location, rotation=rotation
        )
    else:
        raise ValueError(f"Unknown primitive type: {primitive_type}")

    obj = bpy.context.active_object
    if name:
        obj.name = name
    obj.scale = scale

    # Assign UUID
    obj_id = id.assign_uuid(obj)

    return {
        "id": obj_id,
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
    }


def create_empty(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create an empty object."""
    name = params.get("name")
    location = params.get("location", [0, 0, 0])

    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.empty_add(location=location)

    obj = bpy.context.active_object
    if name:
        obj.name = name

    obj_id = id.assign_uuid(obj)

    return {
        "id": obj_id,
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
    }


def create_camera(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a camera."""
    name = params.get("name")
    lens = params.get("lens", 50)
    location = params.get("location", [0, 0, 10])
    look_at = params.get("look_at")

    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.camera_add(location=location)

    obj = bpy.context.active_object
    if name:
        obj.name = name
    obj.data.lens = lens

    # Point camera at target
    if look_at:
        direction = mathutils.Vector(look_at) - obj.location
        rot_quat = direction.to_track_quat("-Z", "Y")
        obj.rotation_euler = rot_quat.to_euler()

    obj_id = id.assign_uuid(obj)

    return {
        "id": obj_id,
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "lens": obj.data.lens,
    }


def create_light(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a light."""
    light_type = params.get("type", "POINT")
    energy = params.get("energy", 100)
    color = params.get("color", [1, 1, 1])
    location = params.get("location", [0, 0, 5])
    rotation = params.get("rotation", [0, 0, 0])

    bpy.ops.object.select_all(action="DESELECT")

    if light_type == "POINT":
        bpy.ops.object.light_add(type="POINT", location=location, rotation=rotation)
    elif light_type == "SUN":
        bpy.ops.object.light_add(type="SUN", location=location, rotation=rotation)
    elif light_type == "SPOT":
        bpy.ops.object.light_add(type="SPOT", location=location, rotation=rotation)
    elif light_type == "AREA":
        bpy.ops.object.light_add(type="AREA", location=location, rotation=rotation)
    else:
        raise ValueError(f"Unknown light type: {light_type}")

    obj = bpy.context.active_object
    obj.data.energy = energy
    obj.data.color = color

    obj_id = id.assign_uuid(obj)

    return {
        "id": obj_id,
        "name": obj.name,
        "type": obj.type,
        "light_type": obj.data.type,
        "energy": obj.data.energy,
        "color": list(obj.data.color),
        "location": list(obj.location),
    }


def set_transform(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set object transform."""
    target_id = params.get("target_id")
    location = params.get("location")
    rotation = params.get("rotation")
    scale = params.get("scale")
    apply = params.get("apply", False)

    obj = id.resolve_id(target_id)
    if not obj:
        raise ValueError(f"Object not found: {target_id}")

    if location:
        obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    if scale:
        obj.scale = scale

    if apply:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(
            location=bool(location), rotation=bool(rotation), scale=bool(scale)
        )

    return {
        "id": id.get_uuid(obj),
        "name": obj.name,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
    }


def select_objects(params: Dict[str, Any]) -> Dict[str, Any]:
    """Select objects."""
    ids = params.get("ids", [])
    mode = params.get("mode", "set")

    if mode == "set":
        bpy.ops.object.select_all(action="DESELECT")

    for obj_id in ids:
        obj = id.resolve_id(obj_id)
        if obj:
            if mode == "remove":
                obj.select_set(False)
            else:
                obj.select_set(True)

    return {
        "count": len(bpy.context.selected_objects),
        "selected": [obj.name for obj in bpy.context.selected_objects],
    }


def delete_objects(params: Dict[str, Any]) -> Dict[str, Any]:
    """Delete objects."""
    ids = params.get("ids", [])

    deleted = []
    for obj_id in ids:
        obj = id.resolve_id(obj_id)
        if obj:
            deleted.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)

    return {"deleted": deleted, "count": len(deleted)}


def duplicate_object(params: Dict[str, Any]) -> Dict[str, Any]:
    """Duplicate an object."""
    obj_id = params.get("id")
    linked = params.get("linked", False)
    count = params.get("count", 1)

    obj = id.resolve_id(obj_id)
    if not obj:
        raise ValueError(f"Object not found: {obj_id}")

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    duplicates = []
    for i in range(count):
        if linked:
            bpy.ops.object.duplicate_move_linked()
        else:
            bpy.ops.object.duplicate_move()

        dup = bpy.context.active_object
        dup_id = id.assign_uuid(dup)
        duplicates.append({"id": dup_id, "name": dup.name})

    return {"original": obj_id, "duplicates": duplicates}


def assign_material_pbr(params: Dict[str, Any]) -> Dict[str, Any]:
    """Assign PBR material to object."""
    target_id = params.get("target_id")
    material_spec = params.get("material_spec", {})

    obj = id.resolve_id(target_id)
    if not obj:
        raise ValueError(f"Object not found: {target_id}")

    # Create or get material
    mat_name = material_spec.get("name", f"{obj.name}_Material")
    if mat_name in bpy.data.materials:
        mat = bpy.data.materials[mat_name]
    else:
        mat = bpy.data.materials.new(name=mat_name)

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    # Create principled BSDF
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")

    # Set material properties
    if "base_color" in material_spec:
        bsdf.inputs["Base Color"].default_value = material_spec["base_color"] + [1]
    if "metallic" in material_spec:
        bsdf.inputs["Metallic"].default_value = material_spec["metallic"]
    if "roughness" in material_spec:
        bsdf.inputs["Roughness"].default_value = material_spec["roughness"]

    # Link nodes
    mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Assign to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    return {"object": obj.name, "material": mat.name}


def set_world_hdri(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set world HDRI."""
    # This is a placeholder - actual implementation would download and set HDRI
    asset_id = params.get("asset_id")
    resolution = params.get("resolution", "2k")

    # For now, just set a color
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new(name="World")
        bpy.context.scene.world = world

    world.use_nodes = True

    return {
        "asset_id": asset_id,
        "resolution": resolution,
        "status": "HDRI setting not fully implemented",
    }


def execute_blender_code(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute arbitrary Python code."""
    code = params.get("code", "")

    # Create namespace with bpy available
    namespace = {"bpy": bpy, "mathutils": mathutils}

    # Execute code
    exec(code, namespace)

    return {"executed": True, "code_length": len(code)}
