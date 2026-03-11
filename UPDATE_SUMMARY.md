# Blender MCP Update Summary

This document summarizes all the changes made to update Blender MCP according to the specifications.

## Summary of Changes

### A) Root-level Files

#### ✅ MODIFIED: `README.md`
- Added "Autonomous workflow" section with recommended agent loop
- Added "Next.js 16 export" section with output folder convention
- Added troubleshooting section covering ports, Blender addon, file permissions

#### ✅ MODIFIED: `AGENTS.md`
- Replaced "Claude-specific" language with "agent-neutral" terminology
- Added autonomous agent guidelines:
  - "Never use execute_blender_code unless needed"
  - "Prefer atomic tools"
  - "Use request_id + idempotency keys"
  - "Verify changes via scene hash + screenshot"
- Added agent loop pattern documentation
- Added Next.js 16 integration section
- Added debugging tips and version compatibility info

#### ✅ MODIFIED: `pyproject.toml`
- Fixed metadata (author: Siddharth Ahuja)
- Added package data configuration
- Added setuptools package discovery

#### ✅ MODIFIED: `.gitignore`
- Added `dist/`, `build/`
- Added `.env`
- Added `exports/`, `out/`, `public/3d/`
- Added `__pycache__/` and other Python artifacts
- Added IDE files and OS generated files

#### 🧹 REMOVED: `.DS_Store`
- Deleted macOS artifact from repo

---

### B) Python MCP Server Package (`src/blender_mcp/*`)

#### ✅ ADDED: `src/blender_mcp/config.py`
- Defines `TelemetryConfig` and `BlenderMCPConfig` dataclasses
- Supports environment variable overrides:
  - `BLENDER_MCP_TELEMETRY_ENABLED`
  - `BLENDER_MCP_SUPABASE_URL`, `BLENDER_MCP_SUPABASE_KEY`
  - `BLENDER_HOST`, `BLENDER_PORT`
  - `DISABLE_TELEMETRY`
  - Export settings

#### ✅ ADDED: `src/blender_mcp/protocol.py`
- Defines `CommandEnvelope`: `{type, params, request_id, idempotency_key?}`
- Defines `ResponseEnvelope`: `{ok, data, error, request_id, meta}`
- Defines data structures:
  - `SceneInfo`, `ObjectInfo`, `Transform`
  - `MaterialSpec`, `ExportManifest`
  - `JobInfo`, `ViewportScreenshot`, `GLBExportSettings`

#### ✅ ADDED: `src/blender_mcp/response.py`
- Helper functions:
  - `ok(data, meta, request_id)` - Create success response
  - `err(code, message, details, request_id)` - Create error response
  - `normalize_exception(e)` - Convert exception to response
- `ResponseBuilder` class for building responses with timing

#### ✅ MODIFIED: `src/blender_mcp/telemetry.py`
- Now imports `telemetry_config` from new `config.py`
- Telemetry disabled is now silent, not noisy
- Respects environment variable configuration

#### ✅ MODIFIED: `src/blender_mcp/__init__.py`
- Set `__version__` to "1.5.5" to match pyproject.toml

#### ✅ ADDED: `src/blender_mcp/tools/__init__.py`
- Package initialization for modular tools

#### ✅ ADDED: `src/blender_mcp/tools/observe.py`
- `observe_scene(detail, include_screenshot, max_screenshot_size)`
- `get_scene_hash()`
- `get_scene_info()`
- `get_object_info(object_name)`
- `get_viewport_screenshot(max_size)`
- `get_selection()`

#### ✅ ADDED: `src/blender_mcp/tools/scene_ops.py`
- `create_primitive(type, name, size, location, rotation, scale)`
- `create_empty(name, location)`
- `create_camera(name, lens, location, look_at)`
- `create_light(type, energy, color, location, rotation)`
- `set_transform(target_id, location, rotation, scale, apply)`
- `select_objects(ids, mode)`
- `delete_objects(ids)`
- `duplicate_object(id, linked, count)`
- `assign_material_pbr(target_id, material_spec)`
- `set_world_hdri(asset_id, resolution)`
- `execute_blender_code(code)`

#### ✅ ADDED: `src/blender_mcp/tools/assets.py`
- PolyHaven: `get_polyhaven_status`, `get_polyhaven_categories`
- PolyHaven: `search_polyhaven_assets`, `download_polyhaven_asset`
- PolyHaven: `set_texture`
- Sketchfab: `get_sketchfab_status`, `search_sketchfab_models`
- Sketchfab: `get_sketchfab_model_preview`, `download_sketchfab_model`

#### ✅ ADDED: `src/blender_mcp/tools/export.py`
- `export_glb(target, name, output_dir, draco, texture_embed, y_up)`
- `render_preview(camera, output_path, resolution)`
- `export_scene_bundle(slug, nextjs_project_root, mode, generate_r3f)`

#### ✅ ADDED: `src/blender_mcp/tools/jobs.py`
- Unified job API: `create_job`, `get_job`, `import_job_result`
- Hyper3D: `get_hyper3d_status`, `generate_hyper3d_model_via_text`
- Hyper3D: `generate_hyper3d_model_via_images`, `poll_rodin_job_status`
- Hyper3D: `import_generated_asset`
- Hunyuan3D: `get_hunyuan3d_status`, `generate_hunyuan3d_model`
- Hunyuan3D: `poll_hunyuan_job_status`, `import_generated_asset_hunyuan`

---

### C) Blender Addon Package (`blender_mcp_addon/*`)

#### ✅ CREATED: `blender_mcp_addon/__init__.py`
- Main addon entry point with `bl_info`
- Version 1.5.5
- Module registration

#### ✅ CREATED: `blender_mcp_addon/protocol.py`
- Mirrors Python server protocol
- `encode_command()` - JSON + newline encoding
- `decode_response()` - Parse response
- `create_response()`, `create_success_response()`, `create_error_response()`
- `parse_command()` - Validate incoming commands
- `get_command_type()`, `get_command_params()`, `get_request_id()`, `get_idempotency_key()`

#### ✅ CREATED: `blender_mcp_addon/server.py`
- `BlenderMCPServer` class
- TCP socket server with NDJSON framing
- Command dispatch system
- Idempotency cache
- Main thread execution via `bpy.app.timers`

#### ✅ CREATED: `blender_mcp_addon/id.py`
- UUID assignment for stable object IDs
- `assign_uuid()`, `get_uuid()`
- `resolve_id()`, `resolve_multiple_ids()`
- `get_object_info_with_uuid()`

#### ✅ CREATED: `blender_mcp_addon/utils.py`
- `ensure_dir()`, `write_json()`, `read_json()`
- `compute_hash()` - Stable hash for scene state
- `get_temp_dir()`, `safe_filename()`
- `format_error()`, `get_scene_bounds()`

#### ✅ CREATED: `blender_mcp_addon/ui.py`
- Blender sidebar panel
- Server start/stop buttons
- Integration toggles (PolyHaven, Sketchfab, Hyper3D, Hunyuan3D)
- Export directory picker
- Telemetry consent checkbox

#### ✅ CREATED: `blender_mcp_addon/handlers/scene_observe.py`
- `observe_scene()` - Comprehensive scene observation
- `get_scene_hash()` - Stable scene hash
- `get_scene_info()` - Scene overview
- `get_object_info()` - Object details
- `get_viewport_screenshot()` - Screenshot capture
- `get_selection()` - Selection info

#### ✅ CREATED: `blender_mcp_addon/handlers/scene_ops.py`
- All atomic scene operations
- Primitives, empties, cameras, lights
- Transform, selection, deletion, duplication
- Material assignment, HDRI setting
- Code execution

#### ✅ CREATED: `blender_mcp_addon/handlers/export_handler.py`
- `export_glb()` - GLB export with settings
- `render_preview()` - Preview rendering
- `export_scene_bundle()` - Complete Next.js bundle
- `generate_manifest()` - Manifest generation
- `generate_r3f_components()` - R3F component generation

#### ✅ CREATED: `blender_mcp_addon/handlers/assets_polyhaven.py`
- PolyHaven integration handlers

#### ✅ CREATED: `blender_mcp_addon/handlers/assets_sketchfab.py`
- Sketchfab integration handlers

#### ✅ CREATED: `blender_mcp_addon/handlers/jobs_hyper3d.py`
- Hyper3D job management
- Unified job API implementation

#### ✅ CREATED: `blender_mcp_addon/handlers/jobs_hunyuan.py`
- Hunyuan3D job management
- Unified job API implementation

---

### D) Skills & Agent Integration (`skills/*`)

#### ✅ MODIFIED: `skills/blender_mcp.json`
- Added all new tool definitions
- Updated with new atomic tools (observe, scene_ops, export, jobs)
- Added "tool_return_schema" section
- Updated notes with best practices

#### ✅ MODIFIED: `skills/blender_mcp_client.py`
- Updated `BlenderMCPClient.send_command()` with request_id and idempotency_key
- Added newline-delimited JSON framing
- Updated `TOOLS` dictionary with all new tools
- Updated `call_tool()` to handle new response envelope format
- Added request_id generation by default

---

### E) Next.js 16 Integration (`packages/nextjs-integration/*`)

#### ✅ CREATED: `packages/nextjs-integration/package.json`
- Package configuration
- Peer dependencies for Next.js 16, React Three Fiber
- Dev dependencies for TypeScript

#### ✅ CREATED: `packages/nextjs-integration/tsconfig.json`
- TypeScript configuration
- ES2020 target with DOM lib
- JSX support

#### ✅ CREATED: `packages/nextjs-integration/src/index.ts`
- `loadBlenderManifest()` - Load manifest from public directory
- `resolvePublicAssetPaths()` - Get asset paths
- `getSceneBounds()` - Get scene bounds
- `getDefaultCamera()` - Get default camera
- `getLights()` - Get lights
- `preloadSceneAssets()` - Preload assets

#### ✅ CREATED: `packages/nextjs-integration/src/manifest.ts`
- `BlenderManifest` type definition with Zod schema
- `ManifestObject`, `ManifestCamera`, `ManifestLight` types
- `validateManifest()` - Validate manifest data
- `safeValidateManifest()` - Safe validation
- `getObjectByName()`, `getObjectById()`
- `getCameraByName()`, `getLightByName()`
- `getSceneCenter()`, `getSceneRadius()`

#### ✅ CREATED: `packages/nextjs-integration/src/r3f.ts`
- Type definitions for R3F components
- `generateModelComponent()` - Generate Model.tsx code
- `generateCameraComponent()` - Generate Camera.tsx code
- `generateSceneComponent()` - Generate Scene.tsx code
- `generateR3FComponents()` - Generate all components

---

### F) Documentation (`docs/*`, `.github/*`, `.cursor/*`)

#### ✅ CREATED: `docs/PROTOCOL.md`
- Complete protocol specification
- Command/response envelope definitions
- Framing rules (newline-delimited JSON)
- Idempotency rules
- Command type reference
- Error codes
- Examples

#### ✅ CREATED: `docs/NEXTJS_EXPORT.md`
- Output folder layout
- Usage examples
- Manifest format documentation
- R3F component examples
- Next.js page examples
- Dynamic import patterns
- Cache invalidation strategies
- Best practices

#### ✅ CREATED: `docs/AGENT_PLAYBOOK.md`
- Golden path for autonomous creation
- Observe-Act-Observe loop pattern
- Step-by-step workflow
- Best practices
- Common patterns
- Error handling
- Performance tips

#### ✅ CREATED: `.github/copilot-instructions.md`
- Core principles for GitHub Copilot
- Tool selection guide
- Common mistakes to avoid
- Response handling
- Testing guidelines

#### ✅ CREATED: `.cursor/rules`
- Cursor IDE rules
- Agent guidelines
- Tool selection guide
- Common mistakes to avoid

---

## Installation Instructions for Blender 5.0.1

To install the addon in Blender 5.0.1:

1. **Zip the addon package:**
   ```bash
   cd blender-mcp
   zip -r blender_mcp_addon.zip blender_mcp_addon/
   ```

2. **Install in Blender:**
   - Open Blender 5.0.1
   - Go to Edit > Preferences > Add-ons
   - Click "Install..."
   - Select `blender_mcp_addon.zip`
   - Enable the addon by checking "Interface: Blender MCP"

3. **Start the server:**
   - Open the 3D View sidebar (press N)
   - Find the "BlenderMCP" tab
   - Click "Start Server"

4. **Connect from Python MCP:**
   - The MCP server will connect automatically on port 9876

---

## File Structure Summary

```
blender-mcp/
├── README.md                          ✅ Updated
├── AGENTS.md                          ✅ Updated
├── pyproject.toml                     ✅ Updated
├── .gitignore                         ✅ Updated
├── .DS_Store                          🧹 Removed
├── main.py                            ✅ Kept (no changes needed)
├── src/blender_mcp/
│   ├── __init__.py                    ✅ Updated version
│   ├── server.py                      ✅ Kept (needs update for tools)
│   ├── telemetry.py                   ✅ Updated
│   ├── telemetry_decorator.py         ✅ Kept
│   ├── config.py                      ✅ Added
│   ├── protocol.py                    ✅ Added
│   ├── response.py                    ✅ Added
│   └── tools/                         ✅ Added
│       ├── __init__.py
│       ├── observe.py
│       ├── scene_ops.py
│       ├── assets.py
│       ├── export.py
│       └── jobs.py
├── blender_mcp_addon/                 ✅ Added (complete addon package)
│   ├── __init__.py
│   ├── protocol.py
│   ├── server.py
│   ├── id.py
│   ├── utils.py
│   ├── ui.py
│   └── handlers/
│       ├── scene_observe.py
│       ├── scene_ops.py
│       ├── export_handler.py
│       ├── assets_polyhaven.py
│       ├── assets_sketchfab.py
│       ├── jobs_hyper3d.py
│       └── jobs_hunyuan.py
├── skills/
│   ├── blender_mcp.json               ✅ Updated
│   └── blender_mcp_client.py          ✅ Updated
├── docs/                              ✅ Added
│   ├── PROTOCOL.md
│   ├── NEXTJS_EXPORT.md
│   └── AGENT_PLAYBOOK.md
├── .github/                           ✅ Added
│   └── copilot-instructions.md
├── .cursor/                           ✅ Added
│   └── rules
└── packages/nextjs-integration/       ✅ Added
    ├── package.json
    ├── tsconfig.json
    └── src/
        ├── index.ts
        ├── manifest.ts
        └── r3f.ts
```

---

## Key Features Implemented

1. **Deterministic structured tool outputs** - All tools return JSON with consistent envelope
2. **Observe → Act → Observe loop** - `observe_scene`, scene hash, selection tools
3. **Atomic scene ops** - Create primitives, lights, cameras, transforms, materials
4. **Job model** - Unified async job API for Hyper3D/Hunyuan3D
5. **Export pipeline for Next.js** - GLB export, manifest.json, preview.png, R3F components
6. **Protocol specification** - Formal command/response envelopes with idempotency
7. **Connection safety** - Thread-safe socket handling with locks
8. **Telemetry configuration** - Environment-based configuration

---

## Next Steps

1. **Update `src/blender_mcp/server.py`** to register the new tools from the tools package
2. **Test the addon** in Blender 5.0.1
3. **Test the MCP server** connection
4. **Test Next.js export** functionality
5. **Add unit tests** for the new modules
6. **Update documentation** with more examples