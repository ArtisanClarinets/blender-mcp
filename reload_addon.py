"""
Script to reload the Blender MCP addon from within Blender.
Run this in Blender's Python console to reload the addon with new changes.
"""

import bpy
import sys

# Disable the addon
bpy.ops.preferences.addon_disable(module="addon")

# Force reload of the module
if "addon" in sys.modules:
    del sys.modules["addon"]

# Re-enable the addon
bpy.ops.preferences.addon_enable(module="addon")

print("Blender MCP addon reloaded successfully!")
