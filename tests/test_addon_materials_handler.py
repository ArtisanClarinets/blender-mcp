import importlib.util
import builtins
import sys
import types
from pathlib import Path
from unittest.mock import patch


class FakeSocket:
    def __init__(self, default_value=None):
        self.default_value = default_value


class FakeSocketMap(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class FakeNode:
    def __init__(self, node_type):
        self.type = node_type
        self.location = (0, 0)
        self.inputs = FakeSocketMap()
        self.outputs = FakeSocketMap()

        if node_type == "ShaderNodeOutputMaterial":
            self.inputs["Surface"] = FakeSocket()
        elif node_type == "ShaderNodeBsdfPrincipled":
            self.inputs["Base Color"] = FakeSocket([0.0, 0.0, 0.0, 1.0])
            self.inputs["Metallic"] = FakeSocket(0.0)
            self.inputs["Roughness"] = FakeSocket(0.5)
            self.inputs["Specular"] = FakeSocket(0.5)
            self.inputs["Specular IOR Level"] = FakeSocket(0.5)
            self.inputs["Subsurface"] = FakeSocket(0.0)
            self.inputs["Subsurface Weight"] = FakeSocket(0.0)
            self.inputs["Subsurface Color"] = FakeSocket([0.0, 0.0, 0.0, 1.0])
            self.inputs["Subsurface Radius"] = FakeSocket([1.0, 1.0, 1.0])
            self.inputs["Transmission"] = FakeSocket(0.0)
            self.inputs["Transmission Weight"] = FakeSocket(0.0)
            self.inputs["IOR"] = FakeSocket(1.45)
            self.inputs["Emission"] = FakeSocket([0.0, 0.0, 0.0, 1.0])
            self.inputs["Emission Color"] = FakeSocket([0.0, 0.0, 0.0, 1.0])
            self.inputs["Emission Strength"] = FakeSocket(0.0)
            self.inputs["Anisotropic"] = FakeSocket(0.0)
            self.inputs["Anisotropy"] = FakeSocket(0.0)
            self.outputs["BSDF"] = FakeSocket()
        elif node_type == "ShaderNodeEmission":
            self.inputs["Color"] = FakeSocket([0.0, 0.0, 0.0, 1.0])
            self.inputs["Strength"] = FakeSocket(1.0)
            self.outputs["Emission"] = FakeSocket()
        elif node_type == "ShaderNodeMapping":
            self.inputs["Vector"] = FakeSocket()
            self.inputs["Scale"] = FakeSocket([1.0, 1.0, 1.0])
            self.outputs["Vector"] = FakeSocket()
        elif node_type == "ShaderNodeTexCoord":
            self.outputs["Object"] = FakeSocket()
        elif node_type.startswith("ShaderNodeTex"):
            self.inputs["Vector"] = FakeSocket()
            self.inputs["Scale"] = FakeSocket(5.0)
            self.inputs["Detail"] = FakeSocket(2.0)
            self.inputs["Roughness"] = FakeSocket(0.5)
            self.inputs["Distortion"] = FakeSocket(0.0)
            self.outputs["Color"] = FakeSocket()
            self.outputs["Fac"] = FakeSocket()


class FakeNodeCollection(list):
    def clear(self):
        del self[:]

    def new(self, type):
        node = FakeNode(type)
        self.append(node)
        return node


class FakeLinkCollection(list):
    def new(self, output_socket, input_socket):
        self.append((output_socket, input_socket))


class FakeNodeTree:
    def __init__(self):
        self.nodes = FakeNodeCollection()
        self.links = FakeLinkCollection()


class FakeMaterial:
    def __init__(self, name, users=0):
        self.name = name
        self.users = users
        self.use_nodes = False
        self.node_tree = FakeNodeTree()


class FakeMaterialCollection:
    def __init__(self, materials=None):
        self._materials = {}
        for material in materials or []:
            self._materials[material.name] = material

    def get(self, name):
        return self._materials.get(name)

    def new(self, name):
        material = FakeMaterial(name)
        self._materials[name] = material
        return material

    def remove(self, material, do_unlink=True):
        self._materials.pop(material.name, None)

    def __iter__(self):
        return iter(self._materials.values())


class FakeObjectData:
    def __init__(self, materials=None):
        self.materials = materials or []


class FakeObject:
    def __init__(self, name, materials=None):
        self.name = name
        self.data = FakeObjectData(materials)


class FakeObjectCollection:
    def __init__(self, objects=None):
        self._objects = {}
        for obj in objects or []:
            self._objects[obj.name] = obj

    def get(self, name):
        return self._objects.get(name)

    def __iter__(self):
        return iter(self._objects.values())


def load_materials_handler(fake_bpy):
    module_name = "test_blender_mcp_addon_materials"
    module_path = (
        Path(__file__).resolve().parents[1]
        / "blender_mcp_addon"
        / "handlers"
        / "materials.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.pop(module_name, None)
    with patch.dict(sys.modules, {"bpy": fake_bpy}):
        spec.loader.exec_module(module)
    return module


def make_fake_bpy(materials=None, objects=None):
    return types.SimpleNamespace(
        data=types.SimpleNamespace(
            materials=FakeMaterialCollection(materials),
            objects=FakeObjectCollection(objects),
        ),
        types=types.SimpleNamespace(Material=FakeMaterial, Node=FakeNode),
    )


def load_legacy_addon(fake_bpy):
    module_name = "test_legacy_addon_materials_fallback"
    module_path = Path(__file__).resolve().parents[1] / "addon.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)

    fake_bpy_module = types.ModuleType("bpy")
    fake_bpy_module.app = types.SimpleNamespace(
        timers=types.SimpleNamespace(register=lambda func, first_interval=0.0: func())
    )
    fake_bpy_module.data = fake_bpy.data

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
    fake_bpy_types.Material = FakeMaterial
    fake_bpy_types.Node = FakeNode

    fake_bpy_module.props = fake_bpy_props
    fake_bpy_module.types = fake_bpy_types

    sys.modules.pop(module_name, None)
    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy_module,
            "bpy.props": fake_bpy_props,
            "bpy.types": fake_bpy_types,
            "requests": types.ModuleType("requests"),
        },
        clear=False,
    ):
        spec.loader.exec_module(module)
    return module


def test_create_bsdf_material_builds_principled_node_tree():
    fake_bpy = make_fake_bpy()
    materials = load_materials_handler(fake_bpy)

    result = materials.create_bsdf_material(
        {
            "name": "TestMaterial",
            "base_color": [0.8, 0.2, 0.1],
            "metallic": 0.9,
            "roughness": 0.15,
            "emission_strength": 3.0,
        }
    )

    material = fake_bpy.data.materials.get("TestMaterial")
    shader = material.node_tree.nodes[1]

    assert result == {
        "status": "success",
        "material": "TestMaterial",
        "type": "principled_bsdf",
        "nodes": 2,
    }
    assert material.use_nodes is True
    assert shader.inputs["Base Color"].default_value == [0.8, 0.2, 0.1, 1.0]
    assert shader.inputs["Metallic"].default_value == 0.9
    assert shader.inputs["Roughness"].default_value == 0.15
    assert shader.inputs["Emission Strength"].default_value == 3.0


def test_assign_material_replaces_first_slot():
    existing = FakeMaterial("Existing")
    replacement = FakeMaterial("Replacement")
    obj = FakeObject("Cube", materials=[existing])
    fake_bpy = make_fake_bpy(materials=[existing, replacement], objects=[obj])
    materials = load_materials_handler(fake_bpy)

    result = materials.assign_material(
        {"object_name": "Cube", "material_name": "Replacement"}
    )

    assert result == {
        "status": "success",
        "object": "Cube",
        "material": "Replacement",
    }
    assert obj.data.materials[0] is replacement


def test_assign_material_appends_when_object_has_multiple_slots():
    primary = FakeMaterial("Primary")
    accent = FakeMaterial("Accent")
    replacement = FakeMaterial("Replacement")
    obj = FakeObject("Cube", materials=[primary, accent])
    fake_bpy = make_fake_bpy(
        materials=[primary, accent, replacement],
        objects=[obj],
    )
    materials = load_materials_handler(fake_bpy)

    result = materials.assign_material(
        {"object_name": "Cube", "material_name": "Replacement"}
    )

    assert result == {
        "status": "success",
        "object": "Cube",
        "material": "Replacement",
    }
    assert obj.data.materials == [primary, accent, replacement]


def test_assign_material_uses_empty_slot_before_appending():
    primary = FakeMaterial("Primary")
    replacement = FakeMaterial("Replacement")
    obj = FakeObject("Cube", materials=[primary, None])
    fake_bpy = make_fake_bpy(materials=[primary, replacement], objects=[obj])
    materials = load_materials_handler(fake_bpy)

    materials.assign_material({"object_name": "Cube", "material_name": "Replacement"})

    assert obj.data.materials == [primary, replacement]


def test_create_glass_material_sets_transmission_defaults():
    fake_bpy = make_fake_bpy()
    materials = load_materials_handler(fake_bpy)

    result = materials.create_glass_material(
        {
            "name": "GlassMaterial",
            "color": [0.8, 0.9, 1.0],
            "roughness": 0.12,
            "ior": 1.52,
            "transmission": 0.95,
        }
    )

    shader = fake_bpy.data.materials.get("GlassMaterial").node_tree.nodes[1]

    assert result == {
        "status": "success",
        "material": "GlassMaterial",
        "type": "glass",
    }
    assert shader.inputs["Base Color"].default_value == [0.8, 0.9, 1.0, 1.0]
    assert shader.inputs["Roughness"].default_value == 0.12
    assert shader.inputs["IOR"].default_value == 1.52
    assert shader.inputs["Transmission"].default_value == 0.95


def test_create_metal_material_sets_metallic_and_anisotropy():
    fake_bpy = make_fake_bpy()
    materials = load_materials_handler(fake_bpy)

    result = materials.create_metal_material(
        {
            "name": "SteelMaterial",
            "base_color": [0.7, 0.7, 0.75],
            "roughness": 0.2,
            "anisotropy": 0.35,
        }
    )

    shader = fake_bpy.data.materials.get("SteelMaterial").node_tree.nodes[1]

    assert result == {
        "status": "success",
        "material": "SteelMaterial",
        "type": "metal",
    }
    assert shader.inputs["Base Color"].default_value == [0.7, 0.7, 0.75, 1.0]
    assert shader.inputs["Metallic"].default_value == 1.0
    assert shader.inputs["Roughness"].default_value == 0.2
    assert shader.inputs["Anisotropic"].default_value == 0.35


def test_create_subsurface_material_sets_radius_and_weight():
    fake_bpy = make_fake_bpy()
    materials = load_materials_handler(fake_bpy)

    result = materials.create_subsurface_material(
        {
            "name": "SkinMaterial",
            "base_color": [0.9, 0.7, 0.6],
            "subsurface_color": [1.0, 0.5, 0.4],
            "subsurface_radius": [1.0, 0.3, 0.2],
            "subsurface": 0.65,
            "roughness": 0.45,
        }
    )

    shader = fake_bpy.data.materials.get("SkinMaterial").node_tree.nodes[1]

    assert result == {
        "status": "success",
        "material": "SkinMaterial",
        "type": "subsurface",
    }
    assert shader.inputs["Base Color"].default_value == [0.9, 0.7, 0.6, 1.0]
    assert shader.inputs["Subsurface"].default_value == 0.65
    assert shader.inputs["Subsurface Color"].default_value == [1.0, 0.5, 0.4, 1.0]
    assert shader.inputs["Subsurface Radius"].default_value == [1.0, 0.3, 0.2]
    assert shader.inputs["Roughness"].default_value == 0.45


def test_create_procedural_texture_builds_texture_chain():
    fake_bpy = make_fake_bpy()
    materials = load_materials_handler(fake_bpy)

    result = materials.create_procedural_texture(
        {
            "name": "NoiseMaterial",
            "texture_type": "noise",
            "scale": 7.5,
            "detail": 4.0,
            "roughness": 0.25,
            "distortion": 0.1,
        }
    )

    nodes = fake_bpy.data.materials.get("NoiseMaterial").node_tree.nodes
    mapping = nodes[2]
    texture = nodes[4]

    assert result == {
        "status": "success",
        "material": "NoiseMaterial",
        "texture_type": "noise",
        "nodes": 5,
    }
    assert mapping.inputs["Scale"].default_value == [7.5, 7.5, 7.5]
    assert texture.inputs["Scale"].default_value == 7.5
    assert texture.inputs["Detail"].default_value == 4.0
    assert texture.inputs["Roughness"].default_value == 0.25
    assert texture.inputs["Distortion"].default_value == 0.1


def test_list_materials_reports_assigned_objects():
    red = FakeMaterial("Red", users=2)
    blue = FakeMaterial("Blue", users=1)
    cube = FakeObject("Cube", materials=[red])
    sphere = FakeObject("Sphere", materials=[red, blue])
    fake_bpy = make_fake_bpy(materials=[red, blue], objects=[cube, sphere])
    materials = load_materials_handler(fake_bpy)

    result = materials.list_materials()

    assert result["count"] == 2
    assert result["materials"] == [
        {
            "name": "Red",
            "use_nodes": False,
            "users": 2,
            "assigned_objects": ["Cube", "Sphere"],
        },
        {
            "name": "Blue",
            "use_nodes": False,
            "users": 1,
            "assigned_objects": ["Sphere"],
        },
    ]


def test_delete_material_removes_existing_material():
    obsolete = FakeMaterial("Obsolete", users=4)
    fake_bpy = make_fake_bpy(materials=[obsolete])
    materials = load_materials_handler(fake_bpy)

    result = materials.delete_material({"name": "Obsolete"})

    assert result == {
        "status": "success",
        "material": "Obsolete",
        "users_before_delete": 4,
    }


def test_legacy_addon_uses_local_material_fallback_when_package_is_missing():
    legacy = FakeMaterial("Legacy", users=1)
    cube = FakeObject("Cube", materials=[legacy])
    fake_bpy = make_fake_bpy(materials=[legacy], objects=[cube])
    addon = load_legacy_addon(fake_bpy)

    real_import = builtins.__import__

    def import_without_material_handlers(
        name, globals=None, locals=None, fromlist=(), level=0
    ):
        if name == "blender_mcp_addon.handlers":
            raise ImportError("materials handler package unavailable")
        return real_import(name, globals, locals, fromlist, level)

    with patch("builtins.__import__", side_effect=import_without_material_handlers):
        result = addon.BlenderMCPServer()._dispatch_command("list_materials", {})

    assert result == {
        "materials": [
            {
                "name": "Legacy",
                "use_nodes": False,
                "users": 1,
                "assigned_objects": ["Cube"],
            }
        ],
        "count": 1,
    }
    assert fake_bpy.data.materials.get("Obsolete") is None
