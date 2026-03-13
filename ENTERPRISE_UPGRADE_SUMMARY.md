# Enterprise Upgrade Summary

## Structural fixes completed

- Replaced hard-coded MCP tool imports with dynamic tool discovery and registration.
- Introduced `src/blender_mcp/tool_registry.py` as the source of truth for the Python-side tool surface.
- Introduced `blender_mcp_addon/command_registry.py` as the source of truth for Blender-side command dispatch.
- Repaired package import coupling so `blender_mcp` no longer imports the full server on package import.
- Aligned package version metadata to `1.5.5`.
- Added safe `mcp` compatibility stubs for test and constrained environments.
- Repaired telemetry/config loading and removed missing-module crashes.
- Expanded payload validation to use registry-backed dynamic schemas, while keeping stricter manual schemas for core commands.
- Removed duplicate `create_subsurface_material` tool definition.
- Fixed protocol dataclass ordering bugs.
- Corrected sensitive-path log summarization for Windows-style paths.
- Replaced deprecated `datetime.utcnow()` usage in the legacy addon path.

## Studio-surface upgrades completed

- Added Blender-side production handlers for:
  - `create_shot`
  - `setup_shot_camera`
  - `create_shot_version`
  - `review_shot`
- Added Blender-side render pipeline handlers for:
  - `create_render_job`
  - `monitor_render_job`
  - `optimize_render_settings`
  - `setup_render_passes`
  - `render_animation_passes`
  - `setup_stereoscopic_render`
- Added Blender-side procedural material handlers for:
  - `generate_procedural_material`
  - `ai_generate_material`
  - `create_material_variations`
- Added Blender-side AI creative handlers for:
  - `ai_scene_composition`
  - `ai_lighting_design`
  - `ai_animation_assist`
  - `ai_quality_check`
- Wired existing advanced rigging, animation, atmospherics, and advanced material handlers into the canonical addon server dispatch.
- Added advanced lighting handlers for:
  - `create_hdri_lighting_setup`
  - `create_volumetric_light_effect`
  - `create_studio_light_rig`
  - `setup_light_linking`
- Added backend alias coverage so the Python MCP wrappers and Blender addon dispatch surface are synchronized.

## Tool surface synchronization

- Regenerated `skills/blender_mcp.json` from the live code surface.
- Added `scripts/generate_skill_manifest.py`.
- Added `scripts/build_addon_zip.py`.
- Updated installation docs to point at the packaged multi-file addon instead of the legacy single-file path.
- Added `docs/USER_GUIDE.md` and `docs/API_REFERENCE.md`.

## Verification

- Test suite status: `142 passed`
