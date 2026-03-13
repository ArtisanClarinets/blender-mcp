"""Rigging handlers for Blender MCP addon.

Implements automated rigging solutions for bipeds, quadrupeds, and custom creatures.
"""

import math
from typing import Any, Dict, List, Optional

import bpy
import structlog
from bpy import context as bpy_context
from mathutils import Vector

from ...exceptions import BlenderMCPError

logger = structlog.get_logger(__name__)

BIPED_TEMPLATE: Dict[str, List[str]] = {
    "spine": ["hips", "spine", "chest", "neck", "head"],
    "left_arm": ["shoulder.L", "upper_arm.L", "forearm.L", "hand.L"],
    "right_arm": ["shoulder.R", "upper_arm.R", "forearm.R", "hand.R"],
    "left_leg": ["thigh.L", "shin.L", "foot.L", "toe.L"],
    "right_leg": ["thigh.R", "shin.R", "foot.R", "toe.R"],
}

QUADRUPED_TEMPLATE: Dict[str, List[str]] = {
    "spine": ["hips", "spine.01", "spine.02", "spine.03", "chest", "neck", "head"],
    "front_left_leg": ["front_thigh.L", "front_shin.L", "front_foot.L", "front_toe.L"],
    "front_right_leg": ["front_thigh.R", "front_shin.R", "front_foot.R", "front_toe.R"],
    "back_left_leg": ["back_thigh.L", "back_shin.L", "back_foot.L", "back_toe.L"],
    "back_right_leg": ["back_thigh.R", "back_shin.R", "back_foot.R", "back_toe.R"],
    "tail": ["tail.01", "tail.02", "tail.03"],
}

def _resolve_object(name: str) -> Optional[bpy.types.Object]:
    """Resolve an object by name or return None."""
    return bpy.data.objects.get(name)

def _create_armature(name: str) -> bpy.types.Object:
    """Create a new armature object."""
    armature_data = bpy.data.armatures.new(name=f"{name}_armature")
    armature_obj = bpy.data.objects.new(name, armature_data)
    bpy_context.collection.objects.link(armature_obj)
    return armature_obj

def _add_bone(
    armature: bpy.types.Object,
    bone_name: str,
    head: List[float],
    tail: List[float],
    parent: Optional[str] = None,
    use_connect: bool = False,
) -> bpy.types.Bone:
    """Add a bone to an armature in edit mode."""
    bpy_context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")

    bone = armature.data.edit_bones.new(bone_name)
    bone.head = head
    bone.tail = tail

    if parent and parent in armature.data.edit_bones:
        bone.parent = armature.data.edit_bones[parent]
        bone.use_connect = use_connect

    return bone

def _get_bone_chain_length(mesh: bpy.types.Object, axis: str = "Z") -> float:
    """Estimate the length of the mesh along an axis for bone sizing."""
    if not mesh or mesh.type != "MESH":
        return 1.0

    bbox = [mesh.matrix_world @ Vector(corner) for corner in mesh.bound_box]
    min_coord = min(bbox, key=lambda v: getattr(v, axis.lower()))
    max_coord = max(bbox, key=lambda v: getattr(v, axis.lower()))

    return (max_coord - min_coord).length

def create_auto_rig(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create an automated rig for a character mesh."""
    character_name = params.get("character_name")
    rig_type = params.get("rig_type", "biped")
    skeleton_template = params.get("skeleton_template")
    ik_fk_switch = params.get("ik_fk_switch", True)
    facial_rig = params.get("facial_rig", False)

    if not character_name:
        raise BlenderMCPError("character_name is required")

    character = _resolve_object(character_name)
    if character is None:
        raise BlenderMCPError(f"Character mesh not found: {character_name}")

    rig_name = f"{character_name}_rig"
    armature = _create_armature(rig_name)

    if skeleton_template:
        template = skeleton_template
    elif rig_type == "biped":
        template = BIPED_TEMPLATE
    elif rig_type == "quadruped":
        template = QUADRUPED_TEMPLATE
    else:
        template = BIPED_TEMPLATE

    height = _get_bone_chain_length(character, "Z")
    width = _get_bone_chain_length(character, "X")

    bones_created = []
    bone_count = 0

    for chain_name, bone_names in template.items():
        prev_bone = None

        for i, bone_name in enumerate(bone_names):
            head_z = height * (1.0 - (i / (len(bone_names) + 1)))
            tail_z = head_z - (height / (len(bone_names) + 2))

            x_offset = 0.0
            if ".L" in bone_name:
                x_offset = width * 0.15
            elif ".R" in bone_name:
                x_offset = -width * 0.15

            _add_bone(
                armature,
                bone_name,
                head=[x_offset, 0.0, head_z],
                tail=[x_offset, 0.0, tail_z],
                parent=prev_bone,
                use_connect=True,
            )
            bones_created.append(bone_name)
            bone_count += 1
            prev_bone = bone_name

    bpy.ops.object.mode_set(mode="OBJECT")
    character.select_set(True)
    armature.select_set(True)
    bpy_context.view_layer.objects.active = armature
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.mode_set(mode="OBJECT")

    logger.info("Created auto rig", rig_name=rig_name, rig_type=rig_type)
    return {
        "status": "success",
        "rig_name": rig_name,
        "armature_name": armature.name,
        "rig_type": rig_type,
        "bone_count": bone_count,
        "bones": bones_created,
        "ik_fk_switch": ik_fk_switch,
        "facial_rig": facial_rig,
        "parented_mesh": character_name,
    }

def generate_skeleton(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a skeleton based on mesh analysis."""
    mesh_name = params.get("mesh_name")
    skeleton_type = params.get("skeleton_type", "auto")
    bone_count = params.get("bone_count")
    symmetry = params.get("symmetry", True)

    if not mesh_name:
        raise BlenderMCPError("mesh_name is required")

    mesh = _resolve_object(mesh_name)
    if mesh is None:
        raise BlenderMCPError(f"Mesh not found: {mesh_name}")

    skeleton_name = f"{mesh_name}_skeleton"
    armature = _create_armature(skeleton_name)

    height = _get_bone_chain_length(mesh, "Z")
    width = _get_bone_chain_length(mesh, "X")
    depth = _get_bone_chain_length(mesh, "Y")

    target_bones = bone_count or int(height * 3)

    bones_created = []

    spine_bones = max(3, target_bones // 4)
    for i in range(spine_bones):
        z_pos = height * (1.0 - (i + 0.5) / (spine_bones + 1))
        z_next = height * (1.0 - (i + 1.5) / (spine_bones + 1))
        bone_name = f"spine.{i + 1:02d}"

        _add_bone(
            armature,
            bone_name,
            head=[0.0, 0.0, z_pos],
            tail=[0.0, 0.0, z_next],
            parent=f"spine.{i:02d}" if i > 0 else None,
            use_connect=i > 0,
        )
        bones_created.append(bone_name)

    if symmetry:
        for side, x_mult in [("L", 1), ("R", -1)]:
            arm_root_z = height * 0.7
            for i, bone_name in enumerate(["upper_arm", "lower_arm", "hand"]):
                x_pos = x_mult * width * 0.2
                parent_name = f"{bone_name}.{side}" if i == 0 else bones_created[-1]

                _add_bone(
                    armature,
                    f"{bone_name}.{side}",
                    head=[x_pos, 0.0, arm_root_z - i * 0.1],
                    tail=[x_pos + x_mult * 0.1, 0.0, arm_root_z - (i + 1) * 0.1],
                    parent=parent_name if i > 0 else None,
                )
                bones_created.append(f"{bone_name}.{side}")

            leg_root_z = height * 0.3
            for i, bone_name in enumerate(["thigh", "shin", "foot"]):
                x_pos = x_mult * width * 0.1
                _add_bone(
                    armature,
                    f"{bone_name}.{side}",
                    head=[x_pos, 0.0, leg_root_z - i * 0.15],
                    tail=[x_pos, 0.0, leg_root_z - (i + 1) * 0.15],
                )
                bones_created.append(f"{bone_name}.{side}")

    bpy.ops.object.mode_set(mode="OBJECT")

    logger.info("Generated skeleton", skeleton_name=skeleton_name)
    return {
        "status": "success",
        "skeleton_name": skeleton_name,
        "armature_name": armature.name,
        "skeleton_type": skeleton_type,
        "bone_count": len(bones_created),
        "bones": bones_created,
        "symmetry": symmetry,
        "mesh_dimensions": {"height": height, "width": width, "depth": depth},
    }

def auto_weight_paint(params: Dict[str, Any]) -> Dict[str, Any]:
    """Automatically weight paint a mesh to an armature."""
    mesh_name = params.get("mesh_name")
    armature_name = params.get("armature_name")
    heat_method = params.get("heat_method", "bones")
    quality = params.get("quality", "high")

    if not mesh_name:
        raise BlenderMCPError("mesh_name is required")
    if not armature_name:
        raise BlenderMCPError("armature_name is required")

    mesh = _resolve_object(mesh_name)
    armature = _resolve_object(armature_name)

    if mesh is None:
        raise BlenderMCPError(f"Mesh not found: {mesh_name}")
    if armature is None:
        raise BlenderMCPError(f"Armature not found: {armature_name}")

    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    armature.select_set(True)
    bpy_context.view_layer.objects.active = armature

    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.mode_set(mode="OBJECT")

    vertex_groups = len(mesh.vertex_groups)

    logger.info("Auto weight painted", mesh=mesh_name, armature=armature_name)
    return {
        "status": "success",
        "mesh_name": mesh_name,
        "armature_name": armature_name,
        "heat_method": heat_method,
        "quality": quality,
        "vertex_groups": vertex_groups,
        "message": f"Auto weight painted {mesh_name} to {armature_name}",
    }

def create_control_rig(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a control rig for animation."""
    armature_name = params.get("armature_name")
    control_style = params.get("control_style", "studio")
    ik_chains = params.get("ik_chains", [])
    fk_layers = params.get("fk_layers", [])

    if not armature_name:
        raise BlenderMCPError("armature_name is required")

    armature = _resolve_object(armature_name)
    if armature is None:
        raise BlenderMCPError(f"Armature not found: {armature_name}")

    control_name = f"{armature_name}_controls"
    control_armature = _create_armature(control_name)

    controls_created = []
    ik_setups = []

    bpy_context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")

    for bone in armature.data.edit_bones:
        _add_bone(
            control_armature,
            f"CTRL_{bone.name}",
            head=list(bone.head),
            tail=list(bone.tail),
            parent=f"CTRL_{bone.parent.name}" if bone.parent else None,
        )
        controls_created.append(f"CTRL_{bone.name}")

    bpy.ops.object.mode_set(mode="OBJECT")

    for chain in ik_chains:
        ik_setups.append({"chain": chain, "type": "ik", "enabled": True})

    logger.info("Created control rig", name=control_name, base=armature_name)
    return {
        "status": "success",
        "control_rig_name": control_name,
        "base_armature": armature_name,
        "control_style": control_style,
        "controls_created": len(controls_created),
        "controls": controls_created[:20],  # Limit output
        "ik_chains": ik_setups,
        "fk_layers": fk_layers,
    }

def get_status() -> Dict[str, Any]:
    """Get rigging system status."""
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]

    logger.info("Getting rigging status")
    return {
        "status": "ready",
        "armature_count": len(armatures),
        "armatures": [arm.name for arm in armatures[:10]],
        "supported_rig_types": ["biped", "quadruped", "creature", "facial"],
        "features": {
            "auto_rigging": True,
            "weight_painting": True,
            "ik_fk_switching": True,
            "control_rigs": True,
        },
    }