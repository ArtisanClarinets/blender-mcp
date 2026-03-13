# AGENTS.md - Blender MCP Development Guide

## Project Overview

BlenderMCP connects Blender to AI assistants (Claude, etc.) through the Model Context Protocol (MCP). The project consists of:
- **MCP Server** (`src/blender_mcp/server.py`): Main Python server implementing MCP protocol using `FastMCP`
- **Blender Addon** (`addon.py`): Runs inside Blender, creates socket server on port 9876
- **Telemetry** (`src/blender_mcp/telemetry.py`): Anonymous usage tracking (privacy-focused)

## Build & Development Commands

### Installation
```bash
# Install in development mode with uv
uv pip install -e .

# Install with all dependencies
uv pip install -e ".[dev]" 2>/dev/null || uv pip install -e .
```

### Running the Server
```bash
# Run directly
python main.py

# Or use the installed script
blender-mcp

# Via uvx (for distribution)
uvx blender-mcp
```

### Testing
This project has **no formal test framework** yet. When adding tests:
```bash
# Install pytest
uv pip install pytest pytest-asyncio

# Run all tests
pytest

# Run single test file
pytest tests/test_server.py

# Run single test
pytest tests/test_server.py::test_function_name
```

### Linting & Type Checking
Currently **no linting tools configured**. Consider adding:
```bash
# Install linting tools
uv pip install ruff mypy

# Run ruff
ruff check src/

# Run mypy
mypy src/
```

## Code Style Guidelines

### Language
- Python 3.10+ (check `.python-version`)
- Type hints required for function signatures

### Imports
```python
# Standard library first
import socket
import json
import asyncio
from typing import Dict, Any, List

# Then third-party
from mcp.server.fastmcp import FastMCP, Context, Image

# Then local
from .telemetry import record_startup
from .telemetry_decorator import telemetry_tool
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `BlenderConnection`)
- **Functions/Variables**: `snake_case` (e.g., `get_blender_connection`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_HOST`, `DEFAULT_PORT`)
- **Private members**: Leading underscore (e.g., `_blender_connection`)

### Error Handling
```python
try:
    result = blender.send_command("command", params)
except Exception as e:
    logger.error(f"Error doing something: {str(e)}")
    return f"Error doing something: {str(e)}"
```
- Always log errors with descriptive messages
- Return user-friendly error messages from tool functions
- Let exceptions propagate for unexpected failures

### MCP Tool Implementation
```python
@telemetry_tool("tool_name")
@mcp.tool()
def my_tool(ctx: Context, param: str) -> str:
    """
    Description of what the tool does.

    Parameters:
    - param: Description of parameter
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("command", {"key": param})
        return f"Success: {result}"
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return f"Error: {str(e)}"
```

### Logging
```python
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BlenderMCPServer")
```

## Adding New MCP Tools

### Step 1: Define the Tool Function
Add to `src/blender_mcp/server.py`:
```python
@telemetry_tool("new_tool_name")
@mcp.tool()
def new_tool(ctx: Context, parameter: str) -> str:
    """Short description of tool."""
    try:
        blender = get_blender_connection()
        result = blender.send_command("command_name", {"param": parameter})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return f"Error: {str(e)}"
```

### Step 2: Update Blender Addon
Add corresponding command handler in `addon.py`:
```python
elif command_type == "command_name":
    # Execute Blender API calls
    return {"status": "success", "result": {...}}
```

### Step 3: Update Documentation
- Update `asset_creation_strategy()` prompt in `server.py`
- Update `README.md` with new capabilities

## Architecture Patterns

### Connection Management
- Single global `BlenderConnection` instance (`_blender_connection`)
- Lazy connection with auto-reconnect via `get_blender_connection()`
- Default host: `localhost`, port: `9876`

### Command Protocol
JSON over TCP sockets:
```python
# Send
{"type": "command_name", "params": {"key": "value"}}

# Receive
{"status": "success", "result": {...}}
# OR
{"status": "error", "message": "error description"}
```

### Telemetry
- Anonymous tracking via Supabase
- Disabled via `DISABLE_TELEMETRY`, `BLENDER_MCP_DISABLE_TELEMETRY`, or `MCP_DISABLE_TELEMETRY`
- Decorate tools with `@telemetry_tool("tool_name")`

## Environment Variables
- `BLENDER_HOST`: Blender socket host (default: "localhost")
- `BLENDER_PORT`: Blender socket port (default: 9876)
- `DISABLE_TELEMETRY`: Disable all telemetry

## Key Files
- `src/blender_mcp/server.py:208` - MCP server initialization
- `src/blender_mcp/server.py:19` - BlenderConnection class
- `src/blender_mcp/server.py:219` - get_blender_connection()
- `addon.py` - Blender addon (111KB, socket server)
- `skills/blender_mcp_client.py` - Agent MCP client tool
- `skills/blender_mcp.json` - Tool definitions for agent integration

## Agent Tool Integration

### Using the Blender MCP Client
Agents can use `skills/blender_mcp_client.py` to call Blender MCP tools:

```python
from skills.blender_mcp_client import call_tool, TOOLS

# Get available tools
print(TOOLS.keys())

# Call a tool
result = call_tool("get_scene_info")
result = call_tool("get_object_info", {"object_name": "Cube"})
result = call_tool("download_sketchfab_model", {"uid": "model123", "target_size": 1.0})
```

### Tool Categories

**Scene & Object Inspection:**
- `get_scene_info()` - Get scene overview
- `get_object_info(object_name)` - Get object details
- `get_viewport_screenshot(max_size)` - Capture viewport

**Code Execution:**
- `execute_blender_code(code)` - Run Python in Blender

**PolyHaven Integration:**
- `get_polyhaven_status()` - Check if enabled
- `get_polyhaven_categories(asset_type)` - List categories
- `search_polyhaven_assets(asset_type, categories)` - Search assets
- `download_polyhaven_asset(asset_id, asset_type, resolution)` - Import asset
- `set_texture(object_name, texture_id)` - Apply texture

**Sketchfab Integration:**
- `get_sketchfab_status()` - Check if enabled
- `search_sketchfab_models(query, categories, count, downloadable)` - Search
- `get_sketchfab_model_preview(uid)` - Get thumbnail
- `download_sketchfab_model(uid, target_size)` - Import model

**Hyper3D Rodin (AI Generation):**
- `get_hyper3d_status()` - Check if enabled
- `generate_hyper3d_model_via_text(text_prompt, bbox_condition)` - Generate from text
- `generate_hyper3d_model_via_images(input_image_paths, input_image_urls, bbox_condition)` - Generate from images
- `poll_rodin_job_status(subscription_key, request_id)` - Check status
- `import_generated_asset(name, task_uuid, request_id)` - Import result

**Hunyuan3D (AI Generation):**
- `get_hunyuan3d_status()` - Check if enabled
- `generate_hunyuan3d_model(text_prompt, input_image_url)` - Generate model
- `poll_hunyuan_job_status(job_id)` - Check job status
- `import_generated_asset_hunyuan(name, zip_file_url)` - Import result

## MCP Prompts and When to Use Them

The server exposes strategy prompts that agents should use for different workflows:

- **asset_creation_strategy** – Use when creating or sourcing 3D assets (models, materials, HDRIs). Prefer PolyHaven, Sketchfab, Hyper3D, Hunyuan3D; fall back to code only when necessary.
- **production_pipeline_strategy** – Use when managing shots, versions, and review: create_shot, setup_shot_camera, create_shot_version, review_shot, create_render_job, monitor_render_job.
- **animation_rigging_strategy** – Use when rigging characters and animating: get_rigging_status/get_animation_status, create_auto_rig, set_keyframe, create_animation_layer, etc.
- **autonomous_production_workflow** – Use for end-to-end production: observe → create shot → layout (assets, camera, lighting) → rigging/animation → shot versions → render setup → review. Emphasizes observe → plan → act → observe and idempotency.

### Command timeouts and idempotency

- **Timeouts**: The addon uses a base command timeout (default 30s, set via `BLENDER_MCP_CMD_TIMEOUT`). Render and export commands get a longer timeout (up to 300s). Clients can pass `timeout_sec` in params (capped at 600s) for heavy operations.
- **Idempotency**: Pass `idempotency_key` when calling `send_command()` (or equivalent from tools) for create_shot, create_render_job, and other operations that should be safe to retry. The addon caches responses by key and returns the cached result for duplicate requests.

### Production and render pipeline workflow

1. Check `get_production_status()` and `get_render_pipeline_status()`.
2. Create shots with `create_shot()`; set up cameras with `setup_shot_camera()`.
3. Use `create_shot_version()` for layout, animation, lighting, render iterations.
4. Use `create_render_job()` and `monitor_render_job()` for local queue; use export_render_manifest (when available) for farm handoff.
5. Use `review_shot()` to record approval or feedback.

### Export options

- **GLB / Next.js**: `export_glb`, `export_scene_bundle` (GLB with Draco, manifest, preview, optional R3F components).
- **Render**: `render_preview`, `setup_render_passes`, `render_animation_passes`; render jobs via `create_render_job`.
- **Pipeline** (when implemented): USD and Alembic export for interchange and farm rendering; render manifest for external runners.

## Autonomous Agent Guidelines

### Never use execute_blender_code unless needed
- Prefer atomic tools for predictable behavior
- Code execution should be last resort
- Complex operations should be broken down

### Prefer atomic tools
- Use specific tools like `create_primitive`, `set_transform` instead of code
- Atomic operations are easier to verify and debug
- Tools provide structured responses for chaining

### Use request_id + idempotency keys
- Include `request_id` in all commands
- Use idempotency keys for repeated operations
- Enables reliable retries and prevents duplicates

### Verify changes via scene hash + screenshot
- Always observe before and after changes
- Use `get_scene_hash()` to detect changes
- Capture screenshots to verify visual results

### Agent Loop Pattern
```
observe_scene → plan → act → observe_scene…```

### Error Handling
- Check tool status before execution
- Handle network errors gracefully
- Use retries with exponential backoff
- Provide meaningful error messages to users

### Performance Considerations
- Batch similar operations when possible
- Use scene hash to avoid unnecessary operations
- Cache results for repeated queries
- Consider network latency for remote connections

### Security
- Never expose sensitive credentials
- Validate user inputs before execution
- Use secure connections when available
- Monitor for suspicious activity patterns

## Next.js 16 Integration

BlenderMCP supports exporting scenes for Next.js 16 applications:

**Output Convention:**
```
your-next-app/public/3d/<slug>/
├── model.glb
├── preview.png
├── manifest.json
└── components/
    ├── Scene.tsx
    ├── Model.tsx
    └── Camera.tsx
```

**Key Features:**
- Export GLB with Draco compression
- Generate scene manifest with transforms, cameras, lights
- Render preview thumbnails
- Optional R3F component generation
- Cache invalidation support

### Integration Steps
1. Use `export_scene_bundle()` to export scene
2. Import into Next.js project
3. Use generated components in pages
4. Verify rendering with `observe_scene()`

## Debugging Tips

### Connection Issues
- Verify Blender addon is running
- Check port 9876 availability
- Test with simple commands first
- Check firewall settings

### Tool Failures
- Verify required integrations are enabled
- Check API keys and credentials
- Test with minimal parameters
- Review error messages in logs

### Performance Issues
- Monitor network latency
- Check Blender memory usage
- Optimize scene complexity
- Use caching for repeated operations

## Contributing

When adding new features:
1. Update tool definitions in `skills/blender_mcp.json`
2. Add corresponding client functions
3. Update documentation
4. Test with autonomous agent patterns
5. Verify Next.js export compatibility

## Version Compatibility

- Blender 3.0+ required
- Python 3.10+ required
- MCP 1.3.0+ required
- Next.js 16+ for export features

## License

MIT License - see LICENSE file for details
