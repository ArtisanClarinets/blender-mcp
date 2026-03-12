import importlib
import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class _DummyFastMCP:
    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def tool():
        return lambda func: func

    @staticmethod
    def prompt():
        return lambda func: func

    def run(self):
        return None


class _FakeSocket:
    def __init__(self, responses):
        self.responses = list(responses)
        self.sent_payloads = []
        self.timeout = None

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendall(self, payload):
        self.sent_payloads.append(payload)

    def recv(self, _buffer_size):
        if self.responses:
            return self.responses.pop(0)
        return b""


def _load_server_module():
    fastmcp_module = types.ModuleType("mcp.server.fastmcp")
    fastmcp_module.FastMCP = _DummyFastMCP
    fastmcp_module.Context = object
    fastmcp_module.Image = object

    telemetry_module = types.ModuleType("blender_mcp.telemetry")
    telemetry_module.record_startup = lambda: None
    telemetry_module.get_telemetry = lambda: None

    decorator_module = types.ModuleType("blender_mcp.telemetry_decorator")
    decorator_module.telemetry_tool = lambda _name: lambda func: func

    with patch.dict(
        sys.modules,
        {
            "mcp.server.fastmcp": fastmcp_module,
            "blender_mcp.telemetry": telemetry_module,
            "blender_mcp.telemetry_decorator": decorator_module,
        },
    ):
        sys.modules.pop("blender_mcp.server", None)
        return importlib.import_module("blender_mcp.server")


def _load_addon_server(
    *,
    lighting_module=None,
    materials_module=None,
    camera_module=None,
    composition_module=None,
):
    fake_bpy = types.SimpleNamespace(
        app=types.SimpleNamespace(
            timers=types.SimpleNamespace(
                register=lambda func, first_interval=0.0: func()
            )
        )
    )
    materials_module = materials_module or types.SimpleNamespace()
    lighting_module = lighting_module or types.SimpleNamespace()
    camera_module = camera_module or types.SimpleNamespace()
    composition_module = composition_module or types.SimpleNamespace()
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
    export_handler = types.SimpleNamespace(
        export_glb=Mock(),
        render_preview=Mock(),
        export_scene_bundle=Mock(),
    )
    assets_polyhaven = types.SimpleNamespace(
        get_status=Mock(),
        get_categories=Mock(),
        search_assets=Mock(),
        download_asset=Mock(),
        set_texture=Mock(),
    )
    assets_sketchfab = types.SimpleNamespace(
        get_status=Mock(),
        search_models=Mock(),
        get_model_preview=Mock(),
        download_model=Mock(),
    )
    jobs_hyper3d = types.SimpleNamespace(
        get_status=Mock(),
        generate_via_text=Mock(),
        generate_via_images=Mock(),
        poll_job_status=Mock(),
        import_asset=Mock(),
        create_job=Mock(),
        get_job=Mock(),
        import_job_result=Mock(),
    )
    jobs_hunyuan = types.SimpleNamespace(
        get_status=Mock(),
        generate_model=Mock(),
        poll_job_status=Mock(),
        import_asset=Mock(),
        create_job=Mock(),
        get_job=Mock(return_value=None),
        import_job_result=Mock(return_value=None),
    )
    jobs_tripo3d = types.SimpleNamespace(
        get_status=Mock(),
        generate_model=Mock(),
        poll_job_status=Mock(),
        import_model=Mock(),
        create_job=Mock(),
        get_job=Mock(return_value=None),
        import_job_result=Mock(return_value=None),
    )
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

    handlers_module = types.ModuleType("blender_mcp_addon.handlers")
    handlers_module.scene_observe = scene_observe
    handlers_module.scene_ops = scene_ops
    handlers_module.camera = camera_module
    handlers_module.composition = composition_module
    handlers_module.materials = materials_module
    handlers_module.lighting = lighting_module
    handlers_module.export_handler = export_handler
    handlers_module.assets_polyhaven = assets_polyhaven
    handlers_module.assets_sketchfab = assets_sketchfab
    handlers_module.jobs_hyper3d = jobs_hyper3d
    handlers_module.jobs_hunyuan = jobs_hunyuan
    handlers_module.jobs_tripo3d = jobs_tripo3d

    package = types.ModuleType("blender_mcp_addon")
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "blender_mcp_addon")]

    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy,
            "blender_mcp_addon": package,
            "blender_mcp_addon.protocol": protocol,
            "blender_mcp_addon.handlers": handlers_module,
            "blender_mcp_addon.handlers.scene_observe": scene_observe,
            "blender_mcp_addon.handlers.scene_ops": scene_ops,
            "blender_mcp_addon.handlers.camera": camera_module,
            "blender_mcp_addon.handlers.composition": composition_module,
            "blender_mcp_addon.handlers.materials": materials_module,
            "blender_mcp_addon.handlers.lighting": lighting_module,
            "blender_mcp_addon.handlers.export_handler": export_handler,
            "blender_mcp_addon.handlers.assets_polyhaven": assets_polyhaven,
            "blender_mcp_addon.handlers.assets_sketchfab": assets_sketchfab,
            "blender_mcp_addon.handlers.jobs_hyper3d": jobs_hyper3d,
            "blender_mcp_addon.handlers.jobs_hunyuan": jobs_hunyuan,
            "blender_mcp_addon.handlers.jobs_tripo3d": jobs_tripo3d,
        },
    ):
        module_name = "blender_mcp_addon.server"
        module_path = (
            Path(__file__).resolve().parents[1] / "blender_mcp_addon" / "server.py"
        )
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        server = importlib.util.module_from_spec(spec)
        sys.modules.pop(module_name, None)
        sys.modules[module_name] = server
        spec.loader.exec_module(server)

    return server


def _dispatch_legacy_addon_command(
    command_type,
    params,
    *,
    lighting_handlers=None,
    material_handlers=None,
    camera_handlers=None,
    composition_handlers=None,
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
    handlers_module.camera = camera_handlers or types.SimpleNamespace()
    handlers_module.composition = composition_handlers or types.SimpleNamespace()
    handlers_module.materials = material_handlers or types.SimpleNamespace()
    handlers_module.lighting = lighting_handlers or types.SimpleNamespace()
    package_module.handlers = handlers_module

    addon_module_name = "test_legacy_addon"
    addon_module_path = Path(__file__).resolve().parents[1] / "addon.py"
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

        result = addon.BlenderMCPServer()._dispatch_command(command_type, params)

    return result


def test_send_command_uses_newline_delimited_json_and_request_id():
    server = _load_server_module()
    fake_socket = _FakeSocket(
        [b'{"ok": true, "request_id": "req-123", ', b'"data": {"material": "Glass"}}\n']
    )
    connection = server.BlenderConnection(host="localhost", port=9876, sock=fake_socket)

    with patch.object(
        server.uuid, "uuid4", return_value=types.SimpleNamespace(hex="req-123")
    ):
        result = connection.send_command("create_glass_material", {"name": "Glass"})

    assert result == {"material": "Glass"}
    sent_command = json.loads(fake_socket.sent_payloads[0].decode("utf-8"))
    assert fake_socket.sent_payloads[0].endswith(b"\n")
    assert sent_command == {
        "type": "create_glass_material",
        "params": {"name": "Glass"},
        "request_id": "req-123",
    }


def test_send_command_supports_legacy_result_envelope():
    server = _load_server_module()
    fake_socket = _FakeSocket(
        [b'{"status": "success", "result": {"material": "Legacy"}}\n']
    )
    connection = server.BlenderConnection(host="localhost", port=9876, sock=fake_socket)

    with patch.object(
        server.uuid, "uuid4", return_value=types.SimpleNamespace(hex="req-legacy")
    ):
        result = connection.send_command("create_metal_material", {"name": "Legacy"})

    assert result == {"material": "Legacy"}


def test_send_command_preserves_open_circuit_message_before_socket_connect():
    server = _load_server_module()
    connection = server.BlenderConnection(host="localhost", port=9876)

    with (
        patch.object(connection, "connect", return_value=False),
        patch.object(connection.circuit_breaker, "allow_request", return_value=False),
    ):
        with pytest.raises(ConnectionError, match=server.CIRCUIT_BREAKER_OPEN_MESSAGE):
            connection.send_command("get_scene_info")


def test_command_param_logging_summary_redacts_sensitive_values():
    server = _load_server_module()

    summary = server._summarize_command_params_for_logging(
        {
            "code": "print('secret')\n" * 30,
            "input_image_paths": [
                r"C:\\Users\\tester\\secret\\reference.png",
                r"D:\\assets\\folder\\another.jpg",
            ],
            "image_data": "QUFBQ" * 40,
            "note": "keep me visible",
        }
    )

    assert summary["code"] == {"type": "code", "length": 480}
    assert summary["input_image_paths"] == [
        {"type": "path", "name": "reference.png"},
        {"type": "path", "name": "another.jpg"},
    ]
    assert summary["image_data"] == {"type": "base64", "length": 200}
    assert summary["note"] == "keep me visible"


def test_addon_dispatch_routes_glass_material_command():
    fake_bpy = types.SimpleNamespace(
        app=types.SimpleNamespace(
            timers=types.SimpleNamespace(
                register=lambda func, first_interval=0.0: func()
            )
        )
    )
    materials_module = types.SimpleNamespace(
        create_glass_material=Mock(return_value={"status": "success"})
    )
    camera_module = types.SimpleNamespace()
    composition_module = types.SimpleNamespace()
    lighting_module = types.SimpleNamespace()
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
    export_handler = types.SimpleNamespace(
        export_glb=Mock(),
        render_preview=Mock(),
        export_scene_bundle=Mock(),
    )
    assets_polyhaven = types.SimpleNamespace(
        get_status=Mock(),
        get_categories=Mock(),
        search_assets=Mock(),
        download_asset=Mock(),
        set_texture=Mock(),
    )
    assets_sketchfab = types.SimpleNamespace(
        get_status=Mock(),
        search_models=Mock(),
        get_model_preview=Mock(),
        download_model=Mock(),
    )
    jobs_hyper3d = types.SimpleNamespace(
        get_status=Mock(),
        generate_via_text=Mock(),
        generate_via_images=Mock(),
        poll_job_status=Mock(),
        import_asset=Mock(),
        create_job=Mock(),
        get_job=Mock(),
        import_job_result=Mock(),
    )
    jobs_hunyuan = types.SimpleNamespace(
        get_status=Mock(),
        generate_model=Mock(),
        poll_job_status=Mock(),
        import_asset=Mock(),
        create_job=Mock(),
        get_job=Mock(return_value=None),
        import_job_result=Mock(return_value=None),
    )
    jobs_tripo3d = types.SimpleNamespace(
        get_status=Mock(),
        generate_model=Mock(),
        poll_job_status=Mock(),
        import_model=Mock(),
        create_job=Mock(),
        get_job=Mock(return_value=None),
        import_job_result=Mock(return_value=None),
    )
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

    handlers_module = types.ModuleType("blender_mcp_addon.handlers")
    handlers_module.scene_observe = scene_observe
    handlers_module.scene_ops = scene_ops
    handlers_module.camera = camera_module
    handlers_module.composition = composition_module
    handlers_module.materials = materials_module
    handlers_module.lighting = lighting_module
    handlers_module.export_handler = export_handler
    handlers_module.assets_polyhaven = assets_polyhaven
    handlers_module.assets_sketchfab = assets_sketchfab
    handlers_module.jobs_hyper3d = jobs_hyper3d
    handlers_module.jobs_hunyuan = jobs_hunyuan
    handlers_module.jobs_tripo3d = jobs_tripo3d

    package = types.ModuleType("blender_mcp_addon")
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "blender_mcp_addon")]

    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy,
            "blender_mcp_addon": package,
            "blender_mcp_addon.protocol": protocol,
            "blender_mcp_addon.handlers": handlers_module,
            "blender_mcp_addon.handlers.scene_observe": scene_observe,
            "blender_mcp_addon.handlers.scene_ops": scene_ops,
            "blender_mcp_addon.handlers.camera": camera_module,
            "blender_mcp_addon.handlers.composition": composition_module,
            "blender_mcp_addon.handlers.materials": materials_module,
            "blender_mcp_addon.handlers.lighting": lighting_module,
            "blender_mcp_addon.handlers.export_handler": export_handler,
            "blender_mcp_addon.handlers.assets_polyhaven": assets_polyhaven,
            "blender_mcp_addon.handlers.assets_sketchfab": assets_sketchfab,
            "blender_mcp_addon.handlers.jobs_hyper3d": jobs_hyper3d,
            "blender_mcp_addon.handlers.jobs_hunyuan": jobs_hunyuan,
            "blender_mcp_addon.handlers.jobs_tripo3d": jobs_tripo3d,
        },
    ):
        module_name = "blender_mcp_addon.server"
        module_path = (
            Path(__file__).resolve().parents[1] / "blender_mcp_addon" / "server.py"
        )
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        server = importlib.util.module_from_spec(spec)
        sys.modules.pop(module_name, None)
        sys.modules[module_name] = server
        spec.loader.exec_module(server)

    result = server.BlenderMCPServer()._dispatch_command(
        "create_glass_material", {"name": "GlassMaterial"}
    )

    assert result == {"status": "success"}
    materials_module.create_glass_material.assert_called_once_with(
        {"name": "GlassMaterial"}
    )


def test_addon_dispatch_routes_area_light_command():
    fake_bpy = types.SimpleNamespace(
        app=types.SimpleNamespace(
            timers=types.SimpleNamespace(
                register=lambda func, first_interval=0.0: func()
            )
        )
    )
    materials_module = types.SimpleNamespace()
    camera_module = types.SimpleNamespace()
    composition_module = types.SimpleNamespace()
    lighting_module = types.SimpleNamespace(
        create_area_light=Mock(return_value={"status": "success", "type": "area"})
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
    export_handler = types.SimpleNamespace(
        export_glb=Mock(),
        render_preview=Mock(),
        export_scene_bundle=Mock(),
    )
    assets_polyhaven = types.SimpleNamespace(
        get_status=Mock(),
        get_categories=Mock(),
        search_assets=Mock(),
        download_asset=Mock(),
        set_texture=Mock(),
    )
    assets_sketchfab = types.SimpleNamespace(
        get_status=Mock(),
        search_models=Mock(),
        get_model_preview=Mock(),
        download_model=Mock(),
    )
    jobs_hyper3d = types.SimpleNamespace(
        get_status=Mock(),
        generate_via_text=Mock(),
        generate_via_images=Mock(),
        poll_job_status=Mock(),
        import_asset=Mock(),
        create_job=Mock(),
        get_job=Mock(),
        import_job_result=Mock(),
    )
    jobs_hunyuan = types.SimpleNamespace(
        get_status=Mock(),
        generate_model=Mock(),
        poll_job_status=Mock(),
        import_asset=Mock(),
        create_job=Mock(),
        get_job=Mock(return_value=None),
        import_job_result=Mock(return_value=None),
    )
    jobs_tripo3d = types.SimpleNamespace(
        get_status=Mock(),
        generate_model=Mock(),
        poll_job_status=Mock(),
        import_model=Mock(),
        create_job=Mock(),
        get_job=Mock(return_value=None),
        import_job_result=Mock(return_value=None),
    )
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

    handlers_module = types.ModuleType("blender_mcp_addon.handlers")
    handlers_module.scene_observe = scene_observe
    handlers_module.scene_ops = scene_ops
    handlers_module.camera = camera_module
    handlers_module.composition = composition_module
    handlers_module.materials = materials_module
    handlers_module.lighting = lighting_module
    handlers_module.export_handler = export_handler
    handlers_module.assets_polyhaven = assets_polyhaven
    handlers_module.assets_sketchfab = assets_sketchfab
    handlers_module.jobs_hyper3d = jobs_hyper3d
    handlers_module.jobs_hunyuan = jobs_hunyuan
    handlers_module.jobs_tripo3d = jobs_tripo3d

    package = types.ModuleType("blender_mcp_addon")
    package.__path__ = [str(Path(__file__).resolve().parents[1] / "blender_mcp_addon")]

    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy,
            "blender_mcp_addon": package,
            "blender_mcp_addon.protocol": protocol,
            "blender_mcp_addon.handlers": handlers_module,
            "blender_mcp_addon.handlers.scene_observe": scene_observe,
            "blender_mcp_addon.handlers.scene_ops": scene_ops,
            "blender_mcp_addon.handlers.camera": camera_module,
            "blender_mcp_addon.handlers.composition": composition_module,
            "blender_mcp_addon.handlers.materials": materials_module,
            "blender_mcp_addon.handlers.lighting": lighting_module,
            "blender_mcp_addon.handlers.export_handler": export_handler,
            "blender_mcp_addon.handlers.assets_polyhaven": assets_polyhaven,
            "blender_mcp_addon.handlers.assets_sketchfab": assets_sketchfab,
            "blender_mcp_addon.handlers.jobs_hyper3d": jobs_hyper3d,
            "blender_mcp_addon.handlers.jobs_hunyuan": jobs_hunyuan,
            "blender_mcp_addon.handlers.jobs_tripo3d": jobs_tripo3d,
        },
    ):
        module_name = "blender_mcp_addon.server"
        module_path = (
            Path(__file__).resolve().parents[1] / "blender_mcp_addon" / "server.py"
        )
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        server = importlib.util.module_from_spec(spec)
        sys.modules.pop(module_name, None)
        sys.modules[module_name] = server
        spec.loader.exec_module(server)

    result = server.BlenderMCPServer()._dispatch_command(
        "create_area_light", {"name": "SoftBox"}
    )

    assert result == {"status": "success", "type": "area"}
    lighting_module.create_area_light.assert_called_once_with({"name": "SoftBox"})


def test_addon_dispatch_routes_additional_lighting_commands():
    lighting_module = types.SimpleNamespace(
        create_three_point_lighting=Mock(
            return_value={"status": "success", "preset": "three_point"}
        ),
        adjust_light_exposure=Mock(
            return_value={"status": "success", "exposure": 1.25, "gamma": 0.95}
        ),
        list_lights=Mock(return_value={"lights": [{"name": "Key"}], "count": 1}),
        clear_lights=Mock(return_value={"status": "success", "removed_count": 2}),
    )
    server = _load_addon_server(lighting_module=lighting_module)

    three_point_result = server.BlenderMCPServer()._dispatch_command(
        "create_three_point_lighting", {"key_intensity": 1200.0}
    )
    exposure_result = server.BlenderMCPServer()._dispatch_command(
        "adjust_light_exposure", {"exposure": 1.25, "gamma": 0.95}
    )
    list_result = server.BlenderMCPServer()._dispatch_command("list_lights", {})
    clear_result = server.BlenderMCPServer()._dispatch_command("clear_lights", {})

    assert three_point_result == {"status": "success", "preset": "three_point"}
    assert exposure_result == {
        "status": "success",
        "exposure": 1.25,
        "gamma": 0.95,
    }
    assert list_result == {"lights": [{"name": "Key"}], "count": 1}
    assert clear_result == {"status": "success", "removed_count": 2}
    lighting_module.create_three_point_lighting.assert_called_once_with(
        {"key_intensity": 1200.0}
    )
    lighting_module.adjust_light_exposure.assert_called_once_with(
        {"exposure": 1.25, "gamma": 0.95}
    )
    lighting_module.list_lights.assert_called_once_with()
    lighting_module.clear_lights.assert_called_once_with()


def test_addon_dispatch_routes_camera_commands():
    camera_module = types.SimpleNamespace(
        create_composition_camera=Mock(
            return_value={"status": "success", "name": "HeroCam"}
        ),
        apply_camera_preset=Mock(
            return_value={"status": "success", "preset": "portrait"}
        ),
        list_cameras=Mock(return_value={"count": 1, "active_camera": "HeroCam"}),
    )
    server = _load_addon_server(camera_module=camera_module)

    create_result = server.BlenderMCPServer()._dispatch_command(
        "create_composition_camera", {"name": "HeroCam"}
    )
    preset_result = server.BlenderMCPServer()._dispatch_command(
        "apply_camera_preset", {"camera_name": "HeroCam", "preset": "portrait"}
    )
    list_result = server.BlenderMCPServer()._dispatch_command("list_cameras", {})

    assert create_result == {"status": "success", "name": "HeroCam"}
    assert preset_result == {"status": "success", "preset": "portrait"}
    assert list_result == {"count": 1, "active_camera": "HeroCam"}
    camera_module.create_composition_camera.assert_called_once_with({"name": "HeroCam"})
    camera_module.apply_camera_preset.assert_called_once_with(
        {"camera_name": "HeroCam", "preset": "portrait"}
    )
    camera_module.list_cameras.assert_called_once_with()


def test_addon_dispatch_routes_composition_commands():
    composition_module = types.SimpleNamespace(
        compose_product_shot=Mock(
            return_value={"status": "success", "preset": "product_shot"}
        ),
        compose_isometric_scene=Mock(
            return_value={"status": "success", "preset": "isometric"}
        ),
        compose_character_scene=Mock(
            return_value={"status": "success", "preset": "character"}
        ),
        compose_automotive_shot=Mock(
            return_value={"status": "success", "preset": "automotive"}
        ),
        compose_food_shot=Mock(return_value={"status": "success", "preset": "food"}),
        compose_jewelry_shot=Mock(
            return_value={"status": "success", "preset": "jewelry"}
        ),
        compose_architectural_shot=Mock(
            return_value={"status": "success", "preset": "architectural"}
        ),
        compose_studio_setup=Mock(
            return_value={"status": "success", "preset": "studio"}
        ),
        clear_scene=Mock(return_value={"status": "success", "removed_count": 2}),
        setup_render_settings=Mock(
            return_value={"status": "success", "engine": "CYCLES"}
        ),
    )
    server = _load_addon_server(composition_module=composition_module)

    product_result = server.BlenderMCPServer()._dispatch_command(
        "compose_product_shot", {"product_name": "Bottle"}
    )
    isometric_result = server.BlenderMCPServer()._dispatch_command(
        "compose_isometric_scene", {"grid_size": 12.0}
    )
    character_result = server.BlenderMCPServer()._dispatch_command(
        "compose_character_scene", {"character_name": "Hero", "environment": "night"}
    )
    automotive_result = server.BlenderMCPServer()._dispatch_command(
        "compose_automotive_shot", {"car_name": "Coupe", "angle": "side"}
    )
    food_result = server.BlenderMCPServer()._dispatch_command(
        "compose_food_shot", {"style": "angled"}
    )
    jewelry_result = server.BlenderMCPServer()._dispatch_command(
        "compose_jewelry_shot", {"style": "catalog", "reflections": False}
    )
    architectural_result = server.BlenderMCPServer()._dispatch_command(
        "compose_architectural_shot", {"interior": True}
    )
    studio_result = server.BlenderMCPServer()._dispatch_command(
        "compose_studio_setup", {"subject_type": "watch", "mood": "moody"}
    )
    clear_result = server.BlenderMCPServer()._dispatch_command(
        "clear_scene", {"keep_camera": True}
    )
    render_result = server.BlenderMCPServer()._dispatch_command(
        "setup_render_settings", {"engine": "CYCLES", "samples": 128}
    )

    assert product_result == {"status": "success", "preset": "product_shot"}
    assert isometric_result == {"status": "success", "preset": "isometric"}
    assert character_result == {"status": "success", "preset": "character"}
    assert automotive_result == {"status": "success", "preset": "automotive"}
    assert food_result == {"status": "success", "preset": "food"}
    assert jewelry_result == {"status": "success", "preset": "jewelry"}
    assert architectural_result == {"status": "success", "preset": "architectural"}
    assert studio_result == {"status": "success", "preset": "studio"}
    assert clear_result == {"status": "success", "removed_count": 2}
    assert render_result == {"status": "success", "engine": "CYCLES"}
    composition_module.compose_product_shot.assert_called_once_with(
        {"product_name": "Bottle"}
    )
    composition_module.compose_isometric_scene.assert_called_once_with(
        {"grid_size": 12.0}
    )
    composition_module.compose_character_scene.assert_called_once_with(
        {"character_name": "Hero", "environment": "night"}
    )
    composition_module.compose_automotive_shot.assert_called_once_with(
        {"car_name": "Coupe", "angle": "side"}
    )
    composition_module.compose_food_shot.assert_called_once_with({"style": "angled"})
    composition_module.compose_jewelry_shot.assert_called_once_with(
        {"style": "catalog", "reflections": False}
    )
    composition_module.compose_architectural_shot.assert_called_once_with(
        {"interior": True}
    )
    composition_module.compose_studio_setup.assert_called_once_with(
        {"subject_type": "watch", "mood": "moody"}
    )
    composition_module.clear_scene.assert_called_once_with({"keep_camera": True})
    composition_module.setup_render_settings.assert_called_once_with(
        {"engine": "CYCLES", "samples": 128}
    )


def test_legacy_addon_dispatch_routes_material_command_to_modular_handlers():
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

    material_handlers = types.SimpleNamespace(
        create_glass_material=Mock(return_value={"status": "success"}),
        create_bsdf_material=Mock(),
        create_emission_material=Mock(),
        create_metal_material=Mock(),
        create_subsurface_material=Mock(),
        create_procedural_texture=Mock(),
        assign_material=Mock(),
        list_materials=Mock(),
        delete_material=Mock(),
    )
    package_module = types.ModuleType("blender_mcp_addon")
    handlers_module = types.ModuleType("blender_mcp_addon.handlers")
    handlers_module.materials = material_handlers
    package_module.handlers = handlers_module

    addon_module_name = "test_legacy_addon"
    addon_module_path = Path(__file__).resolve().parents[1] / "addon.py"
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

        result = addon.BlenderMCPServer()._dispatch_command(
            "create_glass_material", {"name": "GlassMaterial"}
        )

    assert result == {"status": "success"}
    material_handlers.create_glass_material.assert_called_once_with(
        {"name": "GlassMaterial"}
    )


def test_legacy_addon_dispatch_routes_lighting_command_to_modular_handlers():
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

    material_handlers = types.SimpleNamespace()
    lighting_handlers = types.SimpleNamespace(
        create_area_light=Mock(return_value={"status": "success", "type": "area"})
    )
    package_module = types.ModuleType("blender_mcp_addon")
    handlers_module = types.ModuleType("blender_mcp_addon.handlers")
    handlers_module.materials = material_handlers
    handlers_module.lighting = lighting_handlers
    package_module.handlers = handlers_module

    addon_module_name = "test_legacy_addon_lighting"
    addon_module_path = Path(__file__).resolve().parents[1] / "addon.py"
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

        result = addon.BlenderMCPServer()._dispatch_command(
            "create_area_light", {"name": "SoftBox"}
        )

    assert result == {"status": "success", "type": "area"}
    lighting_handlers.create_area_light.assert_called_once_with({"name": "SoftBox"})


def test_legacy_addon_dispatch_routes_additional_lighting_commands_to_modular_handlers():
    lighting_handlers = types.SimpleNamespace(
        create_three_point_lighting=Mock(
            return_value={"status": "success", "preset": "three_point"}
        ),
        list_lights=Mock(return_value={"lights": [{"name": "Fill"}], "count": 1}),
        clear_lights=Mock(return_value={"status": "success", "removed_count": 1}),
    )
    three_point_result = _dispatch_legacy_addon_command(
        "create_three_point_lighting",
        {"fill_intensity": 450.0},
        lighting_handlers=lighting_handlers,
    )
    list_result = _dispatch_legacy_addon_command(
        "list_lights", {}, lighting_handlers=lighting_handlers
    )
    clear_result = _dispatch_legacy_addon_command(
        "clear_lights", {}, lighting_handlers=lighting_handlers
    )

    assert three_point_result == {"status": "success", "preset": "three_point"}
    assert list_result == {"lights": [{"name": "Fill"}], "count": 1}
    assert clear_result == {"status": "success", "removed_count": 1}
    lighting_handlers.create_three_point_lighting.assert_called_once_with(
        {"fill_intensity": 450.0}
    )
    lighting_handlers.list_lights.assert_called_once_with()
    lighting_handlers.clear_lights.assert_called_once_with()


def test_legacy_addon_dispatch_routes_all_camera_commands_to_modular_handlers():
    camera_handlers = types.SimpleNamespace(
        create_composition_camera=Mock(
            return_value={"status": "success", "name": "Hero", "composition": "center"}
        ),
        create_isometric_camera=Mock(return_value={"status": "success", "name": "Iso"}),
        set_camera_depth_of_field=Mock(
            return_value={"status": "success", "camera": "Hero", "lens": 85.0}
        ),
        apply_camera_preset=Mock(
            return_value={"status": "success", "camera": "Hero", "preset": "portrait"}
        ),
        set_active_camera=Mock(
            return_value={"status": "success", "active_camera": "Iso"}
        ),
        list_cameras=Mock(
            return_value={"cameras": [{"name": "Hero"}, {"name": "Iso"}], "count": 2}
        ),
        frame_camera_to_selection=Mock(
            return_value={"status": "success", "camera": "Iso"}
        ),
    )

    composition_result = _dispatch_legacy_addon_command(
        "create_composition_camera",
        {"name": "Hero", "composition": "center"},
        camera_handlers=camera_handlers,
    )
    create_result = _dispatch_legacy_addon_command(
        "create_isometric_camera",
        {"name": "Iso"},
        camera_handlers=camera_handlers,
    )
    dof_result = _dispatch_legacy_addon_command(
        "set_camera_depth_of_field",
        {"camera_name": "Hero", "focus_distance": 4.0},
        camera_handlers=camera_handlers,
    )
    preset_result = _dispatch_legacy_addon_command(
        "apply_camera_preset",
        {"camera_name": "Hero", "preset": "portrait"},
        camera_handlers=camera_handlers,
    )
    active_result = _dispatch_legacy_addon_command(
        "set_active_camera",
        {"camera_name": "Iso"},
        camera_handlers=camera_handlers,
    )
    list_result = _dispatch_legacy_addon_command(
        "list_cameras", {}, camera_handlers=camera_handlers
    )
    frame_result = _dispatch_legacy_addon_command(
        "frame_camera_to_selection",
        {"camera_name": "Iso", "margin": 1.2},
        camera_handlers=camera_handlers,
    )

    assert composition_result == {
        "status": "success",
        "name": "Hero",
        "composition": "center",
    }
    assert create_result == {"status": "success", "name": "Iso"}
    assert dof_result == {"status": "success", "camera": "Hero", "lens": 85.0}
    assert preset_result == {
        "status": "success",
        "camera": "Hero",
        "preset": "portrait",
    }
    assert active_result == {"status": "success", "active_camera": "Iso"}
    assert list_result == {"cameras": [{"name": "Hero"}, {"name": "Iso"}], "count": 2}
    assert frame_result == {"status": "success", "camera": "Iso"}
    camera_handlers.create_composition_camera.assert_called_once_with(
        {"name": "Hero", "composition": "center"}
    )
    camera_handlers.create_isometric_camera.assert_called_once_with({"name": "Iso"})
    camera_handlers.set_camera_depth_of_field.assert_called_once_with(
        {"camera_name": "Hero", "focus_distance": 4.0}
    )
    camera_handlers.apply_camera_preset.assert_called_once_with(
        {"camera_name": "Hero", "preset": "portrait"}
    )
    camera_handlers.set_active_camera.assert_called_once_with({"camera_name": "Iso"})
    camera_handlers.list_cameras.assert_called_once_with()
    camera_handlers.frame_camera_to_selection.assert_called_once_with(
        {"camera_name": "Iso", "margin": 1.2}
    )


def test_legacy_addon_dispatch_routes_composition_commands_to_modular_handlers():
    composition_handlers = types.SimpleNamespace(
        compose_product_shot=Mock(
            return_value={"status": "success", "preset": "product_shot"}
        ),
        compose_isometric_scene=Mock(
            return_value={"status": "success", "preset": "isometric"}
        ),
        compose_character_scene=Mock(
            return_value={"status": "success", "preset": "character"}
        ),
        compose_automotive_shot=Mock(
            return_value={"status": "success", "preset": "automotive"}
        ),
        compose_food_shot=Mock(return_value={"status": "success", "preset": "food"}),
        compose_jewelry_shot=Mock(
            return_value={"status": "success", "preset": "jewelry"}
        ),
        compose_architectural_shot=Mock(
            return_value={"status": "success", "preset": "architectural"}
        ),
        compose_studio_setup=Mock(
            return_value={"status": "success", "preset": "studio"}
        ),
        clear_scene=Mock(return_value={"status": "success", "removed_count": 1}),
        setup_render_settings=Mock(
            return_value={"status": "success", "engine": "EEVEE"}
        ),
    )

    product_result = _dispatch_legacy_addon_command(
        "compose_product_shot",
        {"product_name": "Bottle", "background": "white"},
        composition_handlers=composition_handlers,
    )
    isometric_result = _dispatch_legacy_addon_command(
        "compose_isometric_scene",
        {"grid_size": 14.0, "floor": False},
        composition_handlers=composition_handlers,
    )
    character_result = _dispatch_legacy_addon_command(
        "compose_character_scene",
        {"character_name": "Hero", "environment": "night"},
        composition_handlers=composition_handlers,
    )
    automotive_result = _dispatch_legacy_addon_command(
        "compose_automotive_shot",
        {"car_name": "Coupe", "angle": "side"},
        composition_handlers=composition_handlers,
    )
    food_result = _dispatch_legacy_addon_command(
        "compose_food_shot",
        {"style": "angled"},
        composition_handlers=composition_handlers,
    )
    jewelry_result = _dispatch_legacy_addon_command(
        "compose_jewelry_shot",
        {"style": "catalog", "reflections": False},
        composition_handlers=composition_handlers,
    )
    architectural_result = _dispatch_legacy_addon_command(
        "compose_architectural_shot",
        {"interior": True, "natural_light": False},
        composition_handlers=composition_handlers,
    )
    studio_result = _dispatch_legacy_addon_command(
        "compose_studio_setup",
        {"subject_type": "watch", "mood": "moody"},
        composition_handlers=composition_handlers,
    )
    clear_result = _dispatch_legacy_addon_command(
        "clear_scene",
        {"keep_camera": True, "keep_lights": False},
        composition_handlers=composition_handlers,
    )
    render_result = _dispatch_legacy_addon_command(
        "setup_render_settings",
        {"engine": "EEVEE", "samples": 64},
        composition_handlers=composition_handlers,
    )

    assert product_result == {"status": "success", "preset": "product_shot"}
    assert isometric_result == {"status": "success", "preset": "isometric"}
    assert character_result == {"status": "success", "preset": "character"}
    assert automotive_result == {"status": "success", "preset": "automotive"}
    assert food_result == {"status": "success", "preset": "food"}
    assert jewelry_result == {"status": "success", "preset": "jewelry"}
    assert architectural_result == {"status": "success", "preset": "architectural"}
    assert studio_result == {"status": "success", "preset": "studio"}
    assert clear_result == {"status": "success", "removed_count": 1}
    assert render_result == {"status": "success", "engine": "EEVEE"}
    composition_handlers.compose_product_shot.assert_called_once_with(
        {"product_name": "Bottle", "background": "white"}
    )
    composition_handlers.compose_isometric_scene.assert_called_once_with(
        {"grid_size": 14.0, "floor": False}
    )
    composition_handlers.compose_character_scene.assert_called_once_with(
        {"character_name": "Hero", "environment": "night"}
    )
    composition_handlers.compose_automotive_shot.assert_called_once_with(
        {"car_name": "Coupe", "angle": "side"}
    )
    composition_handlers.compose_food_shot.assert_called_once_with({"style": "angled"})
    composition_handlers.compose_jewelry_shot.assert_called_once_with(
        {"style": "catalog", "reflections": False}
    )
    composition_handlers.compose_architectural_shot.assert_called_once_with(
        {"interior": True, "natural_light": False}
    )
    composition_handlers.compose_studio_setup.assert_called_once_with(
        {"subject_type": "watch", "mood": "moody"}
    )
    composition_handlers.clear_scene.assert_called_once_with(
        {"keep_camera": True, "keep_lights": False}
    )
    composition_handlers.setup_render_settings.assert_called_once_with(
        {"engine": "EEVEE", "samples": 64}
    )
