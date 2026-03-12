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


class FakeObjectCollection:
    def __init__(self, objects=None):
        self._objects = {}
        for obj in objects or []:
            self._objects[obj.name] = obj

    def get(self, name):
        return self._objects.get(name)

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
    return types.SimpleNamespace(
        data=types.SimpleNamespace(
            cameras=FakeCameraCollection(),
            objects=FakeObjectCollection(all_objects),
            worlds=FakeWorldCollection(),
        ),
        context=types.SimpleNamespace(scene=scene, collection=scene.collection),
    )


def load_composition_handler(fake_bpy):
    module_name = "test_blender_mcp_addon_composition"
    module_path = (
        Path(__file__).resolve().parents[1]
        / "blender_mcp_addon"
        / "handlers"
        / "composition.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.pop(module_name, None)
    with patch.dict(sys.modules, {"bpy": fake_bpy}):
        spec.loader.exec_module(module)
    return module


def test_compose_product_shot_sets_active_camera_and_background():
    fake_bpy = make_fake_bpy()
    composition = load_composition_handler(fake_bpy)

    result = composition.compose_product_shot(
        {"product_name": "Bottle", "style": "clean", "background": "transparent"}
    )

    camera_object = fake_bpy.data.objects.get("Bottle Camera")
    assert result["preset"] == "product_shot"
    assert result["camera"] == "Bottle Camera"
    assert fake_bpy.context.scene.camera is camera_object
    assert fake_bpy.context.scene.render.film_transparent is True
    assert camera_object.data.lens == 85.0


def test_compose_isometric_scene_sets_orthographic_camera():
    fake_bpy = make_fake_bpy()
    composition = load_composition_handler(fake_bpy)

    result = composition.compose_isometric_scene({"grid_size": 12.0})

    camera_object = fake_bpy.data.objects.get("Isometric Camera")
    assert result["preset"] == "isometric"
    assert camera_object.data.type == "ORTHO"
    assert camera_object.data.ortho_scale == 12.0


@pytest.mark.parametrize(
    ("handler_name", "params", "expected_preset", "expected_camera", "expected_lens"),
    [
        (
            "compose_character_scene",
            {"character_name": "Hero", "environment": "night", "ground_plane": False},
            "character",
            "Hero Camera",
            70.0,
        ),
        (
            "compose_automotive_shot",
            {"car_name": "Coupe", "angle": "side", "environment": "motion"},
            "automotive",
            "Coupe Camera",
            70.0,
        ),
        (
            "compose_food_shot",
            {"style": "angled"},
            "food",
            "Food Camera",
            65.0,
        ),
        (
            "compose_jewelry_shot",
            {"style": "catalog", "reflections": False},
            "jewelry",
            "Jewelry Camera",
            105.0,
        ),
        (
            "compose_architectural_shot",
            {"interior": True, "natural_light": False},
            "architectural",
            "Architectural Camera",
            24.0,
        ),
        (
            "compose_studio_setup",
            {"subject_type": "watch", "mood": "moody"},
            "studio",
            "Watch Studio Camera",
            80.0,
        ),
    ],
)
def test_composition_presets_set_expected_camera(
    handler_name, params, expected_preset, expected_camera, expected_lens
):
    fake_bpy = make_fake_bpy()
    composition = load_composition_handler(fake_bpy)

    result = getattr(composition, handler_name)(params)

    camera_object = fake_bpy.data.objects.get(expected_camera)
    assert result["preset"] == expected_preset
    assert result["camera"] == expected_camera
    assert fake_bpy.context.scene.camera is camera_object
    assert camera_object.data.lens == expected_lens


def test_compose_product_shot_rejects_unknown_background():
    fake_bpy = make_fake_bpy()
    composition = load_composition_handler(fake_bpy)

    with pytest.raises(ValueError, match="Unsupported product background: neon"):
        composition.compose_product_shot(
            {"product_name": "Bottle", "style": "clean", "background": "neon"}
        )


def test_clear_scene_preserves_camera_when_requested():
    camera_object = FakeObject("HeroCam", "CAMERA", FakeCameraData("HeroCam"))
    light_object = FakeObject("Key", "LIGHT")
    mesh_object = FakeObject("Bottle", "MESH")
    fake_bpy = make_fake_bpy([camera_object, light_object, mesh_object])
    fake_bpy.context.scene.camera = camera_object
    composition = load_composition_handler(fake_bpy)

    result = composition.clear_scene({"keep_camera": True, "keep_lights": False})

    remaining_names = {obj.name for obj in fake_bpy.data.objects}
    assert result["removed_count"] == 2
    assert remaining_names == {"HeroCam"}
    assert result["kept"] == ["HeroCam"]


def test_clear_scene_only_removes_objects_linked_to_active_scene():
    camera_object = FakeObject("HeroCam", "CAMERA", FakeCameraData("HeroCam"))
    mesh_object = FakeObject("Bottle", "MESH")
    external_object = FakeObject("Backdrop", "MESH")
    fake_bpy = make_fake_bpy([camera_object, mesh_object])
    fake_bpy.data.objects._objects[external_object.name] = external_object
    composition = load_composition_handler(fake_bpy)

    result = composition.clear_scene({"keep_camera": False, "keep_lights": False})

    remaining_names = {obj.name for obj in fake_bpy.data.objects}
    assert result["removed"] == ["HeroCam", "Bottle"]
    assert result["removed_count"] == 2
    assert remaining_names == {"Backdrop"}


def test_setup_render_settings_updates_cycles_settings():
    fake_bpy = make_fake_bpy()
    composition = load_composition_handler(fake_bpy)

    result = composition.setup_render_settings(
        {
            "engine": "CYCLES",
            "samples": 256,
            "resolution_x": 2048,
            "resolution_y": 2048,
            "denoise": True,
        }
    )

    scene = fake_bpy.context.scene
    assert result == {
        "status": "success",
        "engine": "CYCLES",
        "samples": 256,
        "resolution_x": 2048,
        "resolution_y": 2048,
        "denoise": True,
    }
    assert scene.render.engine == "CYCLES"
    assert scene.render.resolution_x == 2048
    assert scene.render.resolution_y == 2048
    assert scene.cycles.samples == 256
    assert scene.cycles.use_denoising is True


def test_setup_render_settings_rejects_unknown_engine():
    fake_bpy = make_fake_bpy()
    composition = load_composition_handler(fake_bpy)

    with pytest.raises(ValueError, match="Unsupported render engine"):
        composition.setup_render_settings({"engine": "WORKBENCH"})
