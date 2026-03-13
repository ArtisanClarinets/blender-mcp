# Blender MCP Installation and Usage Guide

## Overview

This guide explains how to install and use the updated Blender MCP system with the new protocol and tools.

## File Structure

```
blender-mcp/
├── blender_mcp_addon/          # Canonical Blender addon package
scripts/build_addon_zip.py   # Builds an installable addon zip
├── src/blender_mcp/            # MCP Server package
│   ├── server.py               # Main server with FastMCP
│   ├── tools/                  # Tool modules
│   │   ├── observe.py          # Scene observation tools
│   │   ├── scene_ops.py        # Scene manipulation tools
│   │   ├── assets.py           # Asset integration tools
│   │   ├── export.py           # Export tools
│   │   └── jobs.py             # Job management tools
│   └── ...
└── README.md
```

## Installation

### 1. Install the Blender Addon

1. Open Blender 5.0.1 (or 3.0.0+)
2. Go to **Edit > Preferences > Add-ons**
3. Click **Install...**
4. Run `python scripts/build_addon_zip.py`, then select `dist/blender_mcp_addon.zip` from the repo root
5. Enable the addon by checking "Interface: Blender MCP"
6. Open the 3D View sidebar (press **N**)
7. Find the **BlenderMCP** tab
8. Set the host (default: `localhost`) and port (default: `9876`)
9. Click **Start Server**

### 2. Install the MCP Server

```bash
# Navigate to the project directory
cd blender-mcp

# Install with uv
uv pip install -e .

# Or with pip
pip install -e .
```

### 3. Configure Claude/Cursor/VS Code

Add the MCP server to your configuration:

**Claude Desktop:**
```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["blender-mcp"]
        }
    }
}
```

**Cursor:**
```json
{
    "mcpServers": {
        "blender": {
            "command": "uvx",
            "args": ["blender-mcp"]
        }
    }
}
```

## Communication Protocol

The server and addon now use **newline-delimited JSON (NDJSON)** protocol:

### Request Format
```json
{"type": "command_name", "params": {...}, "request_id": "uuid", "idempotency_key": "optional"}
```

### Response Format
```json
{"ok": true, "data": {...}, "request_id": "uuid"}
```
or
```json
{"ok": false, "error": {"code": "...", "message": "..."}, "request_id": "uuid"}
```

## Available Tools

### Observation Tools
- `observe_scene` - Get comprehensive scene information
- `get_scene_hash` - Get stable scene hash for change detection
- `get_scene_info` - Get basic scene information
- `get_object_info` - Get detailed object information
- `get_viewport_screenshot` - Capture viewport screenshot
- `get_selection` - Get selected objects

### Scene Operations
- `create_primitive` - Create cubes, spheres, cylinders, etc.
- `create_empty` - Create empty objects
- `create_camera` - Create cameras with look-at support
- `create_light` - Create lights (point, sun, spot, area)
- `set_transform` - Set position, rotation, scale
- `select_objects` - Select/deselect objects
- `delete_objects` - Delete objects
- `duplicate_object` - Duplicate objects
- `assign_material_pbr` - Assign PBR materials
- `set_world_hdri` - Set HDRI environment
- `execute_blender_code` - Execute Python code

### Export Tools
- `export_glb` - Export to GLB format
- `render_preview` - Render preview image
- `export_scene_bundle` - Export complete Next.js bundle

### Asset Integration (Status Only)
- `get_polyhaven_status` - Check PolyHaven status
- `get_sketchfab_status` - Check Sketchfab status
- `get_hyper3d_status` - Check Hyper3D status
- `get_hunyuan3d_status` - Check Hunyuan3D status

## Usage Example

```python
# In Claude/Cursor, the agent can use:

# 1. Observe the scene
result = await observe_scene(detail="med", include_screenshot=True)

# 2. Create a cube
cube = await create_primitive(type="cube", name="MyCube", location=[0, 0, 1])

# 3. Add lighting
light = await create_light(type="SUN", energy=3, location=[5, 5, 10])

# 4. Export for Next.js
bundle = await export_scene_bundle(
    slug="my-scene",
    nextjs_project_root="/path/to/project",
    generate_r3f=True
)
```

## Troubleshooting

### Connection Issues
- Ensure Blender addon is running (check the UI panel)
- Verify host/port match between addon and server
- Check firewall settings
- Look at Blender's System Console for errors

### Protocol Mismatch
- Both server and addon must use the same protocol version
- The new version uses NDJSON with `request_id` and `ok`/`error` responses

### Tool Not Found
- Check that tools are properly decorated with `@mcp.tool()`
- Verify tools are imported in `server.py`

## Key Changes from Previous Version

1. **New Protocol**: NDJSON with standardized request/response envelopes
2. **Request IDs**: All commands include request IDs for tracking
3. **Idempotency**: Support for idempotency keys to prevent duplicate operations
4. **New Tools**: Added atomic scene operations (create_primitive, set_transform, etc.)
5. **Next.js Export**: Complete bundle export with manifest and R3F components
6. **Modular Tools**: Tools organized in separate modules for better maintainability

## Testing

To test the connection:

1. Start Blender with the addon running
2. Run the MCP server: `uvx blender-mcp`
3. In Claude/Cursor, try: "Get the current scene information"

The agent should be able to connect and retrieve scene data successfully.