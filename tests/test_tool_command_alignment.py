"""Ensure every MCP tool's command_name has a handler in the addon command registry."""

import sys
from pathlib import Path

import pytest

from blender_mcp.tool_registry import discover_tool_specs

# Add project root so blender_mcp_addon can be imported when not installed
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _get_addon_handlers():
    try:
        from blender_mcp_addon.command_registry import COMMAND_HANDLERS
        return COMMAND_HANDLERS
    except ImportError:
        return None


def test_every_tool_command_has_addon_handler():
    """Every tool's command_name must exist in the addon COMMAND_HANDLERS."""
    handlers = _get_addon_handlers()
    if handlers is None:
        pytest.skip("blender_mcp_addon not importable (e.g. missing bpy)")

    specs = discover_tool_specs()
    missing = []
    for name, spec in specs.items():
        if spec.command_name not in handlers:
            missing.append(f"{name} -> {spec.command_name}")
    assert not missing, (
        "Tools reference commands that the addon does not handle: " + "; ".join(missing)
    )
