"""AI-assisted creative orchestration helpers.

These are deterministic heuristics rather than opaque ML calls. The goal is to
provide autonomous agents with studio-style planning actions inside Blender.
"""

from __future__ import annotations

from typing import Any, Dict

import bpy

from . import animation, composition, lighting



def get_status() -> Dict[str, Any]:
    return {"status": "ready", "mode": "heuristic_assist"}



def ai_scene_composition(params: Dict[str, Any]) -> Dict[str, Any]:
    scene_type = str(params.get("scene_type") or "product")
    mood = str(params.get("mood") or "balanced")
    complexity = str(params.get("complexity") or "medium")

    dispatch = {
        "product": composition.compose_product_shot,
        "character": composition.compose_character_scene,
        "interior": composition.compose_architectural_shot,
        "exterior": composition.compose_architectural_shot,
    }
    handler = dispatch.get(scene_type, composition.compose_studio_setup)
    result = handler({
        "lighting_style": "dramatic" if mood in {"dramatic", "mysterious"} else "soft",
        "complexity": complexity,
    })
    return {
        "status": "success",
        "scene_type": scene_type,
        "mood": mood,
        "complexity": complexity,
        "composition": result,
    }



def ai_lighting_design(params: Dict[str, Any]) -> Dict[str, Any]:
    time_of_day = str(params.get("time_of_day") or "afternoon")
    mood = str(params.get("mood") or "balanced")
    style = str(params.get("style") or "cinematic")
    preset = "dramatic" if mood in {"dramatic", "mysterious"} else "soft"
    intensity = 900.0 if style == "cinematic" else 500.0
    result = lighting.create_studio_lighting({"preset": preset, "intensity": intensity})
    return {
        "status": "success",
        "design": {
            "time_of_day": time_of_day,
            "mood": mood,
            "style": style,
            "preset": preset,
        },
        "lighting": result,
    }



def ai_animation_assist(params: Dict[str, Any]) -> Dict[str, Any]:
    animation_type = str(params.get("animation_type") or "gesture")
    character_name = str(params.get("character_name") or "Performer")
    action_description = str(params.get("action_description") or animation_type)

    scene = bpy.context.scene
    marker_names = [
        f"{character_name}_start",
        f"{character_name}_anticipation",
        f"{character_name}_action",
        f"{character_name}_settle",
    ]
    frames = [scene.frame_start, scene.frame_start + 6, scene.frame_start + 12, scene.frame_start + 20]
    created = []
    for name, frame in zip(marker_names, frames):
        marker = scene.timeline_markers.get(name) or scene.timeline_markers.new(name, frame=frame)
        marker.frame = frame
        created.append({"name": marker.name, "frame": marker.frame})

    return {
        "status": "success",
        "animation_type": animation_type,
        "character_name": character_name,
        "action_description": action_description,
        "markers": created,
    }



def ai_quality_check(params: Dict[str, Any]) -> Dict[str, Any]:
    check_type = str(params.get("check_type") or "scene")
    quality_level = str(params.get("quality_level") or "production")
    target_objects = list(params.get("target_objects") or [])

    scene = bpy.context.scene
    objects = list(scene.objects)
    cameras = [obj.name for obj in objects if obj.type == "CAMERA"]
    lights = [obj.name for obj in objects if obj.type == "LIGHT"]
    meshes = [obj.name for obj in objects if obj.type == "MESH"]
    issues = []
    if not cameras:
        issues.append("No active camera found.")
    if not lights:
        issues.append("No scene lights found.")
    if quality_level == "production" and scene.render.resolution_x < 1920:
        issues.append("Render resolution is below 1920px width.")
    if check_type == "materials" and not bpy.data.materials:
        issues.append("No materials available for inspection.")
    if target_objects:
        missing = [name for name in target_objects if not bpy.data.objects.get(name)]
        if missing:
            issues.append(f"Missing target objects: {', '.join(missing)}")

    return {
        "status": "success",
        "check_type": check_type,
        "quality_level": quality_level,
        "scene_summary": {
            "camera_count": len(cameras),
            "light_count": len(lights),
            "mesh_count": len(meshes),
        },
        "issues": issues,
    }
