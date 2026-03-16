"""
Color pipeline (OCIO/ACES) tools for Blender MCP.

Provides tools for managing color pipeline configuration.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..mcp_compat import Context
from ..server import mcp
from ..telemetry_decorator import telemetry_tool
from ..pipeline.color import get_color_adapter

logger = logging.getLogger("BlenderMCPTools")


@telemetry_tool("get_color_pipeline")
@mcp.tool()
async def get_color_pipeline(ctx: Context, project_code: str) -> str:
    """
    Get the color pipeline configuration for a project.
    
    Parameters:
    - project_code: Project code
    
    Returns:
    - JSON string with color pipeline configuration
    """
    try:
        adapter = get_color_adapter()
        config = adapter.get_color_pipeline(project_code)
        
        return json.dumps({
            "success": True,
            "config": config.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error getting color pipeline: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("set_project_color_pipeline")
@mcp.tool()
async def set_project_color_pipeline(
    ctx: Context,
    project_code: str,
    working_colorspace: Optional[str] = None,
    render_colorspace: Optional[str] = None,
    display_colorspace: Optional[str] = None,
    texture_colorspace: Optional[str] = None,
    default_display: Optional[str] = None,
    default_view: Optional[str] = None,
) -> str:
    """
    Set the color pipeline configuration for a project.
    
    Parameters:
    - project_code: Project code
    - working_colorspace: Working colorspace (e.g., "ACES - ACEScg")
    - render_colorspace: Render colorspace
    - display_colorspace: Display colorspace
    - texture_colorspace: Texture colorspace
    - default_display: Default display
    - default_view: Default view
    
    Returns:
    - JSON string with updated configuration
    """
    try:
        adapter = get_color_adapter()
        config = adapter.set_project_color_pipeline(
            project_code=project_code,
            working_colorspace=working_colorspace,
            render_colorspace=render_colorspace,
            display_colorspace=display_colorspace,
            texture_colorspace=texture_colorspace,
            default_display=default_display,
            default_view=default_view,
        )
        
        return json.dumps({
            "success": True,
            "config": config.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error setting color pipeline: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("validate_color_pipeline")
@mcp.tool()
async def validate_color_pipeline(ctx: Context, project_code: str) -> str:
    """
    Validate the color pipeline configuration.
    
    Parameters:
    - project_code: Project code
    
    Returns:
    - JSON string with validation results
    """
    try:
        adapter = get_color_adapter()
        result = adapter.validate_color_pipeline(project_code)
        
        return json.dumps({
            "success": True,
            "validation": result,
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error validating color pipeline: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("tag_texture_colorspace")
@mcp.tool()
async def tag_texture_colorspace(
    ctx: Context,
    texture_path: str,
    colorspace: Optional[str] = None,
    project_code: Optional[str] = None,
) -> str:
    """
    Determine the appropriate colorspace for a texture.
    
    Parameters:
    - texture_path: Path to the texture file
    - colorspace: Optional explicit colorspace
    - project_code: Optional project code for context
    
    Returns:
    - JSON string with colorspace assignment
    """
    try:
        adapter = get_color_adapter()
        result = adapter.tag_texture_colorspace(texture_path, colorspace, project_code)
        
        return json.dumps({
            "success": True,
            "assignment": result,
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error tagging texture colorspace: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("prepare_aces_render_outputs")
@mcp.tool()
async def prepare_aces_render_outputs(
    ctx: Context,
    project_code: str,
    output_paths: List[str],
    file_format: str = "EXR",
) -> str:
    """
    Prepare render output configuration for ACES workflow.
    
    Parameters:
    - project_code: Project code
    - output_paths: List of output file paths
    - file_format: Output file format (default: EXR)
    
    Returns:
    - JSON string with render output configuration
    """
    try:
        adapter = get_color_adapter()
        result = adapter.prepare_aces_render_outputs(project_code, output_paths, file_format)
        
        return json.dumps({
            "success": True,
            "configuration": result,
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error preparing render outputs: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_ocio_views")
@mcp.tool()
async def get_ocio_views(ctx: Context, project_code: str) -> str:
    """
    Get available display/view combinations.
    
    Parameters:
    - project_code: Project code
    
    Returns:
    - JSON string with display/view combinations
    """
    try:
        adapter = get_color_adapter()
        views = adapter.get_ocio_views(project_code)
        
        return json.dumps({
            "success": True,
            "views": views,
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting OCIO views: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_available_colorspaces")
@mcp.tool()
async def get_available_colorspaces(ctx: Context) -> str:
    """
    Get list of available colorspaces.
    
    Returns:
    - JSON string with colorspace list
    """
    try:
        adapter = get_color_adapter()
        colorspaces = adapter.get_available_colorspaces()
        
        return json.dumps({
            "success": True,
            "colorspaces": colorspaces,
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting colorspaces: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("create_ocio_config_template")
@mcp.tool()
async def create_ocio_config_template(
    ctx: Context,
    output_path: str,
    project_name: str,
) -> str:
    """
    Create a basic OCIO config template file.
    
    Parameters:
    - output_path: Path to write the config file
    - project_name: Project name for the config
    
    Returns:
    - JSON string with result
    """
    try:
        adapter = get_color_adapter()
        path = adapter.create_ocio_config_template(output_path, project_name)
        
        return json.dumps({
            "success": True,
            "config_path": path,
            "note": "Basic OCIO config template created. Customize for production use.",
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating OCIO config: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_ocio_status")
@mcp.tool()
async def get_ocio_status(ctx: Context) -> str:
    """
    Get OCIO system status.
    
    Returns:
    - JSON string with OCIO status
    """
    try:
        adapter = get_color_adapter()
        
        return json.dumps({
            "success": True,
            "ocio_library_available": adapter.ocio_available,
            "supported_colorspaces_count": len(adapter.get_available_colorspaces()),
            "note": "Color pipeline scaffolding is available. Full OCIO support requires PyOpenColorIO library.",
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting OCIO status: {e}")
        return json.dumps({"error": str(e)})
