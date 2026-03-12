import importlib.util
import math
import sys
import types
import ast
from pathlib import Path
from unittest.mock import Mock, patch


class FakeDOF:
    def __init__(self):
        self.use_dof = False
        self.focus_distance = 0.0
        self.aperture_fstop = 0.0


class FakeCameraData:
    def __init__(self, name):
        self.name = name
        self.type = "PERSP"
        self.lens = 50.0
        self.ortho_scale = 10.0
        self.dof = FakeDOF()


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
        self.dimensions = [0.0, 0.0, 0.0]
        self.selected = False
        self._custom_properties = {}

    def select_get(self):
        return self.selected

    def get(self, key, default=None):
        return self._custom_properties.get(key, default)

    def __getitem__(self, key):
        return self._custom_properties[key]

    def __setitem__(self, key, value):
        self._custom_properties[key] = value


class FakeMatrixWorld:
    def __init__(self, scale=(1.0, 1.0, 1.0), translation=(0.0, 0.0, 0.0)):
        self.scale = [float(component) for component in scale]
        self.translation = [float(component) for component in translation]

    def __matmul__(self, point):
        components = list(point)
        return [
            (components[index] * self.scale[index]) + self.translation[index]
            for index in range(3)
        ]


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

    def __iter__(self):
        return iter(self.linked)


class FakeCollection:
    def __init__(self, linked=None):
        self.objects = FakeCollectionObjects(linked)


class FakeScene:
    def __init__(self, objects=None, selected_objects=None):
        self.objects = [] if objects is None else objects
        self.collection = FakeCollection(self.objects)
        self.selected_objects = [] if selected_objects is None else selected_objects
        self.camera = None


def make_fake_bpy(objects=None, selected_objects=None):
    all_objects = [] if objects is None else list(objects)
    scene = FakeScene(objects=all_objects, selected_objects=selected_objects)
    return types.SimpleNamespace(
        data=types.SimpleNamespace(
            cameras=FakeCameraCollection(),
            objects=FakeObjectCollection(all_objects),
        ),
        context=types.SimpleNamespace(
            scene=scene,
            collection=scene.collection,
            selected_objects=scene.selected_objects,
        ),
    )


def load_camera_handler(fake_bpy):
    module_name = "test_blender_mcp_addon_camera"
    module_path = (
        Path(__file__).resolve().parents[1]
        / "blender_mcp_addon"
        / "handlers"
        / "camera.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.pop(module_name, None)
    with patch.dict(sys.modules, {"bpy": fake_bpy}):
        spec.loader.exec_module(module)
    return module


def load_addon_module(fake_bpy):
    module_name = "test_blender_mcp_addon_legacy"
    module_path = Path(__file__).resolve().parents[1] / "addon.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)

    fake_bpy_module = types.ModuleType("bpy")
    fake_bpy_module.data = fake_bpy.data
    fake_bpy_module.context = fake_bpy.context
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

    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy_module,
            "bpy.props": fake_bpy_props,
            "bpy.types": fake_bpy_types,
            "requests": types.ModuleType("requests"),
        },
    ):
        sys.modules.pop(module_name, None)
        spec.loader.exec_module(module)
    return module


def _read_fallback_literal(function_name, assignment_name):
    addon_source = (Path(__file__).resolve().parents[1] / "addon.py").read_text()
    module_ast = ast.parse(addon_source)

    for node in module_ast.body:
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue
        for statement in node.body:
            if not isinstance(statement, ast.Assign):
                continue
            for target in statement.targets:
                if isinstance(target, ast.Name) and target.id == assignment_name:
                    return ast.literal_eval(statement.value)

    raise AssertionError(f"Could not find {assignment_name} in {function_name}")


def test_create_composition_camera_sets_lens_and_links_camera():
    fake_bpy = make_fake_bpy()
    camera = load_camera_handler(fake_bpy)

    result = camera.create_composition_camera(
        {
            "name": "HeroCam",
            "composition": "rule_of_thirds",
            "focal_length": 85.0,
            "location": [2.0, -5.0, 3.0],
            "target": [0.0, 0.0, 1.0],
        }
    )

    camera_object = fake_bpy.data.objects.get("HeroCam")
    assert result == {
        "status": "success",
        "name": "HeroCam",
        "composition": "rule_of_thirds",
        "lens": 85.0,
    }
    assert camera_object.type == "CAMERA"
    assert camera_object.location == [2.0, -5.0, 3.0]
    assert camera_object.data.lens == 85.0


def test_create_isometric_camera_sets_orthographic_mode():
    fake_bpy = make_fake_bpy()
    camera = load_camera_handler(fake_bpy)

    result = camera.create_isometric_camera(
        {"name": "Iso", "ortho_scale": 12.0, "angle": 35.264}
    )

    camera_object = fake_bpy.data.objects.get("Iso")
    assert result == {
        "status": "success",
        "name": "Iso",
        "type": "orthographic",
        "ortho_scale": 12.0,
        "angle": 35.264,
    }
    assert camera_object.data.type == "ORTHO"
    assert camera_object.data.ortho_scale == 12.0
    assert round(camera_object.rotation_euler[2], 4) == round(math.radians(45.0), 4)


def test_camera_dof_preset_and_active_camera_work_together():
    camera_object = FakeObject("HeroCam", "CAMERA", FakeCameraData("HeroCam"))
    fake_bpy = make_fake_bpy(objects=[camera_object])
    camera = load_camera_handler(fake_bpy)

    dof_result = camera.set_camera_depth_of_field(
        {
            "camera_name": "HeroCam",
            "focus_distance": 4.5,
            "focal_length": 90.0,
            "aperture": 2.8,
        }
    )
    preset_result = camera.apply_camera_preset(
        {"camera_name": "HeroCam", "preset": "portrait"}
    )
    active_result = camera.set_active_camera({"camera_name": "HeroCam"})
    listed = camera.list_cameras()

    assert dof_result == {
        "status": "success",
        "camera": "HeroCam",
        "focus_distance": 4.5,
        "aperture": 2.8,
        "lens": 90.0,
    }
    assert preset_result == {
        "status": "success",
        "camera": "HeroCam",
        "preset": "portrait",
        "lens": 85.0,
        "aperture": 2.8,
    }
    assert active_result == {"status": "success", "active_camera": "HeroCam"}
    assert listed["active_camera"] == "HeroCam"
    assert listed["cameras"][0]["is_active"] is True


def test_frame_camera_to_selection_moves_camera_toward_selection():
    camera_object = FakeObject("HeroCam", "CAMERA", FakeCameraData("HeroCam"))
    selected = FakeObject("Cube", "MESH", data=None)
    selected.location = [1.0, 2.0, 3.0]
    selected.dimensions = [2.0, 4.0, 6.0]
    selected.selected = True
    fake_bpy = make_fake_bpy(
        objects=[camera_object, selected], selected_objects=[selected]
    )
    camera = load_camera_handler(fake_bpy)

    result = camera.frame_camera_to_selection(
        {"camera_name": "HeroCam", "margin": 1.25}
    )

    assert result == {
        "status": "success",
        "camera": "HeroCam",
        "center": [1.0, 2.0, 3.0],
        "size": [2.0, 4.0, 6.0],
        "margin": 1.25,
    }
    assert camera_object.location == [1.0, -13.0, 10.5]


def test_frame_camera_to_selection_uses_world_space_bound_box_when_available():
    camera_object = FakeObject("HeroCam", "CAMERA", FakeCameraData("HeroCam"))
    selected = FakeObject("OffsetCube", "MESH", data=None)
    selected.location = [100.0, 100.0, 100.0]
    selected.dimensions = [1.0, 1.0, 1.0]
    selected.bound_box = [
        [-1.0, -1.0, -1.0],
        [-1.0, -1.0, 1.0],
        [-1.0, 1.0, -1.0],
        [-1.0, 1.0, 1.0],
        [1.0, -1.0, -1.0],
        [1.0, -1.0, 1.0],
        [1.0, 1.0, -1.0],
        [1.0, 1.0, 1.0],
    ]
    selected.matrix_world = FakeMatrixWorld(
        scale=(2.0, 3.0, 4.0), translation=(10.0, 0.0, 5.0)
    )
    selected.selected = True
    fake_bpy = make_fake_bpy(
        objects=[camera_object, selected], selected_objects=[selected]
    )
    camera = load_camera_handler(fake_bpy)
    legacy_addon = load_addon_module(fake_bpy)
    legacy_addon.resolve_id = fake_bpy.data.objects.get

    modular_result = camera.frame_camera_to_selection(
        {"camera_name": "HeroCam", "margin": 1.25}
    )
    modular_location = list(camera_object.location)

    camera_object.location = [0.0, 0.0, 0.0]
    camera_object.rotation_euler = [0.0, 0.0, 0.0]
    fallback_result = legacy_addon._fallback_frame_camera_to_selection(
        {"camera_name": "HeroCam", "margin": 1.25}
    )

    assert modular_result == {
        "status": "success",
        "camera": "HeroCam",
        "center": [10.0, 0.0, 5.0],
        "size": [4.0, 6.0, 8.0],
        "margin": 1.25,
    }
    assert modular_location == [10.0, -20.0, 15.0]
    assert fallback_result == modular_result
    assert camera_object.location == modular_location


def test_legacy_composition_camera_reuses_existing_camera_name():
    fake_bpy = make_fake_bpy()
    legacy_addon = load_addon_module(fake_bpy)
    legacy_addon.resolve_id = fake_bpy.data.objects.get
    create_camera_calls = []

    def fake_create_camera(params):
        requested_name = str(params["name"])
        actual_name = requested_name
        if fake_bpy.data.objects.get(requested_name) is not None:
            actual_name = f"{requested_name}.001"

        camera_data = FakeCameraData(actual_name)
        camera_data.lens = float(params["lens"])
        camera_object = FakeObject(actual_name, "CAMERA", camera_data)
        camera_object.location = list(params["location"])
        camera_object.rotation_euler = legacy_addon._camera_look_at_rotation(
            camera_object.location,
            list(params["look_at"]),
        )
        fake_bpy.data.objects._objects[actual_name] = camera_object
        fake_bpy.context.scene.objects.append(camera_object)
        create_camera_calls.append(actual_name)
        return {"name": actual_name, "lens": camera_data.lens}

    legacy_addon.create_camera = fake_create_camera

    first_result = legacy_addon._fallback_create_composition_camera(
        {
            "name": "HeroCam",
            "composition": "center",
            "focal_length": 50.0,
            "location": [0.0, -6.0, 3.0],
            "target": [0.0, 0.0, 1.0],
        }
    )
    second_result = legacy_addon._fallback_create_composition_camera(
        {
            "name": "HeroCam",
            "composition": "golden_ratio",
            "focal_length": 85.0,
            "location": [2.0, -4.0, 5.0],
            "target": [1.0, 0.0, 0.5],
        }
    )

    camera_object = fake_bpy.data.objects.get("HeroCam")
    assert first_result == {
        "status": "success",
        "name": "HeroCam",
        "composition": "center",
        "lens": 50.0,
    }
    assert second_result == {
        "status": "success",
        "name": "HeroCam",
        "composition": "golden_ratio",
        "lens": 85.0,
    }
    assert create_camera_calls == ["HeroCam"]
    assert fake_bpy.data.objects.get("HeroCam.001") is None
    assert camera_object.location == [2.0, -4.0, 5.0]
    assert camera_object.data.lens == 85.0


def test_legacy_isometric_camera_reuses_existing_camera_name():
    fake_bpy = make_fake_bpy()
    legacy_addon = load_addon_module(fake_bpy)
    legacy_addon.resolve_id = fake_bpy.data.objects.get
    create_camera_calls = []

    def fake_create_camera(params):
        requested_name = str(params["name"])
        actual_name = requested_name
        if fake_bpy.data.objects.get(requested_name) is not None:
            actual_name = f"{requested_name}.001"

        camera_data = FakeCameraData(actual_name)
        camera_data.lens = float(params["lens"])
        camera_object = FakeObject(actual_name, "CAMERA", camera_data)
        camera_object.location = list(params["location"])
        fake_bpy.data.objects._objects[actual_name] = camera_object
        fake_bpy.context.scene.objects.append(camera_object)
        create_camera_calls.append(actual_name)
        return {"name": actual_name, "lens": camera_data.lens}

    legacy_addon.create_camera = fake_create_camera

    first_result = legacy_addon._fallback_create_isometric_camera(
        {"name": "IsoCam", "ortho_scale": 10.0, "angle": 35.264}
    )
    second_result = legacy_addon._fallback_create_isometric_camera(
        {"name": "IsoCam", "ortho_scale": 14.0, "angle": 40.0}
    )

    camera_object = fake_bpy.data.objects.get("IsoCam")
    assert first_result == {
        "status": "success",
        "name": "IsoCam",
        "type": "orthographic",
        "ortho_scale": 10.0,
        "angle": 35.264,
    }
    assert second_result == {
        "status": "success",
        "name": "IsoCam",
        "type": "orthographic",
        "ortho_scale": 14.0,
        "angle": 40.0,
    }
    assert create_camera_calls == ["IsoCam"]
    assert fake_bpy.data.objects.get("IsoCam.001") is None
    assert camera_object.data.type == "ORTHO"
    assert camera_object.data.ortho_scale == 14.0
    assert camera_object.location == [10.0, -10.0, 10.0]


def test_legacy_camera_tables_match_modular_handler_constants():
    fake_bpy = make_fake_bpy()
    camera = load_camera_handler(fake_bpy)

    fallback_composition_offsets = _read_fallback_literal(
        "_fallback_create_composition_camera", "composition_offsets"
    )
    fallback_preset_map = _read_fallback_literal(
        "_fallback_apply_camera_preset", "preset_map"
    )

    assert fallback_composition_offsets == camera._COMPOSITION_OFFSETS
    assert fallback_preset_map == camera._CAMERA_PRESETS
