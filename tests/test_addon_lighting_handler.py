import importlib.util
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
        self.bl_idname = node_type
        self.label = ""
        self.location = (0, 0)
        self.inputs = FakeSocketMap()
        self.outputs = FakeSocketMap()

        if node_type == "ShaderNodeTexCoord":
            self.outputs["Generated"] = FakeSocket()
        elif node_type == "ShaderNodeMapping":
            self.inputs["Vector"] = FakeSocket()
            self.inputs["Rotation"] = FakeSocket([0.0, 0.0, 0.0])
            self.outputs["Vector"] = FakeSocket()
        elif node_type == "ShaderNodeTexEnvironment":
            self.inputs["Vector"] = FakeSocket()
            self.outputs["Color"] = FakeSocket()
        elif node_type == "ShaderNodeRGB":
            self.outputs["Color"] = FakeSocket([0.0, 0.0, 0.0, 1.0])
        elif node_type == "ShaderNodeMixRGB":
            self.inputs["Fac"] = FakeSocket(0.5)
            self.inputs["Color1"] = FakeSocket([0.0, 0.0, 0.0, 1.0])
            self.inputs["Color2"] = FakeSocket([0.0, 0.0, 0.0, 1.0])
            self.outputs["Color"] = FakeSocket([0.0, 0.0, 0.0, 1.0])
        elif node_type == "ShaderNodeBackground":
            self.inputs["Color"] = FakeSocket([0.0, 0.0, 0.0, 1.0])
            self.inputs["Strength"] = FakeSocket(1.0)
            self.outputs["Background"] = FakeSocket()
        elif node_type == "ShaderNodeOutputWorld":
            self.inputs["Surface"] = FakeSocket()
            self.inputs["Volume"] = FakeSocket()
        elif node_type == "ShaderNodeVolumeScatter":
            self.inputs["Color"] = FakeSocket([1.0, 1.0, 1.0, 1.0])
            self.inputs["Density"] = FakeSocket(0.0)
            self.inputs["Anisotropy"] = FakeSocket(0.0)
            self.outputs["Volume"] = FakeSocket()


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


class FakeWorld:
    def __init__(self, name):
        self.name = name
        self.use_nodes = False
        self.node_tree = FakeNodeTree()
        self._custom_properties = {}

    def __getitem__(self, key):
        return self._custom_properties[key]

    def __setitem__(self, key, value):
        self._custom_properties[key] = value


class FakeWorldCollection:
    def __init__(self, worlds=None):
        self._worlds = {}
        for world in worlds or []:
            self._worlds[world.name] = world

    def new(self, name):
        world = FakeWorld(name)
        self._worlds[name] = world
        return world


class FakeLightData:
    def __init__(self, name, light_type):
        self.name = name
        self.type = light_type
        self.energy = 10.0
        self.color = [1.0, 1.0, 1.0]
        self.shape = "SQUARE"
        self.size = 1.0
        self.size_y = 1.0


class FakeLightCollection:
    def __init__(self):
        self._lights = {}

    def new(self, name, type):
        light = FakeLightData(name, type)
        self._lights[name] = light
        return light


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
        obj = FakeObject(name, "LIGHT", object_data)
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


class FakeViewSettings:
    def __init__(self):
        self.exposure = 0.0
        self.gamma = 1.0


class FakeScene:
    def __init__(self, world=None, objects=None):
        self.world = world
        self.objects = [] if objects is None else objects
        self.collection = FakeCollection(self.objects)
        self.view_settings = FakeViewSettings()


def load_lighting_handler(fake_bpy):
    module_name = "test_blender_mcp_addon_lighting"
    module_path = (
        Path(__file__).resolve().parents[1]
        / "blender_mcp_addon"
        / "handlers"
        / "lighting.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules.pop(module_name, None)
    with patch.dict(sys.modules, {"bpy": fake_bpy}):
        spec.loader.exec_module(module)
    return module


def load_legacy_addon(fake_bpy):
    module_name = "test_legacy_addon_lighting_fallback"
    module_path = Path(__file__).resolve().parents[1] / "addon.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)

    fake_bpy_module = types.ModuleType("bpy")
    fake_bpy_module.app = types.SimpleNamespace(
        timers=types.SimpleNamespace(register=lambda func, first_interval=0.0: func())
    )
    fake_bpy_module.context = fake_bpy.context
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
    fake_bpy_types.World = FakeWorld

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


def make_fake_bpy(objects=None, world=None, scene_objects=None):
    all_objects = [] if objects is None else list(objects)
    if scene_objects is None:
        scene_objects = list(all_objects)
    else:
        scene_objects = list(scene_objects)
        if objects is None:
            all_objects = list(scene_objects)

    scene = FakeScene(world=world, objects=scene_objects)
    return types.SimpleNamespace(
        data=types.SimpleNamespace(
            lights=FakeLightCollection(),
            objects=FakeObjectCollection(all_objects),
            worlds=FakeWorldCollection([world] if world else []),
        ),
        context=types.SimpleNamespace(scene=scene, collection=scene.collection),
        types=types.SimpleNamespace(World=FakeWorld),
    )


def test_create_area_light_sets_shape_energy_and_transform():
    fake_bpy = make_fake_bpy()
    lighting = load_lighting_handler(fake_bpy)

    result = lighting.create_area_light(
        {
            "name": "SoftBox",
            "light_type": "RECTANGLE",
            "size": 2.5,
            "energy": 650.0,
            "location": [1.0, -2.0, 3.5],
            "rotation": [0.5, 0.0, 0.25],
            "color": [1.0, 0.95, 0.9],
        }
    )

    light_object = fake_bpy.data.objects.get("SoftBox")

    assert result == {
        "status": "success",
        "name": "SoftBox",
        "type": "area",
        "shape": "RECTANGLE",
        "energy": 650.0,
    }
    assert light_object.data.shape == "RECTANGLE"
    assert light_object.data.size == 2.5
    assert light_object.data.size_y == 2.5
    assert light_object.data.color == [1.0, 0.95, 0.9]
    assert light_object.location == [1.0, -2.0, 3.5]
    assert light_object.rotation_euler == [0.5, 0.0, 0.25]


def test_create_three_point_lighting_creates_three_named_lights():
    fake_bpy = make_fake_bpy()
    lighting = load_lighting_handler(fake_bpy)

    result = lighting.create_three_point_lighting(
        {
            "key_intensity": 1200.0,
            "fill_intensity": 650.0,
            "rim_intensity": 900.0,
        }
    )

    listed = lighting.list_lights()

    assert result == {
        "status": "success",
        "preset": "three_point",
        "lights": ["Three Point Key", "Three Point Fill", "Three Point Rim"],
    }
    assert listed["count"] == 3
    assert [light["name"] for light in listed["lights"]] == [
        "Three Point Key",
        "Three Point Fill",
        "Three Point Rim",
    ]


def test_create_studio_lighting_three_point_uses_default_colors_when_omitted():
    fake_bpy = make_fake_bpy()
    lighting = load_lighting_handler(fake_bpy)

    result = lighting.create_studio_lighting(
        {"preset": "three_point", "intensity": 500.0}
    )

    assert result == {
        "status": "success",
        "preset": "three_point",
        "lights": ["Three Point Key", "Three Point Fill", "Three Point Rim"],
    }
    assert fake_bpy.data.objects.get("Three Point Key").data.color == [1.0, 0.95, 0.9]
    assert fake_bpy.data.objects.get("Three Point Fill").data.color == [0.85, 0.9, 1.0]
    assert fake_bpy.data.objects.get("Three Point Rim").data.color == [1.0, 0.98, 0.92]


def test_create_hdri_environment_builds_world_node_graph():
    fake_bpy = make_fake_bpy()
    lighting = load_lighting_handler(fake_bpy)

    result = lighting.create_hdri_environment(
        {
            "hdri_name": "studio_small_03",
            "strength": 1.2,
            "rotation": 90.0,
            "blur": 0.15,
        }
    )

    world = fake_bpy.context.scene.world
    node_types = [node.type for node in world.node_tree.nodes]
    mapping = world.node_tree.nodes[1]
    placeholder_color = world.node_tree.nodes[3]
    mix = world.node_tree.nodes[4]
    background = world.node_tree.nodes[5]

    assert result == {
        "status": "success",
        "hdri_name": "studio_small_03",
        "strength": 1.2,
        "rotation": 90.0,
        "blur": 0.15,
    }
    assert world.use_nodes is True
    assert node_types == [
        "ShaderNodeTexCoord",
        "ShaderNodeMapping",
        "ShaderNodeTexEnvironment",
        "ShaderNodeRGB",
        "ShaderNodeMixRGB",
        "ShaderNodeBackground",
        "ShaderNodeOutputWorld",
    ]
    assert round(mapping.inputs["Rotation"].default_value[2], 4) == 1.5708
    assert background.inputs["Strength"].default_value == 1.2
    assert placeholder_color.outputs[
        "Color"
    ].default_value == lighting._hdri_placeholder_color("studio_small_03", 0.15)
    assert mix.inputs["Fac"].default_value == 0.15
    assert world["blender_mcp_hdri_name"] == "studio_small_03"
    assert world["blender_mcp_hdri_blur"] == 0.15


def test_create_volumetric_lighting_and_adjust_exposure_update_world_and_scene():
    world = FakeWorld("World")
    fake_bpy = make_fake_bpy(world=world)
    lighting = load_lighting_handler(fake_bpy)

    volume_result = lighting.create_volumetric_lighting(
        {"density": 0.2, "anisotropy": 0.35, "color": [0.7, 0.8, 1.0]}
    )
    exposure_result = lighting.adjust_light_exposure({"exposure": 1.5, "gamma": 1.1})

    volume_node = world.node_tree.nodes[1]

    assert volume_result == {
        "status": "success",
        "density": 0.2,
        "anisotropy": 0.35,
        "color": [0.7, 0.8, 1.0],
    }
    assert volume_node.type == "ShaderNodeVolumeScatter"
    assert volume_node.inputs["Density"].default_value == 0.2
    assert volume_node.inputs["Anisotropy"].default_value == 0.35
    assert fake_bpy.context.scene.view_settings.exposure == 1.5
    assert exposure_result == {"status": "success", "exposure": 1.5, "gamma": 1.1}


def test_clear_lights_removes_only_light_objects():
    light_data = FakeLightData("Key", "AREA")
    key_light = FakeObject("Key", "LIGHT", light_data)
    camera = FakeObject("Camera", "CAMERA", data=None)
    fake_bpy = make_fake_bpy(objects=[key_light, camera])
    lighting = load_lighting_handler(fake_bpy)

    result = lighting.clear_lights()

    assert result == {"status": "success", "removed_count": 1}
    assert fake_bpy.data.objects.get("Key") is None
    assert fake_bpy.data.objects.get("Camera") is camera


def test_scene_scoped_light_commands_ignore_lights_outside_active_scene():
    active_light = FakeObject(
        "Active Light", "LIGHT", FakeLightData("Active Light", "AREA")
    )
    shared_camera = FakeObject("Camera", "CAMERA", data=None)
    other_scene_light = FakeObject(
        "Other Scene Light", "LIGHT", FakeLightData("Other Scene Light", "AREA")
    )
    fake_bpy = make_fake_bpy(
        objects=[active_light, shared_camera, other_scene_light],
        scene_objects=[active_light, shared_camera],
    )
    lighting = load_lighting_handler(fake_bpy)

    listed = lighting.list_lights()
    cleared = lighting.clear_lights()

    assert listed == {
        "lights": [
            {
                "name": "Active Light",
                "type": "AREA",
                "energy": 10.0,
                "color": [1.0, 1.0, 1.0],
                "location": [0.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0],
            }
        ],
        "count": 1,
    }
    assert cleared == {"status": "success", "removed_count": 1}
    assert fake_bpy.data.objects.get("Active Light") is None
    assert fake_bpy.data.objects.get("Other Scene Light") is other_scene_light


def test_legacy_fallback_supports_same_studio_presets_as_modular_handler():
    fake_bpy = make_fake_bpy()
    lighting = load_lighting_handler(fake_bpy)
    legacy_addon = load_legacy_addon(fake_bpy)

    assert legacy_addon._FALLBACK_STUDIO_PRESET_SPECS == lighting._STUDIO_PRESET_SPECS

    result = legacy_addon._fallback_create_studio_lighting(
        {"preset": "butterfly", "intensity": 600.0}
    )

    assert result == {
        "status": "success",
        "preset": "butterfly",
        "lights": ["Butterfly Key", "Butterfly Fill"],
    }


def test_legacy_fallback_three_point_uses_default_colors_when_omitted():
    fake_bpy = make_fake_bpy()
    legacy_addon = load_legacy_addon(fake_bpy)

    result = legacy_addon._fallback_create_studio_lighting(
        {"preset": "three_point", "intensity": 500.0}
    )

    assert result == {
        "status": "success",
        "preset": "three_point",
        "lights": ["Three Point Key", "Three Point Fill", "Three Point Rim"],
    }
    assert fake_bpy.data.objects.get("Three Point Key").data.color == [1.0, 0.95, 0.9]
    assert fake_bpy.data.objects.get("Three Point Fill").data.color == [0.85, 0.9, 1.0]
    assert fake_bpy.data.objects.get("Three Point Rim").data.color == [1.0, 0.98, 0.92]


def test_legacy_fallback_hdri_environment_applies_hdri_name_and_blur_state():
    fake_bpy = make_fake_bpy()
    legacy_addon = load_legacy_addon(fake_bpy)

    result = legacy_addon._fallback_create_hdri_environment(
        {
            "hdri_name": "studio_small_03",
            "strength": 1.2,
            "rotation": 90.0,
            "blur": 0.15,
        }
    )

    world = fake_bpy.context.scene.world
    placeholder_color = world.node_tree.nodes[3]
    mix = world.node_tree.nodes[4]

    assert result == {
        "status": "success",
        "hdri_name": "studio_small_03",
        "strength": 1.2,
        "rotation": 90.0,
        "blur": 0.15,
    }
    assert placeholder_color.outputs["Color"].default_value == (
        legacy_addon._lighting_hdri_placeholder_color("studio_small_03", 0.15)
    )
    assert mix.inputs["Fac"].default_value == 0.15
    assert world["blender_mcp_hdri_name"] == "studio_small_03"
    assert world["blender_mcp_hdri_blur"] == 0.15


def test_legacy_fallback_light_commands_are_scene_scoped():
    active_light = FakeObject(
        "Active Light", "LIGHT", FakeLightData("Active Light", "AREA")
    )
    other_scene_light = FakeObject(
        "Other Scene Light", "LIGHT", FakeLightData("Other Scene Light", "AREA")
    )
    fake_bpy = make_fake_bpy(
        objects=[active_light, other_scene_light],
        scene_objects=[active_light],
    )
    legacy_addon = load_legacy_addon(fake_bpy)

    listed = legacy_addon._fallback_list_lights()
    cleared = legacy_addon._fallback_clear_lights()

    assert listed["count"] == 1
    assert listed["lights"][0]["name"] == "Active Light"
    assert cleared == {"status": "success", "removed_count": 1}
    assert fake_bpy.data.objects.get("Other Scene Light") is other_scene_light
