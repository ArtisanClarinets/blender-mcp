import os
import importlib
from pathlib import Path

def import_all_tool_modules():
    """Dynamically import all tool modules from the handlers directory."""
    handlers_dir = Path(__file__).parent.parent / "blender_mcp_addon" / "handlers"
    for root, _, files in os.walk(handlers_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                module_path = Path(root) / file
                # Construct the module name relative to the blender_mcp_addon directory
                relative_path = module_path.relative_to(Path(__file__).parent.parent)
                module_name = str(relative_path).replace(os.sep, ".")[:-3] # remove .py
                try:
                    importlib.import_module(f"{module_name}")
                except ImportError as e:
                    print(f"Failed to import {module_name}: {e}")