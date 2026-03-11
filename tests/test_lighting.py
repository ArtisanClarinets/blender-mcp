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


def _load_lighting_module(mock_blender_connection):
    class DummyMCP:
        @staticmethod
        def tool():
            return lambda func: func

    server_stub = types.ModuleType("blender_mcp.server")
    server_stub.BlenderConnection = object
    server_stub.get_blender_connection = lambda: mock_blender_connection
    server_stub.mcp = DummyMCP()

    with patch.dict(sys.modules, {"blender_mcp.server": server_stub}):
        sys.modules.pop("blender_mcp.tools.lighting", None)
        return importlib.import_module("blender_mcp.tools.lighting")


class TestLightingTools:
    def test_create_three_point_lighting(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "preset": "three_point",
            "lights": ["Three Point Key", "Three Point Fill", "Three Point Rim"],
        }

        lighting = _load_lighting_module(mock_blender_connection)

        result = asyncio.run(
            lighting.create_three_point_lighting(
                None,
                key_intensity=1200.0,
                fill_intensity=650.0,
                rim_intensity=900.0,
            )
        )

        data = json.loads(result)
        assert data["preset"] == "three_point"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_three_point_lighting",
            {
                "key_intensity": 1200.0,
                "fill_intensity": 650.0,
                "rim_intensity": 900.0,
            },
        )

    def test_create_studio_lighting(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "preset": "cinematic",
            "lights": ["Cinematic Key", "Cinematic Rim"],
        }

        lighting = _load_lighting_module(mock_blender_connection)

        result = asyncio.run(
            lighting.create_studio_lighting(
                None,
                preset="cinematic",
                intensity=750.0,
                color=[0.9, 0.95, 1.0],
            )
        )

        data = json.loads(result)
        assert data["preset"] == "cinematic"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_studio_lighting",
            {
                "preset": "cinematic",
                "intensity": 750.0,
                "color": [0.9, 0.95, 1.0],
            },
        )

    def test_create_area_light(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "name": "SoftBox",
            "type": "area",
            "shape": "RECTANGLE",
        }

        lighting = _load_lighting_module(mock_blender_connection)

        result = asyncio.run(
            lighting.create_area_light(
                None,
                name="SoftBox",
                light_type="RECTANGLE",
                size=2.0,
                location=[1.0, -2.0, 3.0],
                rotation=[0.5, 0.0, 0.2],
                energy=500.0,
                color=[1.0, 0.95, 0.9],
            )
        )

        data = json.loads(result)
        assert data["shape"] == "RECTANGLE"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_area_light",
            {
                "name": "SoftBox",
                "light_type": "RECTANGLE",
                "size": 2.0,
                "energy": 500.0,
                "location": [1.0, -2.0, 3.0],
                "rotation": [0.5, 0.0, 0.2],
                "color": [1.0, 0.95, 0.9],
            },
        )

    def test_create_hdri_environment(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "hdri_name": "studio_small_03",
            "strength": 1.1,
        }

        lighting = _load_lighting_module(mock_blender_connection)

        result = asyncio.run(
            lighting.create_hdri_environment(
                None,
                hdri_name="studio_small_03",
                strength=1.1,
                rotation=45.0,
            )
        )

        data = json.loads(result)
        assert data["hdri_name"] == "studio_small_03"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_hdri_environment",
            {
                "hdri_name": "studio_small_03",
                "strength": 1.1,
                "rotation": 45.0,
                "blur": 0.0,
            },
        )

    def test_create_volumetric_lighting(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "density": 0.2,
            "anisotropy": 0.35,
            "color": [0.7, 0.8, 1.0],
        }

        lighting = _load_lighting_module(mock_blender_connection)

        result = asyncio.run(
            lighting.create_volumetric_lighting(
                None,
                density=0.2,
                anisotropy=0.35,
                color=[0.7, 0.8, 1.0],
            )
        )

        data = json.loads(result)
        assert data["density"] == 0.2
        mock_blender_connection.send_command.assert_called_once_with(
            "create_volumetric_lighting",
            {
                "density": 0.2,
                "anisotropy": 0.35,
                "color": [0.7, 0.8, 1.0],
            },
        )

    def test_clear_lights(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "removed_count": 4,
        }

        lighting = _load_lighting_module(mock_blender_connection)

        result = asyncio.run(lighting.clear_lights(None))

        data = json.loads(result)
        assert data["removed_count"] == 4
        mock_blender_connection.send_command.assert_called_once_with("clear_lights", {})

    def test_list_lights(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "lights": [
                {
                    "name": "Key",
                    "type": "AREA",
                    "energy": 650.0,
                    "color": [1.0, 1.0, 1.0],
                    "location": [1.0, 2.0, 3.0],
                    "rotation": [0.0, 0.0, 0.0],
                }
            ],
            "count": 1,
        }

        lighting = _load_lighting_module(mock_blender_connection)

        result = asyncio.run(lighting.list_lights(None))

        data = json.loads(result)
        assert data["count"] == 1
        assert data["lights"][0]["name"] == "Key"
        mock_blender_connection.send_command.assert_called_once_with("list_lights", {})

    def test_adjust_light_exposure(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "exposure": 1.5,
            "gamma": 1.1,
        }

        lighting = _load_lighting_module(mock_blender_connection)

        result = asyncio.run(
            lighting.adjust_light_exposure(None, exposure=1.5, gamma=1.1)
        )

        data = json.loads(result)
        assert data == {"status": "success", "exposure": 1.5, "gamma": 1.1}
        mock_blender_connection.send_command.assert_called_once_with(
            "adjust_light_exposure",
            {"exposure": 1.5, "gamma": 1.1},
        )

    def test_adjust_light_exposure_returns_error_json(self, mock_blender_connection):
        mock_blender_connection.send_command.side_effect = RuntimeError("boom")

        lighting = _load_lighting_module(mock_blender_connection)

        result = asyncio.run(
            lighting.adjust_light_exposure(None, exposure=1.5, gamma=1.1)
        )

        assert json.loads(result) == {"error": "boom"}
