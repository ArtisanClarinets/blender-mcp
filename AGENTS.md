# AGENTS.md - Blender MCP Development Guide

## Project Overview

BlenderMCP connects Blender to AI assistants (Claude, etc.) through the Model Context Protocol (MCP). The project consists of:

- **MCP Server** (`src/blender_mcp/server.py`): Main Python server implementing MCP protocol using `FastMCP`
- **Blender Addon** (`blender_mcp_addon/`): Packaged addon that runs inside Blender, creates socket server on port 9876
- **Pipeline Domain** (`src/blender_mcp/pipeline/`): Durable file-backed storage for production entities
- **Telemetry** (`src/blender_mcp/telemetry.py`): Anonymous usage tracking (privacy-focused)

## Architecture

### MCP Protocol vs Internal Blender Protocol

**Important**: This project uses TWO distinct protocols:

1. **MCP Protocol** (External): The Model Context Protocol that AI assistants use to communicate with this server
   - Transport: stdio (via MCP SDK)
   - Format: JSON-RPC based
   - Features: Tools, Prompts, Resources, Completions

2. **Internal Blender Socket Protocol** (Internal): JSON-over-TCP between Python server and Blender addon
   - Transport: TCP sockets (localhost:9876)
   - Format: Newline-delimited JSON (NDJSON)
   - Features: Command dispatch, scene manipulation

The MCP server translates MCP tool calls into internal socket commands sent to the Blender addon.

### Package Structure

```
src/blender_mcp/
├── server.py              # Main MCP server with tools, prompts, resources
├── mcp_compat.py          # MCP SDK compatibility layer
├── tool_registry.py       # Tool discovery and registry
├── schemas.py             # Pydantic schemas for validation
├── protocol.py            # Protocol dataclasses
├── response.py            # Response helpers
├── resources.py           # MCP resources implementation
├── completions.py         # MCP completions implementation
├── core/
│   ├── connection.py      # Blender socket connection
│   └── tool_loader.py     # Dynamic tool module loading
├── pipeline/              # Pipeline domain
│   ├── entities.py        # Project, Shot, Asset, Publish entities
│   ├── storage.py         # File-backed storage
│   ├── lineage.py         # Publish lineage tracking
│   ├── publishes.py       # Publish management
│   ├── usd.py             # USD scaffolding
│   ├── color.py           # OCIO/ACES scaffolding
│   └── tracker.py         # Tracker adapter abstraction
└── tools/                 # MCP tool implementations
    ├── observe.py         # Scene observation
    ├── scene_ops.py       # Scene operations
    ├── production.py      # Production tools (scene-local)
    ├── pipeline_tools.py  # Pipeline tools (durable storage)
    ├── usd_tools.py       # USD tools
    ├── color_tools.py     # Color pipeline tools
    └── tracker_tools.py   # Tracker integration tools
```

## Build & Development Commands

### Installation

```bash
# Install in development mode with uv
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Running the Server

```bash
# Run directly
python -m blender_mcp.server

# Or use the installed script
blender-mcp

# Via uvx (for distribution)
uvx blender-mcp
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_pipeline_entities.py

# Run with coverage
pytest --cov=blender_mcp
```

### Linting & Type Checking

```bash
# Run ruff
ruff check src/
ruff format src/

# Run mypy
mypy src/
```

## MCP Feature Surface

### Tools

Tools are defined in `src/blender_mcp/tools/` and registered via `@mcp.tool()` decorator.

Categories:
- **Observation**: `get_scene_info`, `observe_scene`, `get_object_info`
- **Scene Operations**: `create_primitive`, `set_transform`, `assign_material`
- **Assets**: PolyHaven, Sketchfab, AI generation (Hyper3D, Hunyuan3D)
- **Lighting**: `create_three_point_lighting`, `create_area_light`
- **Camera**: `create_composition_camera`, `set_active_camera`
- **Materials**: `create_bsdf_material`, `create_metal_material`
- **Export**: `export_glb`, `export_scene_bundle`
- **Production**: `create_shot`, `create_shot_version`, `review_shot`
- **Pipeline**: `create_project`, `create_shot_pipeline`, `create_publish_pipeline`
- **USD**: `build_usd_asset_manifest`, `export_usd_asset_package`
- **Color**: `get_color_pipeline`, `set_project_color_pipeline`
- **Tracker**: `get_tracker_status`, `sync_project_context`

### Prompts

Prompts provide strategy guidance for agents:

- `asset_creation_strategy`: Preferred strategy for sourcing assets
- `production_pipeline_strategy`: Shot management and versioning workflow
- `animation_rigging_strategy`: Rigging and animation approach
- `autonomous_production_workflow`: End-to-end production workflow

### Resources

Resources expose machine-readable state:

**Static Resources:**
- `catalog://tools` - Tool catalog
- `catalog://commands` - Command catalog
- `catalog://schemas` - Schema catalog
- `catalog://protocol` - Protocol capabilities
- `catalog://pipeline` - Pipeline capabilities
- `scene://current` - Current scene state
- `scene://selection` - Selected objects
- `pipeline://projects` - Pipeline projects
- `pipeline://status` - Pipeline status
- `publish://status` - Publish system status
- `ocio://status` - Color pipeline status
- `usd://status` - USD system status

**Resource Templates:**
- `repo://tree/{path}` - Repository tree
- `repo://file/{path}` - Repository file
- `scene://object/{object_name}` - Scene object
- `pipeline://project/{project_code}` - Project details
- `pipeline://sequence/{sequence_code}` - Sequence details
- `pipeline://shot/{shot_name}` - Shot details
- `pipeline://asset/{asset_type}/{asset_name}` - Asset details
- `publish://entity/{entity_type}/{entity_id}` - Entity publishes
- `publish://manifest/{publish_id}` - Publish manifest
- `ocio://project/{project_code}` - Project color config
- `usd://package/{package_id}` - USD package

### Completions

Completions provide suggestions for:

- Project codes
- Sequence codes
- Shot names
- Asset types and names
- Object names
- Colorspaces
- Tracker adapters

## Pipeline Domain

The pipeline domain provides durable file-backed storage for production entities.

### Entities

- **Project**: Production project with color config
- **Sequence**: Sequence within a project
- **Shot**: Shot within a sequence
- **Asset**: Asset (character, prop, environment, etc.)
- **Publish**: Published version of an entity
- **USDPackage**: USD package metadata

### Storage Layout

```
~/.blender_mcp/pipeline/
├── projects/
│   └── {project_code}/
│       ├── project.json
│       ├── sequences/{sequence_code}.json
│       ├── shots/{shot_name}.json
│       ├── assets/{asset_type}/{asset_name}/asset.json
│       └── config/color_pipeline.json
├── publishes/
│   ├── {publish_id}.json
│   └── {entity_type}/{entity_id}/v{version:03d}.json
├── workfiles/
├── reviews/
├── usd/
└── tracker/
```

### Usage

```python
from blender_mcp.pipeline import get_pipeline_storage, get_publish_manager

# Get storage
storage = get_pipeline_storage()

# Create project
from blender_mcp.pipeline.entities import Project
project = Project(code="MYPROJECT", name="My Project")
storage.create_project(project)

# Create publish
manager = get_publish_manager()
publish = manager.create_publish(
    entity_type="shot",
    entity_id="sh010",
    stage="layout",
    description="Initial layout",
)
```

## USD Scaffolding

USD support is provided as scaffolding that works with or without the USD library.

### With USD Library (pxr.Usd)

Full USD file generation is available.

### Without USD Library

Placeholder files and manifests are created for future USD processing.

### Usage

```python
from blender_mcp.pipeline.usd import get_usd_adapter

adapter = get_usd_adapter()

# Build manifest
manifest = adapter.build_asset_manifest(
    asset_id="hero_char",
    asset_name="hero",
    asset_type="character",
    version=1,
)

# Export package
package = adapter.export_asset_package(
    asset_id="hero_char",
    asset_name="hero",
    asset_type="character",
    output_dir="/path/to/output",
)
```

## Color Pipeline (OCIO/ACES)

Color pipeline configuration with ACES support.

### Features

- Project-level color config
- Working/render/display colorspace management
- Texture colorspace tagging
- OCIO config template generation

### Usage

```python
from blender_mcp.pipeline.color import get_color_adapter

adapter = get_color_adapter()

# Get config
config = adapter.get_color_pipeline("MYPROJECT")

# Set config
adapter.set_project_color_pipeline(
    project_code="MYPROJECT",
    working_colorspace="ACES - ACEScg",
    render_colorspace="ACES - ACEScg",
)

# Validate
result = adapter.validate_color_pipeline("MYPROJECT")
```

## Tracker Integration

Abstracted tracker integration supporting multiple backends.

### Adapters

- **local**: File-based tracker (default)
- **shotgrid**: Autodesk ShotGrid (placeholder)
- **ayon**: Ynput AYON (placeholder)
- **ftrack**: ftrack Studio (placeholder)

### Usage

```python
from blender_mcp.pipeline.tracker import get_tracker_adapter, set_tracker_adapter

# Set adapter
adapter = set_tracker_adapter("local")

# Connect
adapter.connect()

# Get projects
projects = adapter.get_projects()
```

## Code Style Guidelines

### Language

- Python 3.10+ (check `.python-version`)
- Type hints required for function signatures

### Imports

```python
# Standard library first
import json
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
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_HOST`)
- **Private members**: Leading underscore (e.g., `_blender_connection`)

### MCP Tool Implementation

```python
@telemetry_tool("tool_name")
@mcp.tool()
async def my_tool(ctx: Context, param: str) -> str:
    """
    Description of what the tool does.
    
    Parameters:
    - param: Description of parameter
    
    Returns:
    - JSON string with result
    """
    try:
        # Implementation
        result = {"success": True, "data": ...}
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error: {e}")
        return json.dumps({"error": str(e)})
```

## Adding New MCP Tools

### Step 1: Define the Tool Function

Add to appropriate module in `src/blender_mcp/tools/`:

```python
@telemetry_tool("new_tool_name")
@mcp.tool()
async def new_tool(ctx: Context, parameter: str) -> str:
    """Short description of tool."""
    try:
        from ..core.connection import get_blender_connection
        blender = get_blender_connection()
        result = blender.send_command("command_name", {"param": parameter})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error: {e}")
        return json.dumps({"error": str(e)})
```

### Step 2: Update Tool Loader

Add module name to `src/blender_mcp/core/tool_loader.py`:

```python
TOOL_MODULES = [
    # ... existing modules
    "new_module",
]
```

### Step 3: Update Blender Addon (if needed)

Add corresponding command handler in `blender_mcp_addon/command_registry.py`:

```python
COMMAND_HANDLERS = {
    # ... existing handlers
    "command_name": _attr(module, "handler_function"),
}
```

### Step 4: Add Schema (optional)

Add Pydantic schema to `src/blender_mcp/schemas.py` if strict validation needed.

### Step 5: Test

Add tests to `tests/test_new_module.py`.

## Environment Variables

- `BLENDER_HOST`: Blender socket host (default: "localhost")
- `BLENDER_PORT`: Blender socket port (default: 9876)
- `BLENDER_MCP_PIPELINE_ROOT`: Pipeline storage root path
- `DISABLE_TELEMETRY`: Disable all telemetry

## Key Files

- `src/blender_mcp/server.py` - MCP server initialization
- `src/blender_mcp/mcp_compat.py` - MCP SDK compatibility
- `src/blender_mcp/resources.py` - MCP resources
- `src/blender_mcp/completions.py` - MCP completions
- `src/blender_mcp/tool_registry.py` - Tool discovery
- `src/blender_mcp/schemas.py` - Validation schemas
- `src/blender_mcp/pipeline/` - Pipeline domain
- `blender_mcp_addon/command_registry.py` - Addon command handlers
- `blender_mcp_addon/server.py` - Addon socket server
- `blender_mcp_addon/protocol.py` - Internal protocol

## Testing

### Unit Tests

```bash
pytest tests/test_pipeline_entities.py -v
pytest tests/test_pipeline_storage.py -v
pytest tests/test_mcp_resources.py -v
```

### Integration Tests

```bash
# Requires Blender running with addon
pytest tests/test_server_transport.py -v
```

## Debugging Tips

### Connection Issues

- Verify Blender addon is running (port 9876)
- Check `BLENDER_HOST` and `BLENDER_PORT` env vars
- Test with simple `get_scene_info` command first

### Resource Issues

- Check pipeline storage root exists and is writable
- Verify project/sequence/shot entities exist before referencing

### Tool Failures

- Check tool is registered: `catalog://tools` resource
- Verify addon command handler exists
- Review logs for error details

## Version Compatibility

- Blender 3.0+ required
- Python 3.10+ required
- MCP 1.3.0+ required

## License

MIT License - see LICENSE file for details
