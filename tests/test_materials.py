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


def _load_materials_module(mock_blender_connection):
    class DummyMCP:
        @staticmethod
        def tool():
            return lambda func: func

    server_stub = types.ModuleType("blender_mcp.server")
    server_stub.BlenderConnection = object
    server_stub.get_blender_connection = lambda: mock_blender_connection
    server_stub.mcp = DummyMCP()

    with patch.dict(sys.modules, {"blender_mcp.server": server_stub}):
        sys.modules.pop("blender_mcp.tools.materials", None)
        return importlib.import_module("blender_mcp.tools.materials")


class TestMaterialsTools:
    def test_create_bsdf_material(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "material": "TestMaterial",
            "type": "principled_bsdf",
        }

        materials = _load_materials_module(mock_blender_connection)

        result = asyncio.run(
            materials.create_bsdf_material(
                None,
                name="TestMaterial",
                base_color=[0.8, 0.2, 0.2],
                metallic=0.9,
                roughness=0.1,
            )
        )

        data = json.loads(result)
        assert data["status"] == "success"
        assert data["material"] == "TestMaterial"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_bsdf_material",
            {
                "name": "TestMaterial",
                "base_color": [0.8, 0.2, 0.2],
                "metallic": 0.9,
                "roughness": 0.1,
            },
        )

    def test_create_emission_material(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "material": "GlowMaterial",
            "type": "emission",
        }

        materials = _load_materials_module(mock_blender_connection)

        result = asyncio.run(
            materials.create_emission_material(
                None,
                name="GlowMaterial",
                color=[1.0, 0.5, 0.0],
                strength=50.0,
            )
        )

        data = json.loads(result)
        assert data["type"] == "emission"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_emission_material",
            {
                "name": "GlowMaterial",
                "color": [1.0, 0.5, 0.0],
                "strength": 50.0,
                "shadow_mode": "none",
            },
        )

    def test_create_glass_material(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "material": "GlassMaterial",
            "type": "glass",
        }

        materials = _load_materials_module(mock_blender_connection)

        result = asyncio.run(
            materials.create_glass_material(
                None,
                name="GlassMaterial",
                ior=1.52,
            )
        )

        data = json.loads(result)
        assert data["type"] == "glass"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_glass_material",
            {
                "name": "GlassMaterial",
                "roughness": 0.0,
                "ior": 1.52,
                "transmission": 1.0,
            },
        )

    def test_create_metal_material(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "material": "SteelMaterial",
            "type": "metal",
        }

        materials = _load_materials_module(mock_blender_connection)

        result = asyncio.run(
            materials.create_metal_material(
                None,
                name="SteelMaterial",
                base_color=[0.7, 0.7, 0.75],
                roughness=0.2,
                anisotropy=0.35,
            )
        )

        data = json.loads(result)
        assert data["type"] == "metal"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_metal_material",
            {
                "name": "SteelMaterial",
                "base_color": [0.7, 0.7, 0.75],
                "roughness": 0.2,
                "anisotropy": 0.35,
            },
        )

    def test_create_subsurface_material(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "material": "SkinMaterial",
            "type": "subsurface",
        }

        materials = _load_materials_module(mock_blender_connection)

        result = asyncio.run(
            materials.create_subsurface_material(
                None,
                name="SkinMaterial",
                base_color=[0.9, 0.7, 0.6],
                subsurface_color=[1.0, 0.5, 0.4],
                subsurface_radius=[1.0, 0.3, 0.2],
                subsurface=0.65,
                roughness=0.45,
            )
        )

        data = json.loads(result)
        assert data["type"] == "subsurface"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_subsurface_material",
            {
                "name": "SkinMaterial",
                "base_color": [0.9, 0.7, 0.6],
                "subsurface_color": [1.0, 0.5, 0.4],
                "subsurface_radius": [1.0, 0.3, 0.2],
                "subsurface": 0.65,
                "roughness": 0.45,
                "subsurface_method": "random_walk",
            },
        )

    def test_create_procedural_texture(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "material": "NoiseMaterial",
            "texture_type": "noise",
        }

        materials = _load_materials_module(mock_blender_connection)

        result = asyncio.run(
            materials.create_procedural_texture(
                None,
                texture_type="noise",
                name="NoiseMaterial",
                scale=7.5,
                detail=4.0,
                roughness=0.25,
                distortion=0.1,
            )
        )

        data = json.loads(result)
        assert data["texture_type"] == "noise"
        mock_blender_connection.send_command.assert_called_once_with(
            "create_procedural_texture",
            {
                "texture_type": "noise",
                "name": "NoiseMaterial",
                "scale": 7.5,
                "detail": 4.0,
                "roughness": 0.25,
                "distortion": 0.1,
            },
        )

    def test_assign_material(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "status": "success",
            "object": "Cube",
            "material": "TestMaterial",
        }

        materials = _load_materials_module(mock_blender_connection)

        result = asyncio.run(
            materials.assign_material(
                None,
                object_name="Cube",
                material_name="TestMaterial",
            )
        )

        data = json.loads(result)
        assert data["status"] == "success"
        mock_blender_connection.send_command.assert_called_once_with(
            "assign_material",
            {"object_name": "Cube", "material_name": "TestMaterial"},
        )

    def test_list_materials(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "materials": [{"name": "Material"}, {"name": "Glass"}],
            "count": 2,
        }

        materials = _load_materials_module(mock_blender_connection)

        result = asyncio.run(materials.list_materials(None))

        data = json.loads(result)
        assert data["count"] == 2
        assert [item["name"] for item in data["materials"]] == ["Material", "Glass"]
        mock_blender_connection.send_command.assert_called_once_with(
            "list_materials", {}
        )

    def test_delete_material_returns_error_json(self, mock_blender_connection):
        mock_blender_connection.send_command.side_effect = RuntimeError("boom")

        materials = _load_materials_module(mock_blender_connection)

        result = asyncio.run(materials.delete_material(None, name="Broken"))

        assert json.loads(result) == {"error": "boom"}
