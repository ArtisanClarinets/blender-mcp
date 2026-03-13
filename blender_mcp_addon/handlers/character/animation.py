"""Animation handlers for Blender MCP addon.

Implements professional animation workflow tools for timeline management and keyframe animation.
"""

import math
from typing import Any, Dict, List, Optional, Union

import bpy
import structlog
from bpy import context as bpy_context

from ...exceptions import BlenderMCPError

logger = structlog.get_logger(__name__)

def _resolve_object(name: str) -> Optional[bpy.types.Object]:
    """Resolve an object by name or return None."""
    return bpy.data.objects.get(name)

def _get_or_create_action(
    obj: bpy.types.Object, action_name: Optional[str] = None
) -> bpy.types.Action:
    """Get or create an animation action for an object."""
    if action_name is None:
        action_name = f"{obj.name}_Action"

    action = bpy.data.actions.get(action_name)
    if action is None:
        action = bpy.data.actions.new(action_name)

    if obj.animation_data is None:
        obj.animation_data_create()

    obj.animation_data.action = action
    return action

def _interpolate_value(
    t: float,
    interpolation: str = "BEZIER",
    handle_left: Optional[List[float]] = None,
    handle_right: Optional[List[float]] = None,
) -> float:
    """Calculate interpolated value based on interpolation type."""
    if interpolation == "LINEAR":
        return t
    elif interpolation == "CONSTANT":
        return 0.0
    elif interpolation == "BEZIER":
        return t * t * (3 - 2 * t)
    elif interpolation == "EASE_IN":
        return t * t
    elif interpolation == "EASE_OUT":
        return 1 - (1 - t) * (1 - t)
    elif interpolation == "EASE_IN_OUT":
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    return t

def create_animation_layer(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create an animation layer for non-destructive animation."""
    layer_name = params.get("layer_name")
    objects = params.get("objects", [])
    properties = params.get("properties", [])
    influence = params.get("influence", 1.0)

    if not layer_name:
        raise BlenderMCPError("layer_name is required")

    valid_objects = []
    for obj_name in objects:
        obj = _resolve_object(obj_name)
        if obj:
            valid_objects.append(obj_name)

    layers_created = []

    for obj_name in valid_objects:
        obj = _resolve_object(obj_name)
        if obj and obj.animation_data:
            track = obj.animation_data.nla_tracks.new()
            track.name = f"{layer_name}_{obj_name}"
            track.influence = influence
            layers_created.append(track.name)

    logger.info("Created animation layer", layer_name=layer_name, objects=valid_objects)
    return {
        "status": "success",
        "layer_name": layer_name,
        "objects": valid_objects,
        "properties": properties,
        "influence": influence,
        "layers_created": layers_created,
        "message": f"Created animation layer '{layer_name}' for {len(valid_objects)} objects",
    }

def set_keyframe(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set a keyframe for animation."""
    object_name = params.get("object_name")
    property_path = params.get("property_path")
    frame = params.get("frame")
    value = params.get("value")
    interpolation = params.get("interpolation", "BEZIER")

    if not object_name:
        raise BlenderMCPError("object_name is required")
    if not property_path:
        raise BlenderMCPError("property_path is required")
    if frame is None:
        raise BlenderMCPError("frame is required")
    if value is None:
        raise BlenderMCPError("value is required")

    obj = _resolve_object(object_name)
    if obj is None:
        raise BlenderMCPError(f"Object not found: {object_name}")

    if obj.animation_data is None:
        obj.animation_data_create()

    action = _get_or_create_action(obj)
    scene = bpy_context.scene

    original_frame = scene.frame_current
    scene.frame_set(int(frame))

    if isinstance(value, list):
        for i, v in enumerate(value):
            prop = f"{property_path}[{i}]"
            setattr(obj, property_path.split("[")[0], value)
            obj.keyframe_insert(data_path=prop, frame=int(frame))
    else:
        setattr(obj, property_path, value)
        obj.keyframe_insert(data_path=property_path, frame=int(frame))

    for fcurve in action.fcurves:
        if fcurve.data_path.startswith(property_path):
            for keyframe in fcurve.keyframe_points:
                if keyframe.co.x == frame:
                    keyframe.interpolation = interpolation

    scene.frame_set(original_frame)

    logger.info("Set keyframe", object=object_name, property=property_path, frame=frame)
    return {
        "status": "success",
        "object_name": object_name,
        "property_path": property_path,
        "frame": frame,
        "value": value,
        "interpolation": interpolation,
        "action_name": action.name,
    }

def create_animation_curve(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create an animation curve with multiple keyframes."""
    object_name = params.get("object_name")
    property_path = params.get("property_path")
    keyframes = params.get("keyframes", [])
    curve_type = params.get("curve_type", "bezier")

    if not object_name:
        raise BlenderMCPError("object_name is required")
    if not property_path:
        raise BlenderMCPError("property_path is required")
    if not keyframes:
        raise BlenderMCPError("keyframes is required")

    obj = _resolve_object(object_name)
    if obj is None:
        raise BlenderMCPError(f"Object not found: {object_name}")

    action = _get_or_create_action(obj)

    interpolation_map = {
        "bezier": "BEZIER",
        "linear": "LINEAR",
        "stepped": "CONSTANT",
    }
    interpolation = interpolation_map.get(curve_type, "BEZIER")

    keyframes_set = []

    for kf in keyframes:
        frame = kf.get("frame")
        value = kf.get("value")

        if frame is None or value is None:
            continue

        set_keyframe(
            {
                "object_name": object_name,
                "property_path": property_path,
                "frame": frame,
                "value": value,
                "interpolation": interpolation,
            }
        )
        keyframes_set.append(frame)

    logger.info(
        "Created animation curve",
        object=object_name,
        property=property_path,
        count=len(keyframes_set),
    )
    return {
        "status": "success",
        "object_name": object_name,
        "property_path": property_path,
        "curve_type": curve_type,
        "keyframe_count": len(keyframes_set),
        "frames": keyframes_set,
        "action_name": action.name,
    }

def import_motion_capture(params: Dict[str, Any]) -> Dict[str, Any]:
    """Import motion capture data to an armature."""
    file_path = params.get("file_path")
    target_armature = params.get("target_armature")
    scale_factor = params.get("scale_factor", 1.0)
    frame_offset = params.get("frame_offset", 0)

    if not file_path:
        raise BlenderMCPError("file_path is required")
    if not target_armature:
        raise BlenderMCPError("target_armature is required")

    armature = _resolve_object(target_armature)
    if armature is None:
        raise BlenderMCPError(f"Target armature not found: {target_armature}")

    file_ext = file_path.lower().split(".")[-1]

    imported_objects = []

    try:
        if file_ext == "bvh":
            bpy.ops.import_anim.bvh(filepath=file_path, global_scale=scale_factor)
        elif file_ext == "fbx":
            bpy.ops.import_scene.fbx(filepath=file_path, global_scale=scale_factor)
        else:
            raise BlenderMCPError(f"Unsupported motion capture format: {file_ext}")

        for obj in bpy_context.selected_objects:
            imported_objects.append(obj.name)

    except Exception as e:
        raise BlenderMCPError(f"Failed to import motion capture: {str(e)}") from e

    logger.info("Imported motion capture", file_path=file_path)
    return {
        "status": "success",
        "file_path": file_path,
        "target_armature": target_armature,
        "scale_factor": scale_factor,
        "frame_offset": frame_offset,
        "imported_objects": imported_objects,
        "message": f"Imported motion capture from {file_path}",
    }

def retarget_animation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Retarget animation from one armature to another."""
    source_armature_name = params.get("source_armature")
    target_armature_name = params.get("target_armature")
    bone_mapping = params.get("bone_mapping", {})
    preserve_timing = params.get("preserve_timing", True)

    if not source_armature_name:
        raise BlenderMCPError("source_armature is required")
    if not target_armature_name:
        raise BlenderMCPError("target_armature is required")

    source_armature = _resolve_object(source_armature_name)
    target_armature = _resolve_object(target_armature_name)

    if source_armature is None:
        raise BlenderMCPError(f"Source armature not found: {source_armature_name}")
    if target_armature is None:
        raise BlenderMCPError(f"Target armature not found: {target_armature_name}")

    if source_armature.animation_data and source_armature.animation_data.action:
        source_action = source_armature.animation_data.action

        target_action = bpy.data.actions.new(f"{target_armature_name}_retarget")
        target_action.use_fake_user = True

        if target_armature.animation_data is None:
            target_armature.animation_data_create()
        target_armature.animation_data.action = target_action

        bones_retarged = []

        for fcurve in source_action.fcurves:
            data_path = fcurve.data_path

            for source_bone, target_bone in bone_mapping.items():
                if source_bone in data_path:
                    data_path = data_path.replace(source_bone, target_bone)
                    bones_retarged.append(target_bone)
                    break

            new_fcurve = target_action.fcurves.new(
                data_path=data_path, index=fcurve.array_index
            )

            for keyframe in fcurve.keyframe_points:
                new_fcurve.keyframe_points.insert(keyframe.co.x, keyframe.co.y)
                new_fcurve.keyframe_points[-1].interpolation = keyframe.interpolation

        logger.info(
            "Retargeted animation",
            source=source_armature_name,
            target=target_armature_name,
        )
        return {
            "status": "success",
            "source_armature": source_armature_name,
            "target_armature": target_armature_name,
            "bone_mapping": bone_mapping,
            "preserve_timing": preserve_timing,
            "action_name": target_action.name,
            "bones_retarged": list(set(bones_retarged)),
        }

    return {
        "status": "warning",
        "message": f"No animation data found on source armature {source_armature_name}",
    }

def create_facial_animation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create facial animation from audio or emotion curves."""
    character_name = params.get("character_name")
    audio_file = params.get("audio_file")
    emotion_curve = params.get("emotion_curve")
    viseme_library = params.get("viseme_library")

    if not character_name:
        raise BlenderMCPError("character_name is required")

    character = _resolve_object(character_name)
    if character is None:
        raise BlenderMCPError(f"Character not found: {character_name}")

    audio_imported = False
    if audio_file:
        try:
            bpy.context.scene.sequence_editor_create()
            bpy.ops.sequencer.sound_strip_add(filepath=audio_file, frame=1)
            audio_imported = True
        except Exception as e:
            logger.error("Failed to import audio", error=e, exc_info=True)
            audio_imported = False

    shape_keys_animated = []
    if emotion_curve and hasattr(character.data, "shape_keys"):
        if character.data.shape_keys:
            _get_or_create_action(
                character.data.shape_keys, f"{character_name}_facial"
            )

            for emotion_name, keyframes in emotion_curve.items():
                for kf in keyframes:
                    frame = kf.get("frame")
                    value = kf.get("value", 0.0)

                    if frame is not None:
                        character.data.shape_keys.keyframe_insert(
                            data_path=f'key_blocks["{emotion_name}"].value',
                            frame=frame,
                        )
                        shape_keys_animated.append(emotion_name)

    logger.info("Created facial animation", character=character_name)
    return {
        "status": "success",
        "character_name": character_name,
        "audio_file": audio_file,
        "audio_imported": audio_imported,
        "emotion_curve": emotion_curve is not None,
        "viseme_library": viseme_library,
        "shape_keys_animated": list(set(shape_keys_animated)),
        "message": f"Created facial animation for {character_name}",
    }

def get_status() -> Dict[str, Any]:
    """Get animation system status."""
    scene = bpy_context.scene
    objects_with_animation = [
        obj.name
        for obj in bpy.data.objects
        if obj.animation_data and obj.animation_data.action
    ]

    logger.info("Getting animation status")
    return {
        "status": "ready",
        "frame_start": scene.frame_start,
        "frame_end": scene.frame_end,
        "frame_current": scene.frame_current,
        "fps": scene.render.fps,
        "animated_objects_count": len(objects_with_animation),
        "animated_objects": objects_with_animation[:10],
        "features": {
            "keyframe_animation": True,
            "animation_layers": True,
            "motion_capture_import": True,
            "retargeting": True,
            "facial_animation": True,
        },
    }