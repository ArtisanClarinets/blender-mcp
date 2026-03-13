"""
Export handlers

Implements scene export functionality.
"""

import bpy
import os
import json
from pathlib import Path
from typing import Any, Dict, List

from .. import id
from .. import utils


def export_glb(params: Dict[str, Any]) -> Dict[str, Any]:
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
        # Keep current selection
        pass
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


def render_preview(params: Dict[str, Any]) -> Dict[str, Any]:
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
        cam_obj = id.resolve_id(camera)
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


def export_scene_bundle(params: Dict[str, Any]) -> Dict[str, Any]:
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
    utils.write_json(manifest, str(manifest_path))

    # Generate R3F components if requested
    if generate_r3f:
        components_dir = output_dir / "components"
        components_dir.mkdir(exist_ok=True)
        generate_r3f_components(str(components_dir), manifest)

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


def generate_manifest(slug: str) -> Dict[str, Any]:
    """Generate scene manifest."""
    import time

    # Get all objects
    objects = []
    for obj in bpy.data.objects:
        obj_info = {
            "id": id.get_uuid(obj) or id.assign_uuid(obj),
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
    bounds = utils.get_scene_bounds()

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


def generate_r3f_components(output_dir: str, manifest: Dict[str, Any]):
    """Generate React Three Fiber components."""

    # Model.tsx
    model_tsx = (
        """import { useGLTF } from '@react-three/drei'
import { forwardRef } from 'react'

export const Model = forwardRef((props, ref) => {
  const { scene } = useGLTF('/3d/"""
        + manifest["slug"]
        + """/model.glb')
  return <primitive ref={ref} object={scene} {...props} />
})

Model.displayName = 'Model'

useGLTF.preload('/3d/"""
        + manifest["slug"]
        + """/model.glb')
"""
    )

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
      position={default_cam["location"]}
      rotation={default_cam["rotation"]}
      fov={{50}}
    />
  )
}}
'''

    # Scene.tsx
    scene_tsx = """import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment } from '@react-three/drei'
import { Model } from './Model'
import { Camera } from './Camera'
import manifest from '../manifest.json'

export const Scene = () => {
  return (
    <Canvas>
      <Camera />
      <ambientLight intensity={0.5} />
      <Model />
      <OrbitControls />
    </Canvas>
  )
}
"""

    # Write files
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(Path(output_dir) / "Model.tsx", "w") as f:
        f.write(model_tsx)

    with open(Path(output_dir) / "Camera.tsx", "w") as f:
        f.write(camera_tsx)

    with open(Path(output_dir) / "Scene.tsx", "w") as f:
        f.write(scene_tsx)
