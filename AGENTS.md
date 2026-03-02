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
