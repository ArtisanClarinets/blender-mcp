"""Load MCP tool modules so @mcp.tool() decorators run and tools are registered."""

import importlib
import logging

logger = logging.getLogger("blender_mcp.tool_loader")


def import_all_tool_modules():
    """Import all MCP tool modules from src/blender_mcp/tools/ so tools register with FastMCP."""
    from ..tools import __all__ as TOOL_MODULES

    imported = []
    for module_name in TOOL_MODULES:
        try:
            mod = importlib.import_module(f"..tools.{module_name}", __name__)
            imported.append(mod)
        except Exception as e:
            logger.warning("Failed to import tool module %s: %s", module_name, e)
    return imported
