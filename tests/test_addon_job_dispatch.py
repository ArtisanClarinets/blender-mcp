import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_addon_server(*, jobs_hyper3d, jobs_hunyuan, jobs_tripo3d):
    fake_bpy = types.SimpleNamespace(
        app=types.SimpleNamespace(
            timers=types.SimpleNamespace(
                register=lambda func, first_interval=0.0: func()
            )
        )
    )
    scene_observe = types.SimpleNamespace(
        observe_scene=Mock(),
        get_scene_hash=Mock(),
        get_scene_info=Mock(),
        get_object_info=Mock(),
        get_viewport_screenshot=Mock(),
        get_selection=Mock(),
    )
    scene_ops = types.SimpleNamespace(
        create_primitive=Mock(),
        create_empty=Mock(),
        create_camera=Mock(),
        create_light=Mock(),
        set_transform=Mock(),
        select_objects=Mock(),
        delete_objects=Mock(),
        duplicate_object=Mock(),
        assign_material_pbr=Mock(),
        set_world_hdri=Mock(),
        execute_blender_code=Mock(),
    )
    handlers_module = types.ModuleType("blender_mcp_addon.handlers")
    handlers_module.scene_observe = scene_observe
    handlers_module.scene_ops = scene_ops
    handlers_module.camera = types.SimpleNamespace()
    handlers_module.composition = types.SimpleNamespace()
    handlers_module.materials = types.SimpleNamespace()
    handlers_module.lighting = types.SimpleNamespace()
    handlers_module.export_handler = types.SimpleNamespace(
        export_glb=Mock(), render_preview=Mock(), export_scene_bundle=Mock()
    )
    handlers_module.assets_polyhaven = types.SimpleNamespace(
        get_status=Mock(),
        get_categories=Mock(),
        search_assets=Mock(),
        download_asset=Mock(),
        set_texture=Mock(),
    )
    handlers_module.assets_sketchfab = types.SimpleNamespace(
        get_status=Mock(),
        search_models=Mock(),
        get_model_preview=Mock(),
        download_model=Mock(),
    )
    handlers_module.jobs_hyper3d = jobs_hyper3d
    handlers_module.jobs_hunyuan = jobs_hunyuan
    handlers_module.jobs_tripo3d = jobs_tripo3d
    protocol = types.SimpleNamespace(
        parse_command=Mock(),
        create_error_response=Mock(),
        encode_command=Mock(),
        get_command_type=lambda command: command["type"],
        get_command_params=lambda command: command.get("params", {}),
        get_request_id=lambda command: command.get("request_id"),
        get_idempotency_key=lambda command: command.get("idempotency_key"),
        create_success_response=Mock(),
    )
    package = types.ModuleType("blender_mcp_addon")
    package.__path__ = [str(PROJECT_ROOT / "blender_mcp_addon")]

    module_name = "blender_mcp_addon.server"
    module_path = PROJECT_ROOT / "blender_mcp_addon" / "server.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    server = importlib.util.module_from_spec(spec)

    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy,
            "blender_mcp_addon": package,
            "blender_mcp_addon.protocol": protocol,
            "blender_mcp_addon.handlers": handlers_module,
            "blender_mcp_addon.handlers.scene_observe": scene_observe,
            "blender_mcp_addon.handlers.scene_ops": scene_ops,
            "blender_mcp_addon.handlers.camera": handlers_module.camera,
            "blender_mcp_addon.handlers.composition": handlers_module.composition,
            "blender_mcp_addon.handlers.materials": handlers_module.materials,
            "blender_mcp_addon.handlers.lighting": handlers_module.lighting,
            "blender_mcp_addon.handlers.export_handler": handlers_module.export_handler,
            "blender_mcp_addon.handlers.assets_polyhaven": handlers_module.assets_polyhaven,
            "blender_mcp_addon.handlers.assets_sketchfab": handlers_module.assets_sketchfab,
            "blender_mcp_addon.handlers.jobs_hyper3d": jobs_hyper3d,
            "blender_mcp_addon.handlers.jobs_hunyuan": jobs_hunyuan,
            "blender_mcp_addon.handlers.jobs_tripo3d": jobs_tripo3d,
        },
    ):
        sys.modules.pop(module_name, None)
        sys.modules[module_name] = server
        spec.loader.exec_module(server)

    return server


def _dispatch_legacy_addon_command(
    command_type, params, *, jobs_hyper3d, jobs_hunyuan, jobs_tripo3d
):
    fake_bpy_module = types.ModuleType("bpy")
    fake_bpy_module.app = types.SimpleNamespace(
        timers=types.SimpleNamespace(register=lambda func, first_interval=0.0: func())
    )
    fake_bpy_props = types.ModuleType("bpy.props")
    for property_name in (
        "StringProperty",
        "IntProperty",
        "BoolProperty",
        "EnumProperty",
        "PointerProperty",
    ):
        setattr(fake_bpy_props, property_name, lambda **_kwargs: None)
    fake_bpy_types = types.ModuleType("bpy.types")
    fake_bpy_types.Panel = object
    fake_bpy_types.Operator = object
    fake_bpy_types.PropertyGroup = object
    fake_bpy_types.AddonPreferences = object
    fake_bpy_module.props = fake_bpy_props
    fake_bpy_module.types = fake_bpy_types

    package_module = types.ModuleType("blender_mcp_addon")
    handlers_module = types.ModuleType("blender_mcp_addon.handlers")
    handlers_module.camera = types.SimpleNamespace()
    handlers_module.composition = types.SimpleNamespace()
    handlers_module.materials = types.SimpleNamespace()
    handlers_module.lighting = types.SimpleNamespace()
    handlers_module.jobs_hyper3d = jobs_hyper3d
    handlers_module.jobs_hunyuan = jobs_hunyuan
    handlers_module.jobs_tripo3d = jobs_tripo3d
    package_module.handlers = handlers_module

    addon_module_name = "test_legacy_addon_jobs"
    addon_module_path = PROJECT_ROOT / "addon.py"
    spec = importlib.util.spec_from_file_location(addon_module_name, addon_module_path)
    addon = importlib.util.module_from_spec(spec)

    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy_module,
            "bpy.props": fake_bpy_props,
            "bpy.types": fake_bpy_types,
            "requests": types.ModuleType("requests"),
            "blender_mcp_addon": package_module,
            "blender_mcp_addon.handlers": handlers_module,
        },
    ):
        sys.modules.pop(addon_module_name, None)
        spec.loader.exec_module(addon)
        return addon.BlenderMCPServer()._dispatch_command(command_type, params)


def _load_legacy_addon_without_handlers():
    fake_bpy_module = types.ModuleType("bpy")
    fake_bpy_module.app = types.SimpleNamespace(
        timers=types.SimpleNamespace(register=lambda func, first_interval=0.0: func())
    )
    fake_bpy_props = types.ModuleType("bpy.props")
    for property_name in (
        "StringProperty",
        "IntProperty",
        "BoolProperty",
        "EnumProperty",
        "PointerProperty",
    ):
        setattr(fake_bpy_props, property_name, lambda **_kwargs: None)
    fake_bpy_types = types.ModuleType("bpy.types")
    fake_bpy_types.Panel = object
    fake_bpy_types.Operator = object
    fake_bpy_types.PropertyGroup = object
    fake_bpy_types.AddonPreferences = object
    fake_bpy_module.props = fake_bpy_props
    fake_bpy_module.types = fake_bpy_types

    addon_module_name = "test_legacy_addon_jobs_no_handlers"
    addon_module_path = PROJECT_ROOT / "addon.py"
    spec = importlib.util.spec_from_file_location(addon_module_name, addon_module_path)
    addon = importlib.util.module_from_spec(spec)

    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy_module,
            "bpy.props": fake_bpy_props,
            "bpy.types": fake_bpy_types,
            "requests": types.ModuleType("requests"),
        },
    ):
        sys.modules.pop(addon_module_name, None)
        spec.loader.exec_module(addon)
        return addon


def test_server_dispatch_routes_tripo3d_and_unified_jobs():
    jobs_hyper3d = types.SimpleNamespace(
        get_status=Mock(),
        generate_via_text=Mock(),
        generate_via_images=Mock(),
        poll_job_status=Mock(),
        import_asset=Mock(),
        create_job=Mock(),
        get_job=Mock(return_value=None),
        import_job_result=Mock(),
    )
    jobs_hunyuan = types.SimpleNamespace(
        get_status=Mock(),
        generate_model=Mock(),
        poll_job_status=Mock(),
        import_asset=Mock(),
        create_job=Mock(),
        get_job=Mock(return_value=None),
        import_job_result=Mock(),
    )
    jobs_tripo3d = types.SimpleNamespace(
        get_status=Mock(return_value={"enabled": True}),
        generate_model=Mock(return_value={"task_id": "job_tripo"}),
        poll_job_status=Mock(return_value={"status": "completed"}),
        import_model=Mock(return_value={"status": "success", "name": "Robot"}),
        create_job=Mock(return_value={"job_id": "job_tripo", "provider": "tripo3d"}),
        get_job=Mock(return_value={"job_id": "job_tripo", "provider": "tripo3d"}),
        import_job_result=Mock(
            return_value={"status": "success", "job_id": "job_tripo"}
        ),
    )
    server = _load_addon_server(
        jobs_hyper3d=jobs_hyper3d,
        jobs_hunyuan=jobs_hunyuan,
        jobs_tripo3d=jobs_tripo3d,
    )

    status_result = server.BlenderMCPServer()._dispatch_command(
        "get_tripo3d_status", {}
    )
    poll_result = server.BlenderMCPServer()._dispatch_command(
        "poll_tripo3d_status", {"task_id": "job_tripo"}
    )
    import_model_result = server.BlenderMCPServer()._dispatch_command(
        "import_tripo3d_model",
        {"model_url": "memory://tripo3d/job_tripo.glb", "name": "Robot"},
    )
    job_result = server.BlenderMCPServer()._dispatch_command(
        "create_job",
        {"provider": "tripo3d", "payload": {"text_prompt": "robot"}},
    )
    import_result = server.BlenderMCPServer()._dispatch_command(
        "import_job_result",
        {"job_id": "job_tripo", "name": "Robot"},
    )

    assert status_result == {"enabled": True}
    assert poll_result == {"status": "completed"}
    assert import_model_result == {"status": "success", "name": "Robot"}
    assert job_result == {"job_id": "job_tripo", "provider": "tripo3d"}
    assert import_result == {"status": "success", "job_id": "job_tripo"}
    jobs_tripo3d.get_status.assert_called_once_with()
    jobs_tripo3d.poll_job_status.assert_called_once_with({"task_id": "job_tripo"})
    jobs_tripo3d.import_model.assert_called_once_with(
        {"model_url": "memory://tripo3d/job_tripo.glb", "name": "Robot"}
    )
    jobs_tripo3d.create_job.assert_called_once_with({"text_prompt": "robot"})
    jobs_tripo3d.get_job.assert_called_once_with(
        {"job_id": "job_tripo", "name": "Robot"}
    )
    jobs_tripo3d.import_job_result.assert_called_once_with(
        {"job_id": "job_tripo", "name": "Robot"}
    )


def test_server_dispatch_get_job_uses_unified_provider_lookup_order():
    jobs_hyper3d = types.SimpleNamespace(get_job=Mock(return_value=None))
    jobs_hunyuan = types.SimpleNamespace(
        get_job=Mock(
            return_value={
                "job_id": "job_hunyuan",
                "provider": "hunyuan3d",
                "status": "DONE",
            }
        )
    )
    jobs_tripo3d = types.SimpleNamespace(get_job=Mock(return_value=None))
    server = _load_addon_server(
        jobs_hyper3d=jobs_hyper3d,
        jobs_hunyuan=jobs_hunyuan,
        jobs_tripo3d=jobs_tripo3d,
    )

    result = server.BlenderMCPServer()._dispatch_command(
        "get_job", {"job_id": "job_hunyuan"}
    )

    assert result == {
        "job_id": "job_hunyuan",
        "provider": "hunyuan3d",
        "status": "DONE",
    }
    jobs_hyper3d.get_job.assert_called_once_with({"job_id": "job_hunyuan"})
    jobs_hunyuan.get_job.assert_called_once_with({"job_id": "job_hunyuan"})
    jobs_tripo3d.get_job.assert_not_called()


def test_legacy_addon_dispatch_routes_tripo3d_and_unified_jobs_to_handlers():
    jobs_hyper3d = types.SimpleNamespace(
        create_job=Mock(), get_job=Mock(return_value=None), import_job_result=Mock()
    )
    jobs_hunyuan = types.SimpleNamespace(
        create_job=Mock(), get_job=Mock(return_value=None), import_job_result=Mock()
    )
    jobs_tripo3d = types.SimpleNamespace(
        get_status=Mock(return_value={"enabled": True}),
        generate_model=Mock(return_value={"task_id": "job_tripo"}),
        poll_job_status=Mock(return_value={"status": "completed"}),
        import_model=Mock(return_value={"status": "success", "name": "Robot"}),
        create_job=Mock(return_value={"job_id": "job_tripo", "provider": "tripo3d"}),
        get_job=Mock(return_value={"job_id": "job_tripo", "provider": "tripo3d"}),
        import_job_result=Mock(
            return_value={"status": "success", "job_id": "job_tripo"}
        ),
    )

    status_result = _dispatch_legacy_addon_command(
        "get_tripo3d_status",
        {},
        jobs_hyper3d=jobs_hyper3d,
        jobs_hunyuan=jobs_hunyuan,
        jobs_tripo3d=jobs_tripo3d,
    )
    generate_result = _dispatch_legacy_addon_command(
        "generate_tripo3d_model",
        {"text_prompt": "robot"},
        jobs_hyper3d=jobs_hyper3d,
        jobs_hunyuan=jobs_hunyuan,
        jobs_tripo3d=jobs_tripo3d,
    )
    poll_result = _dispatch_legacy_addon_command(
        "poll_tripo3d_status",
        {"task_id": "job_tripo"},
        jobs_hyper3d=jobs_hyper3d,
        jobs_hunyuan=jobs_hunyuan,
        jobs_tripo3d=jobs_tripo3d,
    )
    import_model_result = _dispatch_legacy_addon_command(
        "import_tripo3d_model",
        {"model_url": "memory://tripo3d/job_tripo.glb", "name": "Robot"},
        jobs_hyper3d=jobs_hyper3d,
        jobs_hunyuan=jobs_hunyuan,
        jobs_tripo3d=jobs_tripo3d,
    )
    job_result = _dispatch_legacy_addon_command(
        "create_job",
        {"provider": "tripo3d", "payload": {"text_prompt": "robot"}},
        jobs_hyper3d=jobs_hyper3d,
        jobs_hunyuan=jobs_hunyuan,
        jobs_tripo3d=jobs_tripo3d,
    )

    assert status_result == {"enabled": True}
    assert generate_result == {"task_id": "job_tripo"}
    assert poll_result == {"status": "completed"}
    assert import_model_result == {"status": "success", "name": "Robot"}
    assert job_result == {"job_id": "job_tripo", "provider": "tripo3d"}
    jobs_tripo3d.get_status.assert_called_once_with()
    jobs_tripo3d.generate_model.assert_called_once_with({"text_prompt": "robot"})
    jobs_tripo3d.poll_job_status.assert_called_once_with({"task_id": "job_tripo"})
    jobs_tripo3d.import_model.assert_called_once_with(
        {"model_url": "memory://tripo3d/job_tripo.glb", "name": "Robot"}
    )
    jobs_tripo3d.create_job.assert_called_once_with({"text_prompt": "robot"})


def test_legacy_addon_dispatch_get_job_uses_unified_provider_lookup_order():
    jobs_hyper3d = types.SimpleNamespace(get_job=Mock(return_value=None))
    jobs_hunyuan = types.SimpleNamespace(
        get_job=Mock(
            return_value={
                "job_id": "job_hunyuan",
                "provider": "hunyuan3d",
                "status": "DONE",
            }
        )
    )
    jobs_tripo3d = types.SimpleNamespace(get_job=Mock(return_value=None))

    result = _dispatch_legacy_addon_command(
        "get_job",
        {"job_id": "job_hunyuan"},
        jobs_hyper3d=jobs_hyper3d,
        jobs_hunyuan=jobs_hunyuan,
        jobs_tripo3d=jobs_tripo3d,
    )

    assert result == {
        "job_id": "job_hunyuan",
        "provider": "hunyuan3d",
        "status": "DONE",
    }
    jobs_hyper3d.get_job.assert_called_once_with({"job_id": "job_hunyuan"})
    jobs_hunyuan.get_job.assert_called_once_with({"job_id": "job_hunyuan"})
    jobs_tripo3d.get_job.assert_not_called()


def test_legacy_addon_fallback_create_job_validates_missing_provider_inputs():
    addon = _load_legacy_addon_without_handlers()
    server = addon.BlenderMCPServer()

    with pytest.raises(
        ValueError,
        match="text_prompt, input_image_paths, or input_image_urls is required",
    ):
        server._dispatch_command("create_job", {"provider": "hyper3d", "payload": {}})

    with pytest.raises(ValueError, match="text_prompt or input_image_url is required"):
        server._dispatch_command("create_job", {"provider": "hunyuan3d", "payload": {}})


def test_legacy_addon_fallback_routes_provider_specific_hyper3d_commands():
    addon = _load_legacy_addon_without_handlers()
    addon.APIManager.get_hyper3d_config = staticmethod(
        lambda: {"enabled": True, "api_key": "secret", "mode": "fal"}
    )

    server = addon.BlenderMCPServer()
    status_result = server._dispatch_command("get_hyper3d_status", {})
    generate_result = server._dispatch_command(
        "generate_hyper3d_model_via_text", {"text_prompt": "robot"}
    )
    poll_result = server._dispatch_command(
        "poll_rodin_job_status", {"request_id": generate_result["request_id"]}
    )
    import_result = server._dispatch_command(
        "import_generated_asset",
        {"name": "Robot", "request_id": generate_result["request_id"]},
    )

    assert status_result == {
        "enabled": True,
        "has_api_key": True,
        "mode": "fal",
        "message": "Hyper3D (fal) ready",
        "api_available": True,
        "modes": ["MAIN_SITE", "FAL_AI"],
    }
    assert generate_result["status"] == "IN_QUEUE"
    assert poll_result["status"] == "COMPLETED"
    assert poll_result["request_id"] == generate_result["request_id"]
    assert import_result == {
        "status": "success",
        "provider": "hyper3d",
        "name": "Robot",
        "imported": True,
        "imported_objects": ["Robot"],
        "deferred_import": True,
        "job_id": generate_result["job_id"],
        "source": poll_result["model_url"],
        "request_id": generate_result["request_id"],
        "task_uuid": generate_result["job_id"],
        "model_url": poll_result["model_url"],
    }


def test_legacy_addon_fallback_routes_provider_specific_hunyuan_commands():
    addon = _load_legacy_addon_without_handlers()
    addon.APIManager.get_hunyuan3d_config = staticmethod(
        lambda: {
            "enabled": True,
            "mode": "local",
            "api_key": "secret",
            "local_path": "C:/models/hunyuan",
        }
    )

    server = addon.BlenderMCPServer()
    status_result = server._dispatch_command("get_hunyuan3d_status", {})
    generate_result = server._dispatch_command(
        "generate_hunyuan3d_model", {"input_image_url": "memory://reference.png"}
    )
    poll_result = server._dispatch_command(
        "poll_hunyuan_job_status", {"job_id": generate_result["job_id"]}
    )
    import_result = server._dispatch_command(
        "import_generated_asset_hunyuan",
        {"name": "Vase", "zip_file_url": poll_result["zip_file_url"]},
    )

    assert status_result == {
        "enabled": True,
        "mode": "local",
        "has_api_key": True,
        "has_local_path": True,
        "message": "Hunyuan3D (local) ready",
        "api_available": True,
    }
    assert generate_result == {
        "job_id": generate_result["job_id"],
        "status": "RUN",
        "message": "Generation job created",
    }
    assert poll_result["status"] == "DONE"
    assert import_result == {
        "status": "success",
        "provider": "hunyuan3d",
        "name": "Vase",
        "imported": True,
        "imported_objects": ["Vase"],
        "deferred_import": True,
        "source": poll_result["zip_file_url"],
        "zip_file_url": poll_result["zip_file_url"],
    }
