# Blender MCP Testing Instructions

## Prerequisites

1. Blender 3.0+ must be installed
2. The Blender MCP addon must be installed in Blender
3. The MCP server must be running in Blender

## Installation Steps

1. **Install the addon in Blender:**
   - Open Blender
   - Go to Edit > Preferences > Add-ons
   - Click "Install..."
   - Select the `addon.py` file from this directory
   - Enable the "Interface: Blender MCP" addon
   - The server should start automatically on port 9876

2. **Verify the server is running:**
   - In Blender, go to the 3D Viewport sidebar (press N)
   - Look for the "BlenderMCP" tab
   - Check that it shows "Server: Running"

## Running the Tests

Once the server is running in Blender, open a terminal/command prompt and run:

```bash
python test_mcp_tools.py
```

This will test all the MCP tool functions:
- Scene observation (get_scene_info, get_scene_hash, observe_scene, get_selection)
- Object creation (create_primitive, create_empty, create_camera, create_light)
- Object manipulation (set_transform, select_objects, duplicate_object, get_object_info)
- Materials (assign_material_pbr, create_bsdf_material, list_materials)
- Lighting (create_three_point_lighting, list_lights)
- Rendering (render_preview)
- Cleanup (delete_objects)

## Expected Output

You should see output like:

```
============================================================
Blender MCP Comprehensive Test Suite
============================================================

Connected to Blender MCP server

=== Testing Scene Observation ===
Testing get_scene_info...
  Scene name: Scene
  Objects count: 4
  PASSED
Testing get_scene_hash...
  Hash: abc123...
  PASSED
...

============================================================
ALL TESTS PASSED!
============================================================
```

## Troubleshooting

**Connection refused error:**
- Make sure Blender is running with the addon enabled
- Check that the server shows as "Running" in the BlenderMCP panel
- Verify port 9876 is not blocked by firewall

**AttributeError about 'Context' object:**
- This means a function is trying to access `bpy.context` in a background thread
- The addon has been fixed to handle most of these cases
- If you see this error, note which function failed and report it

**Test failures:**
- Check the Blender console for Python errors
- Some operations (like viewport screenshots) won't work in background threads
- The test script handles these gracefully

## Manual Testing

You can also test individual commands using the MCP client:

```python
from blender_mcp_client import call_tool

# Get scene info
result = call_tool("get_scene_info")
print(result)

# Create a cube
result = call_tool("create_primitive", {
    "type": "cube",
    "name": "MyCube",
    "location": [0, 0, 0]
})
print(result)
```
