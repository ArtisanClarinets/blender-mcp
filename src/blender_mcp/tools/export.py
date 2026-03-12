"""
Export tools

Provides tools for exporting scenes and assets.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool

logger = logging.getLogger("BlenderMCPTools")


@telemetry_tool("export_glb")
@mcp.tool()
async def export_glb(
    ctx: Context,
    target: str = "scene",
    name: str = "export",
    output_dir: str = "exports",
    draco: bool = True,
    texture_embed: bool = True,
    y_up: bool = True,
) -> str:
    """
    Export scene or selection to GLB format.

    Parameters:
    - target: What to export ("scene", "selection", "collection")
    - name: Name for the exported file
    - output_dir: Output directory path
    - draco: Use Draco compression
    - texture_embed: Embed textures in GLB
    - y_up: Use Y-up coordinate system

    Returns:
    - JSON string with export result
    """
    try:
        blender = get_blender_connection()

        params = {
            "target": target,
            "name": name,
            "output_dir": output_dir,
            "draco": draco,
            "texture_embed": texture_embed,
            "y_up": y_up,
        }

        result = blender.send_command("export_glb", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error exporting GLB: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("render_preview")
@mcp.tool()
async def render_preview(
    ctx: Context,
    output_path: str,
    camera: Optional[str] = None,
    resolution: List[int] = None,
) -> str:
    """
    Render a preview image of the scene.

    Parameters:
    - output_path: Path to save the preview image
    - camera: Optional camera name to use
    - resolution: [width, height] in pixels (default: [512, 512])

    Returns:
    - JSON string with render result
    """
    try:
        blender = get_blender_connection()

        params = {"output_path": output_path}
        if camera:
            params["camera"] = camera
        if resolution:
            params["resolution"] = resolution

        result = blender.send_command("render_preview", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error rendering preview: {str(e)}")
        return json.dumps({"error": str(e)})


@telemetry_tool("export_scene_bundle")
@mcp.tool()
async def export_scene_bundle(
    ctx: Context,
    slug: str,
    nextjs_project_root: str,
    mode: str = "scene",
    generate_r3f: bool = False,
) -> str:
    """
    Export a complete scene bundle for Next.js 16 integration.

    Creates the following structure in your-next-app/public/3d/<slug>/:
    - model.glb
    - preview.png
    - manifest.json
    - components/ (if generate_r3f=True)
      - Scene.tsx
      - Model.tsx
      - Camera.tsx

    Parameters:
    - slug: Unique identifier for the scene
    - nextjs_project_root: Path to the Next.js project root
    - mode: Export mode ("scene", "assets")
    - generate_r3f: Generate React Three Fiber components

    Returns:
    - JSON string with bundle export result
    """
    try:
        blender = get_blender_connection()

        params = {
            "slug": slug,
            "nextjs_project_root": nextjs_project_root,
            "mode": mode,
            "generate_r3f": generate_r3f,
        }

        result = blender.send_command("export_scene_bundle", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error exporting scene bundle: {str(e)}")
        return json.dumps({"error": str(e)})



# Add these new functions to the existing export.py file

@telemetry_tool("setup_render_passes")
@mcp.tool()
async def setup_render_passes(
    ctx: Context,
    passes: List[str],
    file_format: str = "EXR",
    color_depth: str = "16",
    compression: str = "zip",
) -> str:
    """
    Setup multiple render passes for compositing.
    
    Parameters:
    - passes: List of render passes ("AO", "Z", "Normal", "Vector", etc.)
    - file_format: Output file format
    - color_depth: Bit depth
    - compression: Compression method
    
    Returns:
    - JSON string with render passes setup result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "passes": passes,
            "file_format": file_format,
            "color_depth": color_depth,
            "compression": compression,
        }
        
        result = blender.send_command("setup_render_passes", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error setting up render passes: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("render_animation_passes")
@mcp.tool()
async def render_animation_passes(
    ctx: Context,
    frame_start: int,
    frame_end: int,
    output_path: str,
    passes: Optional[List[str]] = None,
    resolution: Optional[List[int]] = None,
) -> str:
    """
    Render animation with multiple passes.
    
    Parameters:
    - frame_start: Start frame
    - frame_end: End frame
    - output_path: Output directory
    - passes: Optional list of passes
    - resolution: Optional resolution [width, height]
    
    Returns:
    - JSON string with animation render result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "frame_start": frame_start,
            "frame_end": frame_end,
            "output_path": output_path,
        }
        
        if passes:
            params["passes"] = passes
        if resolution:
            params["resolution"] = resolution
            
        result = blender.send_command("render_animation_passes", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error rendering animation passes: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("setup_stereoscopic_render")
@mcp.tool()
async def setup_stereoscopic_render(
    ctx: Context,
    eye_separation: float = 0.065,
    convergence_distance: float = 1.0,
    mode: str = "parallel",
) -> str:
    """
    Setup stereoscopic rendering for VR/3D content.
    
    Parameters:
    - eye_separation: Distance between eyes
    - convergence_distance: Convergence distance
    - mode: Stereo mode ("parallel", "toe-in", "off-axis")
    
    Returns:
    - JSON string with stereoscopic setup result
    """
    try:
        blender = get_blender_connection()
        
        params = {
            "eye_separation": eye_separation,
            "convergence_distance": convergence_distance,
            "mode": mode,
        }
        
        result = blender.send_command("setup_stereoscopic_render", params)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error setting up stereoscopic render: {str(e)}")
        return json.dumps({"error": str(e)})
