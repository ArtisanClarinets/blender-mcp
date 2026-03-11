# Blender MCP Addon - Single File Version
# This file can be installed directly into Blender
# Generated from blender_mcp_addon package

bl_info = {
    "name": "Blender MCP",
    "author": "BlenderMCP",
    "version": (1, 5, 5),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to AI assistants via MCP with full API support",
    "category": "Interface",
    "support": "COMMUNITY",
}

import bpy
import bpy.props
import threading
import socket
import json
import traceback
import uuid
import hashlib
import tempfile
import os
import requests
import shutil
import zipfile
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    PointerProperty,
)
from bpy.types import Panel, Operator, PropertyGroup, AddonPreferences

# =============================================================================
# PROTOCOL MODULE
# =============================================================================


def encode_command(command):
    """Encode a command to bytes using newline-delimited JSON."""
    json_str = json.dumps(command) + "\n"
    return json_str.encode("utf-8")


def decode_response(data):
    """Decode a response from bytes."""
    try:
        json_str = data.decode("utf-8").strip()
        return json.loads(json_str)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def create_response(ok, data=None, error=None, request_id=None, meta=None):
    """Create a standardized response envelope."""
    response = {"ok": ok, "request_id": request_id}
    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    if meta is not None:
        response["meta"] = meta
    return response


def create_success_response(data, request_id=None, meta=None):
    """Create a success response."""
    return create_response(ok=True, data=data, request_id=request_id, meta=meta)


def create_error_response(code, message, details=None, request_id=None):
    """Create an error response."""
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return create_response(ok=False, error=error, request_id=request_id)


def parse_command(data):
    """Parse a command from bytes."""
    try:
        json_str = data.decode("utf-8").strip()
        command = json.loads(json_str)
        if "type" not in command:
            return None
        if "request_id" not in command:
            return None
        return command
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# =============================================================================
# ID MODULE
# =============================================================================

MCP_UUID_KEY = "mcp_uuid"


def assign_uuid(obj):
    """Assign a stable UUID to a Blender object."""
    if MCP_UUID_KEY not in obj:
        obj[MCP_UUID_KEY] = str(uuid.uuid4())
    return obj[MCP_UUID_KEY]


def get_uuid(obj):
    """Get the UUID of an object if assigned."""
    return obj.get(MCP_UUID_KEY)


def resolve_id(id_or_name):
    """Resolve an ID or name to a Blender object."""
    for obj in bpy.data.objects:
        if get_uuid(obj) == id_or_name:
            return obj
    if id_or_name in bpy.data.objects:
        return bpy.data.objects[id_or_name]
    return None


def resolve_multiple_ids(ids_or_names):
    """Resolve multiple IDs or names to Blender objects."""
    result = []
    for id_or_name in ids_or_names:
        obj = resolve_id(id_or_name)
        if obj:
            result.append(obj)
    return result


def get_object_info_with_uuid(obj):
    """Get object info including UUID."""
    return {
        "id": assign_uuid(obj),
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
        "dimensions": list(obj.dimensions),
        "visible": obj.visible_get(),
        "selected": obj.select_get(),
    }


# =============================================================================
# UTILS MODULE
# =============================================================================


def ensure_dir(path):
    """Ensure a directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def write_json(data, path, indent=2):
    """Write data to JSON file."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    return path


def read_json(path):
    """Read data from JSON file."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_hash(data):
    """Compute a stable hash of data."""
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()[:16]


def get_temp_dir():
    """Get a temporary directory for the addon."""
    temp_dir = os.path.join(tempfile.gettempdir(), "blender_mcp")
    ensure_dir(temp_dir)
    return temp_dir


def get_scene_bounds():
    """Get the bounding box of the entire scene."""
    min_bound = [float("inf")] * 3
    max_bound = [float("-inf")] * 3

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ corner
                for i in range(3):
                    min_bound[i] = min(min_bound[i], world_corner[i])
                    max_bound[i] = max(max_bound[i], world_corner[i])

    if min_bound[0] == float("inf"):
        min_bound = [0, 0, 0]
        max_bound = [0, 0, 0]

    return {
        "min": min_bound,
        "max": max_bound,
        "center": [(min_bound[i] + max_bound[i]) / 2 for i in range(3)],
        "size": [max_bound[i] - min_bound[i] for i in range(3)],
    }


# =============================================================================
# API CONFIGURATION MANAGER
# =============================================================================


class APIManager:
    """Manages API keys and configurations for all providers."""

    @staticmethod
    def get_preferences():
        """Get addon preferences."""
        return bpy.context.preferences.addons[__name__].preferences

    @staticmethod
    def get_polyhaven_config():
        """Get PolyHaven configuration."""
        prefs = APIManager.get_preferences()
        return {
            "enabled": prefs.polyhaven_enabled,
            "api_key": prefs.polyhaven_api_key if prefs.polyhaven_api_key else None,
            "base_url": "https://api.polyhaven.com",
        }

    @staticmethod
    def get_sketchfab_config():
        """Get Sketchfab configuration."""
        prefs = APIManager.get_preferences()
        return {
            "enabled": prefs.sketchfab_enabled,
            "api_key": prefs.sketchfab_api_key if prefs.sketchfab_api_key else None,
            "base_url": "https://api.sketchfab.com/v3",
        }

    @staticmethod
    def get_hyper3d_config():
        """Get Hyper3D Rodin configuration."""
        prefs = APIManager.get_preferences()
        return {
            "enabled": prefs.hyper3d_enabled,
            "api_key": prefs.hyper3d_api_key if prefs.hyper3d_api_key else None,
            "mode": prefs.hyper3d_mode,  # 'fal' or 'main_site'
            "base_url": "https://hyper3d.ai"
            if prefs.hyper3d_mode == "main_site"
            else "https://fal.ai",
        }

    @staticmethod
    def get_hunyuan3d_config():
        """Get Hunyuan3D configuration."""
        prefs = APIManager.get_preferences()
        return {
            "enabled": prefs.hunyuan3d_enabled,
            "mode": prefs.hunyuan3d_mode,  # 'official', 'local', or 'custom'
            "api_key": prefs.hunyuan3d_api_key if prefs.hunyuan3d_api_key else None,
            "secret_key": prefs.hunyuan3d_secret_key
            if prefs.hunyuan3d_secret_key
            else None,
            "local_path": prefs.hunyuan3d_local_path
            if prefs.hunyuan3d_local_path
            else None,
            "custom_endpoint": prefs.hunyuan3d_custom_endpoint
            if prefs.hunyuan3d_custom_endpoint
            else None,
        }

    @staticmethod
    def get_tripo3d_config():
        """Get Tripo3D configuration."""
        prefs = APIManager.get_preferences()
        return {
            "enabled": prefs.tripo3d_enabled,
            "api_key": prefs.tripo3d_api_key if prefs.tripo3d_api_key else None,
            "base_url": "https://api.tripo3d.ai/v1",
        }

    @staticmethod
    def get_local_model_config():
        """Get local 3D generation model configuration."""
        prefs = APIManager.get_preferences()
        return {
            "enabled": prefs.local_model_enabled,
            "model_type": prefs.local_model_type,  # 'hunyuan', 'instantmesh', 'crm', 'etc'
            "model_path": prefs.local_model_path if prefs.local_model_path else None,
            "python_executable": prefs.local_model_python
            if prefs.local_model_python
            else sys.executable,
            "server_port": prefs.local_model_port,
            "launch_command": prefs.local_model_command
            if prefs.local_model_command
            else None,
            "api_endpoint": f"http://localhost:{prefs.local_model_port}"
            if prefs.local_model_enabled
            else None,
        }


# =============================================================================
# LOCAL MODEL SERVER MANAGER
# =============================================================================


class LocalModelServerManager:
    """Manages local 3D generation model servers."""

    _process = None
    _server_running = False

    @classmethod
    def start_server(cls):
        """Start the local model server."""
        config = APIManager.get_local_model_config()
        if not config["enabled"]:
            return {"status": "error", "message": "Local model server is not enabled"}

        if cls._server_running and cls._process:
            return {
                "status": "success",
                "message": "Server already running",
                "port": config["server_port"],
            }

        try:
            if config["launch_command"]:
                # Use custom launch command
                cmd = config["launch_command"]
            else:
                # Default launch based on model type
                model_type = config["model_type"]
                model_path = config["model_path"]
                python = config["python_executable"]
                port = config["server_port"]

                if model_type == "hunyuan":
                    cmd = f"{python} {model_path}/gradio_app.py --server_port {port}"
                elif model_type == "instantmesh":
                    cmd = f"{python} {model_path}/run.py --port {port}"
                else:
                    return {
                        "status": "error",
                        "message": f"Auto-launch not supported for model type: {model_type}",
                    }

            # Start the process
            cls._process = subprocess.Popen(
                cmd.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=config["model_path"],
            )
            cls._server_running = True

            return {
                "status": "success",
                "message": f"Started {config['model_type']} server on port {config['server_port']}",
                "port": config["server_port"],
                "pid": cls._process.pid,
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    @classmethod
    def stop_server(cls):
        """Stop the local model server."""
        if cls._process:
            cls._process.terminate()
            cls._process.wait()
            cls._process = None
            cls._server_running = False
            return {"status": "success", "message": "Server stopped"}
        return {"status": "success", "message": "Server was not running"}

    @classmethod
    def get_status(cls):
        """Get local server status."""
        config = APIManager.get_local_model_config()
        if not config["enabled"]:
            return {
                "enabled": False,
                "running": False,
                "message": "Local model server is disabled",
            }

        # Check if process is still alive
        if cls._process:
            cls._server_running = cls._process.poll() is None

        return {
            "enabled": True,
            "running": cls._server_running,
            "model_type": config["model_type"],
            "port": config["server_port"],
            "endpoint": config["api_endpoint"],
        }


# =============================================================================
# SCENE OBSERVE HANDLER
# =============================================================================


def observe_scene(params):
    """Observe the current scene with configurable detail."""
    detail = params.get("detail", "med")
    include_screenshot = params.get("include_screenshot", False)
    max_screenshot_size = params.get("max_screenshot_size", 800)

    result = {
        "scene_hash": get_scene_hash(),
        "objects": [],
        "collections": [],
        "cameras": [],
        "lights": [],
        "world": {},
        "render_settings": {},
        "bounds": get_scene_bounds(),
    }

    # Get objects based on detail level
    if detail == "low":
        result["objects"] = [
            {"name": obj.name, "type": obj.type} for obj in bpy.data.objects
        ]
    elif detail == "med":
        result["objects"] = [get_object_info_with_uuid(obj) for obj in bpy.data.objects]
    else:  # high
        result["objects"] = [get_detailed_object_info(obj) for obj in bpy.data.objects]

    # Get collections
    result["collections"] = [
        {"name": col.name, "objects": [obj.name for obj in col.objects]}
        for col in bpy.data.collections
    ]

    # Get cameras
    result["cameras"] = [
        {
            "name": cam.name,
            "location": list(cam.location),
            "rotation": list(cam.rotation_euler),
            "lens": cam.data.lens if cam.data else 50,
        }
        for cam in bpy.data.objects
        if cam.type == "CAMERA"
    ]

    # Get lights
    result["lights"] = [
        {
            "name": light.name,
            "type": light.data.type if light.data else "POINT",
            "energy": light.data.energy if light.data else 0,
            "color": list(light.data.color) if light.data else [1, 1, 1],
            "location": list(light.location),
        }
        for light in bpy.data.objects
        if light.type == "LIGHT"
    ]

    # Get world settings
    if bpy.context.scene.world:
        world = bpy.context.scene.world
        result["world"] = {
            "name": world.name,
            "use_nodes": world.use_nodes,
            "color": list(world.color) if not world.use_nodes else None,
        }

    # Get render settings
    render = bpy.context.scene.render
    result["render_settings"] = {
        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "resolution_percentage": render.resolution_percentage,
        "engine": render.engine,
    }

    # Capture screenshot if requested
    if include_screenshot:
        result["screenshot"] = capture_viewport_screenshot(max_screenshot_size)

    return result


def get_scene_hash():
    """Compute a stable hash of the scene state."""
    data = {
        "objects": [
            {
                "name": obj.name,
                "type": obj.type,
                "location": [round(x, 4) for x in obj.location],
                "rotation": [round(x, 4) for x in obj.rotation_euler],
                "scale": [round(x, 4) for x in obj.scale],
                "materials": [mat.name for mat in obj.data.materials]
                if hasattr(obj.data, "materials")
                else [],
            }
            for obj in sorted(bpy.data.objects, key=lambda x: x.name)
        ]
    }
    return compute_hash(data)


def get_scene_info():
    """Get detailed scene information."""
    return {
        "name": bpy.context.scene.name,
        "frame_start": bpy.context.scene.frame_start,
        "frame_end": bpy.context.scene.frame_end,
        "frame_current": bpy.context.scene.frame_current,
        "objects_count": len(bpy.data.objects),
        "objects": [get_object_info_with_uuid(obj) for obj in bpy.data.objects],
        "collections": [col.name for col in bpy.data.collections],
        "active_object": bpy.context.active_object.name
        if bpy.context.active_object
        else None,
    }


def get_object_info(params):
    """Get detailed information about a specific object."""
    object_name = params.get("object_name")
    if not object_name:
        raise ValueError("object_name is required")

    obj = resolve_id(object_name)
    if not obj:
        raise ValueError(f"Object not found: {object_name}")

    return get_detailed_object_info(obj)


def get_detailed_object_info(obj):
    """Get detailed information about an object."""
    import mathutils

    info = get_object_info_with_uuid(obj)

    # Add type-specific info
    if obj.type == "MESH":
        mesh = obj.data
        info["mesh"] = {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
            "materials": [mat.name for mat in mesh.materials if mat],
        }
        # Add bounding box
        local_bbox_corners = [mathutils.Vector(corner) for corner in obj.bound_box]
        world_bbox_corners = [
            obj.matrix_world @ corner for corner in local_bbox_corners
        ]
        min_corner = [min(corner[i] for corner in world_bbox_corners) for i in range(3)]
        max_corner = [max(corner[i] for corner in world_bbox_corners) for i in range(3)]
        info["world_bounding_box"] = [min_corner, max_corner]
    elif obj.type == "CAMERA":
        info["camera"] = {
            "lens": obj.data.lens,
            "sensor_width": obj.data.sensor_width,
            "sensor_height": obj.data.sensor_height,
        }
    elif obj.type == "LIGHT":
        info["light"] = {
            "type": obj.data.type,
            "energy": obj.data.energy,
            "color": list(obj.data.color),
        }

    # Add modifiers
    info["modifiers"] = [{"name": mod.name, "type": mod.type} for mod in obj.modifiers]

    # Add constraints
    info["constraints"] = [
        {"name": con.name, "type": con.type} for con in obj.constraints
    ]

    # Add parent info
    if obj.parent:
        info["parent"] = obj.parent.name

    # Add collection membership
    info["collections"] = [
        col.name for col in bpy.data.collections if obj.name in col.objects
    ]

    return info


def get_viewport_screenshot(params):
    """Capture a screenshot of the viewport."""
    max_size = params.get("max_size", 800)
    return capture_viewport_screenshot(max_size)


def capture_viewport_screenshot(max_size=800):
    """Capture the current viewport as an image."""
    import base64

    # Create temporary file
    temp_path = Path(get_temp_dir()) / f"screenshot_{uuid.uuid4().hex}.png"

    # Set up render settings
    scene = bpy.context.scene
    original_filepath = scene.render.filepath
    original_format = scene.render.image_settings.file_format

    try:
        # Find 3D viewport
        area = None
        for a in bpy.context.screen.areas:
            if a.type == "VIEW_3D":
                area = a
                break

        if not area:
            return {"error": "No 3D viewport found"}

        # Take screenshot
        with bpy.context.temp_override(area=area):
            bpy.ops.screen.screenshot_area(filepath=str(temp_path))

        # Load and resize if needed
        img = bpy.data.images.load(str(temp_path))
        width, height = img.size

        if max(width, height) > max_size:
            scale = max_size / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img.scale(new_width, new_height)
            img.save()
            width, height = new_width, new_height

        # Read and encode image
        with open(temp_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Cleanup
        bpy.data.images.remove(img)

        return {"format": "png", "data": image_data, "width": width, "height": height}

    finally:
        scene.render.filepath = original_filepath
        scene.render.image_settings.file_format = original_format
        if temp_path.exists():
            temp_path.unlink()


def get_selection():
    """Get information about selected objects."""
    selected = bpy.context.selected_objects
    active = bpy.context.active_object

    return {
        "count": len(selected),
        "selected": [get_object_info_with_uuid(obj) for obj in selected],
        "active": get_object_info_with_uuid(active) if active else None,
    }


# =============================================================================
# SCENE OPS HANDLER
# =============================================================================


def create_primitive(params):
    """Create a primitive object."""
    import mathutils

    primitive_type = params.get("type", "cube")
    name = params.get("name")
    size = params.get("size")
    location = params.get("location", [0, 0, 0])
    rotation = params.get("rotation", [0, 0, 0])
    scale = params.get("scale", [1, 1, 1])

    # Deselect all
    bpy.ops.object.select_all(action="DESELECT")

    # Create primitive based on type
    if primitive_type == "cube":
        bpy.ops.mesh.primitive_cube_add(
            size=size or 2, location=location, rotation=rotation
        )
    elif primitive_type == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=size or 1, location=location, rotation=rotation
        )
    elif primitive_type == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(
            radius=size or 1,
            depth=size or 2 if size else 2,
            location=location,
            rotation=rotation,
        )
    elif primitive_type == "cone":
        bpy.ops.mesh.primitive_cone_add(
            radius1=size or 1,
            depth=size or 2 if size else 2,
            location=location,
            rotation=rotation,
        )
    elif primitive_type == "torus":
        bpy.ops.mesh.primitive_torus_add(
            major_radius=size or 1,
            minor_radius=size or 0.25 if size else 0.25,
            location=location,
            rotation=rotation,
        )
    elif primitive_type == "plane":
        bpy.ops.mesh.primitive_plane_add(
            size=size or 2, location=location, rotation=rotation
        )
    else:
        raise ValueError(f"Unknown primitive type: {primitive_type}")

    obj = bpy.context.active_object
    if name:
        obj.name = name
    obj.scale = scale

    obj_id = assign_uuid(obj)

    return {
        "id": obj_id,
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
    }


def create_empty(params):
    """Create an empty object."""
    name = params.get("name")
    location = params.get("location", [0, 0, 0])

    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.empty_add(location=location)

    obj = bpy.context.active_object
    if name:
        obj.name = name

    obj_id = assign_uuid(obj)

    return {
        "id": obj_id,
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
    }


def create_camera(params):
    """Create a camera."""
    import mathutils

    name = params.get("name")
    lens = params.get("lens", 50)
    location = params.get("location", [0, 0, 10])
    look_at = params.get("look_at")

    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.object.camera_add(location=location)

    obj = bpy.context.active_object
    if name:
        obj.name = name
    obj.data.lens = lens

    # Point camera at target
    if look_at:
        direction = mathutils.Vector(look_at) - obj.location
        rot_quat = direction.to_track_quat("-Z", "Y")
        obj.rotation_euler = rot_quat.to_euler()

    obj_id = assign_uuid(obj)

    return {
        "id": obj_id,
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "lens": obj.data.lens,
    }


def create_light(params):
    """Create a light."""
    light_type = params.get("type", "POINT")
    energy = params.get("energy", 100)
    color = params.get("color", [1, 1, 1])
    location = params.get("location", [0, 0, 5])
    rotation = params.get("rotation", [0, 0, 0])

    bpy.ops.object.select_all(action="DESELECT")

    if light_type == "POINT":
        bpy.ops.object.light_add(type="POINT", location=location, rotation=rotation)
    elif light_type == "SUN":
        bpy.ops.object.light_add(type="SUN", location=location, rotation=rotation)
    elif light_type == "SPOT":
        bpy.ops.object.light_add(type="SPOT", location=location, rotation=rotation)
    elif light_type == "AREA":
        bpy.ops.object.light_add(type="AREA", location=location, rotation=rotation)
    else:
        raise ValueError(f"Unknown light type: {light_type}")

    obj = bpy.context.active_object
    obj.data.energy = energy
    obj.data.color = color

    obj_id = assign_uuid(obj)

    return {
        "id": obj_id,
        "name": obj.name,
        "type": obj.type,
        "light_type": obj.data.type,
        "energy": obj.data.energy,
        "color": list(obj.data.color),
        "location": list(obj.location),
    }


def set_transform(params):
    """Set object transform."""
    target_id = params.get("target_id")
    location = params.get("location")
    rotation = params.get("rotation")
    scale = params.get("scale")
    apply = params.get("apply", False)

    obj = resolve_id(target_id)
    if not obj:
        raise ValueError(f"Object not found: {target_id}")

    if location:
        obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    if scale:
        obj.scale = scale

    if apply:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(
            location=bool(location), rotation=bool(rotation), scale=bool(scale)
        )

    return {
        "id": get_uuid(obj),
        "name": obj.name,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
    }


def select_objects(params):
    """Select objects."""
    ids = params.get("ids", [])
    mode = params.get("mode", "set")

    if mode == "set":
        bpy.ops.object.select_all(action="DESELECT")

    for obj_id in ids:
        obj = resolve_id(obj_id)
        if obj:
            if mode == "remove":
                obj.select_set(False)
            else:
                obj.select_set(True)

    return {
        "count": len(bpy.context.selected_objects),
        "selected": [obj.name for obj in bpy.context.selected_objects],
    }


def delete_objects(params):
    """Delete objects."""
    ids = params.get("ids", [])

    deleted = []
    for obj_id in ids:
        obj = resolve_id(obj_id)
        if obj:
            deleted.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)

    return {"deleted": deleted, "count": len(deleted)}


def duplicate_object(params):
    """Duplicate an object."""
    obj_id = params.get("id")
    linked = params.get("linked", False)
    count = params.get("count", 1)

    obj = resolve_id(obj_id)
    if not obj:
        raise ValueError(f"Object not found: {obj_id}")

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    duplicates = []
    for i in range(count):
        if linked:
            bpy.ops.object.duplicate_move_linked()
        else:
            bpy.ops.object.duplicate_move()

        dup = bpy.context.active_object
        dup_id = assign_uuid(dup)
        duplicates.append({"id": dup_id, "name": dup.name})

    return {"original": obj_id, "duplicates": duplicates}


def assign_material_pbr(params):
    """Assign PBR material to object."""
    target_id = params.get("target_id")
    material_spec = params.get("material_spec", {})

    obj = resolve_id(target_id)
    if not obj:
        raise ValueError(f"Object not found: {target_id}")

    # Create or get material
    mat_name = material_spec.get("name", f"{obj.name}_Material")
    if mat_name in bpy.data.materials:
        mat = bpy.data.materials[mat_name]
    else:
        mat = bpy.data.materials.new(name=mat_name)

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    # Create principled BSDF
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")

    # Set material properties
    if "base_color" in material_spec:
        bsdf.inputs["Base Color"].default_value = material_spec["base_color"] + [1]
    if "metallic" in material_spec:
        bsdf.inputs["Metallic"].default_value = material_spec["metallic"]
    if "roughness" in material_spec:
        bsdf.inputs["Roughness"].default_value = material_spec["roughness"]

    # Link nodes
    mat.node_tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Assign to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    return {"object": obj.name, "material": mat.name}


def set_world_hdri(params):
    """Set world HDRI."""
    asset_id = params.get("asset_id")
    resolution = params.get("resolution", "2k")

    # For now, just set a color
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new(name="World")
        bpy.context.scene.world = world

    world.use_nodes = True

    return {
        "asset_id": asset_id,
        "resolution": resolution,
        "status": "HDRI setting requires PolyHaven integration",
    }


def execute_blender_code(params):
    """Execute arbitrary Python code."""
    import mathutils
    import io
    from contextlib import redirect_stdout

    code = params.get("code", "")

    # Create namespace with bpy available
    namespace = {"bpy": bpy, "mathutils": mathutils}

    # Execute code
    capture_buffer = io.StringIO()
    with redirect_stdout(capture_buffer):
        exec(code, namespace)

    captured_output = capture_buffer.getvalue()

    return {"executed": True, "code_length": len(code), "output": captured_output}


# =============================================================================
# EXPORT HANDLER
# =============================================================================


def export_glb(params):
    """Export to GLB format."""
    target = params.get("target", "scene")
    name = params.get("name", "export")
    output_dir = params.get("output_dir", "exports")
    draco = params.get("draco", True)
    texture_embed = params.get("texture_embed", True)
    y_up = params.get("y_up", True)

    # Ensure output directory
    output_path = Path(output_dir) / f"{name}.glb"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Select objects based on target
    if target == "scene":
        bpy.ops.object.select_all(action="SELECT")
    elif target == "selection":
        pass  # Keep current selection
    elif target == "collection":
        collection_name = params.get("collection")
        if collection_name and collection_name in bpy.data.collections:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in bpy.data.collections[collection_name].objects:
                obj.select_set(True)

    # Export settings
    export_settings = {
        "filepath": str(output_path),
        "export_format": "GLB",
        "use_selection": target != "scene",
        "export_draco_mesh_compression_enable": draco,
        "export_materials": "EXPORT",
        "export_yup": y_up,
        "export_apply": True,
    }

    # Export
    bpy.ops.export_scene.gltf(**export_settings)

    return {"path": str(output_path), "target": target, "draco": draco, "y_up": y_up}


def render_preview(params):
    """Render a preview image."""
    output_path = params.get("output_path")
    camera = params.get("camera")
    resolution = params.get("resolution", [512, 512])

    if not output_path:
        raise ValueError("output_path is required")

    # Ensure output directory
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Set camera if specified
    if camera:
        cam_obj = resolve_id(camera)
        if cam_obj and cam_obj.type == "CAMERA":
            bpy.context.scene.camera = cam_obj

    # Set resolution
    bpy.context.scene.render.resolution_x = resolution[0]
    bpy.context.scene.render.resolution_y = resolution[1]
    bpy.context.scene.render.resolution_percentage = 100

    # Render
    bpy.context.scene.render.filepath = output_path
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)

    return {"path": output_path, "resolution": resolution}


def export_scene_bundle(params):
    """Export a complete scene bundle for Next.js."""
    slug = params.get("slug")
    nextjs_project_root = params.get("nextjs_project_root")
    mode = params.get("mode", "scene")
    generate_r3f = params.get("generate_r3f", False)

    if not slug:
        raise ValueError("slug is required")
    if not nextjs_project_root:
        raise ValueError("nextjs_project_root is required")

    # Create output directory
    output_dir = Path(nextjs_project_root) / "public" / "3d" / slug
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export GLB
    glb_path = output_dir / "model.glb"
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        use_selection=False,
        export_draco_mesh_compression_enable=True,
        export_materials="EXPORT",
        export_yup=True,
        export_apply=True,
    )

    # Render preview
    preview_path = output_dir / "preview.png"
    original_filepath = bpy.context.scene.render.filepath
    try:
        bpy.context.scene.render.resolution_x = 512
        bpy.context.scene.render.resolution_y = 512
        bpy.context.scene.render.filepath = str(preview_path)
        bpy.context.scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)
    finally:
        bpy.context.scene.render.filepath = original_filepath

    # Generate manifest
    manifest = generate_manifest(slug)
    manifest_path = output_dir / "manifest.json"
    write_json(manifest, str(manifest_path))

    # Generate R3F components if requested
    if generate_r3f:
        components_dir = output_dir / "components"
        components_dir.mkdir(exist_ok=True)
        generate_r3f_components(str(components_dir), manifest, slug)

    return {
        "slug": slug,
        "output_dir": str(output_dir),
        "files": {
            "model": str(glb_path),
            "preview": str(preview_path),
            "manifest": str(manifest_path),
        },
        "manifest": manifest,
    }


def generate_manifest(slug):
    """Generate scene manifest."""
    import time

    # Get all objects
    objects = []
    for obj in bpy.data.objects:
        obj_info = {
            "id": get_uuid(obj) or assign_uuid(obj),
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "dimensions": list(obj.dimensions),
            "visible": obj.visible_get(),
        }

        # Add type-specific info
        if obj.type == "MESH":
            obj_info["materials"] = [mat.name for mat in obj.data.materials if mat]
        elif obj.type == "CAMERA":
            obj_info["camera"] = {
                "lens": obj.data.lens,
                "sensor_width": obj.data.sensor_width,
            }
        elif obj.type == "LIGHT":
            obj_info["light"] = {
                "type": obj.data.type,
                "energy": obj.data.energy,
                "color": list(obj.data.color),
            }

        objects.append(obj_info)

    # Get cameras
    cameras = [
        {
            "name": obj.name,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "lens": obj.data.lens,
        }
        for obj in bpy.data.objects
        if obj.type == "CAMERA"
    ]

    # Get lights
    lights = [
        {
            "name": obj.name,
            "type": obj.data.type,
            "energy": obj.data.energy,
            "color": list(obj.data.color),
            "location": list(obj.location),
        }
        for obj in bpy.data.objects
        if obj.type == "LIGHT"
    ]

    # Get world
    world = {}
    if bpy.context.scene.world:
        world["name"] = bpy.context.scene.world.name
        world["color"] = list(bpy.context.scene.world.color)

    # Get render settings
    render = bpy.context.scene.render
    render_settings = {
        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "engine": render.engine,
    }

    # Get bounds
    bounds = get_scene_bounds()

    return {
        "version": "1.0.0",
        "timestamp": time.time(),
        "slug": slug,
        "objects": objects,
        "cameras": cameras,
        "lights": lights,
        "world": world,
        "render_settings": render_settings,
        "bounds": bounds,
        "units": {
            "system": bpy.context.scene.unit_settings.system,
            "scale_length": bpy.context.scene.unit_settings.scale_length,
        },
        "dependencies": [],
    }


def generate_r3f_components(output_dir, manifest, slug):
    """Generate React Three Fiber components."""

    # Model.tsx
    model_tsx = f"""import {{ useGLTF }} from '@react-three/drei'
import {{ forwardRef }} from 'react'

export const Model = forwardRef((props, ref) => {{
  const {{ scene }} = useGLTF('/3d/{slug}/model.glb')
  return <primitive ref={{ref}} object={{scene}} {{...props}} />
}})

Model.displayName = 'Model'

useGLTF.preload('/3d/{slug}/model.glb')
"""

    # Camera.tsx
    cameras = manifest.get("cameras", [])
    default_cam = (
        cameras[0]
        if cameras
        else {
            "name": "Camera",
            "location": [0, 0, 10],
            "rotation": [0, 0, 0],
            "lens": 50,
        }
    )

    camera_tsx = f'''import {{ PerspectiveCamera }} from '@react-three/drei'

export const Camera = () => {{
  return (
    <PerspectiveCamera
      name="{default_cam["name"]}"
      makeDefault
      position={[{", ".join(map(str, default_cam["location"]))}]}
      rotation={[{", ".join(map(str, default_cam["rotation"]))}]}
      fov={{{default_cam["lens"]}}}
    />
  )
}}
'''

    # Scene.tsx
    scene_tsx = f"""import {{ Canvas }} from '@react-three/fiber'
import {{ OrbitControls, Environment }} from '@react-three/drei'
import {{ Model }} from './Model'
import {{ Camera }} from './Camera'

export const Scene = () => {{
  return (
    <Canvas shadows>
      <Camera />
      <ambientLight intensity={{0.5}} />
      <Model />
      <OrbitControls />
    </Canvas>
  )
}}
"""

    # Write files
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(Path(output_dir) / "Model.tsx", "w") as f:
        f.write(model_tsx)

    with open(Path(output_dir) / "Camera.tsx", "w") as f:
        f.write(camera_tsx)

    with open(Path(output_dir) / "Scene.tsx", "w") as f:
        f.write(scene_tsx)


# =============================================================================
# ASSET PROVIDERS HANDLERS
# =============================================================================


def get_polyhaven_status():
    """Get PolyHaven integration status."""
    config = APIManager.get_polyhaven_config()
    return {
        "enabled": config["enabled"],
        "has_api_key": config["api_key"] is not None,
        "message": "PolyHaven ready" if config["enabled"] else "PolyHaven disabled",
    }


def get_sketchfab_status():
    """Get Sketchfab integration status."""
    config = APIManager.get_sketchfab_config()
    return {
        "enabled": config["enabled"],
        "has_api_key": config["api_key"] is not None,
        "message": "Sketchfab ready" if config["enabled"] else "Sketchfab disabled",
    }


def get_hyper3d_status():
    """Get Hyper3D Rodin integration status."""
    config = APIManager.get_hyper3d_config()
    return {
        "enabled": config["enabled"],
        "has_api_key": config["api_key"] is not None,
        "mode": config["mode"],
        "message": f"Hyper3D ({config['mode']}) ready"
        if config["enabled"]
        else "Hyper3D disabled",
    }


def get_hunyuan3d_status():
    """Get Hunyuan3D integration status."""
    config = APIManager.get_hunyuan3d_config()
    return {
        "enabled": config["enabled"],
        "mode": config["mode"],
        "has_api_key": config["api_key"] is not None,
        "has_local_path": config["local_path"] is not None,
        "message": f"Hunyuan3D ({config['mode']}) ready"
        if config["enabled"]
        else "Hunyuan3D disabled",
    }


def get_tripo3d_status():
    """Get Tripo3D integration status."""
    config = APIManager.get_tripo3d_config()
    return {
        "enabled": config["enabled"],
        "has_api_key": config["api_key"] is not None,
        "message": "Tripo3D ready" if config["enabled"] else "Tripo3D disabled",
    }


def get_local_model_status():
    """Get local model server status."""
    return LocalModelServerManager.get_status()


def start_local_model_server():
    """Start the local model server."""
    return LocalModelServerManager.start_server()


def stop_local_model_server():
    """Stop the local model server."""
    return LocalModelServerManager.stop_server()


_PROCEDURAL_TEXTURE_NODE_TYPES = {
    "noise": "ShaderNodeTexNoise",
    "voronoi": "ShaderNodeTexVoronoi",
    "wave": "ShaderNodeTexWave",
    "musgrave": "ShaderNodeTexMusgrave",
    "checker": "ShaderNodeTexChecker",
    "brick": "ShaderNodeTexBrick",
    "gradient": "ShaderNodeTexGradient",
    "magic": "ShaderNodeTexMagic",
}


def _material_normalize_color(value, field_name):
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(channel) for channel in value] + [1.0]


def _material_normalize_vector(value, field_name):
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(component) for component in value]


def _material_get_or_create(name):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    return material


def _material_reset_nodes(material):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (300, 0)
    shader = nodes.new(type="ShaderNodeBsdfPrincipled")
    shader.location = (0, 0)
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return shader


def _material_set_first_socket(node, socket_names, value):
    for socket_name in socket_names:
        socket = node.inputs.get(socket_name)
        if socket is None:
            continue
        socket.default_value = value
        return


def _material_describe(material):
    assigned_objects = []
    for obj in bpy.data.objects:
        material_slots = getattr(getattr(obj, "data", None), "materials", None)
        if not material_slots:
            continue
        if any(slot and slot.name == material.name for slot in material_slots):
            assigned_objects.append(obj.name)

    return {
        "name": material.name,
        "use_nodes": bool(material.use_nodes),
        "users": int(material.users),
        "assigned_objects": assigned_objects,
    }


def _fallback_create_bsdf_material(params):
    name = params.get("name")
    if not name:
        raise ValueError("Material name is required")

    material = _material_get_or_create(name)
    shader = _material_reset_nodes(material)

    if params.get("base_color") is not None:
        shader.inputs["Base Color"].default_value = _material_normalize_color(
            params["base_color"], "base_color"
        )
    if params.get("metallic") is not None:
        shader.inputs["Metallic"].default_value = float(params["metallic"])
    if params.get("roughness") is not None:
        shader.inputs["Roughness"].default_value = float(params["roughness"])
    if params.get("specular") is not None:
        _material_set_first_socket(
            shader,
            ("Specular", "Specular IOR Level"),
            float(params["specular"]),
        )
    if params.get("subsurface") is not None:
        _material_set_first_socket(
            shader,
            ("Subsurface", "Subsurface Weight"),
            float(params["subsurface"]),
        )
    if params.get("subsurface_color") is not None:
        _material_set_first_socket(
            shader,
            ("Subsurface Color",),
            _material_normalize_color(params["subsurface_color"], "subsurface_color"),
        )
    if params.get("transmission") is not None:
        _material_set_first_socket(
            shader,
            ("Transmission", "Transmission Weight"),
            float(params["transmission"]),
        )
    if params.get("ior") is not None:
        _material_set_first_socket(shader, ("IOR",), float(params["ior"]))
    if params.get("emission_color") is not None:
        _material_set_first_socket(
            shader,
            ("Emission", "Emission Color"),
            _material_normalize_color(params["emission_color"], "emission_color"),
        )
    if params.get("emission_strength") is not None:
        _material_set_first_socket(
            shader,
            ("Emission Strength",),
            float(params["emission_strength"]),
        )

    return {
        "status": "success",
        "material": material.name,
        "type": "principled_bsdf",
        "nodes": len(material.node_tree.nodes),
    }


def _fallback_create_emission_material(params):
    name = params.get("name")
    color = params.get("color")
    if not name:
        raise ValueError("Material name is required")
    if color is None:
        raise ValueError("color is required")

    material = _material_get_or_create(name)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (200, 0)
    emission = nodes.new(type="ShaderNodeEmission")
    emission.location = (0, 0)
    emission.inputs["Color"].default_value = _material_normalize_color(color, "color")
    emission.inputs["Strength"].default_value = float(params.get("strength", 10.0))
    links.new(emission.outputs["Emission"], output.inputs["Surface"])

    shadow_mode = str(params.get("shadow_mode", "none")).upper()
    if hasattr(material, "shadow_method"):
        material.shadow_method = shadow_mode

    return {
        "status": "success",
        "material": material.name,
        "type": "emission",
        "shadow_mode": shadow_mode.lower(),
    }


def _fallback_create_glass_material(params):
    name = params.get("name")
    if not name:
        raise ValueError("Material name is required")

    material = _material_get_or_create(name)
    shader = _material_reset_nodes(material)

    color = params.get("color")
    if color is not None:
        shader.inputs["Base Color"].default_value = _material_normalize_color(
            color, "color"
        )
    shader.inputs["Roughness"].default_value = float(params.get("roughness", 0.0))
    _material_set_first_socket(shader, ("IOR",), float(params.get("ior", 1.45)))
    _material_set_first_socket(
        shader,
        ("Transmission", "Transmission Weight"),
        float(params.get("transmission", 1.0)),
    )

    return {"status": "success", "material": material.name, "type": "glass"}


def _fallback_create_metal_material(params):
    name = params.get("name")
    base_color = params.get("base_color")
    if not name:
        raise ValueError("Material name is required")
    if base_color is None:
        raise ValueError("base_color is required")

    material = _material_get_or_create(name)
    shader = _material_reset_nodes(material)
    shader.inputs["Base Color"].default_value = _material_normalize_color(
        base_color, "base_color"
    )
    shader.inputs["Metallic"].default_value = 1.0
    shader.inputs["Roughness"].default_value = float(params.get("roughness", 0.3))
    _material_set_first_socket(
        shader,
        ("Anisotropic", "Anisotropy"),
        float(params.get("anisotropy", 0.0)),
    )

    return {"status": "success", "material": material.name, "type": "metal"}


def _fallback_create_subsurface_material(params):
    name = params.get("name")
    base_color = params.get("base_color")
    subsurface_color = params.get("subsurface_color")
    if not name:
        raise ValueError("Material name is required")
    if base_color is None:
        raise ValueError("base_color is required")
    if subsurface_color is None:
        raise ValueError("subsurface_color is required")

    material = _material_get_or_create(name)
    shader = _material_reset_nodes(material)
    shader.inputs["Base Color"].default_value = _material_normalize_color(
        base_color, "base_color"
    )
    _material_set_first_socket(
        shader,
        ("Subsurface", "Subsurface Weight"),
        float(params.get("subsurface", 0.5)),
    )
    _material_set_first_socket(
        shader,
        ("Subsurface Color",),
        _material_normalize_color(subsurface_color, "subsurface_color"),
    )
    _material_set_first_socket(
        shader,
        ("Subsurface Radius",),
        _material_normalize_vector(
            params.get("subsurface_radius", [1.0, 0.2, 0.1]), "subsurface_radius"
        ),
    )
    shader.inputs["Roughness"].default_value = float(params.get("roughness", 0.5))

    return {
        "status": "success",
        "material": material.name,
        "type": "subsurface",
    }


def _fallback_create_procedural_texture(params):
    texture_type = str(params.get("texture_type", "noise")).lower()
    node_type = _PROCEDURAL_TEXTURE_NODE_TYPES.get(texture_type)
    if node_type is None:
        raise ValueError(f"Unsupported procedural texture type: {texture_type}")

    name = params.get("name")
    if not name:
        raise ValueError("Material name is required")

    material = _material_get_or_create(name)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (600, 0)
    shader = nodes.new(type="ShaderNodeBsdfPrincipled")
    shader.location = (350, 0)
    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-250, 0)
    texture_coords = nodes.new(type="ShaderNodeTexCoord")
    texture_coords.location = (-450, 0)
    texture = nodes.new(type=node_type)
    texture.location = (50, 0)

    scale = float(params.get("scale", 5.0))
    mapping.inputs["Scale"].default_value[0] = scale
    mapping.inputs["Scale"].default_value[1] = scale
    mapping.inputs["Scale"].default_value[2] = scale
    _material_set_first_socket(texture, ("Scale",), scale)
    _material_set_first_socket(texture, ("Detail",), float(params.get("detail", 2.0)))
    _material_set_first_socket(
        texture, ("Roughness",), float(params.get("roughness", 0.5))
    )
    _material_set_first_socket(
        texture, ("Distortion",), float(params.get("distortion", 0.0))
    )

    links.new(texture_coords.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], texture.inputs["Vector"])
    if texture.outputs.get("Color") is not None:
        links.new(texture.outputs["Color"], shader.inputs["Base Color"])
    else:
        links.new(texture.outputs["Fac"], shader.inputs["Base Color"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])

    return {
        "status": "success",
        "material": material.name,
        "texture_type": texture_type,
        "nodes": len(nodes),
    }


def _fallback_assign_material(params):
    object_name = params.get("object_name")
    material_name = params.get("material_name")
    if not object_name:
        raise ValueError("object_name is required")
    if not material_name:
        raise ValueError("material_name is required")

    obj = bpy.data.objects.get(object_name)
    if obj is None:
        raise ValueError(f"Object not found: {object_name}")
    if getattr(obj.data, "materials", None) is None:
        raise ValueError(f"Object does not support materials: {object_name}")

    material = bpy.data.materials.get(material_name)
    if material is None:
        raise ValueError(f"Material not found: {material_name}")

    material_slots = obj.data.materials
    if not material_slots:
        material_slots.append(material)
    elif len(material_slots) == 1:
        material_slots[0] = material
    else:
        for slot_index, existing_material in enumerate(material_slots):
            if existing_material is None:
                material_slots[slot_index] = material
                break
            if existing_material.name == material.name:
                break
        else:
            material_slots.append(material)

    return {"status": "success", "object": obj.name, "material": material.name}


def _fallback_list_materials():
    materials = [_material_describe(material) for material in bpy.data.materials]
    return {"materials": materials, "count": len(materials)}


def _fallback_delete_material(params):
    name = params.get("name")
    if not name:
        raise ValueError("Material name is required")

    material = bpy.data.materials.get(name)
    if material is None:
        raise ValueError(f"Material not found: {name}")

    users_before_delete = int(material.users)
    bpy.data.materials.remove(material, do_unlink=True)
    return {
        "status": "success",
        "material": name,
        "users_before_delete": users_before_delete,
    }


def _material_fallback_handlers():
    class _Handlers:
        create_bsdf_material = staticmethod(_fallback_create_bsdf_material)
        create_emission_material = staticmethod(_fallback_create_emission_material)
        create_glass_material = staticmethod(_fallback_create_glass_material)
        create_metal_material = staticmethod(_fallback_create_metal_material)
        create_subsurface_material = staticmethod(_fallback_create_subsurface_material)
        create_procedural_texture = staticmethod(_fallback_create_procedural_texture)
        assign_material = staticmethod(_fallback_assign_material)
        list_materials = staticmethod(_fallback_list_materials)
        delete_material = staticmethod(_fallback_delete_material)

    return _Handlers


def _lighting_normalize_color(value, field_name):
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(channel) for channel in value]


def _lighting_resolve_optional_color(value, default_color, field_name):
    if value is None:
        return list(default_color)
    return _lighting_normalize_color(value, field_name)


def _lighting_normalize_vector(value, field_name):
    if len(value) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values")
    return [float(component) for component in value]


def _lighting_get_or_create_world():
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    return world


def _lighting_get_active_scene_objects():
    scene = getattr(bpy.context, "scene", None)
    scene_objects = getattr(scene, "objects", None)
    if scene_objects is not None:
        return scene_objects

    collection = getattr(scene, "collection", None)
    collection_objects = getattr(collection, "objects", None)
    if collection_objects is not None:
        return collection_objects

    return []


def _lighting_get_link_collection():
    collection = getattr(bpy.context, "collection", None)
    if collection is not None and getattr(collection, "objects", None) is not None:
        return collection

    scene_collection = getattr(getattr(bpy.context, "scene", None), "collection", None)
    if (
        scene_collection is not None
        and getattr(scene_collection, "objects", None) is not None
    ):
        return scene_collection

    raise ValueError("No active collection available to link new light")


def _lighting_ensure_light_object(name, light_data_type="AREA"):
    existing_object = bpy.data.objects.get(name)
    if existing_object is not None:
        if getattr(existing_object, "type", None) != "LIGHT":
            raise ValueError(f"Object exists and is not a light: {name}")
        existing_object.data.type = light_data_type
        return existing_object

    light_data = bpy.data.lights.new(name=name, type=light_data_type)
    light_object = bpy.data.objects.new(name=name, object_data=light_data)
    _lighting_get_link_collection().objects.link(light_object)
    return light_object


def _lighting_configure_area_shape(light_data, light_shape, size, size_y=None):
    normalized_shape = str(light_shape).upper()
    if normalized_shape not in {"RECTANGLE", "SQUARE", "CIRCLE", "DISC"}:
        raise ValueError(f"Unsupported area light shape: {light_shape}")

    light_data.shape = normalized_shape
    light_data.size = float(size)
    if normalized_shape == "RECTANGLE":
        light_data.size_y = float(size if size_y is None else size_y)

    return normalized_shape


def _lighting_find_node(nodes, node_idname):
    for node in nodes:
        if getattr(node, "bl_idname", None) == node_idname:
            return node
        if getattr(node, "type", None) == node_idname:
            return node
    return None


_FALLBACK_STUDIO_PRESET_SPECS = {
    "butterfly": [
        {
            "name": "Butterfly Key",
            "energy_multiplier": 1.8,
            "location": [0.0, -3.5, 4.5],
            "rotation": [0.95, 0.0, 0.0],
            "size": 2.4,
            "color": [1.0, 0.97, 0.92],
        },
        {
            "name": "Butterfly Fill",
            "energy_multiplier": 0.8,
            "location": [0.0, -1.5, 1.5],
            "rotation": [1.2, 0.0, 0.0],
            "size": 2.8,
            "color": [0.95, 0.97, 1.0],
        },
    ],
    "cinematic": [
        {
            "name": "Cinematic Key",
            "energy_multiplier": 1.7,
            "location": [4.0, -4.5, 4.0],
            "rotation": [0.9, 0.0, 0.8],
            "size": 2.8,
            "color": [1.0, 0.9, 0.78],
        },
        {
            "name": "Cinematic Rim",
            "energy_multiplier": 1.1,
            "location": [-3.5, 3.5, 4.5],
            "rotation": [0.7, 0.0, -2.3],
            "size": 2.2,
            "color": [0.7, 0.82, 1.0],
        },
    ],
    "high_key": [
        {
            "name": "High Key Main",
            "energy_multiplier": 1.6,
            "location": [3.5, -3.0, 4.0],
            "rotation": [0.8, 0.0, 0.7],
            "size": 3.0,
            "color": [1.0, 1.0, 1.0],
        },
        {
            "name": "High Key Fill",
            "energy_multiplier": 1.2,
            "location": [-3.5, -2.5, 3.2],
            "rotation": [0.85, 0.0, -0.8],
            "size": 3.2,
            "color": [1.0, 1.0, 1.0],
        },
        {
            "name": "High Key Background",
            "energy_multiplier": 0.9,
            "location": [0.0, 4.5, 2.5],
            "rotation": [1.55, 0.0, 3.14],
            "size": 4.0,
            "color": [1.0, 1.0, 1.0],
        },
    ],
    "loop": [
        {
            "name": "Loop Key",
            "energy_multiplier": 1.6,
            "location": [2.5, -4.0, 4.0],
            "rotation": [0.9, 0.0, 0.55],
            "size": 2.6,
            "color": [1.0, 0.96, 0.9],
        },
        {
            "name": "Loop Fill",
            "energy_multiplier": 0.7,
            "location": [-2.0, -3.0, 2.5],
            "rotation": [1.0, 0.0, -0.6],
            "size": 2.4,
            "color": [0.92, 0.96, 1.0],
        },
    ],
    "low_key": [
        {
            "name": "Low Key Main",
            "energy_multiplier": 1.5,
            "location": [4.0, -4.5, 4.2],
            "rotation": [0.95, 0.0, 0.85],
            "size": 2.5,
            "color": [1.0, 0.92, 0.82],
        },
        {
            "name": "Low Key Rim",
            "energy_multiplier": 0.9,
            "location": [-2.5, 4.0, 4.5],
            "rotation": [0.75, 0.0, -2.4],
            "size": 1.8,
            "color": [0.72, 0.82, 1.0],
        },
    ],
    "portrait": [
        {
            "name": "Portrait Key",
            "energy_multiplier": 1.7,
            "location": [3.0, -3.8, 4.0],
            "rotation": [0.88, 0.0, 0.68],
            "size": 2.7,
            "color": [1.0, 0.95, 0.88],
        },
        {
            "name": "Portrait Fill",
            "energy_multiplier": 0.8,
            "location": [-2.5, -3.0, 2.8],
            "rotation": [0.95, 0.0, -0.72],
            "size": 2.8,
            "color": [0.92, 0.96, 1.0],
        },
        {
            "name": "Portrait Hair",
            "energy_multiplier": 0.95,
            "location": [-1.0, 3.6, 4.8],
            "rotation": [0.7, 0.0, -2.9],
            "size": 1.8,
            "color": [1.0, 0.95, 0.85],
        },
    ],
    "product": [
        {
            "name": "Product Key",
            "energy_multiplier": 1.5,
            "location": [3.5, -3.5, 3.5],
            "rotation": [0.85, 0.0, 0.75],
            "size": 3.0,
            "color": [1.0, 1.0, 1.0],
        },
        {
            "name": "Product Fill",
            "energy_multiplier": 1.1,
            "location": [-3.0, -2.8, 3.2],
            "rotation": [0.9, 0.0, -0.78],
            "size": 3.2,
            "color": [1.0, 1.0, 1.0],
        },
        {
            "name": "Product Rim",
            "energy_multiplier": 0.9,
            "location": [0.0, 4.0, 3.8],
            "rotation": [0.75, 0.0, 3.14],
            "size": 2.4,
            "color": [1.0, 1.0, 1.0],
        },
    ],
    "rim": [
        {
            "name": "Rim Light",
            "energy_multiplier": 1.2,
            "location": [0.0, 4.0, 4.8],
            "rotation": [0.7, 0.0, 3.14],
            "size": 2.0,
            "color": [1.0, 0.96, 0.88],
        },
        {
            "name": "Rim Fill",
            "energy_multiplier": 0.7,
            "location": [0.0, -3.0, 2.4],
            "rotation": [1.1, 0.0, 0.0],
            "size": 2.4,
            "color": [0.88, 0.93, 1.0],
        },
    ],
    "split": [
        {
            "name": "Split Key",
            "energy_multiplier": 1.4,
            "location": [4.0, 0.0, 3.5],
            "rotation": [0.9, 0.0, 1.57],
            "size": 2.3,
            "color": [1.0, 0.94, 0.86],
        }
    ],
    "three_point": [],
}


def _lighting_hdri_placeholder_color(hdri_name, blur):
    normalized_name = str(hdri_name or "default")
    name_seed = sum(
        (index + 1) * ord(char) for index, char in enumerate(normalized_name)
    )
    blur_mix = max(0.0, min(1.0, float(blur)))
    base_color = [0.25 + ((name_seed >> shift) & 31) / 31 * 0.5 for shift in (0, 5, 10)]
    softened_color = [
        round((channel * (1.0 - blur_mix)) + (0.5 * blur_mix), 4)
        for channel in base_color
    ]
    return softened_color + [1.0]


def _fallback_create_area_light(params):
    name = params.get("name")
    if not name:
        raise ValueError("Light name is required")

    light_object = _lighting_ensure_light_object(name, "AREA")
    light_object.location = _lighting_normalize_vector(
        params.get("location", [0.0, 0.0, 5.0]), "location"
    )
    light_object.rotation_euler = _lighting_normalize_vector(
        params.get("rotation", [0.0, 0.0, 0.0]), "rotation"
    )
    light_object.data.energy = float(params.get("energy", 100.0))
    light_object.data.color = _lighting_normalize_color(
        params.get("color", [1.0, 1.0, 1.0]), "color"
    )
    shape = _lighting_configure_area_shape(
        light_object.data,
        params.get("light_type", "RECTANGLE"),
        float(params.get("size", 1.0)),
        params.get("size_y"),
    )

    return {
        "status": "success",
        "name": light_object.name,
        "type": "area",
        "shape": shape,
        "energy": light_object.data.energy,
    }


def _fallback_create_three_point_lighting(params):
    lights = []
    for light_params in (
        {
            "name": "Three Point Key",
            "light_type": "RECTANGLE",
            "size": 2.8,
            "energy": float(params.get("key_intensity", 1000.0)),
            "location": [4.0, -4.0, 5.0],
            "rotation": [0.85, 0.0, 0.78],
            "color": _lighting_resolve_optional_color(
                params.get("key_color"), [1.0, 0.95, 0.9], "key_color"
            ),
        },
        {
            "name": "Three Point Fill",
            "light_type": "RECTANGLE",
            "size": 3.2,
            "energy": float(params.get("fill_intensity", 500.0)),
            "location": [-4.5, -3.0, 2.5],
            "rotation": [1.05, 0.0, -0.78],
            "color": _lighting_resolve_optional_color(
                params.get("fill_color"), [0.85, 0.9, 1.0], "fill_color"
            ),
        },
        {
            "name": "Three Point Rim",
            "light_type": "RECTANGLE",
            "size": 2.0,
            "energy": float(params.get("rim_intensity", 800.0)),
            "location": [-2.0, 4.0, 5.5],
            "rotation": [0.65, 0.0, -2.5],
            "color": _lighting_resolve_optional_color(
                params.get("rim_color"), [1.0, 0.98, 0.92], "rim_color"
            ),
        },
    ):
        _fallback_create_area_light(light_params)
        lights.append(light_params["name"])

    return {"status": "success", "preset": "three_point", "lights": lights}


def _fallback_create_studio_lighting(params):
    preset = str(params.get("preset", "")).lower()
    if not preset:
        raise ValueError("preset is required")
    if preset == "three_point":
        intensity = float(params.get("intensity", 500.0))
        return _fallback_create_three_point_lighting(
            {
                "key_intensity": intensity * 1.6,
                "fill_intensity": intensity * 0.9,
                "rim_intensity": intensity * 1.2,
                "key_color": params.get("color"),
                "fill_color": params.get("color"),
                "rim_color": params.get("color"),
            }
        )

    preset_specs = _FALLBACK_STUDIO_PRESET_SPECS.get(preset)
    if preset_specs is None:
        raise ValueError(f"Unsupported studio lighting preset: {preset}")

    base_intensity = float(params.get("intensity", 500.0))
    override_color = params.get("color")
    lights = []
    for light_params in preset_specs:
        _fallback_create_area_light(
            {
                "name": light_params["name"],
                "light_type": "RECTANGLE",
                "size": light_params["size"],
                "energy": base_intensity * light_params.get("energy_multiplier", 1.0),
                "location": light_params["location"],
                "rotation": light_params["rotation"],
                "color": override_color
                if override_color is not None
                else light_params["color"],
            }
        )
        lights.append(light_params["name"])

    return {"status": "success", "preset": preset, "lights": lights}


def _fallback_create_hdri_environment(params):
    hdri_name = params.get("hdri_name")
    blur = float(params.get("blur", 0.0))
    world = _lighting_get_or_create_world()
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    mapping = nodes.new(type="ShaderNodeMapping")
    env_tex = nodes.new(type="ShaderNodeTexEnvironment")
    placeholder_color = nodes.new(type="ShaderNodeRGB")
    mix = nodes.new(type="ShaderNodeMixRGB")
    background = nodes.new(type="ShaderNodeBackground")
    output = nodes.new(type="ShaderNodeOutputWorld")

    mapping.inputs["Rotation"].default_value[2] = (
        float(params.get("rotation", 0.0)) * 0.0174533
    )
    background.inputs["Strength"].default_value = float(params.get("strength", 1.0))
    placeholder_color.outputs["Color"].default_value = _lighting_hdri_placeholder_color(
        hdri_name, blur
    )
    mix.inputs["Fac"].default_value = max(0.0, min(1.0, blur))
    env_tex.label = f"HDRI Stub: {hdri_name or 'default'}"
    world["blender_mcp_hdri_name"] = "" if hdri_name is None else str(hdri_name)
    world["blender_mcp_hdri_blur"] = blur

    links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], env_tex.inputs["Vector"])
    links.new(env_tex.outputs["Color"], mix.inputs["Color1"])
    links.new(placeholder_color.outputs["Color"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], background.inputs["Color"])
    links.new(background.outputs["Background"], output.inputs["Surface"])

    return {
        "status": "success",
        "hdri_name": hdri_name,
        "strength": float(params.get("strength", 1.0)),
        "rotation": float(params.get("rotation", 0.0)),
        "blur": blur,
    }


def _fallback_create_volumetric_lighting(params):
    world = _lighting_get_or_create_world()
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    output = _lighting_find_node(nodes, "ShaderNodeOutputWorld")
    if output is None:
        output = nodes.new(type="ShaderNodeOutputWorld")
    volume = _lighting_find_node(nodes, "ShaderNodeVolumeScatter")
    if volume is None:
        volume = nodes.new(type="ShaderNodeVolumeScatter")

    volume.inputs["Color"].default_value = _lighting_normalize_color(
        params.get("color", [1.0, 1.0, 1.0]), "color"
    ) + [1.0]
    volume.inputs["Density"].default_value = float(params.get("density", 0.1))
    volume.inputs["Anisotropy"].default_value = float(params.get("anisotropy", 0.0))
    links.new(volume.outputs["Volume"], output.inputs["Volume"])

    return {
        "status": "success",
        "density": float(params.get("density", 0.1)),
        "anisotropy": float(params.get("anisotropy", 0.0)),
        "color": _lighting_normalize_color(
            params.get("color", [1.0, 1.0, 1.0]), "color"
        ),
    }


def _fallback_adjust_light_exposure(params):
    exposure = float(params.get("exposure", 0.0))
    gamma = float(params.get("gamma", 1.0))
    bpy.context.scene.view_settings.exposure = exposure
    bpy.context.scene.view_settings.gamma = gamma
    return {"status": "success", "exposure": exposure, "gamma": gamma}


def _fallback_clear_lights():
    removed_count = 0
    for obj in list(_lighting_get_active_scene_objects()):
        if getattr(obj, "type", None) != "LIGHT":
            continue
        bpy.data.objects.remove(obj, do_unlink=True)
        removed_count += 1
    return {"status": "success", "removed_count": removed_count}


def _fallback_list_lights():
    lights = []
    for obj in _lighting_get_active_scene_objects():
        if getattr(obj, "type", None) != "LIGHT":
            continue
        lights.append(
            {
                "name": obj.name,
                "type": obj.data.type,
                "energy": float(obj.data.energy),
                "color": list(obj.data.color),
                "location": list(obj.location),
                "rotation": list(obj.rotation_euler),
            }
        )
    return {"lights": lights, "count": len(lights)}


def _lighting_fallback_handlers():
    class _Handlers:
        create_three_point_lighting = staticmethod(
            _fallback_create_three_point_lighting
        )
        create_studio_lighting = staticmethod(_fallback_create_studio_lighting)
        create_hdri_environment = staticmethod(_fallback_create_hdri_environment)
        create_area_light = staticmethod(_fallback_create_area_light)
        create_volumetric_lighting = staticmethod(_fallback_create_volumetric_lighting)
        adjust_light_exposure = staticmethod(_fallback_adjust_light_exposure)
        clear_lights = staticmethod(_fallback_clear_lights)
        list_lights = staticmethod(_fallback_list_lights)

    return _Handlers


def _dispatch_lighting_command(command_type, params):
    """Dispatch lighting commands through modular handlers or local fallback."""
    try:
        from blender_mcp_addon.handlers import lighting as lighting_handlers
    except ImportError:
        lighting_handlers = _lighting_fallback_handlers()

    if command_type == "create_three_point_lighting":
        return lighting_handlers.create_three_point_lighting(params)
    elif command_type == "create_studio_lighting":
        return lighting_handlers.create_studio_lighting(params)
    elif command_type == "create_hdri_environment":
        return lighting_handlers.create_hdri_environment(params)
    elif command_type == "create_area_light":
        return lighting_handlers.create_area_light(params)
    elif command_type == "create_volumetric_lighting":
        return lighting_handlers.create_volumetric_lighting(params)
    elif command_type == "adjust_light_exposure":
        return lighting_handlers.adjust_light_exposure(params)
    elif command_type == "clear_lights":
        return lighting_handlers.clear_lights()
    elif command_type == "list_lights":
        return lighting_handlers.list_lights()

    raise ValueError(f"Unknown lighting command type: {command_type}")


# =============================================================================
# SERVER MODULE
# =============================================================================


def _dispatch_material_command(command_type, params):
    """Dispatch material commands through modular handlers or local fallback."""
    try:
        from blender_mcp_addon.handlers import materials as material_handlers
    except ImportError:
        material_handlers = _material_fallback_handlers()

    if command_type == "create_bsdf_material":
        return material_handlers.create_bsdf_material(params)
    elif command_type == "create_emission_material":
        return material_handlers.create_emission_material(params)
    elif command_type == "create_glass_material":
        return material_handlers.create_glass_material(params)
    elif command_type == "create_metal_material":
        return material_handlers.create_metal_material(params)
    elif command_type == "create_subsurface_material":
        return material_handlers.create_subsurface_material(params)
    elif command_type == "create_procedural_texture":
        return material_handlers.create_procedural_texture(params)
    elif command_type == "assign_material":
        return material_handlers.assign_material(params)
    elif command_type == "list_materials":
        return material_handlers.list_materials()
    elif command_type == "delete_material":
        return material_handlers.delete_material(params)

    raise ValueError(f"Unknown material command type: {command_type}")


class BlenderMCPServer:
    """TCP socket server for Blender MCP."""

    def __init__(self, host="localhost", port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
        self.idempotency_cache = {}

    def start(self):
        """Start the server."""
        if self.running:
            print("[BlenderMCP] Server is already running")
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.running = True

            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()

            print(f"[BlenderMCP] Server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"[BlenderMCP] Failed to start server: {e}")
            self.running = False

    def stop(self):
        """Stop the server."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        print("[BlenderMCP] Server stopped")

    def _server_loop(self):
        """Main server loop."""
        while self.running:
            try:
                self.socket.settimeout(1.0)
                client, address = self.socket.accept()
                print(f"[BlenderMCP] Client connected from {address}")
                self._handle_client(client)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[BlenderMCP] Server error: {e}")

    def _handle_client(self, client):
        """Handle a client connection."""
        buffer = b""

        try:
            while self.running:
                data = client.recv(4096)
                if not data:
                    break

                buffer += data

                # Process complete messages (newline-delimited)
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)

                    command = parse_command(line)
                    if not command:
                        response = create_error_response(
                            "invalid_command",
                            "Could not parse command",
                            request_id=None,
                        )
                    else:
                        response = self._execute_command(command)

                    response_bytes = encode_command(response)
                    client.sendall(response_bytes)

        except Exception as e:
            print(f"[BlenderMCP] Client handler error: {e}")
        finally:
            client.close()
            print("[BlenderMCP] Client disconnected")

    def _execute_command(self, command):
        """Execute a command and return response."""
        command_type = command.get("type")
        params = command.get("params", {})
        request_id = command.get("request_id")
        idempotency_key = command.get("idempotency_key")

        # Check idempotency cache
        if idempotency_key and idempotency_key in self.idempotency_cache:
            cached_response = self.idempotency_cache[idempotency_key].copy()
            cached_response["request_id"] = request_id
            return cached_response

        # Execute on main thread
        result_container = {}

        def execute_wrapper():
            try:
                result = self._dispatch_command(command_type, params)
                result_container["result"] = result
            except Exception as e:
                traceback.print_exc()
                result_container["error"] = e
            return None

        bpy.app.timers.register(execute_wrapper, first_interval=0.0)

        # Wait for result (blocking with timeout)
        import time

        timeout = 30.0
        start_time = time.time()
        while time.time() - start_time < timeout:
            if "result" in result_container or "error" in result_container:
                break
            time.sleep(0.01)

        if "error" in result_container:
            response = create_error_response(
                "execution_error", str(result_container["error"]), request_id=request_id
            )
        elif "result" in result_container:
            response = create_success_response(
                data=result_container["result"], request_id=request_id
            )
        else:
            response = create_error_response(
                "timeout", "Command execution timed out", request_id=request_id
            )

        # Cache if idempotent
        if idempotency_key and "error" not in result_container:
            self.idempotency_cache[idempotency_key] = response.copy()

        return response

    def _dispatch_command(self, command_type, params):
        """Dispatch command to appropriate handler."""
        # Scene observation
        if command_type == "observe_scene":
            return observe_scene(params)
        elif command_type == "get_scene_hash":
            return {"hash": get_scene_hash()}
        elif command_type == "get_scene_info":
            return get_scene_info()
        elif command_type == "get_object_info":
            return get_object_info(params)
        elif command_type == "get_viewport_screenshot":
            return get_viewport_screenshot(params)
        elif command_type == "get_selection":
            return get_selection()

        # Scene operations
        elif command_type == "create_primitive":
            return create_primitive(params)
        elif command_type == "create_empty":
            return create_empty(params)
        elif command_type == "create_camera":
            return create_camera(params)
        elif command_type == "create_light":
            return create_light(params)
        elif command_type == "set_transform":
            return set_transform(params)
        elif command_type == "select_objects":
            return select_objects(params)
        elif command_type == "delete_objects":
            return delete_objects(params)
        elif command_type == "duplicate_object":
            return duplicate_object(params)
        elif command_type == "assign_material_pbr":
            return assign_material_pbr(params)
        elif command_type in {
            "create_bsdf_material",
            "create_emission_material",
            "create_glass_material",
            "create_metal_material",
            "create_subsurface_material",
            "create_procedural_texture",
            "assign_material",
            "list_materials",
            "delete_material",
        }:
            return _dispatch_material_command(command_type, params)
        elif command_type in {
            "create_three_point_lighting",
            "create_studio_lighting",
            "create_hdri_environment",
            "create_area_light",
            "create_volumetric_lighting",
            "adjust_light_exposure",
            "clear_lights",
            "list_lights",
        }:
            return _dispatch_lighting_command(command_type, params)
        elif command_type == "set_world_hdri":
            return set_world_hdri(params)
        elif command_type == "execute_blender_code":
            return execute_blender_code(params)

        # Export
        elif command_type == "export_glb":
            return export_glb(params)
        elif command_type == "render_preview":
            return render_preview(params)
        elif command_type == "export_scene_bundle":
            return export_scene_bundle(params)

        # Provider Status
        elif command_type == "get_polyhaven_status":
            return get_polyhaven_status()
        elif command_type == "get_sketchfab_status":
            return get_sketchfab_status()
        elif command_type == "get_hyper3d_status":
            return get_hyper3d_status()
        elif command_type == "get_hunyuan3d_status":
            return get_hunyuan3d_status()
        elif command_type == "get_tripo3d_status":
            return get_tripo3d_status()

        # Local Model Server
        elif command_type == "get_local_model_status":
            return get_local_model_status()
        elif command_type == "start_local_model_server":
            return start_local_model_server()
        elif command_type == "stop_local_model_server":
            return stop_local_model_server()

        else:
            raise ValueError(f"Unknown command type: {command_type}")


# =============================================================================
# ADDON PREFERENCES - API KEY MANAGEMENT
# =============================================================================


class BlenderMCPAddonPreferences(AddonPreferences):
    """Addon preferences for API key management."""

    bl_idname = __name__

    # PolyHaven Settings
    polyhaven_enabled: BoolProperty(
        name="Enable PolyHaven",
        description="Enable PolyHaven asset integration",
        default=True,
    )

    polyhaven_api_key: StringProperty(
        name="PolyHaven API Key",
        description="API key for PolyHaven (optional, for higher rate limits)",
        default="",
        subtype="PASSWORD",
    )

    # Sketchfab Settings
    sketchfab_enabled: BoolProperty(
        name="Enable Sketchfab",
        description="Enable Sketchfab model integration",
        default=True,
    )

    sketchfab_api_key: StringProperty(
        name="Sketchfab API Key",
        description="API key for Sketchfab",
        default="",
        subtype="PASSWORD",
    )

    # Hyper3D Rodin Settings
    hyper3d_enabled: BoolProperty(
        name="Enable Hyper3D Rodin",
        description="Enable Hyper3D Rodin AI generation",
        default=False,
    )

    hyper3d_mode: EnumProperty(
        name="Mode",
        description="Hyper3D API mode",
        items=[
            ("fal", "FAL AI", "Use FAL AI API"),
            ("main_site", "Main Site", "Use Hyper3D main site API"),
        ],
        default="fal",
    )

    hyper3d_api_key: StringProperty(
        name="Hyper3D API Key",
        description="API key for Hyper3D Rodin",
        default="",
        subtype="PASSWORD",
    )

    # Hunyuan3D Settings
    hunyuan3d_enabled: BoolProperty(
        name="Enable Hunyuan3D",
        description="Enable Hunyuan3D AI generation",
        default=False,
    )

    hunyuan3d_mode: EnumProperty(
        name="Mode",
        description="Hunyuan3D operation mode",
        items=[
            ("official", "Official API", "Use Tencent Cloud official API"),
            ("local", "Local Server", "Use locally hosted model"),
            ("custom", "Custom Endpoint", "Use custom API endpoint"),
        ],
        default="local",
    )

    hunyuan3d_api_key: StringProperty(
        name="API Key / SecretId",
        description="API Key or SecretId for Hunyuan3D",
        default="",
        subtype="PASSWORD",
    )

    hunyuan3d_secret_key: StringProperty(
        name="Secret Key",
        description="Secret Key for Hunyuan3D (for official API)",
        default="",
        subtype="PASSWORD",
    )

    hunyuan3d_local_path: StringProperty(
        name="Local Model Path",
        description="Path to local Hunyuan3D installation",
        default="",
        subtype="DIR_PATH",
    )

    hunyuan3d_custom_endpoint: StringProperty(
        name="Custom Endpoint",
        description="Custom API endpoint URL",
        default="http://localhost:8080",
    )

    # Tripo3D Settings
    tripo3d_enabled: BoolProperty(
        name="Enable Tripo3D", description="Enable Tripo3D AI generation", default=False
    )

    tripo3d_api_key: StringProperty(
        name="Tripo3D API Key",
        description="API key for Tripo3D",
        default="",
        subtype="PASSWORD",
    )

    # Local Model Server Settings
    local_model_enabled: BoolProperty(
        name="Enable Local Model Server",
        description="Enable local 3D generation model server",
        default=False,
    )

    local_model_type: EnumProperty(
        name="Model Type",
        description="Type of local 3D generation model",
        items=[
            ("hunyuan", "Hunyuan3D", "Hunyuan3D local installation"),
            ("instantmesh", "InstantMesh", "InstantMesh for fast generation"),
            ("crm", "CRM (Convolutional Reconstruction)", "CRM for image-to-3D"),
            ("trellis", "TRELLIS", "TRELLIS for high-quality generation"),
            ("zero123", "Zero123", "Zero123 for novel view synthesis"),
            ("custom", "Custom", "Custom local model"),
        ],
        default="hunyuan",
    )

    local_model_path: StringProperty(
        name="Model Path",
        description="Path to local model installation directory",
        default="",
        subtype="DIR_PATH",
    )

    local_model_python: StringProperty(
        name="Python Executable",
        description="Python executable for running the model (leave empty for system Python)",
        default="",
        subtype="FILE_PATH",
    )

    local_model_port: IntProperty(
        name="Server Port",
        description="Port for local model server",
        default=8080,
        min=1024,
        max=65535,
    )

    local_model_command: StringProperty(
        name="Custom Launch Command",
        description="Custom command to launch the model server (optional)",
        default="",
    )

    def draw(self, context):
        layout = self.layout

        # Info box
        box = layout.box()
        box.label(text="API Configuration", icon="KEYINGSET")
        box.label(text="Configure API keys for 3D asset providers", icon="INFO")

        # PolyHaven
        box = layout.box()
        box.label(text="PolyHaven", icon="WORLD")
        box.prop(self, "polyhaven_enabled")
        if self.polyhaven_enabled:
            box.prop(self, "polyhaven_api_key")
            box.label(text="Get API key at: https://polyhaven.com/", icon="URL")

        # Sketchfab
        box = layout.box()
        box.label(text="Sketchfab", icon="CUBE")
        box.prop(self, "sketchfab_enabled")
        if self.sketchfab_enabled:
            box.prop(self, "sketchfab_api_key")
            box.label(
                text="Get API key at: https://sketchfab.com/settings/developer",
                icon="URL",
            )

        # Hyper3D
        box = layout.box()
        box.label(text="Hyper3D Rodin", icon="MESH_DATA")
        box.prop(self, "hyper3d_enabled")
        if self.hyper3d_enabled:
            box.prop(self, "hyper3d_mode")
            box.prop(self, "hyper3d_api_key")
            if self.hyper3d_mode == "fal":
                box.label(text="Get API key at: https://fal.ai/dashboard", icon="URL")
            else:
                box.label(text="Get API key at: https://hyper3d.ai/", icon="URL")

        # Hunyuan3D
        box = layout.box()
        box.label(text="Hunyuan3D", icon="MESH_MONKEY")
        box.prop(self, "hunyuan3d_enabled")
        if self.hunyuan3d_enabled:
            box.prop(self, "hunyuan3d_mode")
            if self.hunyuan3d_mode == "official":
                box.prop(self, "hunyuan3d_api_key")
                box.prop(self, "hunyuan3d_secret_key")
                box.label(
                    text="Get credentials at: https://cloud.tencent.com/", icon="URL"
                )
            elif self.hunyuan3d_mode == "local":
                box.prop(self, "hunyuan3d_local_path")
                box.label(text="Path to local Hunyuan3D repository", icon="FILE_FOLDER")
            else:  # custom
                box.prop(self, "hunyuan3d_custom_endpoint")

        # Tripo3D
        box = layout.box()
        box.label(text="Tripo3D", icon="MESH_UVSPHERE")
        box.prop(self, "tripo3d_enabled")
        if self.tripo3d_enabled:
            box.prop(self, "tripo3d_api_key")
            box.label(text="Get API key at: https://trio3d.ai/", icon="URL")

        # Local Model Server
        box = layout.box()
        box.label(text="Local Model Server", icon="SERVER")
        box.prop(self, "local_model_enabled")
        if self.local_model_enabled:
            box.prop(self, "local_model_type")
            box.prop(self, "local_model_path")
            box.prop(self, "local_model_python")
            box.prop(self, "local_model_port")
            box.prop(self, "local_model_command")

            # Instructions
            box.separator()
            box.label(text="Setup Instructions:", icon="INFO")
            if self.local_model_type == "hunyuan":
                box.label(text="1. Clone: https://github.com/tencent/Hunyuan3D-2")
                box.label(text="2. Install dependencies per repository instructions")
                box.label(text="3. Set Model Path to repository root")
            elif self.local_model_type == "instantmesh":
                box.label(text="1. Clone: https://github.com/TencentARC/InstantMesh")
                box.label(text="2. Install dependencies")
                box.label(text="3. Download pretrained weights")
            elif self.local_model_type == "crm":
                box.label(text="1. Clone: https://github.com/thu-ml/CRM")
                box.label(text="2. Install dependencies")
                box.label(text="3. Download pretrained weights")
            elif self.local_model_type == "trellis":
                box.label(text="1. Clone: https://github.com/microsoft/TRELLIS")
                box.label(text="2. Install dependencies")
                box.label(text="3. Download pretrained weights")
            elif self.local_model_type == "zero123":
                box.label(text="1. Clone: https://github.com/cvlab-columbia/zero123")
                box.label(text="2. Install dependencies")
            box.label(text="Leave Python Executable empty to use system Python")


# =============================================================================
# SCENE SETTINGS
# =============================================================================


class BlenderMCPSettings(PropertyGroup):
    """Settings for Blender MCP scene."""

    server_host: StringProperty(
        name="Host", description="Server host address", default="localhost"
    )

    server_port: IntProperty(
        name="Port", description="Server port number", default=9876, min=1024, max=65535
    )

    export_dir: StringProperty(
        name="Export Directory",
        description="Default directory for exports",
        default="//exports",
        subtype="DIR_PATH",
    )


# =============================================================================
# OPERATORS
# =============================================================================


class BLENDERMCP_OT_start_server(Operator):
    """Start the Blender MCP server."""

    bl_idname = "blendermcp.start_server"
    bl_label = "Start Server"
    bl_description = "Start the Blender MCP server"

    def execute(self, context):
        global _server_instance
        if _server_instance is None:
            settings = context.scene.blendermcp_settings
            _server_instance = BlenderMCPServer(
                settings.server_host, settings.server_port
            )
        _server_instance.start()
        self.report({"INFO"}, "Server started")
        return {"FINISHED"}


class BLENDERMCP_OT_stop_server(Operator):
    """Stop the Blender MCP server."""

    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop Server"
    bl_description = "Stop the Blender MCP server"

    def execute(self, context):
        global _server_instance
        if _server_instance:
            _server_instance.stop()
            _server_instance = None
        self.report({"INFO"}, "Server stopped")
        return {"FINISHED"}


class BLENDERMCP_OT_start_local_model(Operator):
    """Start the local model server."""

    bl_idname = "blendermcp.start_local_model"
    bl_label = "Start Local Model"
    bl_description = "Start the local 3D generation model server"

    def execute(self, context):
        result = start_local_model_server()
        if result["status"] == "success":
            self.report({"INFO"}, result["message"])
        else:
            self.report({"ERROR"}, result["message"])
        return {"FINISHED"}


class BLENDERMCP_OT_stop_local_model(Operator):
    """Stop the local model server."""

    bl_idname = "blendermcp.stop_local_model"
    bl_label = "Stop Local Model"
    bl_description = "Stop the local 3D generation model server"

    def execute(self, context):
        result = stop_local_model_server()
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


# =============================================================================
# PANELS
# =============================================================================


class BLENDERMCP_PT_main_panel(Panel):
    """Main panel for Blender MCP."""

    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.blendermcp_settings
        prefs = context.preferences.addons[__name__].preferences

        global _server_instance
        if _server_instance and _server_instance.running:
            layout.label(text="Status: Running", icon="CHECKMARK")
            layout.operator("blendermcp.stop_server")
        else:
            layout.label(text="Status: Stopped", icon="X")
            layout.operator("blendermcp.start_server")

        layout.separator()

        # Settings
        box = layout.box()
        box.label(text="Server Settings:")
        box.prop(settings, "server_host")
        box.prop(settings, "server_port")

        layout.separator()

        # Export settings
        box = layout.box()
        box.label(text="Export:")
        box.prop(settings, "export_dir")

        layout.separator()

        # Local Model Server
        if prefs.local_model_enabled:
            box = layout.box()
            box.label(text="Local Model Server:", icon="SERVER")
            status = LocalModelServerManager.get_status()
            if status["running"]:
                box.label(
                    text=f"Status: Running on port {status['port']}", icon="CHECKMARK"
                )
                box.operator("blendermcp.stop_local_model")
            else:
                box.label(text="Status: Stopped", icon="X")
                box.operator("blendermcp.start_local_model")
            box.label(text=f"Type: {status.get('model_type', 'N/A')}")

        layout.separator()

        # Provider Status
        box = layout.box()
        box.label(text="Provider Status:")

        # PolyHaven
        ph_config = APIManager.get_polyhaven_config()
        if ph_config["enabled"]:
            box.label(text="PolyHaven: Enabled", icon="CHECKMARK")
        else:
            box.label(text="PolyHaven: Disabled", icon="X")

        # Sketchfab
        sf_config = APIManager.get_sketchfab_config()
        if sf_config["enabled"]:
            box.label(text="Sketchfab: Enabled", icon="CHECKMARK")
        else:
            box.label(text="Sketchfab: Disabled", icon="X")

        # AI Generators
        h3d_config = APIManager.get_hyper3d_config()
        if h3d_config["enabled"]:
            box.label(text=f"Hyper3D: {h3d_config['mode']}", icon="CHECKMARK")

        hy_config = APIManager.get_hunyuan3d_config()
        if hy_config["enabled"]:
            box.label(text=f"Hunyuan3D: {hy_config['mode']}", icon="CHECKMARK")

        tripo_config = APIManager.get_tripo3d_config()
        if tripo_config["enabled"]:
            box.label(text="Tripo3D: Enabled", icon="CHECKMARK")


class BLENDERMCP_PT_local_model_panel(Panel):
    """Panel for local model server control."""

    bl_label = "Local Model Server"
    bl_idname = "BLENDERMCP_PT_local_model_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BlenderMCP"
    bl_parent_id = "BLENDERMCP_PT_main_panel"

    @classmethod
    def poll(cls, context):
        prefs = context.preferences.addons[__name__].preferences
        return prefs.local_model_enabled

    def draw(self, context):
        layout = self.layout
        prefs = context.preferences.addons[__name__].preferences

        status = LocalModelServerManager.get_status()

        box = layout.box()
        box.label(text=f"Model Type: {prefs.local_model_type}")
        box.label(text=f"Port: {prefs.local_model_port}")

        if status["running"]:
            box.label(text="Status: Running", icon="CHECKMARK")
            box.operator("blendermcp.stop_local_model")
        else:
            box.label(text="Status: Stopped", icon="X")
            box.operator("blendermcp.start_local_model")

        # Instructions
        layout.separator()
        box = layout.box()
        box.label(text="Quick Start:", icon="INFO")
        box.label(text="1. Configure in Preferences")
        box.label(text="2. Set model path")
        box.label(text="3. Click Start")


# =============================================================================
# REGISTRATION
# =============================================================================

_server_instance = None

classes = [
    BlenderMCPAddonPreferences,
    BlenderMCPSettings,
    BLENDERMCP_OT_start_server,
    BLENDERMCP_OT_stop_server,
    BLENDERMCP_OT_start_local_model,
    BLENDERMCP_OT_stop_local_model,
    BLENDERMCP_PT_main_panel,
    BLENDERMCP_PT_local_model_panel,
]


def register():
    """Register addon."""
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.blendermcp_settings = PointerProperty(type=BlenderMCPSettings)


def unregister():
    """Unregister addon."""
    global _server_instance
    if _server_instance:
        _server_instance.stop()
        _server_instance = None

    # Stop local model server if running
    LocalModelServerManager.stop_server()

    del bpy.types.Scene.blendermcp_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
