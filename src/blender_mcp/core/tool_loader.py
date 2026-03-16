"""Load MCP tool modules so @mcp.tool() decorators run and tools are registered."""

import importlib
import logging

logger = logging.getLogger("blender_mcp.tool_loader")

# All tool modules to import
TOOL_MODULES = [
    "observe",
    "scene_ops",
    "assets",
    "export",
    "jobs",
    "materials",
    "lighting",
    "camera",
    "composition",
    "rigging",
    "animation",
    "procedural_materials",
    "atmospherics",
    "render_farm",
    "production",
    "ai_creative",
    "tripo3d",
    "pipeline_tools",
    "usd_tools",
    "color_tools",
    "tracker_tools",
]


def import_all_tool_modules():
    """Import all MCP tool modules from src/blender_mcp/tools/ so tools register with FastMCP."""
    imported = []
    for module_name in TOOL_MODULES:
        try:
            mod = importlib.import_module(f"..tools.{module_name}", __name__)
            imported.append(mod)
            logger.debug(f"Imported tool module: {module_name}")
        except Exception as e:
            logger.warning(f"Failed to import tool module {module_name}: {e}")
    return imported
