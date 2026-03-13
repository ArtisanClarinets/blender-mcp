"""Render pipeline helpers for Blender MCP."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, UTC
from typing import Any, Dict

import bpy

STORE_KEY = "blender_mcp_render_store"



def _utc_now() -> str:
    return datetime.now(UTC).isoformat()



def _load_store() -> dict[str, Any]:
    scene = bpy.context.scene
    raw = scene.get(STORE_KEY)
    if not raw:
        return {"jobs": {}}
    try:
        return json.loads(raw)
    except Exception:
        return {"jobs": {}}



def _save_store(store: dict[str, Any]) -> None:
    bpy.context.scene[STORE_KEY] = json.dumps(store)



def _set_attr_if_exists(target: Any, name: str, value: Any) -> bool:
    if hasattr(target, name):
        setattr(target, name, value)
        return True
    return False



def get_status() -> Dict[str, Any]:
    store = _load_store()
    return {"status": "ready", "queued_jobs": len(store.get("jobs", {}))}



def create_render_job(params: Dict[str, Any]) -> Dict[str, Any]:
    job_name = str(params.get("job_name") or "").strip() or f"render_{uuid.uuid4().hex[:8]}"
    frame_range = list(params.get("frame_range") or [bpy.context.scene.frame_start, bpy.context.scene.frame_end])
    output_path = str(params.get("output_path") or "").strip() or bpy.path.abspath("//renders")
    priority = int(params.get("priority", 1))
    nodes = int(params.get("nodes", 1))
    render_settings = dict(params.get("render_settings") or {})

    job_id = f"rj_{uuid.uuid4().hex[:12]}"
    job = {
        "job_id": job_id,
        "job_name": job_name,
        "frame_range": frame_range,
        "output_path": output_path,
        "priority": priority,
        "nodes": nodes,
        "render_settings": render_settings,
        "status": "queued",
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }
    store = _load_store()
    store.setdefault("jobs", {})[job_id] = job
    _save_store(store)
    return {"status": "success", "job": job}



def monitor_render_job(params: Dict[str, Any]) -> Dict[str, Any]:
    job_id = str(params.get("job_id") or "").strip()
    store = _load_store()
    job = store.get("jobs", {}).get(job_id)
    if not job:
        raise ValueError(f"Render job not found: {job_id}")
    return {"status": "success", "job": job}



def optimize_render_settings(params: Dict[str, Any]) -> Dict[str, Any]:
    quality_target = str(params.get("quality_target") or "production")
    time_budget = params.get("time_budget")
    memory_limit = params.get("memory_limit")

    scene = bpy.context.scene
    render = scene.render
    cycles = getattr(scene, "cycles", None)

    if quality_target == "preview":
        if cycles:
            cycles.samples = 32
        render.use_motion_blur = False
    elif quality_target == "draft":
        if cycles:
            cycles.samples = 64
        render.use_motion_blur = False
    else:
        if cycles:
            cycles.samples = 256
        render.use_motion_blur = True

    if memory_limit and cycles and hasattr(cycles, "preview_samples"):
        cycles.preview_samples = min(int(float(memory_limit) * 8), cycles.samples)

    applied = {
        "engine": render.engine,
        "quality_target": quality_target,
        "samples": getattr(cycles, "samples", None),
        "time_budget": time_budget,
        "memory_limit": memory_limit,
    }
    return {"status": "success", "settings": applied}



def setup_render_passes(params: Dict[str, Any]) -> Dict[str, Any]:
    profile = str(params.get("profile") or "production")
    use_cryptomatte = bool(params.get("use_cryptomatte", True))
    include_vectors = bool(params.get("include_vectors", True))

    view_layer = bpy.context.view_layer
    enabled = []

    for attr, name in [
        ("use_pass_z", "z"),
        ("use_pass_normal", "normal"),
        ("use_pass_diffuse_color", "diffuse_color"),
        ("use_pass_glossy_color", "glossy_color"),
        ("use_pass_emit", "emission"),
    ]:
        if _set_attr_if_exists(view_layer, attr, True):
            enabled.append(name)

    if include_vectors and _set_attr_if_exists(view_layer, "use_pass_vector", True):
        enabled.append("vector")
    if use_cryptomatte:
        if _set_attr_if_exists(view_layer, "use_pass_cryptomatte_object", True):
            enabled.append("cryptomatte_object")
        if _set_attr_if_exists(view_layer, "use_pass_cryptomatte_material", True):
            enabled.append("cryptomatte_material")

    return {"status": "success", "profile": profile, "enabled_passes": enabled}



def render_animation_passes(params: Dict[str, Any]) -> Dict[str, Any]:
    frame_start = int(params.get("frame_start", bpy.context.scene.frame_start))
    frame_end = int(params.get("frame_end", bpy.context.scene.frame_end))
    output_path = str(params.get("output_path") or bpy.path.abspath("//renders/animation"))
    pass_profile = params.get("pass_profile", "production")

    setup = setup_render_passes({"profile": pass_profile})
    scene = bpy.context.scene
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    scene.render.filepath = output_path

    plan = {
        "frame_range": [frame_start, frame_end],
        "output_path": output_path,
        "pass_profile": pass_profile,
        "enabled_passes": setup.get("enabled_passes", []),
    }
    return {"status": "success", "render_plan": plan}



def setup_stereoscopic_render(params: Dict[str, Any]) -> Dict[str, Any]:
    enabled = bool(params.get("enabled", True))
    view_format = str(params.get("view_format") or "STEREO_3D")
    display_mode = str(params.get("display_mode") or "SIDEBYSIDE")

    render = bpy.context.scene.render
    applied = {"enabled": False, "view_format": view_format, "display_mode": display_mode}
    if hasattr(render, "use_multiview"):
        render.use_multiview = enabled
        applied["enabled"] = enabled
    if hasattr(render, "views_format"):
        render.views_format = view_format
    image_settings = getattr(render, "image_settings", None)
    if image_settings and hasattr(image_settings, "stereo_3d_format"):
        stereo = image_settings.stereo_3d_format
        if hasattr(stereo, "display_mode"):
            stereo.display_mode = display_mode
    return {"status": "success", "stereo": applied}
