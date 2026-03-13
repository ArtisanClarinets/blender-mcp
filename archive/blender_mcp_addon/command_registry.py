"""Canonical command registry for the Blender-side addon server."""

from __future__ import annotations

import importlib
from typing import Any, Callable, Dict

CommandHandler = Callable[[Dict[str, Any]], Any]



def _unavailable(name: str) -> CommandHandler:
    def _handler(params: Dict[str, Any]) -> Any:
        raise ValueError(f"Command backend unavailable for: {name}")

    return _handler



def _load_handler_module(name: str) -> Any:
    package_name = __package__ or "blender_mcp_addon"
    try:
        return importlib.import_module(f"{package_name}.handlers.{name}")
    except Exception:
        try:
            handlers_pkg = importlib.import_module(f"{package_name}.handlers")
            return getattr(handlers_pkg, name)
        except Exception:
            return object()



def _attr(module: Any, name: str) -> CommandHandler:
    value = getattr(module, name, None)
    if callable(value):
        return value
    return _unavailable(name)



def _status(handler: Callable[[], Any]) -> CommandHandler:
    return lambda params: handler()


scene_observe = _load_handler_module("scene_observe")
scene_ops = _load_handler_module("scene_ops")
camera = _load_handler_module("camera")
composition = _load_handler_module("composition")
materials = _load_handler_module("materials")
lighting = _load_handler_module("lighting")
advanced_materials = _load_handler_module("advanced_materials")
assets_polyhaven = _load_handler_module("assets_polyhaven")
assets_sketchfab = _load_handler_module("assets_sketchfab")
jobs_hyper3d = _load_handler_module("jobs_hyper3d")
jobs_hunyuan = _load_handler_module("jobs_hunyuan")
jobs_tripo3d = _load_handler_module("jobs_tripo3d")
rigging = _load_handler_module("rigging")
animation = _load_handler_module("animation")
atmospherics_handler = _load_handler_module("atmospherics_handler")
procedural_materials = _load_handler_module("procedural_materials")
production = _load_handler_module("production")
render_pipeline = _load_handler_module("render_pipeline")
ai_creative = _load_handler_module("ai_creative")
export_handler = _load_handler_module("export_handler")



def _create_job(params: Dict[str, Any]) -> Any:
    provider = params.get("provider")
    payload = params.get("payload", {})
    if provider == "hyper3d":
        return _attr(jobs_hyper3d, "create_job")(payload)
    if provider == "hunyuan3d":
        return _attr(jobs_hunyuan, "create_job")(payload)
    if provider == "tripo3d":
        return _attr(jobs_tripo3d, "create_job")(payload)
    raise ValueError(f"Unknown provider: {provider}")



def _get_job(params: Dict[str, Any]) -> Any:
    for handler in (jobs_hyper3d, jobs_hunyuan, jobs_tripo3d):
        getter = getattr(handler, "get_job", None)
        if not callable(getter):
            continue
        result = getter(params)
        if result:
            return result
    raise ValueError(f"Job not found: {params.get('job_id')}")



def _import_job_result(params: Dict[str, Any]) -> Any:
    for handler in (jobs_hyper3d, jobs_hunyuan, jobs_tripo3d):
        getter = getattr(handler, "get_job", None)
        importer = getattr(handler, "import_job_result", None)
        if not callable(getter) or not callable(importer):
            continue
        if getter(params):
            return importer(params)
    raise ValueError(f"Job not found: {params.get('job_id')}")


COMMAND_HANDLERS: dict[str, CommandHandler] = {
    # Observe
    "observe_scene": _attr(scene_observe, "observe_scene"),
    "get_scene_hash": _status(_attr(scene_observe, "get_scene_hash")),
    "get_scene_info": _status(_attr(scene_observe, "get_scene_info")),
    "get_object_info": _attr(scene_observe, "get_object_info"),
    "get_viewport_screenshot": _attr(scene_observe, "get_viewport_screenshot"),
    "get_selection": _status(_attr(scene_observe, "get_selection")),
    # Scene ops
    "create_primitive": _attr(scene_ops, "create_primitive"),
    "create_empty": _attr(scene_ops, "create_empty"),
    "create_camera": _attr(scene_ops, "create_camera"),
    "create_light": _attr(scene_ops, "create_light"),
    "set_transform": _attr(scene_ops, "set_transform"),
    "select_objects": _attr(scene_ops, "select_objects"),
    "delete_objects": _attr(scene_ops, "delete_objects"),
    "duplicate_object": _attr(scene_ops, "duplicate_object"),
    "assign_material_pbr": _attr(scene_ops, "assign_material_pbr"),
    "set_world_hdri": _attr(scene_ops, "set_world_hdri"),
    "execute_blender_code": _attr(scene_ops, "execute_blender_code"),
    # Camera
    "create_composition_camera": _attr(camera, "create_composition_camera"),
    "create_isometric_camera": _attr(camera, "create_isometric_camera"),
    "set_camera_depth_of_field": _attr(camera, "set_camera_depth_of_field"),
    "apply_camera_preset": _attr(camera, "apply_camera_preset"),
    "set_active_camera": _attr(camera, "set_active_camera"),
    "list_cameras": _status(_attr(camera, "list_cameras")),
    "frame_camera_to_selection": _attr(camera, "frame_camera_to_selection"),
    # Materials
    "create_bsdf_material": _attr(materials, "create_bsdf_material"),
    "create_emission_material": _attr(materials, "create_emission_material"),
    "create_glass_material": _attr(materials, "create_glass_material"),
    "create_metal_material": _attr(materials, "create_metal_material"),
    "create_subsurface_material": _attr(materials, "create_subsurface_material"),
    "create_procedural_texture": _attr(materials, "create_procedural_texture"),
    "assign_material": _attr(materials, "assign_material"),
    "list_materials": _status(_attr(materials, "list_materials")),
    "delete_material": _attr(materials, "delete_material"),
    "create_volume_material": _attr(advanced_materials, "create_volume_material"),
    "create_layered_material": _attr(advanced_materials, "create_layered_material"),
    "create_hair_material": _attr(advanced_materials, "create_hair_material"),
    "generate_procedural_material": _attr(procedural_materials, "generate_procedural_material"),
    "ai_generate_material": _attr(procedural_materials, "ai_generate_material"),
    "create_material_variations": _attr(procedural_materials, "create_material_variations"),
    # Lighting
    "create_three_point_lighting": _attr(lighting, "create_three_point_lighting"),
    "create_studio_lighting": _attr(lighting, "create_studio_lighting"),
    "create_hdri_environment": _attr(lighting, "create_hdri_environment"),
    "create_area_light": _attr(lighting, "create_area_light"),
    "create_volumetric_lighting": _attr(lighting, "create_volumetric_lighting"),
    "adjust_light_exposure": _attr(lighting, "adjust_light_exposure"),
    "clear_lights": _status(_attr(lighting, "clear_lights")),
    "list_lights": _status(_attr(lighting, "list_lights")),
    "create_hdri_lighting_setup": _attr(lighting, "create_hdri_lighting_setup"),
    "create_volumetric_light_effect": _attr(lighting, "create_volumetric_light_effect"),
    "create_studio_light_rig": _attr(lighting, "create_studio_light_rig"),
    "setup_light_linking": _attr(lighting, "setup_light_linking"),
    # Composition
    "compose_product_shot": _attr(composition, "compose_product_shot"),
    "compose_isometric_scene": _attr(composition, "compose_isometric_scene"),
    "compose_character_scene": _attr(composition, "compose_character_scene"),
    "compose_automotive_shot": _attr(composition, "compose_automotive_shot"),
    "compose_food_shot": _attr(composition, "compose_food_shot"),
    "compose_jewelry_shot": _attr(composition, "compose_jewelry_shot"),
    "compose_architectural_shot": _attr(composition, "compose_architectural_shot"),
    "compose_studio_setup": _attr(composition, "compose_studio_setup"),
    "clear_scene": _attr(composition, "clear_scene"),
    "setup_render_settings": _attr(composition, "setup_render_settings"),
    # Export
    "export_glb": _attr(export_handler, "export_glb"),
    "render_preview": _attr(export_handler, "render_preview"),
    "export_scene_bundle": _attr(export_handler, "export_scene_bundle"),
    # Assets
    "get_polyhaven_status": _status(_attr(assets_polyhaven, "get_status")),
    "get_polyhaven_categories": _attr(assets_polyhaven, "get_categories"),
    "search_polyhaven_assets": _attr(assets_polyhaven, "search_assets"),
    "download_polyhaven_asset": _attr(assets_polyhaven, "download_asset"),
    "set_texture": _attr(assets_polyhaven, "set_texture"),
    "get_sketchfab_status": _status(_attr(assets_sketchfab, "get_status")),
    "search_sketchfab_models": _attr(assets_sketchfab, "search_models"),
    "get_sketchfab_model_preview": _attr(assets_sketchfab, "get_model_preview"),
    "download_sketchfab_model": _attr(assets_sketchfab, "download_model"),
    # Jobs
    "get_hyper3d_status": _status(_attr(jobs_hyper3d, "get_status")),
    "generate_hyper3d_model_via_text": _attr(jobs_hyper3d, "generate_via_text"),
    "generate_hyper3d_model_via_images": _attr(jobs_hyper3d, "generate_via_images"),
    "create_rodin_job": _attr(jobs_hyper3d, "create_job"),
    "poll_rodin_job_status": _attr(jobs_hyper3d, "poll_job_status"),
    "import_generated_asset": _attr(jobs_hyper3d, "import_asset"),
    "get_hunyuan3d_status": _status(_attr(jobs_hunyuan, "get_status")),
    "generate_hunyuan3d_model": _attr(jobs_hunyuan, "generate_model"),
    "create_hunyuan_job": _attr(jobs_hunyuan, "create_job"),
    "poll_hunyuan_job_status": _attr(jobs_hunyuan, "poll_job_status"),
    "import_generated_asset_hunyuan": _attr(jobs_hunyuan, "import_asset"),
    "get_tripo3d_status": _status(_attr(jobs_tripo3d, "get_status")),
    "generate_tripo3d_model": _attr(jobs_tripo3d, "generate_model"),
    "poll_tripo3d_status": _attr(jobs_tripo3d, "poll_job_status"),
    "import_tripo3d_model": _attr(jobs_tripo3d, "import_model"),
    "create_job": _create_job,
    "get_job": _get_job,
    "import_job_result": _import_job_result,
    # Rigging and animation
    "get_rigging_status": _status(_attr(rigging, "get_status")),
    "create_auto_rig": _attr(rigging, "create_auto_rig"),
    "generate_skeleton": _attr(rigging, "generate_skeleton"),
    "auto_weight_paint": _attr(rigging, "auto_weight_paint"),
    "create_control_rig": _attr(rigging, "create_control_rig"),
    "get_animation_status": _status(_attr(animation, "get_status")),
    "create_animation_layer": _attr(animation, "create_animation_layer"),
    "set_keyframe": _attr(animation, "set_keyframe"),
    "create_animation_curve": _attr(animation, "create_animation_curve"),
    "import_motion_capture": _attr(animation, "import_motion_capture"),
    "retarget_animation": _attr(animation, "retarget_animation"),
    "create_facial_animation": _attr(animation, "create_facial_animation"),
    # Atmospherics
    "get_atmospherics_status": _status(_attr(atmospherics_handler, "get_status")),
    "create_volumetric_fog": _attr(atmospherics_handler, "create_volumetric_fog"),
    "create_weather_system": _attr(atmospherics_handler, "create_weather_system"),
    "create_sky_system": _attr(atmospherics_handler, "create_sky_system"),
    "create_atmospheric_scattering": _attr(atmospherics_handler, "create_atmospheric_scattering"),
    # Production and render pipeline
    "get_production_status": _status(_attr(production, "get_status")),
    "create_shot": _attr(production, "create_shot"),
    "setup_shot_camera": _attr(production, "setup_shot_camera"),
    "create_shot_version": _attr(production, "create_shot_version"),
    "review_shot": _attr(production, "review_shot"),
    "get_render_pipeline_status": _status(_attr(render_pipeline, "get_status")),
    "create_render_job": _attr(render_pipeline, "create_render_job"),
    "monitor_render_job": _attr(render_pipeline, "monitor_render_job"),
    "optimize_render_settings": _attr(render_pipeline, "optimize_render_settings"),
    "setup_render_passes": _attr(render_pipeline, "setup_render_passes"),
    "render_animation_passes": _attr(render_pipeline, "render_animation_passes"),
    "setup_stereoscopic_render": _attr(render_pipeline, "setup_stereoscopic_render"),
    # AI creative
    "get_ai_creative_status": _status(_attr(ai_creative, "get_status")),
    "ai_scene_composition": _attr(ai_creative, "ai_scene_composition"),
    "ai_lighting_design": _attr(ai_creative, "ai_lighting_design"),
    "ai_animation_assist": _attr(ai_creative, "ai_animation_assist"),
    "ai_quality_check": _attr(ai_creative, "ai_quality_check"),
}


def dispatch_command(command_type: str, params: Dict[str, Any] | None = None) -> Any:
    try:
        handler = COMMAND_HANDLERS[command_type]
    except KeyError as exc:
        raise ValueError(f"Unknown command type: {command_type}") from exc
    return handler(params or {})
