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


def _load_composition_module(mock_blender_connection):
    class DummyMCP:
        @staticmethod
        def tool():
            return lambda func: func

    server_stub = types.ModuleType("blender_mcp.server")
    server_stub.BlenderConnection = object
    server_stub.get_blender_connection = lambda: mock_blender_connection
    server_stub.mcp = DummyMCP()

    with patch.dict(sys.modules, {"blender_mcp.server": server_stub}):
        sys.modules.pop("blender_mcp.tools.composition", None)
        return importlib.import_module("blender_mcp.tools.composition")


class TestCompositionTools:
    def test_compose_product_shot(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "preset": "product_shot",
            "camera": "Bottle Camera",
            "background": "white",
        }

        composition = _load_composition_module(mock_blender_connection)

        result = asyncio.run(
            composition.compose_product_shot(
                None,
                product_name="Bottle",
                style="clean",
                background="white",
            )
        )

        assert json.loads(result)["preset"] == "product_shot"
        mock_blender_connection.send_command.assert_called_once_with(
            "compose_product_shot",
            {
                "product_name": "Bottle",
                "style": "clean",
                "background": "white",
            },
        )

    def test_compose_isometric_scene(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "preset": "isometric",
            "camera": "Isometric Camera",
            "ortho_scale": 12.0,
        }

        composition = _load_composition_module(mock_blender_connection)

        result = asyncio.run(
            composition.compose_isometric_scene(
                None,
                grid_size=12.0,
                floor=False,
                shadow_catcher=False,
            )
        )

        assert json.loads(result)["ortho_scale"] == 12.0
        mock_blender_connection.send_command.assert_called_once_with(
            "compose_isometric_scene",
            {"grid_size": 12.0, "floor": False, "shadow_catcher": False},
        )

    @pytest.mark.parametrize(
        ("tool_name", "kwargs", "command_type", "expected_params", "result_payload"),
        [
            (
                "compose_character_scene",
                {
                    "character_name": "Hero",
                    "ground_plane": False,
                    "environment": "night",
                },
                "compose_character_scene",
                {
                    "character_name": "Hero",
                    "ground_plane": False,
                    "environment": "night",
                },
                {"status": "success", "preset": "character", "environment": "night"},
            ),
            (
                "compose_automotive_shot",
                {"car_name": "Coupe", "angle": "side", "environment": "motion"},
                "compose_automotive_shot",
                {"car_name": "Coupe", "angle": "side", "environment": "motion"},
                {"status": "success", "preset": "automotive", "angle": "side"},
            ),
            (
                "compose_food_shot",
                {"style": "angled"},
                "compose_food_shot",
                {"style": "angled"},
                {"status": "success", "preset": "food", "style": "angled"},
            ),
            (
                "compose_jewelry_shot",
                {"style": "catalog", "reflections": False},
                "compose_jewelry_shot",
                {"style": "catalog", "reflections": False},
                {"status": "success", "preset": "jewelry", "style": "catalog"},
            ),
            (
                "compose_architectural_shot",
                {"interior": True, "natural_light": False},
                "compose_architectural_shot",
                {"interior": True, "natural_light": False},
                {"status": "success", "preset": "architectural", "interior": True},
            ),
            (
                "compose_studio_setup",
                {"subject_type": "watch", "mood": "moody"},
                "compose_studio_setup",
                {"subject_type": "watch", "mood": "moody"},
                {"status": "success", "preset": "studio", "mood": "moody"},
            ),
        ],
    )
    def test_composition_tool_wrappers(
        self,
        mock_blender_connection,
        tool_name,
        kwargs,
        command_type,
        expected_params,
        result_payload,
    ):
        mock_blender_connection.send_command.return_value = result_payload

        composition = _load_composition_module(mock_blender_connection)

        result = asyncio.run(getattr(composition, tool_name)(None, **kwargs))

        assert json.loads(result) == result_payload
        mock_blender_connection.send_command.assert_called_once_with(
            command_type, expected_params
        )

    def test_clear_scene(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "removed_count": 3,
        }

        composition = _load_composition_module(mock_blender_connection)

        result = asyncio.run(
            composition.clear_scene(None, keep_camera=True, keep_lights=False)
        )

        assert json.loads(result)["removed_count"] == 3
        mock_blender_connection.send_command.assert_called_once_with(
            "clear_scene",
            {"keep_camera": True, "keep_lights": False},
        )

    def test_setup_render_settings(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "engine": "CYCLES",
            "samples": 256,
        }

        composition = _load_composition_module(mock_blender_connection)

        result = asyncio.run(
            composition.setup_render_settings(
                None,
                engine="CYCLES",
                samples=256,
                resolution_x=2048,
                resolution_y=2048,
                denoise=False,
            )
        )

        assert json.loads(result)["engine"] == "CYCLES"
        mock_blender_connection.send_command.assert_called_once_with(
            "setup_render_settings",
            {
                "engine": "CYCLES",
                "samples": 256,
                "resolution_x": 2048,
                "resolution_y": 2048,
                "denoise": False,
            },
        )

    def test_compose_product_shot_returns_error_json(self, mock_blender_connection):
        mock_blender_connection.send_command.side_effect = RuntimeError("boom")

        composition = _load_composition_module(mock_blender_connection)

        result = asyncio.run(composition.compose_product_shot(None))

        assert json.loads(result) == {"error": "boom"}
