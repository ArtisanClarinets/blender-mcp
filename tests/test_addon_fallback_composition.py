import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest


class FakeRender:
    def __init__(self):
        self.engine = "BLENDER_EEVEE"
        self.resolution_x = 1920
        self.resolution_y = 1080
        self.film_transparent = False


class FakeCycles:
    def __init__(self):
        self.samples = 64
        self.use_denoising = False


class FakeEevee:
    def __init__(self):
        self.taa_render_samples = 16


class FakeWorld:
    def __init__(self, name):
        self.name = name
        self.color = [0.0, 0.0, 0.0]


class FakeWorldCollection:
    def __init__(self):
        self._worlds = {}

    def new(self, name):
        world = FakeWorld(name)
        self._worlds[name] = world
        return world


class FakeCameraData:
    def __init__(self, name):
        self.name = name
        self.type = "PERSP"
        self.lens = 50.0
        self.ortho_scale = 10.0


class FakeCameraCollection:
    def __init__(self):
        self._cameras = {}

    def new(self, name):
        camera = FakeCameraData(name)
        self._cameras[name] = camera
        return camera


class FakeObject:
    def __init__(self, name, object_type, data=None):
        self.name = name
        self.type = object_type
        self.data = data
        self.location = [0.0, 0.0, 0.0]
        self.rotation_euler = [0.0, 0.0, 0.0]
        self._properties = {}

    def __contains__(self, key):
        return key in self._properties

    def __getitem__(self, key):
        return self._properties[key]

    def __setitem__(self, key, value):
        self._properties[key] = value

    def get(self, key, default=None):
        return self._properties.get(key, default)


class FakeObjectCollection:
    def __init__(self, objects=None):
        self._objects = {}
        for obj in objects or []:
            self._objects[obj.name] = obj

    def get(self, name):
        if name in self._objects:
            return self._objects[name]
        for obj in self._objects.values():
            if obj.name == name:
                return obj
        return None

    def __contains__(self, name):
        return self.get(name) is not None

    def __getitem__(self, name):
        obj = self.get(name)
        if obj is None:
            raise KeyError(name)
        return obj

    def new(self, name, object_data):
        object_type = "CAMERA" if isinstance(object_data, FakeCameraData) else "EMPTY"
        obj = FakeObject(name, object_type, object_data)
        self._objects[name] = obj
        return obj

    def remove(self, obj, do_unlink=True):
        self._objects.pop(obj.name, None)

    def __iter__(self):
        return iter(self._objects.values())


class FakeCollectionObjects:
    def __init__(self, linked=None):
        self.linked = [] if linked is None else linked

    def link(self, obj):
        if obj not in self.linked:
            self.linked.append(obj)


class FakeCollection:
    def __init__(self, linked=None):
        self.objects = FakeCollectionObjects(linked)


class FakeScene:
    def __init__(self, objects=None):
        self.objects = [] if objects is None else objects
        self.collection = FakeCollection(self.objects)
        self.camera = None
        self.world = None
        self.render = FakeRender()
        self.cycles = FakeCycles()
        self.eevee = FakeEevee()


def make_fake_bpy(objects=None):
    all_objects = [] if objects is None else list(objects)
    scene = FakeScene(all_objects)

    bpy_module = types.ModuleType("bpy")
    bpy_props = types.ModuleType("bpy.props")
    for property_name in (
        "StringProperty",
        "IntProperty",
        "BoolProperty",
        "EnumProperty",
        "PointerProperty",
    ):
        setattr(bpy_props, property_name, lambda **_kwargs: None)

    bpy_types = types.ModuleType("bpy.types")
    bpy_types.Panel = object
    bpy_types.Operator = object
    bpy_types.PropertyGroup = object
    bpy_types.AddonPreferences = object

    bpy_module.app = types.SimpleNamespace(
        timers=types.SimpleNamespace(register=lambda func, first_interval=0.0: func())
    )
    bpy_module.data = types.SimpleNamespace(
        cameras=FakeCameraCollection(),
        objects=FakeObjectCollection(all_objects),
        worlds=FakeWorldCollection(),
    )
    bpy_module.context = types.SimpleNamespace(
        scene=scene, collection=scene.collection, active_object=None
    )

    def camera_add(*, location):
        camera_data = bpy_module.data.cameras.new("Camera")
        camera_object = bpy_module.data.objects.new("Camera", camera_data)
        camera_object.location = list(location)
        scene.collection.objects.link(camera_object)
        bpy_module.context.active_object = camera_object

    bpy_module.ops = types.SimpleNamespace(
        object=types.SimpleNamespace(
            select_all=lambda action: None,
            camera_add=camera_add,
        )
    )
    bpy_module.props = bpy_props
    bpy_module.types = bpy_types
    return bpy_module


def load_composition_handler(fake_bpy):
    module_name = "test_addon_fallback_composition_handler"
    module_path = (
        Path(__file__).resolve().parents[1]
        / "blender_mcp_addon"
        / "handlers"
        / "composition.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.pop(module_name, None)
    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy,
            "bpy.props": fake_bpy.props,
            "bpy.types": fake_bpy.types,
        },
    ):
        spec.loader.exec_module(module)
    return module


def load_legacy_addon_without_composition_handler(fake_bpy):
    addon_module_name = "test_addon_fallback_composition"
    addon_module_path = Path(__file__).resolve().parents[1] / "addon.py"
    spec = importlib.util.spec_from_file_location(addon_module_name, addon_module_path)
    addon = importlib.util.module_from_spec(spec)

    package_module = types.ModuleType("blender_mcp_addon")
    handlers_module = types.ModuleType("blender_mcp_addon.handlers")
    package_module.handlers = handlers_module

    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy,
            "bpy.props": fake_bpy.props,
            "bpy.types": fake_bpy.types,
            "mathutils": types.ModuleType("mathutils"),
            "requests": types.ModuleType("requests"),
            "blender_mcp_addon": package_module,
            "blender_mcp_addon.handlers": handlers_module,
        },
    ):
        sys.modules.pop(addon_module_name, None)
        spec.loader.exec_module(addon)
    return addon


def make_default_scene_bpy():
    return make_fake_bpy()


def make_clear_scene_bpy():
    camera_object = FakeObject("HeroCam", "CAMERA", FakeCameraData("HeroCam"))
    light_object = FakeObject("Key", "LIGHT")
    mesh_object = FakeObject("Bottle", "MESH")
    external_object = FakeObject("Backdrop", "MESH")
    fake_bpy = make_fake_bpy([camera_object, light_object, mesh_object])
    fake_bpy.data.objects._objects[external_object.name] = external_object
    fake_bpy.context.scene.camera = camera_object
    return fake_bpy


def dispatch_legacy_fallback(fake_bpy, command_type, params):
    addon = load_legacy_addon_without_composition_handler(fake_bpy)
    with patch.dict(sys.modules, {"mathutils": types.ModuleType("mathutils")}):
        return addon.BlenderMCPServer()._dispatch_command(command_type, params)


def snapshot_scene_state(fake_bpy):
    scene = fake_bpy.context.scene
    objects = {}
    for obj in fake_bpy.data.objects:
        objects[obj.name] = {
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "camera_type": getattr(getattr(obj, "data", None), "type", None),
            "lens": getattr(getattr(obj, "data", None), "lens", None),
            "ortho_scale": getattr(getattr(obj, "data", None), "ortho_scale", None),
        }

    return {
        "active_camera": getattr(getattr(scene, "camera", None), "name", None),
        "world_color": list(scene.world.color) if scene.world is not None else None,
        "film_transparent": scene.render.film_transparent,
        "render": {
            "engine": scene.render.engine,
            "resolution_x": scene.render.resolution_x,
            "resolution_y": scene.render.resolution_y,
            "cycles_samples": scene.cycles.samples,
            "cycles_denoising": scene.cycles.use_denoising,
            "eevee_samples": scene.eevee.taa_render_samples,
        },
        "objects": objects,
    }


@pytest.mark.parametrize(
    ("command_type", "params", "bpy_factory"),
    [
        (
            "compose_product_shot",
            {
                "product_name": "Bottle",
                "style": "dramatic",
                "background": "transparent",
            },
            make_default_scene_bpy,
        ),
        (
            "compose_isometric_scene",
            {"grid_size": 12.0, "floor": False, "shadow_catcher": False},
            make_default_scene_bpy,
        ),
        (
            "compose_character_scene",
            {
                "character_name": "Hero",
                "environment": "night",
                "ground_plane": False,
            },
            make_default_scene_bpy,
        ),
        (
            "compose_automotive_shot",
            {"car_name": "Coupe", "angle": "side", "environment": "motion"},
            make_default_scene_bpy,
        ),
        ("compose_food_shot", {"style": "angled"}, make_default_scene_bpy),
        (
            "compose_jewelry_shot",
            {"style": "catalog", "reflections": False},
            make_default_scene_bpy,
        ),
        (
            "compose_architectural_shot",
            {"interior": True, "natural_light": False},
            make_default_scene_bpy,
        ),
        (
            "compose_studio_setup",
            {"subject_type": "watch", "mood": "moody"},
            make_default_scene_bpy,
        ),
        (
            "clear_scene",
            {"keep_camera": True, "keep_lights": False},
            make_clear_scene_bpy,
        ),
        (
            "setup_render_settings",
            {
                "engine": "EEVEE",
                "samples": 64,
                "resolution_x": 1280,
                "resolution_y": 720,
                "denoise": False,
            },
            make_default_scene_bpy,
        ),
    ],
)
def test_legacy_addon_fallback_composition_matches_modular_handler(
    command_type, params, bpy_factory
):
    legacy_bpy = bpy_factory()
    modular_bpy = bpy_factory()
    composition = load_composition_handler(modular_bpy)

    legacy_result = dispatch_legacy_fallback(legacy_bpy, command_type, params)
    modular_result = getattr(composition, command_type)(params)

    assert legacy_result == modular_result
    assert snapshot_scene_state(legacy_bpy) == snapshot_scene_state(modular_bpy)
