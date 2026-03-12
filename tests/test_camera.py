import asyncio
import importlib
import json
import sys
import types
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_blender_connection():
    return Mock()


def _load_camera_module(mock_blender_connection):
    class DummyMCP:
        @staticmethod
        def tool():
            return lambda func: func

    server_stub = types.ModuleType("blender_mcp.server")
    server_stub.BlenderConnection = object
    server_stub.get_blender_connection = lambda: mock_blender_connection
    server_stub.mcp = DummyMCP()

    with patch.dict(sys.modules, {"blender_mcp.server": server_stub}):
        sys.modules.pop("blender_mcp.tools.camera", None)
        return importlib.import_module("blender_mcp.tools.camera")


class TestCameraTools:
    def test_create_composition_camera(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "name": "HeroCam",
            "composition": "rule_of_thirds",
        }

        camera = _load_camera_module(mock_blender_connection)

        result = asyncio.run(
            camera.create_composition_camera(
                None,
                name="HeroCam",
                composition="rule_of_thirds",
                focal_length=85.0,
                location=[3.0, -4.0, 2.0],
                target=[0.0, 0.0, 1.0],
            )
        )

        assert json.loads(result)["composition"] == "rule_of_thirds"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_composition_camera",
            {
                "name": "HeroCam",
                "composition": "rule_of_thirds",
                "focal_length": 85.0,
                "location": [3.0, -4.0, 2.0],
                "target": [0.0, 0.0, 1.0],
            },
        )

    def test_create_isometric_camera(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "name": "Iso",
            "type": "orthographic",
        }

        camera = _load_camera_module(mock_blender_connection)

        result = asyncio.run(
            camera.create_isometric_camera(
                None, name="Iso", ortho_scale=12.0, angle=35.264
            )
        )

        assert json.loads(result)["type"] == "orthographic"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_isometric_camera",
            {"name": "Iso", "ortho_scale": 12.0, "angle": 35.264},
        )

    def test_set_camera_depth_of_field(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "camera": "HeroCam",
            "aperture": 2.8,
        }

        camera = _load_camera_module(mock_blender_connection)

        result = asyncio.run(
            camera.set_camera_depth_of_field(
                None,
                camera_name="HeroCam",
                focus_distance=4.5,
                focal_length=85.0,
                aperture=2.8,
            )
        )

        assert json.loads(result)["camera"] == "HeroCam"
        mock_blender_connection.send_command.assert_called_once_with(
            "set_camera_depth_of_field",
            {
                "camera_name": "HeroCam",
                "aperture": 2.8,
                "focus_distance": 4.5,
                "focal_length": 85.0,
            },
        )

    def test_apply_camera_preset(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "camera": "HeroCam",
            "preset": "portrait",
        }

        camera = _load_camera_module(mock_blender_connection)

        result = asyncio.run(
            camera.apply_camera_preset(None, camera_name="HeroCam", preset="portrait")
        )

        assert json.loads(result)["preset"] == "portrait"
        mock_blender_connection.send_command.assert_called_once_with(
            "apply_camera_preset",
            {"camera_name": "HeroCam", "preset": "portrait"},
        )

    def test_list_and_activate_camera(self, mock_blender_connection):
        mock_blender_connection.send_command.side_effect = [
            {"status": "success", "active_camera": "HeroCam"},
            {"count": 1, "active_camera": "HeroCam", "cameras": [{"name": "HeroCam"}]},
        ]

        camera = _load_camera_module(mock_blender_connection)

        activate_result = asyncio.run(
            camera.set_active_camera(None, camera_name="HeroCam")
        )
        list_result = asyncio.run(camera.list_cameras(None))

        assert json.loads(activate_result)["active_camera"] == "HeroCam"
        assert json.loads(list_result)["count"] == 1
        assert mock_blender_connection.send_command.call_args_list == [
            (("set_active_camera", {"camera_name": "HeroCam"}),),
            (("list_cameras", {}),),
        ]

    def test_frame_camera_to_selection(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "camera": "HeroCam",
            "margin": 1.2,
        }

        camera = _load_camera_module(mock_blender_connection)

        result = asyncio.run(
            camera.frame_camera_to_selection(None, camera_name="HeroCam", margin=1.2)
        )

        assert json.loads(result)["margin"] == 1.2
        mock_blender_connection.send_command.assert_called_once_with(
            "frame_camera_to_selection",
            {"camera_name": "HeroCam", "margin": 1.2},
        )

    def test_create_composition_camera_returns_error_json(
        self, mock_blender_connection
    ):
        mock_blender_connection.send_command.side_effect = RuntimeError("boom")

        camera = _load_camera_module(mock_blender_connection)

        result = asyncio.run(camera.create_composition_camera(None))

        assert json.loads(result) == {"error": "boom"}
